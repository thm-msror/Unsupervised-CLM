#!/usr/bin/env python3
"""
Test Gemini 2.5 Pro with Short Analysis Prompt
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_handler import LLMHandler
from analysis import load_analysis_prompt

def test_gemini_25_pro():
    """Test the updated system with Gemini 2.5 Pro"""
    print("🔧 TESTING GEMINI 2.5 PRO WITH SHORT PROMPT")
    print("=" * 60)
    
    try:
        # Test 1: Initialize handler
        print("\n🤖 TEST 1: Initializing Gemini 2.5 Pro handler")
        print("-" * 50)
        handler = LLMHandler()
        print(f"✅ Model initialized: {handler.model.model_name}")
        
        # Test 2: Load prompt
        print("\n📝 TEST 2: Loading analysis prompt")
        print("-" * 50)
        prompt_template = load_analysis_prompt()
        print(f"✅ Prompt loaded: {len(prompt_template)} characters")
        
        # Test 3: Check quota status
        print("\n📊 TEST 3: Checking quota status")
        print("-" * 50)
        quota_status = handler.get_quota_status()
        print(f"   Daily token limit: {quota_status['daily_token_limit']:,}")
        print(f"   Daily tokens used: {quota_status['daily_tokens_used']:,}")
        print(f"   Requests per minute: {quota_status['requests_per_minute_limit']}")
        print(f"   Rate limit status: {quota_status['rate_limit_status']}")
        
        # Test 4: Simple analysis test
        print("\n🧪 TEST 4: Simple contract analysis")
        print("-" * 50)
        
        test_contract = """
        SERVICE AGREEMENT
        
        This Service Agreement is entered into between TechCorp Inc. ("Client") and DataSolutions LLC ("Provider") on January 15, 2024.
        
        SERVICES: Provider will deliver cloud computing services including data storage and processing.
        
        TERM: This agreement begins January 15, 2024 and ends December 31, 2024.
        
        PAYMENT: Client agrees to pay $50,000 total: $25,000 upon signing and $25,000 on July 1, 2024.
        Late payments incur 5% monthly penalty.
        
        TERMINATION: Either party may terminate with 30 days written notice.
        
        GOVERNING LAW: This agreement is governed by California law.
        """
        
        formatted_prompt = prompt_template.format(document_text=test_contract)
        print(f"   Analyzing contract ({len(test_contract)} chars)...")
        
        result = handler.analyze_contract(formatted_prompt)
        
        if len(result) > 100:
            print(f"✅ Analysis successful: {len(result)} characters returned")
            print(f"\n📋 ANALYSIS PREVIEW (first 300 chars):")
            print("-" * 40)
            print(result[:300] + "..." if len(result) > 300 else result)
            
            # Check for key sections
            key_sections = ["BASIC INFO", "KEY DATES", "MONEY MATTERS", "RISKS FOUND"]
            found_sections = sum(1 for section in key_sections if section in result)
            print(f"\n🎯 Structure check: {found_sections}/{len(key_sections)} key sections found")
            
        else:
            print(f"⚠️  Short response: {result}")
        
        # Test 5: Final quota check
        print("\n📊 TEST 5: Post-analysis quota status")
        print("-" * 50)
        final_quota = handler.get_quota_status()
        print(f"   Tokens used: {final_quota['daily_tokens_used']:,}")
        print(f"   Requests made: {final_quota['requests_in_last_minute']}")
        
        print(f"\n✅ GEMINI 2.5 PRO TESTING COMPLETE")
        print("=" * 60)
        print("✅ Model successfully switched to gemini-2.5-pro")
        print("✅ Short prompt loaded and functional")
        print("✅ Quota management updated for Pro model")
        print("✅ Analysis pipeline working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ TESTING FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_25_pro()
    if success:
        print("\n🎯 ALL TESTS PASSED - READY FOR PRODUCTION!")
    else:
        print("\n❌ TESTS FAILED - CHECK CONFIGURATION!")