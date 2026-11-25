"""P10 Standalone Streamlit UI (runs via `streamlit run app/ui.py --server.port 8501`)."""

from __future__ import annotations

DISCLAIMER = "Informational only. Verify on the official portal."


def run_streamlit_app() -> None:
    """Launch Streamlit interface for HF Spaces / Docker standalone deployment."""
    import streamlit as st  # type: ignore[import-not-found]

    from agents.graph import YojanaMitraAgentGraph
    from agents.scam_checker import analyze_scam_message
    from pipeline.indexer import load_cached_schemes
    from rules.optimizer import optimize_benefit_stack

    st.set_page_config(page_title="Yojana Mitra", layout="wide")
    st.title("Yojana Mitra — Neurosymbolic Welfare Copilot")
    st.info(DISCLAIMER)

    consent = st.checkbox("DPDP Act 2023 Consent: I understand PII is masked before logs/LLM calls and Aadhaar is never stored.", value=True)
    if not consent:
        st.warning("Please accept the DPDP Act 2023 privacy notice to continue.")
        return

    agent = YojanaMitraAgentGraph()
    tab_chat, tab_stack, tab_scam = st.tabs(["Copilot Chat", "Benefit Stack Optimizer", "Scam Shield"])

    with tab_chat:
        q = st.text_input("Ask in English, Telugu, Hindi, Kannada, or Tamil", "తెలంగాణ రైతు భరోసా అర్హతలు ఏమిటి?")
        if st.button("Run Copilot"):
            res = agent.run(q, profile={"age": 38, "income": 140000, "state": "Telangana", "category": "SC", "gender": "Female", "occupation": "Farmer", "land": 2.0, "disability": False, "bpl": True, "residence": "Rural"})
            st.write(res["answer"])
            st.json(res["trace"])

    with tab_stack:
        if st.button("Optimize Telangana SC Woman Farmer Stack"):
            stack = optimize_benefit_stack({"age": 38, "income": 140000, "state": "Telangana", "category": "SC", "gender": "Female", "occupation": "Farmer", "land": 2.0, "disability": False, "bpl": True, "residence": "Rural"}, load_cached_schemes())
            st.metric("Total Annual Welfare", f"Rs {stack['total_annual_inr']:,}", f"+{stack['gain_vs_top1_pct']}% vs Top-1")
            st.table(stack["selected_schemes"])

    with tab_scam:
        msg = st.text_area("Paste forwarded WhatsApp/SMS message")
        if st.button("Verify Message") and msg.strip():
            st.json(analyze_scam_message(msg))


if __name__ == "__main__":
    run_streamlit_app()
