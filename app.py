from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict

import streamlit as st
from langchain_core.messages import AIMessage

from src.rag_pipeline import build_rag_chain
from src.rag_pipeline import vectorstore_exists
from src.loaders import load_files, load_urls
from src.rag_pipeline import build_vectorstore
from src.utils import get_config
from src.knowledge import quick_answer

st.set_page_config(page_title="SpartyWiz — UNCG", page_icon="📘", layout="wide")

PRIMARY = "#0b2d52"  # UNCG blue tone
ACCENT = "#f4b400"   # Gold

CUSTOM_CSS = f"""
<style>
.stApp {{
    background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 100%);
}}
header, .st-emotion-cache-18ni7ap, .stAppHeader {{
    background-color: white !important;
}}
.block-container {{
    padding-top: 3.5rem; /* Push content lower so title/logo aren't jammed at top */
}}
.chat-bubble-user {{
    background: {PRIMARY};
    color: white;
    padding: 12px 14px;
    border-radius: 16px;
}}
.chat-bubble-ai {{
    background: #f1f5f9;
    color: #0f172a;
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
}}
.source-card {{
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 10px;
    background: #ffffff;
}}
.footer-note {{
    color: #475569; font-size: 0.9rem;
}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Hero header
logo_path = Path('uncgimage.png')
if logo_path.exists():
    st.image(str(logo_path), width=160)
st.markdown(
    f"<h2 style='margin:0.25rem 0 0.75rem 0;color:{PRIMARY}'>SpartyWiz — UNCG AI Assistant</h2>",
    unsafe_allow_html=True,
)
st.caption("Ask about admissions, registrar, financial aid, IT, housing, deadlines, and more.")
if 'welcomed' not in st.session_state:
    st.info("Hey Spartan! I’m SpartyWiz—your UNCG guide. Ask me anything from deadlines to housing. I’ll keep it simple and only show links if you want them.")
    st.session_state['welcomed'] = True

cfg = get_config()
if not cfg['GROQ_API_KEY']:
    st.warning("Set GROQ_API_KEY in .env or environment to chat.")
if 'rag_built' not in st.session_state:
    st.session_state['rag_built'] = False

@st.cache_resource(show_spinner=True)
def get_chain():
    chain, retriever = build_rag_chain()
    return chain, retriever

# Replace sidebar with UNCG help & quick links
with st.sidebar:
    st.header("UNCG Help & Info")
    st.markdown("- Emergency: 911 or (336) 334-4444 (UNCG Police)")
    st.markdown("- IT Service Desk: (336) 256-8324 | 6-TECH@uncg.edu")
    st.markdown("- Financial Aid: finaid@uncg.edu | (336) 334-5702")
    st.markdown("- Registrar: registrar@uncg.edu | (336) 334-5946")
    st.markdown("- Housing & Residence Life: hrl@uncg.edu | (336) 334-5636")
    st.markdown("---")
    st.markdown("Tips: Use specific terms like 'drop deadline' or 'reset password'.")
    st.markdown("This assistant cites sources; always verify time-sensitive policies.")
    st.markdown("---")
    show_src = st.toggle("Show sources", value=False, help="Include 1–3 official links when available")

st.markdown("---")

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'profile' not in st.session_state:
    st.session_state.profile = {"name": None, "role": None, "program": None}
if 'ack_idx' not in st.session_state:
    st.session_state.ack_idx = 0

def extract_profile(text: str, profile: Dict[str, str]) -> Dict[str, str]:
    """Very lightweight extractor for name/role/program; avoids sensitive data."""
    t = text.lower()
    if ("my name is" in t or t.startswith("i am ")) and not profile.get("name"):
        # Naive name grab: words after 'my name is' up to punctuation
        try:
            import re
            m = re.search(r"my name is\s+([a-zA-Z\-']{2,}(?:\s+[a-zA-Z\-']{2,}){0,2})", t)
            if m:
                profile["name"] = m.group(1).title()
        except Exception:
            pass
    if "transfer student" in t and not profile.get("role"):
        profile["role"] = "transfer"
    elif "graduate student" in t and not profile.get("role"):
        profile["role"] = "graduate"
    elif "undergrad" in t or "undergraduate" in t and not profile.get("role"):
        profile["role"] = "undergraduate"
    # Program keyword hints
    if "erm" in t and not profile.get("program"):
        profile["program"] = "ERM"
    return profile

def friendly_prefix(question: str) -> str:
    """Occasionally add a short, friendly prefix instead of repeating the question.
    Rotates options and only uses them sometimes to avoid sounding scripted.
    """
    q = (question or "").strip()
    # advance a small counter to vary behavior
    st.session_state.ack_idx = (st.session_state.ack_idx + 1) % 6
    # Only prefix roughly 1/3 of the time and skip for long inputs
    if len(q) > 120 or st.session_state.ack_idx not in {0, 3}:
        return ""
    options = [
        "Sure —",
        "On it —",
        "Here you go —",
        "Happy to help —",
    ]
    return options[st.session_state.ack_idx % len(options)]

user_q = st.chat_input("Type your question… e.g., 'What are the key registration deadlines?'")

# Lazy init chain
if not st.session_state['rag_built']:
    try:
        chain, retriever = get_chain()
        st.session_state['chain'] = chain
        st.session_state['retriever'] = retriever
        st.session_state['rag_built'] = True
    except Exception as e:
        # Friendly recovery UI
        cfg = get_config()
        idx_ok = vectorstore_exists(cfg['VECTOR_DIR'])
        st.error(
            "Could not initialize RAG chain. If this is your first run, please build the index.")
        with st.expander("Build index now (quick setup)", expanded=not idx_ok):
            st.write("Add public UNCG URLs (optional). We'll also index any files under the data/ folder.")
            urls_txt = st.text_area(
                "URLs (one per line)",
                value="https://www.uncg.edu/\nhttps://reg.uncg.edu/",
                height=120,
            )
            if st.button("Build Index"):
                with st.spinner("Building FAISS index…"):
                    file_docs = load_files(["data"])  # PDFs/MDs
                    url_list = [u.strip() for u in urls_txt.splitlines() if u.strip()]
                    url_docs = load_urls(url_list)
                    docs = file_docs + url_docs
                    if not docs:
                        st.warning("No documents found. Add PDFs/MDs to data/ or provide URLs.")
                    else:
                        try:
                            build_vectorstore(
                                docs,
                                vector_dir=cfg['VECTOR_DIR'],
                                embed_model=cfg['EMBED_MODEL'],
                                chunk_size=cfg['CHUNK_SIZE'],
                                chunk_overlap=cfg['CHUNK_OVERLAP'],
                            )
                            st.success("Index built! Reloading chain…")
                            # Re-init chain
                            chain, retriever = get_chain()
                            st.session_state['chain'] = chain
                            st.session_state['retriever'] = retriever
                            st.session_state['rag_built'] = True
                            st.rerun()
                        except Exception as ie:
                            st.error(f"Index build failed: {ie}")

# Quick suggestions
with st.container():
    st.caption("Try one:")
    cols = st.columns(5)
    suggestions = [
        "What are the registration deadlines this semester?",
        "How do I contact Financial Aid?",
        "What are the undergrad admissions requirements?",
        "How can I reset my UNCG password?",
        "Where can graduate students find housing info?",
    ]
    for i, text in enumerate(suggestions):
        if cols[i].button(text, use_container_width=True):
            user_q = text

# Render history
for msg in st.session_state.messages:
    role_class = 'chat-bubble-user' if msg['role'] == 'user' else 'chat-bubble-ai'
    st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)

if user_q and st.session_state.get('chain'):
    st.session_state.messages.append({"role": "user", "content": user_q})
    # Update profile from the latest user message (no sensitive info)
    st.session_state.profile = extract_profile(user_q, st.session_state.profile)
    with st.spinner("Thinking…"):
        try:
            # Quick-answer from curated facts/programs
            qa = quick_answer(user_q, st.session_state.profile)
            if qa:
                base, srcs = qa
                prefix = friendly_prefix(user_q)
                answer = (prefix + "\n\n" if prefix else "") + base
                links = [f"- [{u}]({u})" for u in srcs if isinstance(u, str) and u.startswith("http")][:2]
                if show_src and links:
                    answer += "\n\n**Sources**:\n" + "\n".join(links)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
                raise SystemExit
            # Retrieve sources separately for explicit citation rendering
            retriever = st.session_state['retriever']
            # New retriever API
            chat_history_text = "\n".join(
                f"{m['role']}: {m['content']}" for m in st.session_state.messages[-8:]
            )
            docs = retriever.invoke({"input": user_q, "chat_history": chat_history_text})[:5]
            ai_msg: AIMessage = st.session_state['chain'].invoke({
                "question": user_q,
                "chat_history": chat_history_text,
                "profile": st.session_state.profile,
            })
            # Friendly prefix occasionally (do not repeat the question every time)
            prefix = friendly_prefix(user_q)
            answer = (prefix + "\n\n" if prefix else "") + ai_msg.content
            # Build sources UI block
            links = []
            if docs:
                seen = set()
                for d in docs:
                    meta = d.metadata or {}
                    src = meta.get('source') or ''
                    title = meta.get('title') or Path(src).stem if src else 'Document'
                    key = (title, src)
                    if key in seen:
                        continue
                    seen.add(key)
                    if src.startswith('http') and len(links) < 3:
                        links.append(f"- [{title}]({src})")
            if show_src and links:
                answer = answer + "\n\n**Sources**:\n" + "\n".join(links)
        except Exception as e:
            answer = f"I couldn't complete that request. Please try again. (Error: {e})"
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div class='footer-note'>SpartyWiz provides helpful guidance based on retrieved UNCG sources. Always verify time-sensitive policies on official pages.</div>",
    unsafe_allow_html=True,
)
