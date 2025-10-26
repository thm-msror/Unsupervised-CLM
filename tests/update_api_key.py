#!/usr/bin/env python3
"""
Helper script to update API key in .env file
"""
import os
from pathlib import Path

def update_api_key():
    """Interactive API key updater"""
    env_file = Path("../.env")  # .env file is in parent directory
    
    print("🔑 API KEY UPDATER")
    print("=" * 30)
    
    # Get current key
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        current_key = None
        for line in lines:
            if line.startswith('GEMINI_API_KEY='):
                current_key = line.split('=')[1].strip()
                break
        
        if current_key:
            print(f"Current API key: {current_key[:6]}...{current_key[-4:]}")
        else:
            print("No current API key found")
    
    # Get new key
    new_key = input("\nEnter new API key (or press Enter to cancel): ").strip()
    
    if not new_key:
        print("❌ Cancelled")
        return
    
    # Validate format
    if not new_key.startswith('AIza') or len(new_key) != 39:
        print("⚠️  Warning: API key format may be incorrect")
        print("Expected: Starts with 'AIza', 39 characters long")
        confirm = input("Continue anyway? (y/N): ").lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return
    
    # Update .env file
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace the API key line
        if 'GEMINI_API_KEY=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('GEMINI_API_KEY='):
                    lines[i] = f'GEMINI_API_KEY={new_key}'
                    break
            
            new_content = '\n'.join(lines)
        else:
            # Add API key if not exists
            new_content = content + f'\nGEMINI_API_KEY={new_key}\n'
    else:
        # Create new .env file
        new_content = f"""# Google Gemini API key for contract analysis
GEMINI_API_KEY={new_key}

# App configurations
STREAMLIT_SERVER_PORT=8501
"""
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ API key updated successfully!")
    print(f"📁 File: {env_file.absolute()}")
    
    # Test the new key
    print(f"\n🔄 Testing new API key...")
    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
        
        load_dotenv(env_file, override=True)  # Reload .env from correct path
        api_key = os.getenv('GEMINI_API_KEY')
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        print(f"✅ New API key working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing new API key: {e}")
        print(f"Please check the API key and try again")

if __name__ == "__main__":
    update_api_key()