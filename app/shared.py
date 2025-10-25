# app/shared.py
import os
from pathlib import Path
from textwrap import dedent
import streamlit as st

# --- THEME INJECTION (call on every page) ---
def use_theme():
    root = Path(__file__).parent
    css = (root / "theme.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- Header (same as yours, but with real page links) ---
def header():
    st.markdown(dedent("""
    <header class="mf-header" id="site-header">
      <nav class="mf-nav">
        <a class="brand-lockup" href="/" aria-label="VERDICT home">
          <svg class="brand-mark" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <defs><linearGradient id="brandStroke" x1="0" x2="1">
              <stop offset="0%"  stop-color="var(--brand)"/><stop offset="100%" stop-color="var(--brand-2)"/>
            </linearGradient></defs>
            <g fill="none" stroke="url(#brandStroke)" stroke-width="10" opacity=".95">
              <path d="M100 10 160 70 100 130 40 70Z"/><path d="M100 70 160 130 100 190 40 130Z"/>
            </g>
          </svg>
          <span class="brand-text">VERDICT</span>
        </a>
        <ul class="nav-links nav-right">
          <li><a class="nav-pill" href="/Upload">Upload</a></li>
          <li><a class="nav-pill" href="/Create">Create</a></li>
          <li><a class="nav-pill" href="/Edit">Edit</a></li>
        </ul>
      </nav>
    </header>
    """), unsafe_allow_html=True)

# --- Demo backend stubs (unchanged) ---
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
