# pages/2_Create.py
from textwrap import dedent
import streamlit as st
from app.shared import use_theme, header

st.set_page_config(page_title="VERDICT — Create", layout="wide")
use_theme()
header()

st.markdown('<div class="mf-container">', unsafe_allow_html=True)
st.markdown("## Create a New Contract")
st.caption("Select industry, subject, and governing law. Defaults auto-load. Jurisdictional language is swapped to keep the draft legally coherent.")

industries = ["Technology (SaaS)", "Consulting/Professional Services", "Construction", "Healthcare"]
subjects = {
    "Technology (SaaS)": ["Master Subscription Agreement", "Data Processing Addendum", "Support & SLA"],
    "Consulting/Professional Services": ["Service Agreement", "Statement of Work", "NDA"],
    "Construction": ["General Construction Contract", "Subcontract", "Change Order"],
    "Healthcare": ["Services Agreement", "BAA (HIPAA)", "NDA"],
}
laws = ["Qatar", "United Kingdom"]
jurisdictions = {"Qatar": ["Qatari Courts (Doha)"], "United Kingdom": ["England & Wales Courts (London)"]}

col1, col2 = st.columns(2)
with col1:
    industry = st.selectbox("Industry", industries, index=0)
    service  = st.selectbox("Subject / Service", subjects[industry], index=0)
with col2:
    law      = st.selectbox("Governing Law", laws, index=0)
    forum    = st.selectbox("Jurisdiction", jurisdictions[law], index=0)

DEFAULTS = {
    ("Technology (SaaS)", "Master Subscription Agreement"): [
        "License & Access: Customer is granted a non-exclusive, non-transferable right to access the Service.",
        "Data Protection: Provider implements industry-standard security controls and encrypts Customer Data in transit and at rest.",
        "Uptime & SLA: Target uptime is 99.9% monthly; service credits apply for verified downtime.",
        "Fees & Payment: Invoices are due Net 30 from invoice date; late fees may apply.",
        "Confidentiality: Each party shall protect Confidential Information using reasonable safeguards.",
        "Limitation of Liability: Capped at the fees paid in the 12 months preceding the claim.",
    ],
    ("Consulting/Professional Services", "Service Agreement"): [
        "Scope: Consultant will deliver the Services as described in the Statement of Work.",
        "Deliverables & Acceptance: Client shall review and accept deliverables within 10 days.",
        "Fees & Expenses: Time & materials; pre-approved expenses reimbursed.",
        "IP Ownership: Work product becomes Client property upon full payment.",
        "Confidentiality: Both parties will maintain strict confidentiality.",
        "Liability: Consultant’s aggregate liability capped at fees paid for the Services.",
    ],
    ("Construction", "General Construction Contract"): [
        "Scope of Work: Contractor shall perform the Work in accordance with the Specifications.",
        "Schedule: Contractor will diligently pursue Substantial Completion by the Milestone Date.",
        "Payment: Progress payments monthly based on percent completion.",
        "Change Orders: Variations must be in writing and signed by both parties.",
        "Insurance & Safety: Contractor maintains insurance and complies with safety regulations.",
        "Dispute Resolution: Parties will negotiate in good faith prior to formal proceedings.",
    ],
    ("Healthcare", "Services Agreement"): [
        "Compliance: Provider complies with applicable healthcare regulations.",
        "PHI Handling: Restricted access; use and disclosure only as permitted.",
        "Security Safeguards: Technical, administrative, and physical safeguards implemented.",
        "Audit Rights: Client may audit reasonable aspects upon notice.",
        "Fees & Payment: As set forth in the Order; Net 30.",
        "Liability: Limited as permitted by applicable law.",
    ],
}

LAW_PATCH = {
    "Qatar": [
        "Governing Law: This Agreement is governed by the laws of the State of Qatar.",
        "Jurisdiction: The courts located in Doha, Qatar, shall have exclusive jurisdiction.",
        "Public Policy: Any provision inconsistent with mandatory Qatari public policy shall be interpreted to the maximum lawful extent.",
    ],
    "United Kingdom": [
        "Governing Law: This Agreement is governed by the laws of England and Wales.",
        "Jurisdiction: The courts of England and Wales seated in London shall have exclusive jurisdiction.",
        "Statutory Rights: Nothing in this Agreement excludes or limits liability that cannot be excluded under the laws of England and Wales.",
    ],
}

base = DEFAULTS.get((industry, service), [])
law_bits = LAW_PATCH.get(law, [])
draft = f"# {service}\n\n" \
        f"**Industry:** {industry}\n" \
        f"**Governing Law:** {law}\n" \
        f"**Jurisdiction:** {forum}\n\n" \
        "## Clauses\n" + "".join([f"- {c}\n" for c in base + law_bits])

st.markdown("### Draft (auto-tailored)")
st.text_area("Generated draft", value=draft, height=280, label_visibility="collapsed")

cA, cB = st.columns([1,1])
with cA:
    if st.button("Use this draft"):
        # Store the draft in session state
        st.session_state["created_result"] = {
            "summary": "Demo: Created a tailored draft.",
            "extracted": {"contracting_parties": [], "key_dates": {}, "governing_law": law, "jurisdiction": forum},
            "risks": ["Draft not reviewed by LLM yet."],
            "raw_text": draft,
        }
        st.session_state["show_create_results"] = True
        st.rerun()

# Show results section if draft was created
if st.session_state.get("show_create_results", False) and "created_result" in st.session_state:
    st.markdown("---")
    st.success("✅ Draft created successfully!")
    
    result = st.session_state["created_result"]
    draft_text = result["raw_text"]
    
    st.markdown("### Created Contract Draft")
    st.text_area("Contract Draft", value=draft_text, height=300, key="created_draft_preview", label_visibility="collapsed")
    
    st.download_button(
        "📥 Download Draft (.txt)", 
        draft_text.encode("utf-8"), 
        file_name="contract_draft.txt",
        type="primary",
        use_container_width=True
    )

st.markdown('</div>', unsafe_allow_html=True)
