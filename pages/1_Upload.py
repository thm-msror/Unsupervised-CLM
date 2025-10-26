# pages/1_Upload.py
import os
import json
import tempfile
from pathlib import Path
from textwrap import dedent
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="VERDICT — Upload", layout="wide")

# Import all necessary functions from main.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.doc_reader import read_docu
from src.rag.rag_model import TfidfIndex
import google.generativeai as genai

# Initialize session state
if 'upload_analysis_results' not in st.session_state:
    st.session_state.upload_analysis_results = []
if 'upload_current_analysis' not in st.session_state:
    st.session_state.upload_current_analysis = None
if 'upload_rag_index' not in st.session_state:
    st.session_state.upload_rag_index = None
if 'upload_rag_built' not in st.session_state:
    st.session_state.upload_rag_built = False
if 'upload_chat_history' not in st.session_state:
    st.session_state.upload_chat_history = []

# Helper functions (copied from main.py)
def get_backend_config():
    """Returns the Gemini model configuration"""
    return {
        "model_name": "gemini-2.5-pro-preview-03-25",
        "api_key": os.getenv("GEMINI_API_KEY")
    }

def parse_document_upload(file_bytes, filename):
    """Parse uploaded document"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    
    try:
        result = read_docu(tmp_path)
        
        # Save parsed data
        parsed_dir = Path("data/parsed")
        parsed_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"{Path(filename).stem}_{timestamp}.json"
        json_path = parsed_dir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result, str(json_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def analyze_text_with_gemini_upload(parsed_data, json_path):
    """Analyze contract using Gemini API"""
    config = get_backend_config()
    genai.configure(api_key=config["api_key"])
    model = genai.GenerativeModel(config["model_name"])
    
    # Create analysis prompt
    text_content = parsed_data.get('text', '')
    
    prompt = f"""Analyze this contract thoroughly and provide a comprehensive analysis covering:

1. Contract Overview
2. Key Parties and Their Roles
3. Important Dates and Deadlines
4. Legal Framework and Governing Law
5. Main Obligations and Responsibilities
6. Financial Terms and Conditions
7. Risk Analysis and Potential Issues

Contract Text:
{text_content}

Provide a detailed, structured analysis."""

    response = model.generate_content(prompt)
    analysis_text = response.text
    
    # Save analysis
    analysis_dir = Path("data/analysis")
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Path(json_path).stem
    analysis_filename = f"{filename}_analysis_{timestamp}.txt"
    analysis_path = analysis_dir / analysis_filename
    
    with open(analysis_path, 'w', encoding='utf-8') as f:
        f.write(analysis_text)
    
    return {
        'content': analysis_text,
        'file_path': str(analysis_path),
        'timestamp': timestamp,
        'source_file': Path(json_path).name
    }

def build_rag_index_upload(analysis_text):
    """Build RAG index from analysis"""
    try:
        index = TfidfIndex()
        sections = analysis_text.split('\n\n')
        documents = [s.strip() for s in sections if s.strip()]
        index.build_index(documents)
        return index
    except Exception as e:
        st.error(f"Error building RAG index: {e}")
        return None

def answer_question_upload(question, rag_index, analysis_text):
    """Answer question using RAG"""
    if not rag_index:
        return "RAG index not available. Please analyze a document first."
    
    try:
        config = get_backend_config()
        genai.configure(api_key=config["api_key"])
        model = genai.GenerativeModel(config["model_name"])
        
        # Get relevant context from RAG
        results = rag_index.search(question, top_k=3)
        context = "\n\n".join([doc for doc, _ in results])
        
        # Generate answer
        prompt = f"""Based on the following contract analysis context, answer the question:

Context:
{context}

Question: {question}

Provide a clear, concise answer based only on the information in the context."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating answer: {e}"

# Load custom CSS
css_file = Path(__file__).parent.parent / "app" / "theme.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
st.markdown("""
<header class="mf-header">
  <nav class="mf-nav">
    <a href="/" class="brand-lockup" target="_self">
      <img src="https://i.imgur.com/nSd8jWD.png" class="brand-mark" alt="VERDICT">
      <div class="brand-text">VERDICT</div>
    </a>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/Upload">Upload</a></li>
      <li><a href="/Create">Create</a></li>
      <li><a href="/Edit">Edit</a></li>
    </ul>
  </nav>
</header>
""", unsafe_allow_html=True)

