# pages/4_Results.py
import streamlit as st
from app.shared import use_theme, header

st.set_page_config(page_title="VERDICT — Results", layout="wide")
use_theme()
header()

res = st.session_state.get("result")

st.markdown('<div class="mf-container results-wrap">', unsafe_allow_html=True)

if not res:
    st.info("No results yet. Upload a contract or create a draft first.")
    st.link_button("Go to Upload", "/Upload")
else:
    left_col, right_col = st.columns([14, 10], gap="small")

    with left_col:
        tabs = st.tabs([
            "📄 Summary","👥 Parties","📅 Key Dates","⚖️ Law & Jurisdiction",
            "📌 Obligations & Deliverables","💰 Financial Terms","⚠️ Risks"
        ])
        summary     = res.get("summary")
        extracted   = res.get("extracted", {})
        risks       = res.get("risks", [])

        with tabs[0]:
            safe = (summary or "_No summary._").replace("\n","<br>")
            st.markdown(f'<div class="card">{safe}</div>', unsafe_allow_html=True)

        with tabs[1]:
            parties = extracted.get("contracting_parties") or extracted.get("parties")
            if isinstance(parties, list):
                inner = "".join(f'<div class="kv"><div class="kv-key">Party</div><div class="kv-value">{p}</div></div>' for p in parties)
            else:
                inner = f'<div class="kv"><div class="kv-key">Parties</div><div class="kv-value">{parties or "—"}</div></div>'
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[2]:
            d = extracted.get("key_dates", {}) or {}
            inner = "".join([
                f'<div class="kv"><div class="kv-key">Effective Date</div><div class="kv-value">{d.get("effective_date","—")}</div></div>',
                f'<div class="kv"><div class="kv-key">Expiration Date</div><div class="kv-value">{d.get("expiration_date","—")}</div></div>',
                f'<div class="kv"><div class="kv-key">Renewal Date</div><div class="kv-value">{d.get("renewal_date","—")}</div></div>',
            ])
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[3]:
            law   = extracted.get("governing_law") or extracted.get("law_and_jurisdiction")
            juris = extracted.get("jurisdiction")
            inner = "".join([
                f'<div class="kv"><div class="kv-key">Governing Law</div><div class="kv-value">{law or "—"}</div></div>',
                f'<div class="kv"><div class="kv-key">Jurisdiction</div><div class="kv-value">{juris or "—"}</div></div>',
            ])
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[4]:
            obligations = extracted.get("obligations") or extracted.get("deliverables")
            if isinstance(obligations, list):
                inner = "".join(f'<div class="kv"><div class="kv-key">Obligation</div><div class="kv-value">{o}</div></div>' for o in obligations)
            else:
                inner = f'<div class="kv"><div class="kv-key">Obligations</div><div class="kv-value">{obligations or "—"}</div></div>'
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[5]:
            fin = extracted.get("financial_terms") or {}
            if isinstance(fin, dict):
                inner = "".join(f'<div class="kv"><div class="kv-key">{k.replace("_"," ").title()}</div><div class="kv-value">{v}</div></div>' for k,v in fin.items())
            else:
                inner = f'<div class="kv"><div class="kv-key">Financial Terms</div><div class="kv-value">{fin or "—"}</div></div>'
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

        with tabs[6]:
            if risks:
                inner = "<ul>" + "".join(f"<li>{r}</li>" for r in risks) + "</ul>"
            else:
                inner = "No explicit risks found."
            st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)

    with right_col:
        chat = st.session_state.setdefault("chat", [{"role":"assistant","text":"Hi! How can I help you with this contract?"}])

        bubbles = []
        for m in chat:
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
            c1, c2 = st.columns([10,2])
            with c1:
                msg = st.text_input("Ask the assistant about this contract…", key="compose_text", label_visibility="collapsed")
            with c2:
                submitted = st.form_submit_button("Send", use_container_width=True)
            if submitted:
                text = (st.session_state.get("compose_text") or "").strip()
                if text:
                    chat.append({"role":"user","text":text})
                    chat.append({"role":"assistant","text":"Demo: backend not wired yet."})
                st.session_state["chat"] = chat
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
