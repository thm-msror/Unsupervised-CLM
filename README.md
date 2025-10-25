# 🤖 AI-Driven Contract Lifecycle Management (CLM)

## 📋 Overview

**CLM-AI-Hackathon** is a web-based AI prototype that automates legal contract management. The platform helps legal and procurement teams reduce manual effort, minimize errors, accelerate contract review, and provide actionable insights. It supports contracts in **English and Arabic**.

### 🎯 Key Capabilities

- 📄 **Secure Contract Upload** — Support for PDF and DOCX files
- 🤖 **AI-Powered Data Extraction** — Automated extraction of key contract information
- ⚠️ **Risk & Compliance Analysis** — Identify potential issues and missing clauses
- 📊 **Contract Summarization** — AI-generated insights and summaries
- ❓ **Question-Answering** — Interactive Q&A over contract content
- 🔍 **Smart Clause Automation** — Industry and law-specific clause suggestions *(optional)*

---

## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | [Streamlit](https://streamlit.io/) | Web UI and orchestration |
| **LLM** | [Google Gemini 2.5 Flash](https://ai.google.dev/) | Contract analysis and NLP |
| **OCR** | PaddleOCR, EasyOCR, Doctr | Document text extraction *(optional)* |
| **Embeddings** | Sentence-Transformers, E5 Multilingual | Semantic search and RAG |
| **Cloud Deployment** | [Render](https://render.com/) | Demo hosting |
| **API Backend** | Google Gemini API | Fast, free-tier AI processing |

---

## ✨ Features

### 🎯 Core Features

1. **📄 Secure Contract Upload & Processing**  
   Users can securely upload PDF/DOCX files for automated analysis.

2. **🔍 AI-Powered Data Extraction**  
   Automatically extracts:
   - Contracting parties and entities
   - Key dates (effective, expiration, renewal)
   - Governing law & jurisdiction
   - Obligations & deliverables
   - Financial terms and payment schedules

3. **⚠️ Risk & Compliance Analysis**  
   Intelligent identification of:
   - High-risk or unusual clauses
   - Missing standard legal protections
   - Consistency errors in defined terms
   - Non-standard language patterns

4. **📊 Intelligent Dashboard & Visualization**  
   Clean summary of extracted data, risk assessments, and AI-generated insights.

### 🚀 Advanced Features

- **🔍 Smart Clause Automation** — Industry and governing law-specific recommendations
- **🔎 Natural Language Search** — Semantic search over contract content
- **🌐 Multilingual Support** — English and Arabic contract processing

---

## 📁 Repository Structure

```
UNSUPERVISED-CLM/
│
├── � main.py                        # Streamlit application entry point
├── 📱 app/                           # Streamlit components & UI modules
│   ├── config.py                     # Configuration & environment variables
│   ├── utils.py                      # Helper functions (PDF/DOCX parsing)
│   └── dashboard.py                  # Dashboard components & visualizations
│
├── 🧠 src/                           # Core AI logic & LLM integration
│   ├── llm_handler.py                # LLM wrapper (Google Gemini API)
│   ├── data_extraction.py            # Contract information extraction
│   ├── risk_analysis.py              # Risk assessment & clause analysis
│   ├── summarization.py              # Contract summarization
│   └── qa_module.py                  # Question-answering system
│
├── 💬 prompts/                       # Prompt engineering templates
│   ├── extraction_prompt.txt         # Information extraction prompts
│   ├── risk_prompt.txt               # Risk analysis prompts
│   └── summarization_prompt.txt      # Summarization & search prompts
│
├── 📊 data/                          # Sample contracts & test data
│   ├── english/                      # English contract samples
│   │   ├── sample_contract_1.pdf
│   │   └── sample_contract_2.docx
│   └── arabic/                       # Arabic contract samples
│       ├── sample_contract_1.pdf
│       └── sample_contract_2.docx
│
├── 🧪 tests/                         # Unit & integration tests
│   ├── test_data_extraction.py
│   ├── test_risk_analysis.py
│   ├── test_summarization.py
│   └── test_qa_module.py
│
├── 🎨 assets/                        # Images, logos, screenshots
│   ├── demo_screenshot.png
│   └── logo.png
│
├── 📋 requirements.txt               # Python dependencies
├── 🔒 .env                          # Environment variables (API keys)
├── .gitignore                       # Git ignore file
└── 📖 README.md                     # Project documentation
```

---

## � Requirements

### System Requirements
- **Python 3.8+** — Main runtime
- **Internet connection** — For Google Gemini API access
- **Google AI API Key** — Free tier available at [Google AI Studio](https://makersuite.google.com/app/apikey)

### Installation Commands
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python --version
pip list | grep google-generativeai
```

---

## �🚀 Quick Start

### 🏠 Local Development (Recommended for Privacy)

**Step 1: Clone & Install**
```powershell
git clone https://github.com/thm-msror/Unsupervised-CLM.git
cd Unsupervised-CLM
pip install -r requirements.txt
```

**Step 2: Get Google Gemini API Key**
```powershell
# 1. Go to Google AI Studio: https://makersuite.google.com/app/apikey
# 2. Sign in with Google account
# 3. Click "Create API Key" 
# 4. Copy the API key (starts with AIza...)
```

**Step 3: Configure Environment**
```powershell
# Create a .env file
New-Item -ItemType File -Path .env -Force

# Add your Gemini API key:
echo "GEMINI_API_KEY=your_api_key_here" >> .env
```

> 💡 **Free Tier**: Google Gemini offers generous free limits: 15 req/min, 1500 req/day, 1M tokens/month

**Step 4: Run Application**
```powershell
# Run from repository root
streamlit run main.py --server.port 8501
# Open your browser at: http://localhost:8501
```

> 🔑 **API Key Security**: Your Gemini API key is used client-side and not stored permanently  
> 📁 **Structure Note**: The main entry point is `main.py` at the repository root for simple deployment

---

### ☁️ Cloud Deployment (Demo Only)

For hackathon demos, deploy on Render using cloud-hosted LLMs:

**Step 1: Connect Repository**
- Link your GitHub repository to [Render](https://render.com/)

**Step 2: Configure Environment**
- Add environment variables from `.env` to Render dashboard
- Include API keys, model endpoints, and configuration

**Step 3: Set Start Command**
```bash
streamlit run main.py --server.port $PORT --server.address 0.0.0.0
```

> 🔒 **Security**: Add your GEMINI_API_KEY as an environment variable in Render dashboard

---

## 🧪 Testing & Development

### Running Tests
```powershell
# Run all tests
pytest tests/

# Run specific test modules
pytest tests/test_data_extraction.py -v
pytest tests/test_risk_analysis.py -v
```

### Development Setup
```powershell
# Install development dependencies
pip install -r requirements.txt
```

---

## 🔐 AI Configuration & API Setup

### 🤖 Google Gemini 2.5 Flash

This application uses **Google Gemini 2.5 Flash** for contract analysis:

| Feature | Specification |
|---------|---------------|
| **Model** | gemini-2.5-flash (latest) |
| **Context Window** | 32K tokens |
| **Speed** | Optimized for low-latency |
| **Free Tier** | 15 req/min, 1500 req/day, 1M tokens/month |

### 🔑 API Key Setup

**Get Your Free API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

**Add to Environment:**
```powershell
# Create .env file
echo "GEMINI_API_KEY=AIza..." >> .env
```

### 🧪 Testing Gemini API

**Quick Test Script:**
```powershell
# Run the test script
python tests/test_gemini_api.py
```

**Manual Test with Python:**
```python
import google.generativeai as genai

# Configure API
genai.configure(api_key="your_api_key_here")
model = genai.GenerativeModel('gemini-2.5-flash')

# Test contract analysis
contract_text = "Agreement between ABC Corp and XYZ Ltd, effective Jan 2025, $150/hour"
prompt = f"Extract key information from this contract: {contract_text}"

response = model.generate_content(prompt)
print(response.text)
```

### 💡 Why Gemini for Hackathons?

- **🆓 Free Tier**: Generous limits for development and demos
- **⚡ Fast**: Optimized for quick responses
- **🧠 Smart**: Excellent at structured data extraction
- **📄 Contract-Ready**: Great performance on legal document analysis