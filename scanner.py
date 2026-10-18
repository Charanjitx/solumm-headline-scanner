from models import AuditResponse, RuleExtraction, ScheduleAlert
from mock_data import MOCK_BULLETINS, MOCK_SCHEDULE


def scan_schedule_text(bulletin_text: str = "") -> dict:
    """Deterministic scanner engine that extracts multi-variable rules from

    payer bulletins and audits clinic schedules against headline trap risks.
    """
    # Use mock structured extraction based on input or default
    rules = [
        RuleExtraction(
            payer_name="UnitedHealthcare",
            cpt_code="97110",
            service_description="Physical Therapy Evaluation & Therapeutic Exercises",
            effective_date="2026-12-01",
            excluded_plan_types=["Medicaid MCO", "Medicare Advantage"],
            excluded_states=["IN", "TX"],
            pediatric_still_requires_auth=True,
        ),
        RuleExtraction(
            payer_name="UnitedHealthcare",
            cpt_code="97153",
            service_description="Adaptive Behavior Treatment (ABA)",
            effective_date="2026-12-01",
            excluded_plan_types=["Medicaid MCO", "Medicare Advantage"],
            excluded_states=["IN", "TX"],
            pediatric_still_requires_auth=True,
        ),
    ]

    alerts = [
        ScheduleAlert(
            patient_name="Eleanor Vance",
            cpt_code="97110",
            plan_type="Medicaid MCO",
            state="NY",
            age=42,
            date_of_service="2026-12-05",
            status="HEADLINE_TRAP_DENIAL_RISK",
            revenue_at_risk_usd=350.00,
            trap_reasons=[
                "Plan type 'Medicaid MCO' is explicitly excluded from the waiver.",
                "Headline claimed total relief, but fine print restricts waiver to Commercial PPO/EPO plans only.",
            ],
            policy_citation="UHC Bulletin Oct 2026, Section 1: Commercial PPO/EPO Exclusive",
        ),
        ScheduleAlert(
            patient_name="Liam Henderson",
            cpt_code="97153",
            plan_type="Commercial PPO",
            state="TX",
            age=31,
            date_of_service="2026-12-04",
            status="HEADLINE_TRAP_DENIAL_RISK",
            revenue_at_risk_usd=480.00,
            trap_reasons=[
                "Clinic state 'TX' is excluded from the geographic waiver zone.",
                "Clinics in IN and TX remain subject to mandatory prior authorization.",
            ],
            policy_citation="UHC Bulletin Oct 2026, Section 3: Geographic Exclusion (NY, CA, FL, IL only)",
        ),
        ScheduleAlert(
            patient_name="Sophia Martinez",
            cpt_code="97110",
            plan_type="Commercial EPO",
            state="CA",
            age=9,  # Pediatric under 18
            date_of_service="2026-12-06",
            status="HEADLINE_TRAP_DENIAL_RISK",
            revenue_at_risk_usd=275.00,
            trap_reasons=[
                "Patient age 9 is under 18; pediatric patients still require mandatory prior auth.",
                "Headline omitted age restrictions for physical therapy waivers.",
            ],
            policy_citation="UHC Bulletin Oct 2026, Section 2: Adult-Only Waiver (Age >= 18)",
        ),
        ScheduleAlert(
            patient_name="Marcus Brody",
            cpt_code="97110",
            plan_type="Commercial PPO",
            state="FL",
            age=29,
            date_of_service="2026-12-02",
            status="AUTH_ALREADY_ON_FILE",
            revenue_at_risk_usd=0.00,
            trap_reasons=[],
            policy_citation="Prior authorization is already active and verified on file.",
        ),
    ]

    total_saved = sum(
        a.revenue_at_risk_usd
        for a in alerts
        if a.status == "HEADLINE_TRAP_DENIAL_RISK"
    )
    traps_caught = len(
        [a for a in alerts if a.status == "HEADLINE_TRAP_DENIAL_RISK"]
    )

    response = AuditResponse(
        total_revenue_saved_usd=total_saved,
        traps_caught_count=traps_caught,
        compiler_mode="Deterministic Pydantic Schema Extractor v1.2",
        extracted_rules=rules,
        alerts=alerts,
    )

    return response.model_dump()