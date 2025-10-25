# pages/1_Upload.py
import time
import streamlit as st
from textwrap import dedent
from app.shared import use_theme, header, parse_document, summarize_contract, extract_key_data, analyze_risk, get_backend_config

st.set_page_config(page_title="VERDICT — Upload", layout="wide")
use_theme()
header()

st.markdown('<div class="mf-container">', unsafe_allow_html=True)

st.markdown("""
<div class="section-heading">
  <div class="kicker">①</div>
  <h2>Upload an Existing Contract</h2>
</div>
<p class="section-desc">
  Drop in a PDF/DOCX and we’ll produce a structured summary, key fields, and risk flags.
</p>
""", unsafe_allow_html=True)

up = st.file_uploader("Upload contract (PDF/DOCX)", type=["pdf","docx"], label_visibility="collapsed", key="upload_uploader")

if up is not None:
    with st.spinner("Analyzing…"):
        b = up.getvalue()
        text = parse_document(b, up.name)
        summary = summarize_contract(text, get_backend_config("x"))
        extracted = extract_key_data(text, get_backend_config("x"))
        risks = analyze_risk(text, get_backend_config("x"))
        st.session_state["result"] = {
            "summary": summary, "extracted": extracted, "risks": risks, "raw_text": text,
            "doc_name": up.name
        }
        time.sleep(0.2)
    st.success("Done! View the results.")
    st.link_button("Open Results", "/Results")

st.markdown('</div>', unsafe_allow_html=True)
