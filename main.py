#!/usr/bin/env python3
"""
AI-Driven Contract Lifecycle Management (CLM) - Streamlit Application
Main entry point for the web application
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add the src directory to the Python path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

# Import app modules (create these later)
try:
    from app.config import load_config
    from app.utils import initialize_session_state
except ImportError:
    # Fallback if modules don't exist yet
    def load_config():
        return {"app_name": "CLM AI Hackathon"}
    def initialize_session_state():
        pass

# =============================================================================
# 🎯 Streamlit Page Configuration
# =============================================================================
st.set_page_config(
    page_title="CLM AI - Contract Lifecycle Management",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/thm-msror/Unsupervised-CLM',
        'Report a bug': 'https://github.com/thm-msror/Unsupervised-CLM/issues',
        'About': "AI-Driven Contract Lifecycle Management - AIX Hackathon 2025"
    }
)

# =============================================================================
# 🎨 Custom CSS Styling
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🚀 Main Application
# =============================================================================
def main():
    """Main Streamlit application function"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 CLM AI - Contract Lifecycle Management</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/ffffff?text=CLM+AI", 
                 caption="AI-Driven Contract Analysis")
        
        st.markdown("### 🎯 Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Home", "📄 Contract Upload", "🔍 Analysis", "📊 Dashboard", "🧪 Test API"]
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
                st.markdown(f'<p class="status-error">{status} {component}</p>', unsafe_allow_html=True)
        
        st.markdown("### 🚀 Quick Start")
        if st.button("📄 Upload Your First Contract", type="primary"):
            st.session_state.page = "📄 Contract Upload"
            st.rerun()

def show_upload_page():
    """Contract upload page"""
    st.markdown("### 📄 Upload Contract")
    
    uploaded_file = st.file_uploader(
        "Choose a contract file",
        type=['pdf', 'docx'],
        help="Upload PDF or DOCX contract files for analysis"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # File details
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size:,} bytes",
            "File type": uploaded_file.type
        }
        
        st.json(file_details)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Analyze Contract", type="primary"):
                with st.spinner("Analyzing contract..."):
                    # Placeholder for actual analysis
                    st.success("Analysis complete! Check the Analysis tab.")
        
        with col2:
            if st.button("💾 Save for Later"):
                st.info("Contract saved to session.")

def show_analysis_page():
    """Contract analysis results page"""
    st.markdown("### 🔍 Contract Analysis")
    
    if "analyzed_contract" not in st.session_state:
        st.info("📄 No contract analyzed yet. Please upload a contract first.")
        return
    
    # Sample analysis results (replace with real analysis)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Extracted Information")
        sample_data = {
            "Parties": ["ABC Corporation", "XYZ Limited"],
            "Effective Date": "January 15, 2025",
            "Duration": "12 months",
            "Governing Law": "New York State"
        }
        st.json(sample_data)
    
    with col2:
        st.markdown("#### ⚠️ Risk Assessment")
        st.error("🚨 High Risk: Automatic renewal clause detected")
        st.warning("⚠️ Medium Risk: Missing indemnification clause")
        st.success("✅ Low Risk: Standard termination provisions")

def show_dashboard_page():
    """Analytics dashboard page"""
    st.markdown("### 📊 Dashboard")
    
    # Sample metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Contracts Processed", "42", "+5")
    with col2:
        st.metric("Risk Flags", "8", "-2")
    with col3:
        st.metric("Avg Processing Time", "45s", "-10s")
    with col4:
        st.metric("Accuracy Score", "94%", "+3%")
    
    # Sample chart
    import pandas as pd
    import numpy as np
    
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['Contract Volume', 'Risk Score', 'Processing Time']
    )
    
    st.line_chart(chart_data)

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