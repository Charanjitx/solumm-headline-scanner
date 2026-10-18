from datetime import date
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class PayerAuthExceptionRule(BaseModel):
    """
    Replaces the broken 'Yes/No per CPT code' model with JP Montoya's
    multi-variable matrix: Code + Plan + State + Age + Effective Date.
    """
    payer_name: str = Field(description="Name of the insurance company, e.g., UnitedHealthcare")
    cpt_code: str = Field(description="5-digit medical billing code, e.g., 97110 or 97153")
    service_description: str = Field(description="Plain English name of the therapy service")
    headline_relief_claimed: bool = Field(
        description="True if the payer headline claims prior auth was removed for this code"
    )
    effective_date: date = Field(
        description="Date the prior auth removal actually starts (not announcement date)"
    )
    excluded_plan_types: List[Literal["Medicaid MCO", "Commercial HMO", "Commercial PPO", "ACA Exchange"]] = Field(
        default_factory=list,
        description="Plans that STILL require prior auth despite the headline"
    )
    excluded_states: List[str] = Field(
        default_factory=list,
        description="2-letter state codes where prior auth is STILL required"
    )
    pediatric_still_requires_auth: bool = Field(
        default=False,
        description="True if patients under 18 are excluded from relief and still need prior auth"
    )
    policy_citation: str = Field(
        description="Exact quote from the payer bulletin explaining the fine-print exception"
    )

class ScheduledAppointment(BaseModel):
    """Represents a single patient visit on the clinic's upcoming schedule."""
    appointment_id: str
    patient_name: str
    patient_age: int
    state: str
    payer_name: str
    plan_type: Literal["Medicaid MCO", "Commercial HMO", "Commercial PPO", "ACA Exchange"]
    cpt_code: str
    date_of_service: date
    prior_auth_on_file: bool
    estimated_reimbursement_usd: float

class AuditAlert(BaseModel):
    """Output generated when a scheduled appointment falls into a 'Headline Trap'."""
    appointment_id: str
    patient_name: str
    cpt_code: str
    status: Literal["SAFE_NO_AUTH_NEEDED", "AUTH_ALREADY_ON_FILE", "HEADLINE_TRAP_DENIAL_RISK"]
    trap_reasons: List[str]
    revenue_at_risk_usd: float
    policy_citation: str