st.markdown(dedent("""
<main id="top">
  <section class="hero-block hero-tight">
    <div class="hero-content">
      <h1 class="hero-title">Upload & Analyze Contract</h1>
      <p class="hero-subtitle">Upload a PDF/DOCX contract for comprehensive AI-powered analysis</p>
    </div>
  </section>
</main>
"""), unsafe_allow_html=True)

# Upload section
st.markdown('<span class="sc-card sc-upload-flag"></span>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload contract (PDF/DOCX)", 
    type=["pdf", "docx"], 
    label_visibility="collapsed",
    key="upload_page_file"
)

if uploaded_file is not None:
    with st.spinner("📄 Parsing document..."):
        parsed_data, json_path = parse_document_upload(uploaded_file.getvalue(), uploaded_file.name)
        st.success(f"✅ Document parsed: {uploaded_file.name}")
    
    with st.spinner("🤖 Analyzing contract with Gemini AI..."):
        analysis = analyze_text_with_gemini_upload(parsed_data, json_path)
        st.session_state.upload_current_analysis = analysis
        
        # Build RAG index in background
        rag_index = build_rag_index_upload(analysis['content'])
        st.session_state.upload_rag_index = rag_index
        st.session_state.upload_rag_built = True
        
        st.success("✅ Analysis complete!")
    
    # Display analysis in tabs
    st.markdown("---")
    
    tabs = st.tabs(["📄 Full Analysis", "🌐 Arabic Translation"])
    
    with tabs[0]:
        st.markdown("### 📄 Complete Analysis")
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
                <pre style="white-space: pre-wrap; margin: 0; font-size: 14px; line-height: 1.6; color: #f2f4fb;">{analysis['content']}</pre>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with tabs[1]:
        st.markdown("### 🌐 Arabic Translation")
        
        try:
            from src.translation_utils import (
                translate_to_arabic, 
                save_arabic_translation, 
                load_arabic_translation,
                has_arabic_translation
            )
            
            file_path = analysis.get('file_path', '')
            arabic_exists = has_arabic_translation(file_path) if file_path else False
            
            if arabic_exists:
                arabic_text = load_arabic_translation(file_path)
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
                        direction: rtl;
                        text-align: right;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    ">
                        <pre style="white-space: pre-wrap; margin: 0; font-size: 14px; line-height: 1.6; color: #f2f4fb; direction: rtl;">{arabic_text}</pre>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                if st.button("🌐 Translate to Arabic", key="translate_btn"):
                    with st.spinner("Translating to Arabic..."):
                        arabic_text = translate_to_arabic(analysis['content'])
                        save_arabic_translation(file_path, arabic_text)
                        st.success("✅ Translation complete!")
                        st.rerun()
        except Exception as e:
            st.error(f"Translation feature unavailable: {e}")
    
    # Q&A Section
    st.markdown("---")
    st.markdown("### 💬 Ask Questions About This Contract")
    
    if st.session_state.upload_rag_built:
        question = st.text_input(
            "Ask a question about the contract",
            placeholder="e.g., What are the main obligations?",
            key="upload_question"
        )
        
        if st.button("Ask", key="upload_ask_btn"):
            if question:
                with st.spinner("Analyzing..."):
                    answer = answer_question_upload(
                        question,
                        st.session_state.upload_rag_index,
                        st.session_state.upload_current_analysis['content']
                    )
                    
                    st.session_state.upload_chat_history.append({
                        "question": question,
                        "answer": answer
                    })
        
        # Display chat history
        if st.session_state.upload_chat_history:
            st.markdown("#### Conversation History")
            for i, chat in enumerate(st.session_state.upload_chat_history):
                st.markdown(f"**Q{i+1}:** {chat['question']}")
                st.markdown(f"**A{i+1}:** {chat['answer']}")
                st.markdown("---")

