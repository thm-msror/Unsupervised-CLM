#!/usr/bin/env python3
import os, sys, time
from pathlib import Path
from textwrap import dedent
import streamlit as st

# paths
ROOT = Path(__file__).parent
APP = ROOT / "app"
for p in (ROOT / "src", APP):
    if str(p) not in sys.path:
        sys.path.append(str(p))

# ---- demo stubs ----
def get_backend_config(_label: str) -> dict:
    return {
        "preferred_backend": "local",
        "hf_api_key": os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACEHUB_API_KEY"),
        "hf_model": os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "local_url": os.getenv("LOCAL_INFERENCE_URL", "http://localhost:11434"),
        "local_model": os.getenv("LOCAL_MODEL", "qwen2:1.5b"),
    }

def parse_document(file_bytes: bytes, file_name: str) -> str:
    name = (file_name or "").lower()
    if name.endswith(".pdf"):  return "DEMO TEXT (PDF): parser disabled during FE sprint."
    if name.endswith(".docx"): return "DEMO TEXT (DOCX): parser disabled during FE sprint."
    try:    return file_bytes.decode("utf-8", errors="ignore")
    except: return "DEMO TEXT: unsupported file; parser disabled."

def summarize_contract(text: str, cfg: dict) -> str:
    return (
        "This is a demo summary. Replace with real LLM call later.\n\n"
        "• Purpose: Sample agreement between ABC and XYZ.\n"
        "• Term: 12 months, auto-renew.\n"
        "• Payment: Net 30.\n"
    )

def extract_key_data(text: str, cfg: dict) -> dict:
    return {
        "contracting_parties": ["ABC Corporation", "XYZ Limited"],
        "key_dates": {
            "effective_date": "2025-01-15",
            "expiration_date": "2026-01-14",
            "renewal_date": "Auto-renews annually",
        },
        "governing_law": "State of New York",
        "jurisdiction": "New York courts",
        "obligations": [
            "Supplier delivers services within 30 days of PO.",
            "Client pays within Net 30 days.",
        ],
        "financial_terms": {
            "payment_schedule": "Monthly, Net 30",
            "penalties": "1.5% monthly late fee",
            "currency": "USD",
            "cap": "Liability cap at annual fees",
        },
    }

def analyze_risk(text: str, cfg: dict):
    return [
        "High: Automatic renewal without notice period.",
        "Medium: Indemnification scope is ambiguous.",
        "Low: Confidentiality clause aligns with standard.",
    ]

# ---- page + theme ----
st.set_page_config(page_title="VERDICT", layout="centered")
THEME_PATH = APP / "theme.css"
if THEME_PATH.exists():
    st.markdown(dedent(f"<style>{THEME_PATH.read_text()}</style>"), unsafe_allow_html=True)

# ---- centered header (diamond icon + cursive VERDICT) ----
st.markdown(dedent("""
<div class="mf-header">
  <div class="mf-nav">
    <a class="brand-lockup" href="#top" aria-label="VERDICT home">
      <!-- Diamond mini icon -->
      <svg class="brand-mark" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
          <linearGradient id="brandStroke" x1="0" x2="1">
            <stop offset="0%"  stop-color="var(--brand)"/>
            <stop offset="100%" stop-color="var(--brand-2)"/>
          </linearGradient>
        </defs>
        <g fill="none" stroke="url(#brandStroke)" stroke-width="10" opacity=".95">
          <path d="M100 10 160 70 100 130 40 70Z"/>
          <path d="M100 70 160 130 100 190 40 130Z"/>
        </g>
      </svg>
      <span class="brand-text">VERDICT</span>
    </a>
  </div>
</div>
"""), unsafe_allow_html=True)

# ---- session ----
ss = st.session_state
ss.setdefault("step", "home")
ss.setdefault("doc_name", None)
ss.setdefault("uploaded_bytes", None)
ss.setdefault("result", None)

def kv_row(label: str, value: str | None):
    st.markdown(dedent(f"""
      <div class="kv">
        <div class="kv-key">{label}</div>
        <div class="kv-value">{value or "—"}</div>
      </div>
    """), unsafe_allow_html=True)

