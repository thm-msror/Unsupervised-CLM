#!/usr/bin/env python3
"""
CLM AI — 3-screen Streamlit app (FE-first, stubs for backend):
1) Home (Masjid-style hero with centered upload)
2) Loading (progress while parsing/analysis)
3) Results (clean text header + tabs with glass cards)
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

# ---------------- FE-only fallbacks (Option B) ----------------
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
    if name.endswith(".pdf"):
        return "DEMO TEXT (PDF): parser disabled during FE sprint."
    if name.endswith(".docx"):
        return "DEMO TEXT (DOCX): parser disabled during FE sprint."
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return "DEMO TEXT: unsupported file; parser disabled."

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

# ---- Streamlit page + theme ----
st.set_page_config(page_title="CLM AI", page_icon="🤖", layout="centered")
THEME_PATH = APP / "theme.css"
if THEME_PATH.exists():
    st.markdown(f"<style>{THEME_PATH.read_text()}</style>", unsafe_allow_html=True)

# ---- Sticky header (Masjid-style) ----
st.markdown(
"""<div class="mf-header">
  <div class="mf-nav">
    <a class="mf-brand" href="#top" aria-label="CLM AI home">
      <span class="mf-logo" aria-hidden="true">✦</span>
      <span>CLM AI</span>
    </a>
    <div class="mf-links">
      <a class="active" href="#top">Home</a>
      <a href="#results">Results</a>
    </div>
  </div>
</div>""",
    unsafe_allow_html=True,
)

# ---- session state ----
ss = st.session_state
ss.setdefault("step", "home")           # "home" | "loading" | "results"
ss.setdefault("doc_name", None)
ss.setdefault("uploaded_bytes", None)
ss.setdefault("result", None)

# ---- UI helper ----
def kv_row(label: str, value: str | None):
    st.markdown(
        f"""<div class="kv">
          <div class="kv-key">{label}</div>
          <div class="kv-value">{value or "—"}</div>
        </div>""",
        unsafe_allow_html=True
    )

# ---- Screens ----
def screen_home():
    st.markdown(
"""<section class="mf-hero" id="top" aria-label="Welcome">
  <div class="mf-container mf-hero-grid">
    <div>
      <div class="hero-copy" style="text-align:center">
        <h1 class="mf-title" style="margin-top:6px">CLM AI</h1>
        <div class="mf-sub" style="margin-top:8px">
          Upload contracts. Get clean summaries, key data & risk flags.
          (PDF/DOCX • English & Arabic)
        </div>
        <div class="upload-inline"></div>
      </div>
    </div>
    <div class="mf-card" aria-hidden="true">
      <svg viewBox="0 0 400 360" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <linearGradient id="g" x1="0" x2="1">
            <stop offset="0%" stop-color="var(--brand)" />
            <stop offset="100%" stop-color="var(--brand-2)" />
          </linearGradient>
        </defs>
        <g fill="none" stroke="url(#g)" stroke-width="2" opacity=".9">
          <path d="M200 20l60 60-60 60-60-60 60-60Z" />
          <path d="M200 80l60 60-60 60-60-60 60-60Z" />
          <path d="M200 140l60 60-60 60-60-60 60-60Z" />
          <path d="M200 200l60 60-60 60-60-60 60-60Z" />
          <circle cx="200" cy="180" r="150" opacity=".25" />
          <circle cx="200" cy="180" r="110" opacity=".35" />
        </g>
      </svg>
    </div>
  </div>
</section>""",
        unsafe_allow_html=True,
    )

    up = st.file_uploader(
        label="Upload contract (PDF/DOCX)",
        type=["pdf", "docx"],
        label_visibility="collapsed"
    )
    if up is not None:
        ss.uploaded_bytes = up.getvalue()
        ss.doc_name = up.name
        ss.step = "loading"
        st.rerun()

def screen_loading():
    st.markdown(
        f"""<div class="section-head">
          <h2>Analyzing <code>{ss.doc_name or "your file"}</code>…</h2>
          <p>Extracting fields, summarizing, and scanning for risks.</p>
        </div>""",
        unsafe_allow_html=True
    )
    p = st.progress(5)
    for pct in (12, 25, 42):
        time.sleep(0.15); p.progress(pct)
    text = parse_document(ss.uploaded_bytes, ss.doc_name)
    for pct in (55, 66):
        time.sleep(0.1); p.progress(pct)
    summary = summarize_contract(text, get_backend_config("x"))
    for pct in (74, 82):
        time.sleep(0.1); p.progress(pct)
    extracted = extract_key_data(text, get_backend_config("x"))
    risks = analyze_risk(text, get_backend_config("x"))
    for pct in (90, 100):
        time.sleep(0.1); p.progress(pct)
    ss.result = {"summary": summary, "extracted": extracted, "risks": risks, "raw_text": text}
    ss.step = "results"
    st.rerun()

def screen_results():
    st.markdown(
        f"""<div class="section-head" id="results">
          <h2>Results for <code>{ss.doc_name}</code></h2>
          <p>Explore the tabs below.</p>
        </div>""",
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
            for p in parties:
                kv_row("Party", str(p))
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
            for o in obligations:
                kv_row("Obligation", str(o))
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
