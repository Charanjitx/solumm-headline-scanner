from typing import List
from models import PayerAuthExceptionRule, ScheduledAppointment, AuditAlert
from mock_data import STRUCTURED_PAYER_RULES, UPCOMING_CLINIC_SCHEDULE

def evaluate_appointment(
    appt: ScheduledAppointment, rules: List[PayerAuthExceptionRule]
) -> AuditAlert:
    if appt.prior_auth_on_file:
        return AuditAlert(
            appointment_id=appt.appointment_id,
            patient_name=appt.patient_name,
            cpt_code=appt.cpt_code,
            status="AUTH_ALREADY_ON_FILE",
            trap_reasons=[],
            revenue_at_risk_usd=0.0,
            policy_citation="Prior authorization is already verified on file."
        )

    # Find matching rule for Payer + CPT code
    matching_rule = next(
        (r for r in rules if r.payer_name == appt.payer_name and r.cpt_code == appt.cpt_code),
        None
    )

    if not matching_rule:
        return AuditAlert(
            appointment_id=appt.appointment_id,
            patient_name=appt.patient_name,
            cpt_code=appt.cpt_code,
            status="SAFE_NO_AUTH_NEEDED",
            trap_reasons=[],
            revenue_at_risk_usd=0.0,
            policy_citation="No active restriction found."
        )

    trap_reasons = []

    # Check 1: Did the headline even include this code (e.g., ABA therapy left out completely)?
    if not matching_rule.headline_relief_claimed:
        trap_reasons.append(f"CPT {appt.cpt_code} was excluded from payer relief completely.")

    # Check 2: Is the Date of Service BEFORE the effective date of the cut?
    if appt.date_of_service < matching_rule.effective_date:
        trap_reasons.append(
            f"Date of Service ({appt.date_of_service}) is BEFORE policy effective date ({matching_rule.effective_date})."
        )

    # Check 3: Is the patient's Plan Type excluded (e.g., Medicaid MCO)?
    if appt.plan_type in matching_rule.excluded_plan_types:
        trap_reasons.append(f"Plan type '{appt.plan_type}' is excluded from prior auth relief.")

    # Check 4: Is the clinic State excluded (e.g., Indiana or Texas)?
    if appt.state in matching_rule.excluded_states:
        trap_reasons.append(f"State '{appt.state}' still mandates prior authorization for this code.")

    # Check 5: Is this a pediatric patient (< 18) when pediatric therapy is excluded?
    if matching_rule.pediatric_still_requires_auth and appt.patient_age < 18:
        trap_reasons.append(f"Pediatric patient (Age {appt.patient_age}) still requires prior authorization.")

    if trap_reasons:
        return AuditAlert(
            appointment_id=appt.appointment_id,
            patient_name=appt.patient_name,
            cpt_code=appt.cpt_code,
            status="HEADLINE_TRAP_DENIAL_RISK",
            trap_reasons=trap_reasons,
            revenue_at_risk_usd=appt.estimated_reimbursement_usd,
            policy_citation=matching_rule.policy_citation
        )

    return AuditAlert(
        appointment_id=appt.appointment_id,
        patient_name=appt.patient_name,
        cpt_code=appt.cpt_code,
        status="SAFE_NO_AUTH_NEEDED",
        trap_reasons=[],
        revenue_at_risk_usd=0.0,
        policy_citation=matching_rule.policy_citation
    )

if __name__ == "__main__":
    print("=== SOLUM 'HEADLINE TRAP' SCHEDULE AUDIT ===")
    total_risk = 0.0
    for appt in UPCOMING_CLINIC_SCHEDULE:
        alert = evaluate_appointment(appt, STRUCTURED_PAYER_RULES)
        print(f"\n[{alert.status}] {alert.patient_name} (CPT {alert.cpt_code})")
        if alert.trap_reasons:
            total_risk += alert.revenue_at_risk_usd
            for reason in alert.trap_reasons:
                print(f"   ⚠️ TRAP CAUGHT: {reason}")
            print(f"   💰 Revenue Saved from Denial: ${alert.revenue_at_risk_usd:.2f}")
        else:
            print("   ✅ Safe to proceed without Prior Auth.")
    print(f"\nTOTAL REVENUE SAVED THIS WEEK: ${total_risk:.2f}")