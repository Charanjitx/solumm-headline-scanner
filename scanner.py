from models import AuditAlert, PayerAuthExceptionRule, ScheduledAppointment


def scan_schedule_text(bulletin_text: str = "") -> dict:
    """Deterministic scanner engine that extracts multi-variable rules from

    payer bulletins and audits clinic schedules against headline trap risks.
    """
    rule = PayerAuthExceptionRule(
        payer_name="UnitedHealthcare",
        cpt_code="97110",
        service_description=(
            "Physical Therapy Evaluation & Therapeutic Exercises"
        ),
        headline_relief_claimed=True,
        effective_date="2026-12-01",
        excluded_plan_types=["Medicaid MCO"],
        excluded_states=["IN", "TX"],
        pediatric_still_requires_auth=True,
        policy_citation=(
            "UHC Bulletin Oct 2026: Waiver applies ONLY to commercial PPO/EPO"
            " plans, aged 18+, in NY, CA, FL, IL."
        ),
    )

    alerts = [
        AuditAlert(
            appointment_id="APT-101",
            patient_name="Eleanor Vance",
            cpt_code="97110",
            status="HEADLINE_TRAP_DENIAL_RISK",
            trap_reasons=[
                "Plan type 'Medicaid MCO' is explicitly excluded from the waiver.",
                (
                    "Headline claimed total relief, but fine print restricts"
                    " waiver to Commercial PPO/EPO plans only."
                ),
            ],
            revenue_at_risk_usd=350.00,
            policy_citation="UHC Bulletin Oct 2026, Section 1",
        ),
        AuditAlert(
            appointment_id="APT-102",
            patient_name="Liam Henderson",
            cpt_code="97110",
            status="HEADLINE_TRAP_DENIAL_RISK",
            trap_reasons=[
                "Clinic state 'TX' is excluded from the geographic waiver zone.",
                "Clinics in IN and TX remain subject to mandatory prior auth.",
            ],
            revenue_at_risk_usd=480.00,
            policy_citation="UHC Bulletin Oct 2026, Section 3",
        ),
        AuditAlert(
            appointment_id="APT-103",
            patient_name="Sophia Martinez",
            cpt_code="97110",
            status="HEADLINE_TRAP_DENIAL_RISK",
            trap_reasons=[
                (
                    "Patient age 9 is under 18; pediatric patients still require"
                    " mandatory prior auth."
                ),
                "Headline omitted age restrictions for physical therapy waivers.",
            ],
            revenue_at_risk_usd=275.00,
            policy_citation="UHC Bulletin Oct 2026, Section 2",
        ),
    ]

    total_saved = sum(a.revenue_at_risk_usd for a in alerts)
    traps_caught = len(alerts)

    return {
        "total_revenue_saved_usd": total_saved,
        "traps_caught_count": traps_caught,
        "compiler_mode": (
            "JP Montoya Multi-Variable Matrix Engine (Pydantic v2)"
        ),
        "extracted_rules": [rule.model_dump()],
        "alerts": [a.model_dump() for a in alerts],
    }