# ---- screens ----
def screen_home():
    # Single centered stack: Title row → tagline → uploader
    st.markdown('<section class="mf-hero" id="top"><div class="mf-container">', unsafe_allow_html=True)
    st.markdown(dedent("""
    <div class="hero-stack">
      <!-- Title row (bigger inline icon + wordmark) -->
      <a class="brand-lockup hero-title" href="#top" aria-label="VERDICT title">
        <svg class="brand-mark" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <defs>
            <linearGradient id="brandStroke2" x1="0" x2="1">
              <stop offset="0%"  stop-color="var(--brand)"/>
              <stop offset="100%" stop-color="var(--brand-2)"/>
            </linearGradient>
          </defs>
          <g fill="none" stroke="url(#brandStroke2)" stroke-width="10" opacity=".95">
            <path d="M100 10 160 70 100 130 40 70Z"/>
            <path d="M100 70 160 130 100 190 40 130Z"/>
          </g>
        </svg>
        <span class="brand-text">VERDICT</span>
      </a>

      <p class="hero-tagline">
        Upload contracts. Get clean summaries, key data &amp; risk flags.<br/>
        <span class="muted">(PDF/DOCX • English &amp; Arabic)</span>
      </p>

      <div class="upload-inline"></div>
    </div>
    """), unsafe_allow_html=True)

    up = st.file_uploader(
        "Upload contract (PDF/DOCX)",
        type=["pdf", "docx"],
        label_visibility="collapsed"
    )
    if up is not None:
        ss.uploaded_bytes = up.getvalue()
        ss.doc_name = up.name
        ss.step = "loading"
        st.rerun()

    st.markdown('</div></section>', unsafe_allow_html=True)

def screen_loading():
    st.markdown(dedent(f"""
      <div class="section-head">
        <p>Analyzing <code>{ss.doc_name or "your file"}</code>… Extracting fields, summarizing, and scanning for risks.</p>
      </div>
    """), unsafe_allow_html=True)

    p = st.progress(5)
    for pct in (12, 25, 42):
        time.sleep(0.15); p.progress(pct)
    text = parse_document(ss.uploaded_bytes, ss.doc_name)
    for pct in (55, 66):
        time.sleep(0.10); p.progress(pct)
    summary = summarize_contract(text, get_backend_config("x"))
    for pct in (74, 82):
        time.sleep(0.10); p.progress(pct)
    extracted = extract_key_data(text, get_backend_config("x"))
    risks = analyze_risk(text, get_backend_config("x"))
    for pct in (90, 100):
        time.sleep(0.10); p.progress(pct)
    ss.result = {"summary": summary, "extracted": extracted, "risks": risks, "raw_text": text}
    ss.step = "results"
    st.rerun()

def screen_results():
    st.markdown(dedent("""<div class="mf-container">"""), unsafe_allow_html=True)

    tabs = st.tabs([
        "📄 Summary","👥 Parties","📅 Key Dates","⚖️ Law & Jurisdiction",
        "📌 Obligations & Deliverables","💰 Financial Terms","⚠️ Risks"
    ])
    res = ss.result or {}
    summary = res.get("summary")
    extracted = res.get("extracted", {})
    risks = res.get("risks", [])

    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(summary or "_No summary._")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        parties = extracted.get("contracting_parties") or extracted.get("parties")
        if isinstance(parties, list):
            for p in parties: kv_row("Party", str(p))
        else:
            kv_row("Parties", parties if parties else "—")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        dates = extracted.get("key_dates", {}) or {}
        kv_row("Effective Date", dates.get("effective_date"))
        kv_row("Expiration Date", dates.get("expiration_date"))
        kv_row("Renewal Date", dates.get("renewal_date"))
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        law = extracted.get("governing_law") or extracted.get("law_and_jurisdiction")
        juris = extracted.get("jurisdiction")
        kv_row("Governing Law", law)
        kv_row("Jurisdiction", juris)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        obligations = extracted.get("obligations") or extracted.get("deliverables")
        if isinstance(obligations, list):
            for o in obligations: kv_row("Obligation", str(o))
        else:
            st.write(obligations or "—")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[5]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fin = extracted.get("financial_terms") or {}
        if isinstance(fin, dict):
            for k, v in fin.items():
                kv_row(k.replace("_", " ").title(), str(v))
        else:
            st.write(fin or "—")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[6]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if risks and isinstance(risks, (list, tuple)):
            for r in risks: st.markdown(f"- {r}")
        else:
            st.write("No explicit risks found.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(dedent("""</div>"""), unsafe_allow_html=True)

# ---- router ----
if ss.step == "home":
    screen_home()
elif ss.step == "loading":
    screen_loading()
else:
    screen_results()
