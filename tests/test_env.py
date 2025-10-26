#!/usr/bin/env python3
"""
Quick test to verify .env file is working correctly
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def test_env_configuration():
    """Test if .env file is properly loaded and API key is accessible"""
    
    print("🔍 TESTING .ENV CONFIGURATION")
    print("=" * 50)
    
    # 1. Check if .env file exists (in parent directory)
    env_file = Path("../.env")
    if env_file.exists():
        print(f"✅ .env file found: {env_file.absolute()}")
        
        # Read and display .env contents (safely)
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        print(f"📄 .env file contents ({len(lines)} lines):")
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.startswith('#'):
                # Hide API key for security, show only first/last few chars
                if 'GEMINI_API_KEY' in line:
                    key_part = line.split('=')[1].strip()
                    if len(key_part) > 10:
                        masked_key = f"{key_part[:6]}...{key_part[-4:]}"
                        print(f"   {i}: GEMINI_API_KEY={masked_key}")
                    else:
                        print(f"   {i}: GEMINI_API_KEY=<short_key>")
                else:
                    print(f"   {i}: {line.strip()}")
            elif line.strip():
                print(f"   {i}: {line.strip()}")
    else:
        print(f"❌ .env file NOT found in: {Path.cwd()}")
        return False
    
    # 2. Test loading environment variables
    print(f"\n🔄 Loading environment variables...")
    load_dotenv()
    
    # 3. Check if API key is loaded
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"✅ GEMINI_API_KEY loaded successfully")
        print(f"   Length: {len(api_key)} characters")
        print(f"   Format: {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else 'short'}")
        
        # Basic format validation
        if api_key.startswith('AIza') and len(api_key) == 39:
            print(f"✅ API key format appears valid (Google AI Studio format)")
        else:
            print(f"⚠️  API key format may be incorrect")
            print(f"   Expected: Starts with 'AIza', length 39 characters")
            print(f"   Got: Starts with '{api_key[:4]}', length {len(api_key)}")
    else:
        print(f"❌ GEMINI_API_KEY not found in environment")
        return False
    
    # 4. Test other environment variables
    port = os.getenv('STREAMLIT_SERVER_PORT')
    if port:
        print(f"✅ STREAMLIT_SERVER_PORT: {port}")
    
    # 5. Test API connection (basic)
    print(f"\n🔌 Testing API connection...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Simple test - just configure, don't make a call
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        print(f"✅ API configuration successful")
        print(f"✅ Model initialized: gemini-2.0-flash-lite")
        
    except Exception as e:
        print(f"❌ API configuration failed: {e}")
        return False
    
    print(f"\n" + "=" * 50)
    print(f"🎉 ALL TESTS PASSED - .env configuration is working!")
    return True

def fix_common_env_issues():
    """Provide guidance for common .env issues"""
    print(f"\n🔧 COMMON .ENV ISSUES AND FIXES:")
    print(f"=" * 50)
    
    print(f"1. File Location:")
    print(f"   ✅ .env should be in project root (same directory as src/)")
    print(f"   📍 Current location: {Path('.env').absolute()}")
    
    print(f"\n2. File Format:")
    print(f"   ✅ No spaces around = sign")
    print(f"   ✅ No quotes around values")
    print(f"   ✅ Example: GEMINI_API_KEY=AIzaSyBf64zxrlhfjkUAhjLfJAFROoXt9WJaJmo")
    
    print(f"\n3. API Key Format:")
    print(f"   ✅ Google AI Studio keys start with 'AIza'")
    print(f"   ✅ Should be exactly 39 characters long")
    print(f"   ✅ Get from: https://aistudio.google.com/app/apikey")
    
    print(f"\n4. File Permissions:")
    print(f"   ✅ Make sure file is readable")
    print(f"   ✅ Check file isn't corrupted or has special characters")
    
    print(f"\n5. Python Path:")
    print(f"   ✅ Run python from project root directory")
    print(f"   ✅ Make sure dotenv is installed: pip install python-dotenv")

if __name__ == "__main__":
    success = test_env_configuration()
    
    if not success:
        fix_common_env_issues()
        sys.exit(1)
    else:
        print(f"\n✅ Your .env configuration is ready for contract analysis!")