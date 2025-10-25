#!/usr/bin/env python3
"""
Quick test script for Qwen local setup with Ollama
Run this to verify your local Qwen installation is working
"""

import requests
import json
import time

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2:1.5b"  # Change to qwen2:7b if you have more RAM

def test_ollama_connection():
    """Test if Ollama server is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Ollama server is running")
            print(f"📦 Available models: {[m['name'] for m in models]}")
            return True
        else:
            print("❌ Ollama server responded with error:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama server at", OLLAMA_BASE_URL)
        print("💡 Make sure Ollama is installed and running: ollama serve")
        return False

def test_qwen_model():
    """Test Qwen model with contract-related prompts"""
    
    test_prompts = [
        {
            "name": "Contract Party Extraction",
            "prompt": "Extract the parties from this text: 'This Agreement is between ABC Corporation and XYZ Limited.' Return only the party names.",
            "expected_keywords": ["ABC", "XYZ"]
        },
        {
            "name": "Date Recognition", 
            "prompt": "What is the effective date in: 'This agreement shall be effective as of January 15, 2024.'",
            "expected_keywords": ["January", "15", "2024"]
        },
        {
            "name": "Risk Analysis",
            "prompt": "Is this clause risky: 'Party A may terminate this agreement at any time without cause or notice.' Explain briefly.",
            "expected_keywords": ["risky", "terminate", "without"]
        }
    ]
    
    for i, test in enumerate(test_prompts, 1):
        print(f"\n🧪 Test {i}: {test['name']}")
        print(f"📝 Prompt: {test['prompt']}")
        
        # Make request to Ollama
        payload = {
            "model": MODEL_NAME,
            "prompt": test['prompt'],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent results
                "num_predict": 100   # Limit response length
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate", 
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                
                print(f"✅ Response ({end_time - start_time:.1f}s): {answer}")
                
                # Check if response contains expected keywords
                found_keywords = [kw for kw in test['expected_keywords'] 
                                if kw.lower() in answer.lower()]
                if found_keywords:
                    print(f"✅ Found expected keywords: {found_keywords}")
                else:
                    print(f"⚠️  No expected keywords found: {test['expected_keywords']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out (>30s)")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    print("🚀 Testing Qwen Local Setup with Ollama\n")
    
    # Test 1: Connection
    if not test_ollama_connection():
        print("\n💡 Setup Instructions:")
        print("1. Install Ollama: https://ollama.ai/download")  
        print("2. Pull Qwen model: ollama pull qwen2:1.5b")
        print("3. Start server: ollama serve")
        return
    
    # Test 2: Check if our model is available
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]
        
        if MODEL_NAME not in model_names:
            print(f"\n❌ Model {MODEL_NAME} not found")
            print(f"📦 Available models: {model_names}")
            print(f"💡 Pull the model: ollama pull {MODEL_NAME}")
            return
        else:
            print(f"✅ Model {MODEL_NAME} is available")
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return
    
    # Test 3: Run contract-specific tests
    test_qwen_model()
    
    print(f"\n🎉 Testing complete! If all tests passed, Qwen {MODEL_NAME} is ready for use.")
    print("\n📝 Next steps:")
    print("1. Update your .env file with: PREFERRED_BACKEND=local")
    print(f"2. Set: LOCAL_MODEL={MODEL_NAME}")
    print("3. Set: LOCAL_INFERENCE_URL=http://localhost:11434")

if __name__ == "__main__":
    main()