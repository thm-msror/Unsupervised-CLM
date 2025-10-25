#!/usr/bin/env python3
"""
Test script for Google Gemini 2.5 Flash API
Tests contract analysis capabilities with free tier
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

def test_gemini_api():
    """Test Gemini API connection and contract analysis"""
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ Error: google-generativeai not installed")
        print("💡 Run: pip install google-generativeai")
        return False
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        print("❌ Error: GEMINI_API_KEY not set in .env file")
        print("💡 Get your key from: https://makersuite.google.com/app/apikey")
        print("💡 Add to .env: GEMINI_API_KEY=AIza...")
        return False
    
    # Configure API
    genai.configure(api_key=api_key)
    
    print("🔑 API Key loaded successfully")
    
    # Test basic connection
    try:
        # List available models
        models = genai.list_models()
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        print(f"✅ Connected to Gemini API")
        print(f"📋 Available models: {len(available_models)}")
        for model in available_models[:3]:  # Show first 3
            print(f"   - {model}")
        
    except Exception as e:
        print(f"❌ API Connection Error: {e}")
        return False
    
    # Test contract analysis
    try:
        print("\n🧪 Testing Contract Analysis...")
        
        # Initialize the model (using the available Gemini 2.5 Flash)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Sample contract text for testing
        sample_contract = """
        CONSULTING AGREEMENT
        
        This Consulting Agreement ("Agreement") is entered into on January 15, 2025, 
        between ABC Corporation, a Delaware corporation ("Company") and John Smith, 
        an independent contractor ("Consultant").
        
        1. SERVICES: Consultant agrees to provide software development consulting services.
        2. TERM: This Agreement shall commence on February 1, 2025 and terminate on July 31, 2025.
        3. COMPENSATION: Company shall pay Consultant $150 per hour for services rendered.
        4. CONFIDENTIALITY: Consultant agrees to maintain confidentiality of Company information.
        """
        
        # Contract analysis prompt
        prompt = f"""
        Analyze the following contract and extract key information:
        
        Contract Text:
        {sample_contract}
        
        Please provide:
        1. Contract Type
        2. Parties Involved
        3. Key Dates (start, end)
        4. Financial Terms
        5. Risk Assessment (High/Medium/Low)
        6. Missing Clauses or Potential Issues
        
        Format as JSON for easy parsing.
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        print("✅ Contract Analysis Complete!")
        print("\n📄 Analysis Results:")
        print("-" * 50)
        print(response.text)
        
        # Test token usage (Gemini provides usage info)
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            print(f"\n📊 Token Usage:")
            print(f"   Input tokens: {usage.prompt_token_count}")
            print(f"   Output tokens: {usage.candidates_token_count}")
            print(f"   Total tokens: {usage.total_token_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Contract Analysis Error: {e}")
        return False

def test_gemini_streaming():
    """Test streaming response for long contract analysis"""
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ API key not configured")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("\n🌊 Testing Streaming Response...")
        
        prompt = """
        Create a detailed risk assessment checklist for contract review. 
        Include 15-20 key items that legal teams should verify.
        """
        
        print("📝 Generating checklist...")
        response = model.generate_content(prompt, stream=True)
        
        print("\n✅ Streaming Response:")
        print("-" * 50)
        
        full_response = ""
        for chunk in response:
            if chunk.text:
                print(chunk.text, end='')
                full_response += chunk.text
        
        print(f"\n\n📏 Response length: {len(full_response)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Streaming Error: {e}")
        return False

def main():
    """Run all Gemini API tests"""
    
    print("🧪 Google Gemini 1.5 Flash API Tests")
    print("=" * 50)
    
    # Test basic API
    success1 = test_gemini_api()
    
    if success1:
        # Test streaming
        success2 = test_gemini_streaming()
        
        if success1 and success2:
            print(f"\n🎉 All tests passed!")
            print(f"💡 Ready to integrate Gemini into CLM system")
            print(f"🔗 Free tier: 15 req/min, 1500 req/day, 1M tokens/month")
        else:
            print(f"\n⚠️  Some tests failed, but basic API works")
    else:
        print(f"\n❌ Tests failed - check API key and connection")
    
    print("\n💡 Next steps:")
    print("   1. Add your Gemini API key to .env")
    print("   2. Update Streamlit app to include Gemini option")
    print("   3. Integrate with contract processing pipeline")

if __name__ == "__main__":
    main()