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

# ---------------- Demo stubs ----------------
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

# ---------------- Page + theme ----------------
st.set_page_config(page_title="VERDICT", layout="wide")
THEME_PATH = APP / "theme.css"
if THEME_PATH.exists():
    st.markdown(dedent(f"<style>{THEME_PATH.read_text()}</style>"), unsafe_allow_html=True)

# ---------- Custom Header ----------
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
        <!-- point to real pages; design unchanged -->
        <li><a class="nav-pill" href="/Upload">Upload</a></li>
        <li><a class="nav-pill" href="/Create">Create</a></li>
        <li><a class="nav-pill" href="/Edit">Edit</a></li>
    </ul>
  </nav>
</header>
"""), unsafe_allow_html=True)

# ---------------- Session ----------------
ss = st.session_state
ss.setdefault("step", "home")
ss.setdefault("doc_name", None)
ss.setdefault("uploaded_bytes", None)
ss.setdefault("result", None)
ss.setdefault("chat", [{"role":"assistant","text":"Hi! How can I help you with this contract?"}])
ss.setdefault("clear_compose", False)

# ---------------- Screens ----------------
def screen_home():
    # Hero (unchanged)
    st.markdown(
        """
        <main id="top">
          <section class="hero-block hero-tight">
            <div class="hero-content">
              <h1 class="hero-title">VERDICT</h1>
              <p class="hero-subtitle">
              </p>
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
        up = st.file_uploader("Upload contract (PDF/DOCX)", type=["pdf", "docx"],
                              label_visibility="collapsed", key="home_uploader")
        if up is not None:
            ss.uploaded_bytes = up.getvalue()
            ss.doc_name = up.name
            ss.result = None                  # clear previous results
            ss.pending_upload = True          # tell Results to process it
            st.switch_page("/Results")        # go to real Results page (URL updates)


    # ===== 2) Create (card with button INSIDE) =====
    st.markdown('<span id="create"></span><div class="anchor-spacer"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<span class="sc-card sc-create-flag"></span>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="section-heading">
              <div class="kicker">②</div>
              <h2>Create a New Contract</h2>
            </div>
            <p class="section-desc">
              Pick industry, subject, and governing law. We prefill jurisdiction-aware clauses so you start with a clean draft.
            </p>
            """,
            unsafe_allow_html=True
        )
        # centered button inside the same card → link to Create page
        c1, _ = st.columns([1,5])
        with c1:
            st.link_button("Go to Create", "/Create", key="home_go_create")

    # ===== 3) Edit (card with button INSIDE) =====
    st.markdown('<span id="edit"></span><div class="anchor-spacer"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<span class="sc-card sc-edit-flag"></span>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="section-heading">
              <div class="kicker">③</div>
              <h2>Edit a Contract Inline</h2>
            </div>
            <p class="section-desc">
              Paste or upload text to tweak clauses and metadata on-screen, then export. (Demo stub — wire this next.)
            </p>
            """,
            unsafe_allow_html=True
        )
        e1, _ = st.columns([1,5])
        with e1:
            # keep your disabled logic if you want to gate access
            disabled = ss.get("result") is None
            st.link_button("Go to Edit", "/Edit", key="home_go_edit", disabled=disabled)

def screen_loading():
    st.markdown(dedent(f"""
      <div class="section-head">
        <p>Analyzing <code>{ss.doc_name or "your file"}</code>… Extracting fields, summarizing, and scanning for risks.</p>
      </div>
    """), unsafe_allow_html=True)

    p = st.progress(5)
    for pct in (12, 25, 42): time.sleep(0.15); p.progress(pct)
    text = parse_document(ss.uploaded_bytes, ss.doc_name)
    for pct in (55, 66): time.sleep(0.10); p.progress(pct)
    summary = summarize_contract(text, get_backend_config("x"))
    for pct in (74, 82): time.sleep(0.10); p.progress(pct)
    extracted = extract_key_data(text, get_backend_config("x"))
    risks = analyze_risk(text, get_backend_config("x"))
    for pct in (90, 100): time.sleep(0.10); p.progress(pct)
    ss.result = {"summary": summary, "extracted": extracted, "risks": risks, "raw_text": text}
    ss.step = "results"
    st.rerun()

def screen_results():
    st.markdown(dedent("""<div class="mf-container results-wrap">"""), unsafe_allow_html=True)
    left_col, right_col = st.columns([14, 10], gap="small")

    with left_col:
        tabs = st.tabs([
            "📄 Summary","👥 Parties","📅 Key Dates","⚖️ Law & Jurisdiction",
            "📌 Obligations & Deliverables","💰 Financial Terms","⚠️ Risks"
        ])
        res = ss.result or {}
        summary = res.get("summary")
        extracted = res.get("extracted", {})
        risks = res.get("risks", [])

        with tabs[0]:
            safe_summary = (summary or "_No summary._").replace("\n", "<br>")
            st.markdown(f'<div class="card">{safe_summary}</div>', unsafe_allow_html=True)

        with tabs[1]:
            parties = extracted.get("contracting_parties") or extracted.get("parties")
            if isinstance(parties, list):
                inner = "".join(
                    f'<div class="kv"><div class="kv-key">Party</div><div class="kv-value">{str(p)}</div></div>'
                    for p in parties
                )
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

    base_clauses = DEFAULTS.get((industry, service), [])
    law_clauses  = LAW_PATCH.get(law, [])
    draft = f"# {service}\n\n" \
            f"**Industry:** {industry}\n" \
            f"**Governing Law:** {law}\n" \
            f"**Jurisdiction:** {forum}\n\n" \
            "## Clauses\n" + "".join([f"- {c}\n" for c in base_clauses + law_clauses])

    st.markdown("### Draft (auto-tailored)")
    st.text_area("Generated draft", value=draft, height=280, label_visibility="collapsed")

    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Use this draft", type="primary"):
            ss.step = "results"
            st.rerun()
    with colB:
        st.download_button("Download .txt", draft.encode("utf-8"), file_name="contract_draft.txt")

    st.markdown(dedent("""</div>"""), unsafe_allow_html=True)

# ---------------- Router ----------------
if ss.step == "home":
    screen_home()
elif ss.step == "loading":
    screen_loading()
elif ss.step == "form":
    screen_form()
else:
    screen_results()
