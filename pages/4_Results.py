# pages/4_Results.py
import time
import streamlit as st
from textwrap import dedent

st.set_page_config(page_title="VERDICT — Results", layout="wide")

# theme + header (or inline like in main.py)
from app.shared import use_theme, header
use_theme(); header()

# ---- import the same demo stub funcs you used in main.py ----
from app.shared import get_backend_config, parse_document, summarize_contract, extract_key_data, analyze_risk
# If those stubs live in main.py, copy them into app/shared.py so all pages can import them.

ss = st.session_state

# If an upload just happened on any page, do the work now
if ss.get("pending_upload") and ss.get("uploaded_bytes"):
    with st.spinner(f"Analyzing {ss.get('doc_name','your file')}…"):
        time.sleep(0.15)  # just to show spinner briefly
        text = parse_document(ss.uploaded_bytes, ss.doc_name)
        summary = summarize_contract(text, get_backend_config("x"))
        extracted = extract_key_data(text, get_backend_config("x"))
        risks = analyze_risk(text, get_backend_config("x"))
        ss.result = {
            "summary": summary,
            "extracted": extracted,
            "risks": risks,
            "raw_text": text
        }
    ss.pending_upload = False

# Guard: no data yet
if not ss.get("result"):
    st.info("No document uploaded yet.")
    st.link_button("Go to Upload", "/Upload")
    st.stop()

# --------- your existing Results UI (unchanged) ----------
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
    bubbles = []
    for m in ss.get("chat", [{"role":"assistant","text":"Hi! How can I help you with this contract?"}]):
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
