# pages/3_Edit.py
import streamlit as st
from app.shared import use_theme, header
import json
from datetime import date # Import date for date inputs

st.set_page_config(page_title="VERDICT — Edit", layout="wide")
use_theme()
header()

# --- Utility Functions for Demo ---
def apply_edits_demo(raw_text, metadata):
    """
    Simulates applying the metadata edits to the raw contract text.
    For the demo, it prepends the new metadata as a block.
    """
    metadata_str = json.dumps(metadata, indent=4)
    
    edited_text = (
        "***CONTRACT EDITED SUCCESSFULLY (DEMO)***\n\n"
        "--- New Structured Metadata ---\n"
        f"{metadata_str}\n"
        "-------------------------------\n\n"
        "***Original Contract Text Follows***\n\n"
        f"{raw_text}"
    )
    return edited_text

# --- Edit Page Content ---

st.markdown('<div class="mf-container edit-wrap">', unsafe_allow_html=True)
st.markdown("## Edit a Contract Inline")
st.caption("Upload an existing contract and modify its key metadata/clauses using the form below, then view the revised draft.")

c_upload, c_form = st.columns([1, 1], gap="large")

# 1. Upload/Paste Column (Kept concise for this response)
with c_upload:
    st.markdown("### Original Contract Text")
    
    uploaded_file = st.file_uploader(
        "Upload contract (PDF/DOCX/TXT)",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        key="edit_uploader"
    )
    
    # --- Simplified file parsing logic for demo ---
    contract_text_input = st.session_state.get("raw_text_to_edit", "")
    if uploaded_file is not None:
        try:
            contract_text_input = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        except:
            contract_text_input = "DEMO TEXT: unsupported file; parser disabled."
        st.session_state["raw_text_to_edit"] = contract_text_input

    contract_text_input = st.text_area(
        "Paste contract text", 
        value=st.session_state.get("raw_text_to_edit", ""),
        height=400, 
        key="edit_contract_text_area"
    )
    st.session_state["raw_text_to_edit"] = contract_text_input
    # ---------------------------------------------

# 2. Structured Metadata Form Column
with c_form:
    st.markdown("### Structured Metadata Edits")
    st.caption("Fill out the fields to guide the contract modification.")
    
    # --- Define Dropdown Options ---
    CONTRACT_TEMPLATES = ["MSA", "Services Agreement", "NDA", "SaaS", "Supply", "Employment", "Consulting", "Construction", "Franchise", "Licensing", "Joint Venture", "Custom"]
    INDUSTRIES = ["Technology", "Construction", "Healthcare", "Finance", "Manufacturing", "Education", "Energy", "Retail", "Transportation", "Hospitality"]
    JURISDICTIONS = ["Qatar", "United Kingdom", "United States"]
    LANGUAGES = ["English", "Arabic"]
    ROLES_A = ["Customer", "Client", "Employer", "Buyer", "Licensee"]
    ROLES_B = ["Supplier", "Contractor", "Consultant", "Employee", "Licensor"]


    with st.form("metadata_form", clear_on_submit=False):
        # --- Core Details ---
        st.subheader("General Terms")
        col1, col2 = st.columns(2)
        with col1:
            # Dropdown
            contract_type = st.selectbox(
                "Contract Template", 
                CONTRACT_TEMPLATES,
                index=CONTRACT_TEMPLATES.index("Services Agreement")
            )
            # Date Picker
            start_date = st.date_input("Start Date", value=date(2025, 11, 1))
        with col2:
            # Dropdown
            industry = st.selectbox(
                "Industry", 
                INDUSTRIES,
                index=INDUSTRIES.index("Technology")
            )
            # Date Picker
            end_date = st.date_input("End Date", value=date(2026, 11, 1))

        st.divider()
        st.subheader("Legal & Context")
        col3, col4 = st.columns(2)
        with col3:
            # Dropdown
            law = st.selectbox("Governing Law", JURISDICTIONS, index=JURISDICTIONS.index("Qatar"))
        with col4:
            # Dropdown
            language = st.selectbox("Contract Language", LANGUAGES, index=LANGUAGES.index("English"))
            
        # Text Input - Defaulting to text
        jurisdiction_forum = st.text_input("Jurisdiction Forum", value="Qatari Courts (Doha)")

        # Text Area
        context = st.text_area(
            "Contract Context/Purpose",
            value="Software development and maintenance of a web-based platform...",
            height=100
        )

        st.divider()
        st.subheader("Party Details")

        # --- Party A ---
        st.markdown("#### Party A")
        col5, col6, col7 = st.columns([2, 1, 3])
        party_a_name = col5.text_input("Legal Name (A)", value="QTech Solutions W.L.L.", label_visibility="collapsed")
        # Dropdown
        party_a_role = col6.selectbox("Role (A)", ROLES_A, index=ROLES_A.index("Client"), label_visibility="collapsed")
        party_a_address = col7.text_input("Address (A)", value="Office 304, Doha Tower, West Bay, Doha, Qatar", label_visibility="collapsed")

        # --- Party B ---
        st.markdown("#### Party B")
        col8, col9, col10 = st.columns([2, 1, 3])
        party_b_name = col8.text_input("Legal Name (B)", value="CodeBridge Technologies Ltd.", label_visibility="collapsed")
        # Dropdown
        party_b_role = col9.selectbox("Role (B)", ROLES_B, index=ROLES_B.index("Contractor"), label_visibility="collapsed")
        party_b_address = col10.text_input("Address (B)", value="45 Innovation Street, London, United Kingdom", label_visibility="collapsed")

        st.divider()
        
        # --- Submit Button ---
        c_spacer, c_submit = st.columns([3, 1])
        with c_submit:
            submit_button = st.form_submit_button("Generate Edited Contract", type="primary", use_container_width=True)

        if submit_button:
            # 1. Compile the metadata dictionary
            metadata = {
                "ContractTemplate": contract_type,
                "Industry": industry,
                "Governing_Law": law,
                "Language": language,
                "Jurisdiction": jurisdiction_forum,
                "Start_date": start_date.isoformat() if start_date else None,
                "End_date": end_date.isoformat() if end_date else None,
                "PartyA": {
                    "LegalName": party_a_name,
                    "Role": party_a_role,
                    "Address": party_a_address
                },
                "PartyB": {
                    "LegalName": party_b_name,
                    "Role": party_b_role,
                    "Address": party_b_address
                },
                "Context": context
            }
            
            # 2. Apply edits (using demo logic)
            edited_contract_text = apply_edits_demo(
                raw_text=st.session_state.get("raw_text_to_edit", ""),
                metadata=metadata
            )

            # 3. Save results to session state
            st.session_state["result"] = {
                "summary": "Demo: Contract metadata edited. Review the 'Raw Text' tab on the Results page to see the generated draft.",
                "extracted": metadata,
                "risks": ["Demo: Risk analysis required on new draft."],
                "raw_text": edited_contract_text,
                "is_edited_draft": True,
            }
            
            # 4. Switch to Results page
            st.switch_page("pages/4_Results.py")

st.markdown('</div>', unsafe_allow_html=True)