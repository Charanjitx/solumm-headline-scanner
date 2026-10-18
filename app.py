import streamlit as st
from scanner import scan_schedule_text

st.set_page_config(
    page_title="Solum 'Headline Trap' Schedule Scanner",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Solum Health: 'Headline Trap' Schedule Scanner")
st.markdown(
    "*Built for Solum Health | Inspired by JP Montoya's October 2026 Forbes Article on Payer Prior Auth Relief Gaps.*"
)

st.sidebar.header("1. Payer Policy Bulletin")
st.sidebar.markdown(
    "Paste a confusing insurance announcement below. Our engine compiles it into multi-variable rules and audits next week's schedule."
)

# Default text fallback
default_text = """PAYER BULLETIN: UnitedHealthcare Policy Update (Published October 2026)
HEADLINE: UnitedHealthcare Reduces Administrative Burden by Cutting Prior Authorizations!

Effective December 1, 2026, UnitedHealthcare is removing prior authorization requirements for Physical Therapy code 97110 and ABA therapy code 97153.

EXCEPTIONS & FINE PRINT: 
1. This waiver applies ONLY to commercial PPO and EPO plans. Medicaid MCO and Medicare Advantage plans are strictly excluded.
2. Applies ONLY to patients aged 18 and older. Pediatric patients (under 18) still require prior authorization.
3. Applies ONLY to clinics located in NY, CA, FL, and IL. Clinics in IN and TX remain subject to mandatory prior auth.
4. Any date of service prior to December 1, 2026 is excluded."""

bulletin_input = st.sidebar.text_area(
    "Raw Payer Announcement Text", value=default_text, height=250
)

if st.sidebar.button("🚨 Run Schedule Audit", type="primary"):
    with st.spinner("Compiling multi-variable rules & scanning schedule..."):
        try:
            data = scan_schedule_text(bulletin_input)
        except Exception as e:
            st.error(f"Error running scanner: {e}")
            st.stop()

    # Top Metrics Banner
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Total Revenue Saved",
        f"${data['total_revenue_saved_usd']:,.2f}",
        delta="Denied Claims Prevented",
        delta_color="normal",
    )
    col2.metric("Headline Traps Caught", f"{data['traps_caught_count']} Appointments")
    col3.metric("Compiler Engine Mode", data["compiler_mode"])

    st.divider()

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("📅 Next Week's Clinic Schedule Audit")
        st.markdown(
            "Appointments flagged in **red** would have been denied if front-desk staff fell for the headline relief trap."
        )

        for alert in data["alerts"]:
            if alert["status"] == "HEADLINE_TRAP_DENIAL_RISK":
                with st.expander(
                    f"⚠️ DENIAL RISK: {alert['patient_name']} (CPT {alert['cpt_code']}) — Loss Avoided: ${alert['revenue_at_risk_usd']:,.2f}",
                    expanded=True,
                ):
                    st.error(f"**Status:** HEADLINE TRAP DENIAL RISK")
                    for reason in alert["trap_reasons"]:
                        st.markdown(f"- 🔴 {reason}")
                    st.info(f"**Policy Rule Citation:** {alert['policy_citation']}")
            elif alert["status"] == "AUTH_ALREADY_ON_FILE":
                with st.expander(
                    f"✅ SAFE (Auth on File): {alert['patient_name']} (CPT {alert['cpt_code']})"
                ):
                    st.success("Prior authorization is already verified on file.")
            else:
                with st.expander(
                    f"✅ SAFE (No Auth Needed): {alert['patient_name']} (CPT {alert['cpt_code']})"
                ):
                    st.success(f"Passed all checks. {alert['policy_citation']}")

    with right_col:
        st.subheader("🧠 Compiled Payer Rules")
        st.markdown("Multi-variable conditions extracted from fine print:")
        for rule in data["extracted_rules"]:
            with st.container(border=True):
                st.markdown(f"**{rule['payer_name']} ({rule['cpt_code']})**")
                st.caption(rule["service_description"])
                st.markdown(f"🗓️ Effective: `{rule['effective_date']}`")
                if rule["excluded_plan_types"]:
                    st.markdown(
                        f"❌ Excluded Plans: `{', '.join(rule['excluded_plan_types'])}`"
                    )
                if rule["excluded_states"]:
                    st.markdown(
                        f"❌ Excluded States: `{', '.join(rule['excluded_states'])}`"
                    )
                if rule["pediatric_still_requires_auth"]:
                    st.markdown("👶 Pediatric (<18) Still Requires Auth")
else:
    st.info(
        "👈 Click **'Run Schedule Audit'** in the sidebar to scan the clinic calendar against the insurance bulletin."
    )