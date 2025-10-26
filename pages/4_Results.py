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
        "📄 Full Analysis",
        "🌐 Arabic Translation"
    ])

    res = ss.result or {}
    summary = res.get("summary")
    extracted = res.get("extracted", {})
    risks = res.get("risks", [])
    raw_text = res.get("raw_text", "")

    # Full Analysis tab - show complete analysis
    with tabs[0]:
        st.markdown("### 📄 Complete Analysis")
        
        # Combine all sections into full analysis display
        full_analysis = f"""
**Summary:**
{summary or "_No summary available._"}

---

**Key Parties:**
{extracted.get("contracting_parties") or extracted.get("parties") or "—"}

---

**Key Dates:**
- Effective Date: {(extracted.get("key_dates", {}) or {}).get("effective_date") or "—"}
- Expiration Date: {(extracted.get("key_dates", {}) or {}).get("expiration_date") or "—"}
- Renewal Date: {(extracted.get("key_dates", {}) or {}).get("renewal_date") or "—"}

---

**Governing Law & Jurisdiction:**
- Governing Law: {extracted.get("governing_law") or extracted.get("law_and_jurisdiction") or "—"}
- Jurisdiction: {extracted.get("jurisdiction") or "—"}

---

**Obligations & Deliverables:**
{extracted.get("obligations") or extracted.get("deliverables") or "—"}

---

**Financial Terms:**
{extracted.get("financial_terms") or "—"}

---

**Risk Analysis:**
"""
        if risks and isinstance(risks, (list, tuple)):
            full_analysis += "\n".join(f"- {str(r)}" for r in risks)
        else:
            full_analysis += "No explicit risks found."
        
        st.markdown(
            f"""
            <div style="
                background-color: #0d1933;
                border: 2px solid #1a2847;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                max-height: 600px;
                overflow-y: auto;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            ">
                <pre style="white-space: pre-wrap; margin: 0; font-size: 14px; line-height: 1.6; color: #f2f4fb;">{full_analysis}</pre>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # Arabic Translation tab
    with tabs[1]:
        st.markdown("### 🌐 Arabic Translation")
        st.info("Arabic translation feature available in main page analysis workflow.")

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
