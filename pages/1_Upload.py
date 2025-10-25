# pages/1_Upload.py
from textwrap import dedent
import streamlit as st

st.set_page_config(page_title="VERDICT — Upload", layout="wide")

# reuse theme & header that your CSS relies on
from app.shared import use_theme, header   # if you don't have this, just inline your CSS/header like in main.py
use_theme(); header()

st.markdown(dedent("""
<main id="top">
  <section class="hero-block hero-tight">
    <div class="hero-content">
      <h1 class="hero-title">Upload an Existing Contract</h1>
      <p class="hero-subtitle">Drop in a PDF/DOCX and we'll analyze it.</p>
    </div>
  </section>
</main>
"""), unsafe_allow_html=True)

# same wrapper classes so it looks like a card on this page too (optional)
st.markdown('<span class="sc-card sc-upload-flag"></span>', unsafe_allow_html=True)

up = st.file_uploader("Upload contract (PDF/DOCX)", type=["pdf","docx"], label_visibility="collapsed", key="upload_page_uploader")

if up is not None:
    ss = st.session_state
    ss.uploaded_bytes = up.getvalue()
    ss.doc_name = up.name
    ss.result = None
    ss.pending_upload = True
    st.switch_page("pages/4_Results.py")
