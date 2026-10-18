from datetime import date
from models import PayerAuthExceptionRule, ScheduledAppointment

# This is the raw text we will feed to Gemini in Step 2.
RAW_PAYER_BULLETIN_TEXT = """
PAYER BULLETIN: UnitedHealthcare Policy Update (Published October 2026)
HEADLINE: UnitedHealthcare Reduces Administrative Burden by Cutting Prior Authorizations!

Effective December 1, 2026, UnitedHealthcare is removing prior authorization requirements 
for Physical Therapy code 97110 (Therapeutic Exercises) and Speech Therapy code 92507.
NOTE / FINE PRINT:
1. This prior authorization removal applies ONLY to dates of service on or after December 1, 2026.
2. Pediatric ABA Therapy codes (97151, 97153) receive ZERO prior authorization cuts and still require full clinical substantiation.
3. For code 97110 and 92507, prior authorization is STILL REQUIRED for all Medicaid MCO plans, plans operating in Indiana (IN) or Texas (TX), and pediatric patients under age 18.
"""

# Here is the structured version of those rules:
STRUCTURED_PAYER_RULES = [
    PayerAuthExceptionRule(
        payer_name="UnitedHealthcare",
        cpt_code="97110",
        service_description="Physical Therapy - Therapeutic Exercises",
        headline_relief_claimed=True,
        effective_date=date(2026, 12, 1),
        excluded_plan_types=["Medicaid MCO"],
        excluded_states=["IN", "TX"],
        pediatric_still_requires_auth=True,
        policy_citation="Section 3: Prior auth still required for Medicaid MCO, IN/TX states, Children under 18, or visits before Dec 1, 2026."
    ),
    PayerAuthExceptionRule(
        payer_name="UnitedHealthcare",
        cpt_code="97153",
        service_description="ABA Adaptive Behavior Treatment by Protocol",
        headline_relief_claimed=False,
        effective_date=date(2026, 12, 1),
        excluded_plan_types=["Medicaid MCO", "Commercial HMO", "Commercial PPO", "ACA Exchange"],
        excluded_states=["CA", "TX", "IN", "NY", "FL"],
        pediatric_still_requires_auth=True,
        policy_citation="Section 2: Pediatric ABA Therapy codes (97151, 97153) receive ZERO prior authorization cuts."
    )
]

# 4 patients on the schedule where the receptionist stopped pulling prior auths (`prior_auth_on_file=False`)
# because they heard the news that "UnitedHealthcare cut prior authorizations!"
UPCOMING_CLINIC_SCHEDULE = [
    ScheduledAppointment(
        appointment_id="APT-101",
        patient_name="Leo Carter (Pediatric PT)",
        patient_age=9,
        state="CA",
        payer_name="UnitedHealthcare",
        plan_type="Commercial PPO",
        cpt_code="97110",
        date_of_service=date(2026, 12, 5),
        prior_auth_on_file=False,
        estimated_reimbursement_usd=240.00
    ),
    ScheduledAppointment(
        appointment_id="APT-102",
        patient_name="Maya Lin (Early Visit Date Trap)",
        patient_age=34,
        state="CA",
        payer_name="UnitedHealthcare",
        plan_type="Commercial PPO",
        cpt_code="97110",
        date_of_service=date(2026, 10, 26),  # Trap! Relief doesn't start until Dec 1, 2026
        prior_auth_on_file=False,
        estimated_reimbursement_usd=185.00
    ),
    ScheduledAppointment(
        appointment_id="APT-103",
        patient_name="Noah Williams (Indiana Medicaid ABA)",
        patient_age=6,
        state="IN",
        payer_name="UnitedHealthcare",
        plan_type="Medicaid MCO",
        cpt_code="97153",
        date_of_service=date(2026, 12, 5),
        prior_auth_on_file=False,
        estimated_reimbursement_usd=680.00
    ),
    ScheduledAppointment(
        appointment_id="APT-104",
        patient_name="Sarah Jenkins (Adult PPO - Actually Safe)",
        patient_age=42,
        state="CA",
        payer_name="UnitedHealthcare",
        plan_type="Commercial PPO",
        cpt_code="97110",
        date_of_service=date(2026, 12, 5),
        prior_auth_on_file=False,
        estimated_reimbursement_usd=210.00
    ),
]