#!/usr/bin/env python3
import os, sys, time, base64
from pathlib import Path
from textwrap import dedent
import streamlit as st

# ---------- paths ----------
ROOT = Path(__file__).parent
APP  = ROOT / "app"
ASSETS = APP / "assets"
for p in (ROOT / "src", APP):
    if str(p) not in sys.path:
        sys.path.append(str(p))

# ---------- tiny util: embed image as base64 (tries several names) ----------
def img_b64(*candidates) -> str | None:
    for name in candidates:
        p = ASSETS / name
        if p.exists():
            mime = "png" if p.suffix.lower() == ".png" else "jpeg"
            return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    return None

# ---------- Demo stubs (unchanged) ----------
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

# ---------- Page + theme ----------
st.set_page_config(page_title="VERDICT", layout="wide")
THEME_PATH = APP / "theme.css"
if THEME_PATH.exists():
    st.markdown(dedent(f"<style>{THEME_PATH.read_text()}</style>"), unsafe_allow_html=True)

# --- local CSS: center hero content + size the logo ---
st.markdown(dedent("""
<style>
  .hero-block .hero-content{ display:flex; flex-direction:column; align-items:center; }
  .hero-title-wrap{ display:flex; align-items:center; gap:.85rem; justify-content:center; }
  .hero-title{ margin:0; }
  .hero-logo{ width:84px; height:auto; border-radius:12px; box-shadow:0 10px 35px rgba(0,0,0,.35); }
  @media (max-width: 640px){ .hero-logo{ width:64px; } }
</style>
"""), unsafe_allow_html=True)

