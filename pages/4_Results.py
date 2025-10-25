# pages/4_Results.py
import time
from textwrap import dedent
import streamlit as st

st.set_page_config(page_title="VERDICT — Results", layout="wide")

# --- theme + header (same look as other pages) ---
from app.shared import use_theme, header
use_theme(); header()

# --- import demo stubs so this page can process uploads ---
from app.shared import (
    get_backend_config,
    parse_document,
    summarize_contract,
    extract_key_data,
    analyze_risk,
)

# ============== Session ==============
ss = st.session_state
ss.setdefault("result", None)
ss.setdefault("uploaded_bytes", None)
ss.setdefault("doc_name", None)
ss.setdefault("pending_upload", False)
ss.setdefault("chat", [{"role": "assistant", "text": "Hi! How can I help you with this contract?"}])
ss.setdefault("compose_text", "")

# ============== Process a fresh upload (from Home or Upload page) ==============
if ss.get("pending_upload") and ss.get("uploaded_bytes"):
    with st.spinner(f"Analyzing {ss.get('doc_name', 'your file')}…"):
        time.sleep(0.15)  # brief spinner
        text = parse_document(ss.uploaded_bytes, ss.doc_name)
        summary = summarize_contract(text, get_backend_config("x"))
        extracted = extract_key_data(text, get_backend_config("x"))
        risks = analyze_risk(text, get_backend_config("x"))
        ss.result = {
            "summary": summary,
            "extracted": extracted,
            "risks": risks,
            "raw_text": text,
        }
    ss.pending_upload = False

# Guard: if no data yet, route user to Upload
if not ss.get("result"):
    st.info("No document uploaded yet.")
    st.link_button("Go to Upload", "/Upload")
    st.stop()

# ============== Results UI (unchanged styling) ==============
st.markdown(dedent("""<div class="mf-container results-wrap">"""), unsafe_allow_html=True)

left_col, right_col = st.columns([14, 10], gap="small")

with left_col:
    tabs = st.tabs([
        "📄 Summary",
        "👥 Parties",
        "📅 Key Dates",
        "⚖️ Law & Jurisdiction",
        "📌 Obligations & Deliverables",
        "💰 Financial Terms",
        "⚠️ Risks",
    ])

    res = ss.result or {}
    summary = res.get("summary")
    extracted = res.get("extracted", {})
    risks = res.get("risks", [])

    # Summary
    with tabs[0]:
        safe_summary = (summary or "_No summary._").replace("\n", "<br>")
        st.markdown(f'<div class="card">{safe_summary}</div>', unsafe_allow_html=True)

    # Parties
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

    # Key Dates
    with tabs[2]:
        d = extracted.get("key_dates", {}) or {}
        inner = "".join([
            f'<div class="kv"><div class="kv-key">Effective Date</div><div class="kv-value">{d.get("effective_date") or "—"}</div></div>',
            f'<div class="kv"><div class="kv-key">Expiration Date</div><div class="kv-value">{d.get("expiration_date") or "—"}</div></div>',
            f'<div class="kv"><div class="kv-key">Renewal Date</div><div class="kv-value">{d.get("renewal_date") or "—"}</div></div>',
        ])
        st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

    # Law & Jurisdiction
    with tabs[3]:
        law = extracted.get("governing_law") or extracted.get("law_and_jurisdiction")
        juris = extracted.get("jurisdiction")
        inner = "".join([
            f'<div class="kv"><div class="kv-key">Governing Law</div><div class="kv-value">{law or "—"}</div></div>',
            f'<div class="kv"><div class="kv-key">Jurisdiction</div><div class="kv-value">{juris or "—"}</div></div>',
        ])
        st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

    # Obligations & Deliverables
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

    # Financial Terms
    with tabs[5]:
        fin = extracted.get("financial_terms") or {}
        if isinstance(fin, dict):
            inner = "".join(
                f'<div class="kv"><div class="kv-key">{k.replace("_"," ").title()}</div>'
                f'<div class="kv-value">{str(v)}</div></div>'
                for k, v in fin.items()
            )
        else:
            inner = f'<div class="kv"><div class="kv-key">Financial Terms</div><div class="kv-value">{fin or "—"}</div></div>'
        # IMPORTANT: no extra parenthesis here!
        st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

    # Risks
    with tabs[6]:
        if risks and isinstance(risks, (list, tuple)):
            inner = "<ul>" + "".join(f"<li>{str(r)}</li>" for r in risks) + "</ul>"
        else:
            inner = "No explicit risks found."
        st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

with right_col:
    # ---- chat transcript ----
    bubbles = []
    # seed greeting if somehow empty
    if not ss.get("chat"):
        ss.chat = [{"role": "assistant", "text": "Hi! How can I help you with this contract?"}]
    for m in ss["chat"]:
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

    # ---- compose row (textbox + send button) ----
    st.markdown('<div class="chat-compose">', unsafe_allow_html=True)
    with st.form("compose", clear_on_submit=True):
        c1, c2 = st.columns([10, 2])
        with c1:
            st.text_input(
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
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
