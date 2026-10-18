import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import PayerAuthExceptionRule, ScheduledAppointment, AuditAlert
from mock_data import (
    RAW_PAYER_BULLETIN_TEXT,
    STRUCTURED_PAYER_RULES,
    UPCOMING_CLINIC_SCHEDULE,
)
from scanner import evaluate_appointment

app = FastAPI(
    title="Solum 'Headline Trap' Schedule Scanner API",
    description="Compiles payer prior-auth bulletins into multi-variable Pydantic rules and audits clinic schedules.",
    version="1.0.0",
)

# Enable CORS so our UI in Step 3 can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BulletinCompileRequest(BaseModel):
    bulletin_text: str

class ExtractedRuleSet(BaseModel):
    """Wrapper schema for Gemini structured output."""
    rules: List[PayerAuthExceptionRule]

class ScheduleScanResponse(BaseModel):
    compiler_mode: str
    extracted_rules: List[PayerAuthExceptionRule]
    alerts: List[AuditAlert]
    total_appointments_scanned: int
    traps_caught_count: int
    total_revenue_saved_usd: float


def compile_bulletin_with_gemini(bulletin_text: str) -> tuple[str, List[PayerAuthExceptionRule]]:
    """
    Uses Google GenAI SDK with Pydantic Structured Outputs to parse messy payer bulletins.
    Automatically falls back to deterministic rules if GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ("DETERMINISTIC_FALLBACK (Set GEMINI_API_KEY for live LLM parsing)", STRUCTURED_PAYER_RULES)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are a Healthcare Revenue Cycle AI Architect for Solum Health.
        Read the following Payer Policy Bulletin and extract every CPT code mentioned into 
        strict multi-variable Prior Authorization exception rules.
        Pay special attention to:
        - Effective dates vs announcement dates
        - Excluded plan types (Medicaid MCO, Commercial HMO, Commercial PPO, ACA Exchange)
        - Excluded 2-letter US states
        - Whether pediatric patients (<18) or ABA codes still require prior authorization.

        BULLETIN TEXT:
        {bulletin_text}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedRuleSet,
                temperature=0.0,
            ),
        )
        parsed = ExtractedRuleSet.model_validate_json(response.text)
        return ("LIVE_GEMINI_STRUCTURED_OUTPUT", parsed.rules)
    except Exception as e:
        print(f"Gemini API warning ({e}) - using fallback rules.")
        return (f"FALLBACK_MODE ({type(e).__name__})", STRUCTURED_PAYER_RULES)


@app.get("/default-data")
def get_default_data():
    """Returns the default sneaky payer bulletin and upcoming clinic schedule."""
    return {
        "default_bulletin_text": RAW_PAYER_BULLETIN_TEXT.strip(),
        "upcoming_schedule": UPCOMING_CLINIC_SCHEDULE,
    }


@app.post("/scan-schedule", response_model=ScheduleScanResponse)
def scan_schedule(req: BulletinCompileRequest):
    """
    1. Compiles the raw payer bulletin text into multi-variable Pydantic rules.
    2. Scans every appointment on the clinic's upcoming schedule.
    3. Returns exact denial traps caught and total revenue saved.
    """
    mode, rules = compile_bulletin_with_gemini(req.bulletin_text)

    alerts: List[AuditAlert] = []
    total_saved = 0.0
    traps_count = 0

    for appt in UPCOMING_CLINIC_SCHEDULE:
        alert = evaluate_appointment(appt, rules)
        alerts.append(alert)
        if alert.status == "HEADLINE_TRAP_DENIAL_RISK":
            traps_count += 1
            total_saved += alert.revenue_at_risk_usd

    return ScheduleScanResponse(
        compiler_mode=mode,
        extracted_rules=rules,
        alerts=alerts,
        total_appointments_scanned=len(UPCOMING_CLINIC_SCHEDULE),
        traps_caught_count=traps_count,
        total_revenue_saved_usd=total_saved,
    )