# ---------- Header (links to real pages) ----------
st.markdown(dedent("""
<header class="mf-header" id="site-header">
  <nav class="mf-nav">
    <a class="brand-lockup" href="#top" aria-label="VERDICT home">
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

# ---------- Session ----------
ss = st.session_state
ss.setdefault("step", "home")
ss.setdefault("doc_name", None)
ss.setdefault("uploaded_bytes", None)
ss.setdefault("result", None)
ss.setdefault("chat", [{"role":"assistant","text":"Hi! How can I help you with this contract?"}])
ss.setdefault("clear_compose", False)

# pre-encode logo once
HERO_LOGO = img_b64("logo1.jpeg", "logo2.jpeg", "image.png")

# ---------- Screens ----------
def screen_home():
    # Hero (centered title + logo)
    logo_html = f'<img class="hero-logo" src="{HERO_LOGO}" alt="VERDICT logo"/>' if HERO_LOGO else ""
    st.markdown(
        f"""
        <main id="top">
          <section class="hero-block hero-tight">
            <div class="hero-content">
              <div class="hero-title-wrap">
                <h1 class="hero-title">VERDICT</h1>
                {logo_html}
              </div>
              <p class="hero-subtitle"></p>
            </div>
          </section>
        </main>
        """,
        unsafe_allow_html=True
    )

    # ===== 1) Upload (card with uploader INSIDE) =====
    st.markdown('<span id="upload"></span><div class="anchor-spacer"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<span class="sc-card sc-upload-flag"></span>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="section-heading">
              <div class="kicker">①</div>
              <h2>Upload an Existing Contract</h2>
            </div>
            <p class="section-desc">
              Drop in a PDF/DOCX and we’ll produce a structured summary, key fields, and risk flags.
              You’ll also get a chat assistant on the right so you can ask questions about the contract.
            </p>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("### ⚙️ Settings")
        st.info("🔷 Using Google Gemini API for AI-powered contract analysis")
    
    # Main content based on selected page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📄 Contract Upload":
        show_upload_page()
    elif page == "🔍 Analysis":
        show_analysis_page()
    elif page == "📊 Dashboard":
        show_dashboard_page()
    elif page == "🧪 Test API":
        show_test_page()

# =============================================================================
# 📄 Page Functions
# =============================================================================
def show_home_page():
    """Homepage with overview and features"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎯 Welcome to CLM AI")
        st.write("""
        This AI-powered platform automates legal contract management, helping legal and procurement 
        teams reduce manual effort, minimize errors, and accelerate contract review processes.
        """)
        
        st.markdown("### ✨ Key Features")
        
        features = [
            ("📄", "Secure Contract Upload", "Support for PDF and DOCX files"),
            ("🤖", "AI-Powered Extraction", "Automated extraction of key contract data"),
            ("⚠️", "Risk Analysis", "Identify potential issues and missing clauses"),
            ("📊", "Smart Summarization", "AI-generated insights and summaries"),
            ("❓", "Q&A System", "Interactive questions about contract content"),
            ("🌐", "Multilingual Support", "English and Arabic contract processing")
        ]
        
        for icon, title, desc in features:
            with st.container():
                st.markdown(f"""
                <div class="feature-card">
                    <h4>{icon} {title}</h4>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🔧 System Status")
        
        # Check system components
        status_checks = check_system_status()
        
        for component, status in status_checks.items():
            if status == "✅":
                st.markdown(f'<p class="status-success">{status} {component}</p>', unsafe_allow_html=True)
            elif status == "⚠️":
                st.markdown(f'<p class="status-warning">{status} {component}</p>', unsafe_allow_html=True)
            else:
                inner = f'<div class="kv"><div class="kv-key">Parties</div><div class="kv-value">{parties or "—"}</div></div>'
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[2]:
            d = extracted.get("key_dates", {}) or {}
            inner = "".join([
                f'<div class="kv"><div class="kv-key">Effective Date</div><div class="kv-value">{d.get("effective_date") or "—"}</div></div>',
                f'<div class="kv"><div class="kv-key">Expiration Date</div><div class="kv-value">{d.get("expiration_date") or "—"}</div></div>',
                f'<div class="kv"><div class="kv-key">Renewal Date</div><div class="kv-value">{d.get("renewal_date") or "—"}</div></div>',
            ])
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[3]:
            law = extracted.get("governing_law") or extracted.get("law_and_jurisdiction")
            juris = extracted.get("jurisdiction")
            inner = "".join([
                f'<div class="kv"><div class="kv-key">Governing Law</div><div class="kv-value">{law or "—"}</div></div>',
                f'<div class="kv"><div class="kv-key">Jurisdiction</div><div class="kv-value">{juris or "—"}</div></div>',
            ])
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[4]:
            obligations = extracted.get("obligations") or extracted.get("deliverables")
            if isinstance(obligations, list):
                inner = "".join(
                    f'<div class="kv"><div class="kv-key">Obligation</div><div class="kv-value">{str(o)}</div></div>'
                    for o in obligations
                )
            else:
                inner = f'<div class="kv"><div class="kv-key">Obligations</div><div class="kv-value">{obligations or "—"}</div></div>'
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[5]:
            fin = extracted.get("financial_terms") or {}
            if isinstance(fin, dict):
                inner = "".join(
                    f'<div class="kv"><div class="kv-key">{k.replace("_"," ").title()}</div><div class="kv-value">{str(v)}</div></div>'
                    for k, v in fin.items()
                )
            else:
                inner = f'<div class="kv"><div class="kv-key">Financial Terms</div><div class="kv-value">{fin or "—"}</div></div>'
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[6]:
            if risks and isinstance(risks, (list, tuple)):
                inner = "<ul>" + "".join(f"<li>{str(r)}</li>" for r in risks) + "</ul>"
            else:
                inner = "No explicit risks found."
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

    with right_col:
        if ss.get("clear_compose"):
            ss["compose_text"] = ""
            ss["clear_compose"] = False

        bubbles = []
        for m in ss.chat:
            role_cls = "u" if m["role"] == "user" else "a"
            bubbles.append(f'<div class="bubble {role_cls}">{m["text"]}</div>')

        chat_html = (
            '<div class="chat-wrap">'
            '  <div class="chat-card">'
            '    <div class="chat-titlebar">Assistant Chat</div>'
            f'    {"".join(bubbles)}'
            '  </div>'
            '</div>'
        )
        st.markdown(chat_html, unsafe_allow_html=True)

        st.markdown('<div class="chat-compose">', unsafe_allow_html=True)
        with st.form("compose", clear_on_submit=True):
            c1, c2 = st.columns([10, 2])
            with c1:
                msg = st.text_input(
                    "Ask the assistant about this contract…",
                    key="compose_text",
                    label_visibility="collapsed",
                )
            with c2:
                submitted = st.form_submit_button("Send", use_container_width=True)

            if submitted:
                text = (ss.get("compose_text") or "").strip()
                if text:
                    ss.chat.append({"role": "user", "text": text})
                    ss.chat.append({
                        "role": "assistant",
                        "text": "Demo: I’ll analyze this once the backend is wired. Try asking about governing law, key dates, or renewal."
                    })
                ss["clear_compose"] = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def screen_form():
    st.markdown(dedent("""<div class="mf-container">"""), unsafe_allow_html=True)
    st.markdown("## Create a new contract")
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

def show_test_page():
    """API testing page"""
    st.markdown("### 🧪 Test API Connection")
    
    st.markdown("#### 🔷 Google Gemini API Test")
    
    gemini_key = st.text_input("Gemini API Key", type="password", 
                              placeholder="AIza...", help="Enter your Google AI API key")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 Test API Connection", type="primary"):
            if gemini_key:
                with st.spinner("Testing Gemini API..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content("Say 'API test successful' if you can read this.")
                        st.success("✅ Gemini API connection successful!")
                        st.info("🎯 Model: gemini-2.5-flash (latest)")
                    except Exception as e:
                        st.error(f"❌ Gemini API error: {str(e)}")
            else:
                st.error("❌ Please enter a Gemini API key")
    
    with col2:
        if st.button("📄 Test Contract Analysis"):
            if gemini_key:
                with st.spinner("Testing contract analysis..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        sample_contract = "CONSULTING AGREEMENT between ABC Corp and John Smith, effective January 2025, $150/hour, 6 months duration."
                        prompt = f"Analyze this contract and extract: parties, duration, rate, risks: {sample_contract}"
                        
                        response = model.generate_content(prompt)
                        st.success("✅ Contract analysis successful!")
                        st.text_area("Analysis Result:", response.text, height=150)
                    except Exception as e:
                        st.error(f"❌ Analysis error: {str(e)}")
            else:
                st.error("❌ Please enter a Gemini API key")

# =============================================================================
# 🔧 Helper Functions
# =============================================================================
def check_system_status():
    """Check status of system components"""
    status = {}
    
    # Check Python environment
    status["Python Environment"] = "✅"
    
    # Check required packages
    try:
        import streamlit, requests
        status["Required Packages"] = "✅"
    except ImportError:
        status["Required Packages"] = "❌"
    
    # Check .env file
    if os.path.exists(".env"):
        status[".env Configuration"] = "✅"
    else:
        status[".env Configuration"] = "⚠️"
    
    # Check Gemini API availability
    try:
        import google.generativeai
        status["Google Gemini SDK"] = "✅"
    except ImportError:
        status["Google Gemini SDK"] = "❌"
    
    return status

# =============================================================================
# 🚀 Application Entry Point
# =============================================================================
if __name__ == "__main__":
    main()
