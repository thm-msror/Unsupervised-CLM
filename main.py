#!/usr/bin/env python3
import os, sys, time, base64
from pathlib import Path
from textwrap import dedent
import streamlit as st
from datetime import datetime
import tempfile
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

# ---------- paths ----------
ROOT = Path(__file__).parent
APP  = ROOT / "app"
ASSETS = APP / "assets"
SRC = ROOT / "src"
DATA = ROOT / "data"

# Add paths to system path
for p in (SRC, APP):
    if str(p) not in sys.path:
        sys.path.append(str(p))

# Import our analysis modules
try:
    from src.translation_handler import TranslationHandler
    from src.contract_summary_generator import ContractSummaryGenerator
    from src.doc_reader import read_docu
    from src.analysis import analyze_document
    from src.llm_handler import LLMHandler
    from src.analysis_metrics import ContractAnalysisMetrics
    from src.bilingual_analyzer import BilingualContractAnalyzer
    from src.rag_model import build_index, ask
    MODULES_LOADED = True
    # Initialize translation handler
    translation_handler = TranslationHandler()
except ImportError as e:
    st.error(f"⚠️ Module import error: {e}")
    MODULES_LOADED = False
    translation_handler = None

# ---------- Data Persistence Functions ----------
def load_saved_analyses_simple():
    """Load only Streamlit-processed analyses from disk (files with _analysis_ timestamp pattern)"""
    saved_analyses = []
    analysed_dir = DATA / "analysed_documents"
    parsed_dir = DATA / "parsed"
    summaries_dir = DATA / "contract_summaries"
    
    if not analysed_dir.exists():
        return saved_analyses
    
    # Load only analysis files that were processed through Streamlit (have _analysis_YYYYMMDD_HHMMSS pattern)
    for analysis_file in analysed_dir.glob("*_analysis_*.txt"):
        try:
            # Read analysis content
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_content = f.read()
            
            # Extract filename without extension
            base_name = analysis_file.stem  # e.g., "english_contract_name"
            display_name = base_name.replace('english_', '').replace('arabic_', '')
            
            # Try to find corresponding parsed file
            parsed_file = parsed_dir / f"{base_name}.json"
            parsed_data = {}
            if parsed_file.exists():
                with open(parsed_file, 'r', encoding='utf-8') as f:
                    parsed_data = json.load(f)
            
            # Try to find corresponding summary
            summary_files = list(summaries_dir.glob(f"{base_name}*_summary_*.txt"))
            summary_content = None
            if summary_files:
                with open(summary_files[-1], 'r', encoding='utf-8') as f:  # Get most recent
                    summary_content = f.read()
            
            # Create basic analysis entry (sections will be parsed on demand)
            analysis_entry = {
                'filename': display_name,
                'content': analysis_content,
                'timestamp': datetime.fromtimestamp(analysis_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'file_path': str(analysis_file),
                'parsed_data': parsed_data,
                'summary': summary_content,
                # Sections will be parsed when needed
                'contract_overview': '',
                'key_parties': '',
                'important_dates': '',
                'financial_terms': '',
                'legal_framework': '',
                'main_obligations': '',
                'risk_analysis': ''
            }
            
            saved_analyses.append(analysis_entry)
        except Exception as e:
            print(f"Error loading {analysis_file}: {e}")
            continue
    
    # Sort by timestamp (most recent first)
    saved_analyses.sort(key=lambda x: x['timestamp'], reverse=True)
    return saved_analyses

# Initialize session state with persistent data
if 'analysis_results' not in st.session_state:
    # Load saved analyses from disk
    st.session_state.analysis_results = load_saved_analyses_simple()
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = True
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'show_analysis_modal' not in st.session_state:
    st.session_state.show_analysis_modal = False
if 'chat' not in st.session_state:
    st.session_state.chat = [{"role":"assistant","text":"Hi! How can I help you with this contract?"}]
if 'rag_index' not in st.session_state:
    st.session_state.rag_index = None
if 'rag_built' not in st.session_state:
    st.session_state.rag_built = False

# ---------- tiny util: embed image as base64 (tries several names) ----------
def img_b64(*candidates) -> str | None:
    for name in candidates:
        p = ASSETS / name
        if p.exists():
            mime = "png" if p.suffix.lower() == ".png" else "jpeg"
            return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    return None

# ---------- Analysis Functions ----------
def get_backend_config(_label: str) -> dict:
    return {
        "preferred_backend": "gemini",
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "model": "gemini-2.5-pro-preview-03-25",  # Using preview model to avoid quota
    }

def parse_analysis_content(analysis_text):
    """Parse the analysis text to extract structured data"""
    sections = {
        'contract_overview': '',
        'key_parties': '',
        'important_dates': '',
        'financial_terms': '',
        'legal_framework': '',
        'main_obligations': '',
        'risk_analysis': ''
    }
    
    current_section = None
    lines = analysis_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Identify section headers
        if '**1. CONTRACT OVERVIEW**' in line or '### **1. CONTRACT OVERVIEW**' in line:
            current_section = 'contract_overview'
        elif '**2. KEY PARTIES**' in line or '### **2. KEY PARTIES**' in line:
            current_section = 'key_parties'
        elif '**3. IMPORTANT DATES**' in line or '### **3. IMPORTANT DATES**' in line:
            current_section = 'important_dates'
        elif '**4. FINANCIAL TERMS**' in line or '### **4. FINANCIAL TERMS**' in line:
            current_section = 'financial_terms'
        elif '**5. LEGAL FRAMEWORK**' in line or '### **5. LEGAL FRAMEWORK**' in line:
            current_section = 'legal_framework'
        elif '**6. MAIN OBLIGATIONS**' in line or '### **6. MAIN OBLIGATIONS**' in line:
            current_section = 'main_obligations'
        elif '**7. RISK ANALYSIS**' in line or '### **7. RISK ANALYSIS**' in line:
            current_section = 'risk_analysis'
        elif current_section and line:
            sections[current_section] += line + '\n'
    
    return sections

def parse_document(file_bytes, file_name):
    """Parse uploaded document using our real parsers and return structured data"""
    try:
        # Save uploaded file temporarily
        temp_dir = Path(tempfile.gettempdir()) / "contract_uploads"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file_name
        
        with open(temp_file, 'wb') as f:
            f.write(file_bytes)
        
        # Use the doc_reader to parse
        doc_result = read_docu(str(temp_file))
        
        if isinstance(doc_result, dict):
            # Save to parsed folder
            if doc_result.get("full_text"):
                parsed_folder = DATA / "parsed"
                parsed_folder.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = Path(file_name).stem
                language = doc_result.get("language", "en")
                json_filename = f"{base_name}_{language}_{timestamp}.json"
                json_path = parsed_folder / json_filename
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(doc_result, f, ensure_ascii=False, indent=2)
                
                # Return success with parsed data
                return {
                    "success": True,
                    "parsed_data": doc_result,
                    "json_path": str(json_path),
                    "json_filename": json_filename
                }
        else:
            return {
                "success": False,
                "error": "Document parsing returned unexpected format",
                "parsed_data": {
                    "full_text": str(doc_result) if doc_result else "",
                    "language": "en",
                    "length": len(str(doc_result)) if doc_result else 0
                }
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_text_with_gemini(text: str, language: str) -> dict:
    """Analyze text using our analysis system"""
    try:
        # Create LLM handler with error handling
        try:
            handler = LLMHandler()
        except Exception as e:
            return {"success": False, "error": f"Failed to initialize LLM handler: {str(e)}"}
        
        # Create temporary JSON file with the text in the correct format expected by analyze_document
        temp_data = {
            "full_text": text,  # This is the key field that analyze_document expects
            "language": language,
            "file_name": "uploaded_contract",
            "length": len(text),
            "parsed_timestamp": datetime.now().isoformat()
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(temp_data, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)
        
        # Create metrics tracker
        metrics = ContractAnalysisMetrics()
        
        # Use the proper analysed_documents directory
        analysis_dir = DATA / "analysed_documents"
        analysis_dir.mkdir(exist_ok=True)
        
        # Use a simple but comprehensive prompt for analysis
        prompt_template = """Analyze this contract comprehensively and provide:

1. **CONTRACT OVERVIEW**
   - Document type and purpose
   - Primary business relationship

2. **KEY PARTIES**
   - All contracting parties and their roles
   - Legal entities involved

3. **IMPORTANT DATES**
   - Effective dates
   - Expiration dates
   - Key deadlines and milestones

4. **FINANCIAL TERMS**
   - Payment amounts and schedules
   - Pricing structures
   - Penalties and fees

5. **LEGAL FRAMEWORK**
   - Governing law
   - Jurisdiction
   - Dispute resolution

6. **MAIN OBLIGATIONS**
   - Each party's responsibilities
   - Deliverables and requirements

7. **RISK ANALYSIS**
   - High-risk clauses
   - Potential liability issues
   - Compliance requirements

Contract text: {document_text}

Provide a detailed, structured analysis in clear sections."""
        
        # Analyze using the existing system
        st.info(f"🤖 Analyzing document... This may take up to 2 minutes.")
        result = analyze_document(tmp_path, handler, prompt_template, analysis_dir, metrics)
        
        # Check if files were created and read the content
        analysis_files = list(analysis_dir.glob("*_analysis_*.txt"))
        analysis_content = ""
        
        if analysis_files and result.get('success'):
            latest_file = max(analysis_files, key=os.path.getctime)
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    analysis_content = f.read()
                
                # Extract just the contract summary (remove header info)
                lines = analysis_content.split('\n')
                start_idx = 0
                for i, line in enumerate(lines):
                    if '===' in line and i > 5:  # Skip the first header section
                        start_idx = i + 1
                        break
                
                if start_idx > 0:
                    analysis_content = '\n'.join(lines[start_idx:]).strip()
                
                # Parse the content into sections
                parsed_sections = parse_analysis_content(analysis_content)
                
                st.success(f"✅ Analysis completed successfully!")
                
                # Save to session state
                analysis_data = {
                    'content': analysis_content,
                    'sections': parsed_sections,
                    'timestamp': datetime.now().isoformat(),
                    'language': language,
                    'filename': 'uploaded_contract',
                    'file_path': str(latest_file)
                }
                
                st.session_state.current_analysis = analysis_data
                st.session_state.analysis_results.append(analysis_data)
                st.session_state.show_analysis_modal = True
                
                # Build RAG index for Q&A in parallel
                with st.spinner("🔍 Building Q&A system and generating summary..."):
                    # Build RAG index
                    rag_index = build_rag_index_for_analysis(analysis_data)
                    if rag_index:
                        st.session_state.rag_index = rag_index
                        st.session_state.rag_built = True
                        st.success("✅ Q&A system ready!")
                    else:
                        st.warning("⚠️ Q&A system could not be built")
                    
                    # Generate summary
                    summary_result = generate_contract_summary(latest_file)
                    if summary_result and summary_result.get('success'):
                        st.session_state.current_analysis['summary'] = summary_result
                        st.success("✅ Summary generated and saved!")
                
            except Exception as e:
                st.error(f"Error reading analysis file: {str(e)}")
        else:
            st.warning("Analysis completed but content could not be retrieved")
        
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def display_analysis_modal():
    """Display the analysis results in a modal-style container with tabs"""
    if st.session_state.current_analysis and st.session_state.show_analysis_modal:
        analysis = st.session_state.current_analysis
        
        # Create a container for the modal
        modal_container = st.container()
        
        with modal_container:
            # Header with close button
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown("## 📋 Contract Analysis Complete")
                st.markdown(f"*Generated on {datetime.fromisoformat(analysis['timestamp']).strftime('%B %d, %Y at %I:%M %p')}*")
            
            with col2:
                if st.button("❌ Close", key="close_modal", help="Close analysis window"):
                    st.session_state.show_analysis_modal = False
                    st.rerun()
            
            st.markdown("---")
            
            # Create tabs for different sections (only Full Analysis and Arabic Translation)
            tabs = st.tabs([
                "� Full Analysis", 
                "🌐 Arabic Translation"
            ])
            
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
                
                # Import translation utilities
                try:
                    from src.translation_utils import (
                        translate_to_arabic, 
                        save_arabic_translation, 
                        load_arabic_translation,
                        has_arabic_translation
                    )
                    
                    # Check if Arabic version exists
                    file_path = analysis.get('file_path', '')
                    arabic_exists = has_arabic_translation(file_path) if file_path else False
                    
                    if arabic_exists:
                        # Load and display existing Arabic translation
                        arabic_content = load_arabic_translation(file_path)
                        st.success("✅ Arabic translation available")
                        
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
                                font-family: 'Arial', sans-serif;
                                direction: rtl;
                                text-align: right;
                            ">
                                <pre style="white-space: pre-wrap; margin: 0; font-size: 14px; line-height: 1.8; color: #f2f4fb; direction: rtl; text-align: right;">{arabic_content}</pre>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        # Button to regenerate translation
                        if st.button("🔄 Regenerate Arabic Translation", key="regenerate_arabic"):
                            with st.spinner("🌐 Translating to Arabic... This may take a minute..."):
                                arabic_text = translate_to_arabic(analysis['content'])
                                arabic_file = save_arabic_translation(file_path, arabic_text)
                                st.success(f"✅ Arabic translation regenerated and saved!")
                                st.rerun()
                    else:
                        # Show button to generate Arabic translation
                        st.info("📝 No Arabic translation available yet. Click below to generate.")
                        
                        if st.button("🌐 Translate to Arabic", key="translate_arabic", type="primary"):
                            with st.spinner("🌐 Translating to Arabic... This may take a minute..."):
                                try:
                                    arabic_text = translate_to_arabic(analysis['content'])
                                    arabic_file = save_arabic_translation(file_path, arabic_text)
                                    st.success(f"✅ Translation complete! Saved to: {arabic_file}")
                                    st.info("🔄 Refresh the page to see the Arabic version")
                                except Exception as e:
                                    st.error(f"❌ Translation error: {str(e)}")
                        
                        st.markdown("""
                        **Note:** 
                        - Translation uses Google Translate API via Deep Translator
                        - Large documents are split into chunks automatically
                        - Arabic version will be saved as `filename-arabic.txt`
                        - You can view it anytime in this tab after translation
                        """)
                
                except ImportError as e:
                    st.error(f"❌ Translation module not available: {e}")
                    st.info("Run: `pip install deep-translator`")
            
            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("💾 Save Analysis", key="save_analysis"):
                    st.success("Analysis saved to your session!")
            
            with col2:
                if st.button("📄 View File", key="view_file"):
                    st.info(f"Analysis saved at: {analysis['file_path']}")
            
            # Add Chat Interface in the modal
            st.markdown("---")
            st.markdown("### 💬 Ask Questions About This Contract")
            
            # Chat display area
            chat_container = st.container()
            with chat_container:
                for i, message in enumerate(st.session_state.chat):
                    if message["role"] == "user":
                        st.chat_message("user").write(message["text"])
                    else:
                        st.chat_message("assistant").write(message["text"])
            
            # Chat input
            if prompt := st.chat_input("Ask about governing law, parties, dates, obligations, risks..."):
                # Add user message
                st.session_state.chat.append({"role": "user", "text": prompt})
                
                # Generate response using RAG
                if st.session_state.rag_built and st.session_state.rag_index:
                    with st.spinner("🤔 Thinking..."):
                        response = answer_contract_question(prompt, st.session_state.rag_index)
                    st.session_state.chat.append({"role": "assistant", "text": response})
                else:
                    response = "I need to build the Q&A system first. Please analyze a contract document."
                    st.session_state.chat.append({"role": "assistant", "text": response})
                
                st.rerun()

def show_saved_analyses():
    """Display saved analyses in a sidebar like Google Docs"""
    if st.session_state.analysis_results:
        st.sidebar.markdown("## 📚 Saved Analyses")
        
        # Show data loaded indicator
        if st.session_state.get('data_loaded'):
            loaded_count = len(st.session_state.analysis_results)
            st.sidebar.info(f"✅ Loaded Contract Analysis #{loaded_count} from disk")
        
        st.sidebar.markdown("*Click to view previous analyses*")
        
        for i, analysis in enumerate(reversed(st.session_state.analysis_results)):
            timestamp = datetime.fromisoformat(analysis['timestamp'])
            display_time = timestamp.strftime('%m/%d %I:%M %p')
            
            # Create a document-like entry
            with st.sidebar.container():
                if st.sidebar.button(
                    f"📄 Contract Analysis #{len(st.session_state.analysis_results) - i}", 
                    key=f"load_analysis_{i}",
                    use_container_width=True
                ):
                    # Parse sections if not already parsed (for loaded analyses)
                    if not analysis.get('contract_overview') and analysis.get('content'):
                        sections = parse_analysis_content(analysis['content'])
                        analysis.update(sections)
                    
                    st.session_state.current_analysis = analysis
                    st.session_state.show_analysis_modal = True
                    
                    # Rebuild RAG index for loaded analysis
                    rag_index = build_rag_index_for_analysis(analysis)
                    if rag_index:
                        st.session_state.rag_index = rag_index
                        st.session_state.rag_built = True
                    
                    st.rerun()
                
                st.sidebar.caption(f"📅 {display_time} | {analysis.get('language', 'en').upper()}")
                st.sidebar.markdown("---")
        
        # Clear all button
        if st.sidebar.button("🗑️ Clear All", key="clear_all_analyses"):
            st.session_state.analysis_results = []
            st.session_state.current_analysis = None
            st.session_state.show_analysis_modal = False
            st.sidebar.success("All analyses cleared!")
            st.rerun()

def clear_analysis_state():
    """Clear current analysis state (for new uploads)"""
    st.session_state.show_analysis_modal = False
    st.session_state.current_analysis = None

def save_uploaded_file(file_bytes: bytes, file_name: str, language: str) -> str:
    """Save uploaded file to correct language folder"""
    try:
        # Determine folder based on language
        if language == 'ar':
            folder = DATA / "arabic"
        else:
            folder = DATA / "english"
        
        # Create folder if it doesn't exist
        folder.mkdir(parents=True, exist_ok=True)
        
        # Save file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = folder / f"{timestamp}_{file_name}"
        
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        return str(file_path)
    except Exception as e:
        return f"Error saving file: {str(e)}"

def generate_contract_summary(analysis_file_path):
    """Generate summary from analysis file using ContractSummaryGenerator"""
    if not MODULES_LOADED:
        return None
    
    try:
        from src.contract_summary_generator import ContractSummaryGenerator
        
        generator = ContractSummaryGenerator()
        analysis_path = Path(analysis_file_path)
        
        # Extract contract name from filename
        contract_name = analysis_path.stem.split('_analysis_')[0]
        
        # Generate summary for this contract
        summary_content = generator.generate_summary_for_contract_group(
            contract_name=contract_name,
            analysis_files=[analysis_path],
            dry_run=False  # Actually save the summary
        )
        
        if summary_content:
            return {
                'success': True,
                'summary': summary_content,
                'file_path': generator.summary_dir / f"{contract_name}_summary.txt"
            }
        else:
            return {'success': False, 'error': 'No summary generated'}
            
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return {'success': False, 'error': str(e)}

def build_rag_index_for_analysis(analysis_data):
    """Build RAG index from current analysis for Q&A"""
    if not MODULES_LOADED or not analysis_data:
        return None
    
    try:
        # Convert analysis content to segments for RAG
        content = analysis_data.get('content', '')
        sections = analysis_data.get('sections', {})
        
        # Create segments from analysis sections
        segments = []
        segment_id = 0
        
        # Add full content as first segment
        if content:
            segments.append({
                "id": str(segment_id),
                "text": content,
                "title": "Full Analysis",
                "level": 1
            })
            segment_id += 1
        
        # Add each section as a segment
        for section_name, section_content in sections.items():
            if section_content and section_content.strip():
                segments.append({
                    "id": str(segment_id),
                    "text": section_content.strip(),
                    "title": section_name.replace('_', ' ').title(),
                    "level": 2
                })
                segment_id += 1
        
        if not segments:
            return None
        
        # Build index using RAG model
        from src.rag_model import TfidfIndex
        index = TfidfIndex(segments)
        
        # Create index object compatible with RAG model
        index_data = {
            "type": "tfidf",
            "ids": index.ids,
            "texts": index.texts,
            "X": index.X,
            "vectorizer": index.vectorizer,
            "meta": {
                "engine": "tfidf",
                "built_at": int(time.time()),
                "count": len(segments)
            }
        }
        
        return index_data
        
    except Exception as e:
        st.error(f"Error building RAG index: {str(e)}")
        return None

def answer_contract_question(question, index_data):
    """Answer a question using the RAG model"""
    if not MODULES_LOADED or not index_data or not question:
        return "I need an analyzed contract to answer questions about it."
    
    try:
        # Save index temporarily
        temp_index_path = DATA / "temp_rag_index.joblib"
        temp_index_path.parent.mkdir(exist_ok=True)
        
        from joblib import dump
        dump(index_data, str(temp_index_path))
        
        # Use RAG model to answer
        result = ask(str(temp_index_path), question, k=5, mode="generative")
        
        # Clean up temp file
        try:
            temp_index_path.unlink()
        except:
            pass
        
        if result and result.get('result'):
            answer_data = result['result']
            answer = answer_data.get('answer', 'I could not find an answer in the contract analysis.')
            
            if answer != "NOT_FOUND":
                citations = answer_data.get('citations', [])
                if citations:
                    return f"{answer}\n\n*Source: Analysis sections {', '.join(citations)}*"
                return answer
            else:
                return "I couldn't find specific information about that in the contract analysis. Could you try rephrasing your question?"
        
        return "I couldn't process your question. Please try asking about specific contract terms like governing law, parties, dates, or obligations."
        
    except Exception as e:
        return f"Sorry, I encountered an error while processing your question: {str(e)}"

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
    
    # Check Analysis modules
    if MODULES_LOADED:
        status["Analysis Modules"] = "✅"
    else:
        status["Analysis Modules"] = "❌"
    
    # Check RAG system
    if st.session_state.rag_built:
        status["RAG Q&A System"] = "✅"
    else:
        status["RAG Q&A System"] = "⚠️"
    
    return status

def parse_document(file_bytes, file_name):
    """Parse uploaded document using our real parsers and return structured data"""
    try:
        # Save uploaded file temporarily
        temp_dir = Path(tempfile.gettempdir()) / "contract_uploads"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file_name
        
        with open(temp_file, 'wb') as f:
            f.write(file_bytes)
        
        # Use the doc_reader to parse
        doc_result = read_docu(str(temp_file))
        
        if isinstance(doc_result, dict):
            # Save to parsed folder
            if doc_result.get("full_text"):
                parsed_folder = DATA / "parsed"
                parsed_folder.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = Path(file_name).stem
                language = doc_result.get("language", "en")
                json_filename = f"{base_name}_{language}_{timestamp}.json"
                json_path = parsed_folder / json_filename
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(doc_result, f, ensure_ascii=False, indent=2)
                
                # Return success with parsed data
                return {
                    "success": True,
                    "parsed_data": doc_result,
                    "json_path": str(json_path),
                    "json_filename": json_filename
                }
        else:
            return {
                "success": False,
                "error": "Document parsing returned unexpected format",
                "parsed_data": {
                    "full_text": str(doc_result) if doc_result else "",
                    "language": "en",
                    "length": len(str(doc_result)) if doc_result else 0
                }
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_uploaded_file(file_bytes, file_name, language):
    """Save uploaded file to appropriate folder"""
    if language == 'ar':
        folder = DATA / "arabic"
    else:
        folder = DATA / "english"
    
    folder.mkdir(exist_ok=True)
    file_path = folder / file_name
    
    with open(file_path, 'wb') as f:
        f.write(file_bytes)
    
    return str(file_path)

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
ss.setdefault("clear_compose", False)

# pre-encode logo once
HERO_LOGO = img_b64("logo1.jpeg", "logo2.jpeg", "image.png")

# ---------- Main Screen ----------
def screen_home():
    # Show saved analyses in sidebar
    show_saved_analyses()
    
    # Display analysis modal if active
    if st.session_state.show_analysis_modal:
        display_analysis_modal()
        return  # Don't show the main interface when modal is active
    
    # ===== Hero Section =====
    st.markdown('<span id="top"></span><div class="anchor-spacer"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown(dedent(f"""
        <div class="hero-block">
          <div class="hero-content">
            <div class="hero-title-wrap">
              <h1 class="hero-title">VERDICT</h1>
              {f'<img class="hero-logo" src="{HERO_LOGO}" alt="Logo"/>' if HERO_LOGO else ""}
            </div>
            <p class="hero-desc">
              Empowering contract clarity with precision-driven AI analysis and actionable insights.
            </p>
          </div>
        </div>
        """), unsafe_allow_html=True)

    # ===== Upload Section =====
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
              📤 **Upload Process:** Drop in a PDF/DOCX → 🔄 **Parse to JSON** → 🤖 **AI Analysis** → 📊 **Results**
              <br>Your document will be converted to structured JSON format, then analyzed by AI to extract key contract information.
            </p>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("### ⚙️ Settings")
        st.info("🔷 Using Google Gemini 2.5 Pro for AI-powered contract analysis")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a contract file",
            type=['pdf', 'docx', 'txt'],
            key="contract_uploader"
        )
        
        if uploaded_file:
            # Check if this is a new file or already processed
            if ss.get("last_uploaded_file") != uploaded_file.name:
                try:
                    # Process the uploaded file
                    file_bytes = uploaded_file.read()
                    file_name = uploaded_file.name
                    
                    # Parse document
                    with st.spinner("📄 Parsing document and converting to JSON..."):
                        parse_result = parse_document(file_bytes, file_name)
                        
                    if parse_result.get("success"):
                        parsed_data = parse_result["parsed_data"]
                        text = parsed_data["full_text"]
                        language = parsed_data["language"]
                        json_path = parse_result.get("json_path")
                        json_filename = parse_result.get("json_filename")
                        
                        # Save original file
                        saved_path = save_uploaded_file(file_bytes, file_name, language)
                        
                        # Store in session state
                        ss["uploaded_bytes"] = file_bytes
                        ss["doc_name"] = file_name
                        ss["contract_text"] = text
                        ss["language"] = language
                        ss["saved_path"] = saved_path
                        ss["parsed_data"] = parsed_data
                        ss["json_path"] = json_path
                        ss["json_filename"] = json_filename
                        ss["step"] = "analysis"
                        ss["last_uploaded_file"] = file_name
                        
                        # Show parsing success with details
                        lang_display = "🇸🇦 Arabic" if language == 'ar' else "🇺🇸 English"
                        st.success(f"✅ **Document Processed Successfully!**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"📄 **Original File:** {file_name}")
                            st.info(f"🗣️ **Language Detected:** {lang_display}")
                            st.info(f"📏 **Text Length:** {len(text):,} characters")
                        
                        with col2:
                            if json_filename:
                                st.info(f"� **JSON Created:** {json_filename}")
                                st.info(f"💾 **Saved to:** data/parsed/")
                            st.info(f"⏱️ **Processed:** {datetime.now().strftime('%H:%M:%S')}")
                        
                        st.rerun()
                    else:
                        error_msg = parse_result.get("error", "Unknown parsing error")
                        st.error(f"❌ **Parsing Failed:** {error_msg}")
                        
                except Exception as e:
                    st.error(f"❌ **Error processing file:** {str(e)}")
            else:
                # File already processed, show existing data
                if ss.get("doc_name"):
                    st.info(f"📄 Currently loaded: {ss['doc_name']}")
                    if ss.get("json_filename"):
                        st.info(f"📋 JSON available: {ss['json_filename']}")
                    if ss.get("step") == "analysis":
                        # File is ready for analysis
                        pass
        
        # Analysis and Results Section
        if ss.get("step") == "analysis" and ss.get("contract_text"):
            st.markdown("---")
            
            # Show file info
            lang_display = "🇸🇦 Arabic" if ss.get("language") == 'ar' else "🇺🇸 English"
            st.info(f"📄 **File:** {ss.get('doc_name')} | **Language:** {lang_display}")
            
            # Analysis button
            if st.button("🤖 Analyze Contract", type="primary", use_container_width=True):
                clear_analysis_state()  # Clear previous analysis modal state
                
                cfg = get_backend_config("analysis")
                text = ss.get("contract_text")
                language = ss.get("language", 'en')
                
                # Run the analysis (this will trigger the modal)
                analysis_result = analyze_text_with_gemini(text, language)
                
                # The modal will be displayed automatically by analyze_text_with_gemini
                # via session state changes
                st.rerun()
            
            # Show last analysis if available
            if st.session_state.current_analysis:
                st.markdown("### 📋 Last Analysis")
                last_analysis = st.session_state.current_analysis
                timestamp = datetime.fromisoformat(last_analysis['timestamp'])
                display_time = timestamp.strftime('%B %d, %Y at %I:%M %p')
                
                st.success(f"✅ **Analysis completed on:** {display_time}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 View Full Analysis", type="primary", use_container_width=True):
                        st.session_state.show_analysis_modal = True
                        st.rerun()
                
                with col2:
                    if st.button("🔄 Analyze Again", use_container_width=True):
                        clear_analysis_state()
                        cfg = get_backend_config("analysis")
                        text = ss.get("contract_text")
                        language = ss.get("language", 'en')
                        analyze_text_with_gemini(text, language)
                        st.rerun()
                
                # Add compact chat interface for quick questions
                st.markdown("---")
                st.markdown("### 💬 Quick Q&A")
                
                if st.session_state.rag_built:
                    st.success("🤖 **Q&A System Ready** - Ask questions about your contract!")
                    
                    # Show recent chat messages (last 4)
                    recent_messages = st.session_state.chat[-4:] if len(st.session_state.chat) > 4 else st.session_state.chat
                    
                    for message in recent_messages:
                        if message["role"] == "user":
                            st.chat_message("user").write(message["text"])
                        else:
                            st.chat_message("assistant").write(message["text"])
                    
                    # Chat input
                    if prompt := st.chat_input("Ask about this contract: governing law, parties, dates, risks..."):
                        # Add user message
                        st.session_state.chat.append({"role": "user", "text": prompt})
                        
                        # Generate response using RAG
                        with st.spinner("🤔 Thinking..."):
                            response = answer_contract_question(prompt, st.session_state.rag_index)
                        st.session_state.chat.append({"role": "assistant", "text": response})
                        st.rerun()
                    
                    # Link to full chat in modal
                    st.info("💡 **Tip:** Open the full analysis view for complete chat history and all analysis tabs.")
                else:
                    st.info("🔄 Q&A system is being built... Please wait or re-analyze the contract.")
            else:
                st.markdown("### 📋 Ready for Analysis")
                st.info("📝 **Document parsed and ready!** Click the 'Analyze Contract' button above to start AI-powered analysis.")
                    
            # System Status in sidebar
            with st.sidebar:
                st.markdown("### 🔧 System Status")
                
                # Check system components
                status_checks = check_system_status()
                
                for component, status in status_checks.items():
                    if status == "✅":
                        st.success(f"{status} {component}")
                    elif status == "⚠️":
                        st.warning(f"{status} {component}")
                    else:
                        st.error(f"{status} {component}")

# =============================================================================
# 🚀 Application Entry Point
# =============================================================================
def main():
    """Main application entry point"""
    screen_home()

if __name__ == "__main__":
    main()