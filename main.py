#!/usr/bin/env python3
"""
CLM AI — 3-screen Streamlit app:
1) Home (title + instructions + centered upload)
2) Loading (progress while parsing/analysis)
3) Results (tabs: Summary, Parties, Dates, Law, Obligations, Financials, Risks)
"""

import time
import os
import sys
from pathlib import Path
import streamlit as st

# Ensure we can import from src/ and app/
ROOT = Path(__file__).parent
SRC = ROOT / "src"
APP = ROOT / "app"
for p in (SRC, APP):
    if str(p) not in sys.path:
        sys.path.append(str(p))

# ---- optional config helpers (safe fallbacks if missing) ----
try:
    from app.config import get_backend_config  # prefer this name
except Exception:
    # fallback to your existing load_config (if present)
    try:
        from app.config import load_config as _load_config
        def get_backend_config(_label: str) -> dict:
            return _load_config()
    except Exception:
        def get_backend_config(_label: str) -> dict:
            return {
                "preferred_backend": "local",
                "hf_api_key": os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACEHUB_API_KEY"),
                "hf_model": os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
                "local_url": os.getenv("LOCAL_INFERENCE_URL", "http://localhost:11434"),
                "local_model": os.getenv("LOCAL_MODEL", "qwen2:1.5b"),
            }

try:
    from app.utils import parse_document
except Exception:
    # very small fallback parser
    from io import BytesIO
    import docx  # python-docx
    from PyPDF2 import PdfReader
    def _read_pdf(b: bytes) -> str:
        text = []
        reader = PdfReader(BytesIO(b))
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text).strip()
    def _read_docx(b: bytes) -> str:
        d = docx.Document(BytesIO(b))
        return "\n".join(p.text for p in d.paragraphs).strip()
    def parse_document(file_bytes: bytes, file_name: str) -> str:
        n = (file_name or "").lower()
        if n.endswith(".pdf"):
            return _read_pdf(file_bytes)
        if n.endswith(".docx"):
            return _read_docx(file_bytes)
        return file_bytes.decode("utf-8", errors="ignore")

# Import AI pipeline pieces with safe fallbacks
try:
    from src.summarization import summarize_contract as _summarize
except Exception:
    def _summarize(text, cfg): return "No summary available yet. (wire summarize_contract)"

try:
    from src.data_extraction import extract_key_data as _extract
except Exception:
    def _extract(text, cfg):
        # skeleton keys used by the UI
        return {
            "contracting_parties": [],
            "key_dates": {"effective_date": None, "expiration_date": None, "renewal_date": None},
            "governing_law": None,
            "jurisdiction": None,
            "obligations": [],
            "financial_terms": {}
        }

try:
    from src.risk_analysis import analyze_risk as _risks
except Exception:
    def _risks(text, cfg): return []

# ---- Streamlit page + theme ----
st.set_page_config(page_title="CLM AI", page_icon="🤖", layout="centered")
THEME_PATH = APP / "theme.css"
if THEME_PATH.exists():
    st.markdown(f"<style>{THEME_PATH.read_text()}</style>", unsafe_allow_html=True)

# ---- sidebar backend selector ----
st.sidebar.header("⚙️ Settings")
backend_label = st.sidebar.radio("LLM Backend:", ["HuggingFace API", "Local Ollama"], index=0)
CFG = get_backend_config(backend_label)

# ---- session state ----
ss = st.session_state
ss.setdefault("step", "home")           # "home" | "loading" | "results"
ss.setdefault("doc_name", None)
ss.setdefault("uploaded_bytes", None)
ss.setdefault("result", None)

# ---- UI helpers (dashboard components) ----
def kv_row(label: str, value: str | None):
    st.markdown(
        f"""
        <div class="kv">
          <div class="kv-key">{label}</div>
          <div class="kv-value">{value or "—"}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def screen_home():
    st.markdown(
        """
        <div class="hero">
          <div class="hero-card">
            <h1>🎐 CLM&nbsp;AI</h1>
            <p class="subtitle">
              Upload a contract and let the AI extract key data, summarize terms, and flag risks.
              (PDF or DOCX • English & Arabic)
            </p>
            <ol class="instructions">
              <li>Upload your file below.</li>
              <li>We’ll process it on a loading screen.</li>
              <li>Review results in tabs (Summary, Parties, Dates, Law, Obligations, Financials).</li>
            </ol>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="card upload-card">', unsafe_allow_html=True)
    up = st.file_uploader("Upload contract (PDF/DOCX)", type=["pdf", "docx"])
    st.markdown("</div>", unsafe_allow_html=True)

    if up is not None:
        ss.uploaded_bytes = up.getvalue()
        ss.doc_name = up.name
        ss.step = "loading"
        st.rerun()

def screen_loading():
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-card">
            <h2>Analyzing <code>{ss.doc_name or "your file"}</code>…</h2>
            <p class="subtitle">Extracting fields, summarizing, and scanning for risks.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    p = st.progress(5)
    for pct in (12, 25, 42):
        time.sleep(0.15); p.progress(pct)

    # run pipeline
    text = parse_document(ss.uploaded_bytes, ss.doc_name)
    for pct in (55, 66): time.sleep(0.1); p.progress(pct)

    summary = _summarize(text, CFG)
    for pct in (74, 82): time.sleep(0.1); p.progress(pct)

    extracted = _extract(text, CFG)
    risks = _risks(text, CFG)
    for pct in (90, 100): time.sleep(0.1); p.progress(pct)

    ss.result = {
        "summary": summary,
        "extracted": extracted,
        "risks": risks,
        "raw_text": text
    }
    ss.step = "results"
    st.rerun()

def screen_results():
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-card">
            <h2>Results for <code>{ss.doc_name}</code></h2>
            <p class="subtitle">Explore the tabs below.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    res = ss.result or {}
    summary = res.get("summary")
    extracted = res.get("extracted", {})
    risks = res.get("risks", [])

    tabs = st.tabs([
        "📄 Summary",
        "👥 Parties",
        "📅 Key Dates",
        "⚖️ Law & Jurisdiction",
        "📌 Obligations & Deliverables",
        "💰 Financial Terms",
        "⚠️ Risks"
    ])

    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(summary or "_No summary._")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        parties = extracted.get("contracting_parties") or extracted.get("parties")
        if isinstance(parties, list):
            for p in parties: kv_row("Party", str(p))
        else:
            kv_row("Parties", parties if parties else "—")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        dates = extracted.get("key_dates", {}) or {}
        kv_row("Effective Date", dates.get("effective_date"))
        kv_row("Expiration Date", dates.get("expiration_date"))
        kv_row("Renewal Date", dates.get("renewal_date"))
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        law = extracted.get("governing_law") or extracted.get("law_and_jurisdiction")
        juris = extracted.get("jurisdiction")
        kv_row("Governing Law", law)
        kv_row("Jurisdiction", juris)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        obligations = extracted.get("obligations") or extracted.get("deliverables")
        if isinstance(obligations, list):
            for o in obligations: kv_row("Obligation", str(o))
        else:
            st.write(obligations or "—")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[5]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fin = extracted.get("financial_terms") or {}
        if isinstance(fin, dict):
            for k, v in fin.items():
                kv_row(k.replace("_", " ").title(), str(v))
        else:
            st.write(fin or "—")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[6]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if risks and isinstance(risks, (list, tuple)):
            for r in risks:
                st.markdown(f"- {r}")
        else:
            st.write("No explicit risks found.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---- router ----
if ss.step == "home":
    screen_home()
elif ss.step == "loading":
    screen_loading()
else:
    screen_results()
