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
| **LLM** | [Qwen 2](https://huggingface.co/qwen-2) (7B/1.5B) | Contract analysis and NLP |
| **OCR** | PaddleOCR, EasyOCR, Doctr | Document text extraction *(optional)* |
| **Embeddings** | Sentence-Transformers, E5 Multilingual | Semantic search and RAG |
| **Cloud Deployment** | [Render](https://render.com/) | Demo hosting |
| **Local Deployment** | Ollama, Local binaries | **Data confidentiality** and offline use |

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
│   ├── llm_handler.py                # LLM wrapper (Qwen, HuggingFace, local)
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
- **Windows 10/11** — For winget package manager
- **4GB+ RAM** — For Qwen 1.5B model (16GB+ recommended for 7B model)
- **Internet connection** — For downloading models and dependencies

### Installation Commands
```powershell
# Python packages (pip checks for existing installations)
pip install -r requirements.txt

# Ollama LLM runtime (winget checks if already installed and skips if found)
winget install Ollama.Ollama

# Verify installations
python --version
ollama --version
```

> ✅ **Smart Installation**: Both `pip` and `winget` automatically check for existing installations and skip if already present, just like other modern package managers.

---

## �🚀 Quick Start

### 🏠 Local Development (Recommended for Privacy)

**Step 1: Clone & Install**
```powershell
git clone https://github.com/thm-msror/Unsupervised-CLM.git
cd Unsupervised-CLM
pip install -r requirements.txt
```

**Step 2: Install Ollama (for local LLM)**
```powershell
# Install Ollama using winget (checks if already installed)
winget install Ollama.Ollama

# Alternative: Download from https://ollama.ai/download/windows
```

**Step 3: Configure Environment**
```powershell
# Create a .env file
New-Item -ItemType File -Path .env -Force

# Add your configuration (choose one backend):
# For Hugging Face API (cloud, quick setup):
echo "PREFERRED_BACKEND=huggingface" >> .env
echo "HUGGINGFACE_API_KEY=your_hf_token_here" >> .env
echo "HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct" >> .env

# OR for local Ollama (privacy, requires step 2):
echo "PREFERRED_BACKEND=local" >> .env
echo "LOCAL_INFERENCE_URL=http://localhost:11434" >> .env
echo "LOCAL_MODEL=qwen2:1.5b" >> .env
```

> 💡 **Get HF API Key**: Sign up at [Hugging Face](https://huggingface.co/join) and get your token from [Settings > Access Tokens](https://huggingface.co/settings/tokens)

**Step 4: Run Locally**
```powershell
# Run from repository root
streamlit run main.py --server.port 8501
# Open your browser at: http://localhost:8501
```

> ✅ **Privacy Note**: Local deployment ensures full confidentiality — contract data never leaves your machine.  
> 📁 **Structure Note**: The main entry point is `main.py` at the repository root for simple deployment.

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

> ⚠️ **Security Note**: Cloud deployment is for demos only. For sensitive contracts, use local deployment or private cloud/VPC.

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

## 🔐 Model Deployment & Privacy

### 🤖 LLM Configuration

This application uses **Qwen 2** for contract analysis, extraction, and Q&A:

| Model Variant | Use Case | Memory Requirements |
|---------------|----------|-------------------|
| **Qwen 2 — 7B** | Recommended for quality | ~16GB RAM |
| **Qwen 2 — 1.5B** | Low-resource environments | ~4GB RAM |

### ☁️ Cloud vs 🏠 Local Deployment

**For Hackathon Demos:**
- Uses Hugging Face Inference API
- Quick deployment without specialized hardware
- Suitable for public demonstrations

**For Production/Confidential Use:**
- Run Qwen locally via [Ollama](https://ollama.ai/) or local binaries
- Complete data privacy — no external API calls
- Configurable model size based on hardware

### 🔄 Switching Between Cloud & Local

The application supports seamless switching via environment variables:

```bash
# Use cloud API (demo)
PREFERRED_BACKEND=huggingface
HUGGINGFACE_API_KEY=your_api_key

# Use local model (production)
PREFERRED_BACKEND=local
LOCAL_INFERENCE_URL=http://localhost:11434
LOCAL_MODEL=qwen-2-7b
```
When running locally, pick the model size that matches your hardware (1.5B for low RAM, 7B for a better balance of performance and resource use).

### 🧪 Testing Qwen Locally with Ollama

**Quick Test Setup:**
```powershell
# 1. Install Ollama (Windows)
# Download from: https://ollama.ai/download/windows
# Or use winget: winget install Ollama.Ollama

# 2. Pull Qwen model (choose based on your RAM)
ollama pull qwen2:1.5b    # For low-RAM machines (~4GB RAM)
ollama pull qwen2:7b      # For moderate RAM (~16GB RAM)

# 3. Test the model directly
ollama run qwen2:1.5b "Summarize this contract clause: The party agrees to deliver services within 30 days."

# 4. Start Ollama server (runs on http://localhost:11434)
ollama serve
```

**Test with curl:**
```powershell
# Test API endpoint
curl -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d '{"model": "qwen2:1.5b", "prompt": "Extract parties from: Agreement between ABC Corp and XYZ Ltd", "stream": false}'
```

### 🌐 Testing Qwen with Hugging Face API (Cloud)

**Quick Setup:**
```powershell
# 1. Get API key from https://huggingface.co/settings/tokens
# 2. Set environment variable
$env:HUGGINGFACE_API_KEY="your_hf_token_here"

# 3. Test with curl
curl -X POST "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct" -H "Authorization: Bearer $env:HUGGINGFACE_API_KEY" -H "Content-Type: application/json" -d '{"inputs": "Extract parties from: Agreement between ABC Corp and XYZ Ltd"}'
```

**Test with Python:**
```python
import requests
import os

# Your HF API key
api_key = os.getenv("HUGGINGFACE_API_KEY")
headers = {"Authorization": f"Bearer {api_key}"}

# Available Qwen models on HF
models = [
    "Qwen/Qwen2.5-7B-Instruct",  # Latest and best
    "Qwen/Qwen2.5-1.5B-Instruct",  # Smaller, faster
    "Qwen/Qwen2-7B-Instruct"    # Previous version
]

```