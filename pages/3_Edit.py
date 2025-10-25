# pages/3_Edit.py
import streamlit as st
from app.shared import use_theme, header

st.set_page_config(page_title="VERDICT — Edit", layout="wide")
use_theme()
header()

st.markdown('<div class="mf-container">', unsafe_allow_html=True)
st.markdown("## Edit a Contract Inline")
st.caption("Paste or upload text to tweak clauses and metadata on-screen, then export. (Demo stub.)")

text = st.text_area("Paste contract text", height=320)
c1, c2 = st.columns([1,1])
with c1:
    st.button("Analyze (stub)")
with c2:
    if st.button("View Results"):
        st.session_state["result"] = {
            "summary": "Demo: Inline edit summary.",
            "extracted": {},
            "risks": [],
            "raw_text": text,
        }
        st.switch_page("pages/4_Results.py")

st.markdown('</div>', unsafe_allow_html=True)
