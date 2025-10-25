import os
import requests
import json
from dotenv import load_dotenv

# ========================================================
# 1️⃣ Setup: Load Token from .env file
# ========================================================
# Load environment variables from .env file in project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Get HuggingFace API token from multiple possible environment variable names
HF_TOKEN = (
    os.getenv("HUGGINGFACE_API_KEY") or 
    os.getenv("HUGGINGFACEHUB_API_KEY") or 
    os.getenv("HF_TOKEN") or 
    os.getenv("HUGGING_FACE_HUB_TOKEN")
)

# Validate token is available
if not HF_TOKEN:
    print("❌ Hugging Face API token not found!")
    print("💡 Add one of these to your .env file:")
    print("   HUGGINGFACEHUB_API_KEY=your_token_here")
    print("   OR HUGGINGFACE_API_KEY=your_token_here") 
    print("💡 Get token from: https://huggingface.co/settings/tokens")
    exit(1)

print(f"✅ HF Token loaded: {HF_TOKEN[:8]}...{HF_TOKEN[-4:]}")

# ========================================================
# 2️⃣ Define API Endpoint and Headers
# ========================================================
# Updated to use new Inference Providers API (Nov 2025)
# Old deprecated endpoint: https://api-inference.huggingface.co/
# New endpoint: https://router.huggingface.co/hf-inference/
API_URL = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# ========================================================
# 3️⃣ Define Helper Function
# ========================================================
def query_contract_extraction(contract_text):
    """Query HuggingFace API for contract extraction using Qwen model"""
    
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct:together",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant that extracts key legal information from contracts. Always respond in valid JSON format."
            },
            {
                "role": "user",
                "content": f"Extract and summarize the following contract:\n\n{contract_text}\n\nReturn the output in JSON format with fields: parties, effective_date, duration, and obligations."
            }
        ],
        "temperature": 0.3,
        "max_tokens": 300
    }

    print("📤 Sending request to HuggingFace API...")
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                print("✅ API Response received successfully!")
                print(f"📄 Extracted Contract Information:\n{content}")
                
                # Try to parse as JSON to validate format
                try:
                    parsed_json = json.loads(content)
                    print("✅ Response is valid JSON format")
                    return parsed_json
                except json.JSONDecodeError:
                    print("⚠️ Response is not valid JSON, but content received")
                    return content
                    
            except (KeyError, IndexError) as e:
                print(f"⚠️ Unexpected response structure: {e}")
                print(f"Full response: {response.text}")
                return None
                
        elif response.status_code == 401:
            print("❌ Authentication failed - check your API token")
            return None
        elif response.status_code == 429:
            print("❌ Rate limit exceeded - try again later")
            return None
        elif response.status_code == 503:
            print("❌ Service unavailable - model might be loading")
            return None
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet connection")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

# ========================================================
# 4️⃣ Example Contract Text
# ========================================================
sample_contract = """
This Service Agreement (“Agreement”) is made on January 15, 2025, between
Alpha Technologies Ltd (“Provider”) and Beta Solutions FZ-LLC (“Client”).
The Provider agrees to deliver cloud maintenance services for a duration of 12 months.
Both parties agree to the terms and conditions stated herein.
"""

# ========================================================
# 5️⃣ Run Test
# ========================================================
if __name__ == "__main__":
    print("🚀 Testing Hugging Face Qwen API via Together AI...")
    print(f"📡 API URL: {API_URL}")
    print(f"🎯 Model: Qwen/Qwen2.5-7B-Instruct:together")
    print(f"📄 Testing contract extraction...\n")
    
    try:
        query_contract_extraction(sample_contract)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("💡 This might be due to:")
        print("   - Invalid API token")
        print("   - Model not available on the endpoint")
        print("   - Network connectivity issues")
        print("   - API rate limits")
        
        print(f"\n🔧 Debug info:")
        print(f"   .env file path: {env_path}")
        print(f"   .env file exists: {os.path.exists(env_path)}")
        print(f"   Token source: {[k for k in ['HUGGINGFACE_API_KEY', 'HUGGINGFACEHUB_API_KEY', 'HF_TOKEN', 'HUGGING_FACE_HUB_TOKEN'] if os.getenv(k)]}")
        
        print(f"\n💡 Alternative: Try local Ollama instead:")
        print(f"   winget install Ollama.Ollama")
        print(f"   ollama pull qwen2:1.5b")
        print(f"   ollama run qwen2:1.5b")
