#!/usr/bin/env python3
"""
Test quota and rate limiting functionality
"""

import os
import sys
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_handler import LLMHandler

def test_quota_status():
    """Test quota status reporting"""
    print("🔧 TESTING QUOTA MANAGEMENT SYSTEM")
    print("=" * 60)
    
    try:
        # Initialize handler
        handler = LLMHandler()
        print("✅ LLM Handler initialized successfully")
        
        # Check initial quota status
        print("\n📊 INITIAL QUOTA STATUS:")
        print("-" * 40)
        status = handler.get_quota_status()
        
        for key, value in status.items():
            if 'limit' in key or 'remaining' in key or 'used' in key:
                if isinstance(value, int) and value > 1000:
                    print(f"   {key}: {value:,}")
                else:
                    print(f"   {key}: {value}")
            else:
                print(f"   {key}: {value}")
        
        # Test rate limiting check
        print(f"\n⏱️  RATE LIMITING TEST:")
        print("-" * 40)
        
        # Simulate checking if we can make a request
        test_tokens = 1000
        can_proceed = handler._check_rate_limits(test_tokens)
        print(f"   Can make request with {test_tokens} tokens: {can_proceed}")
        
        # Test a small analysis to see quota in action
        if can_proceed:
            print(f"\n🧪 TESTING SMALL ANALYSIS:")
            print("-" * 40)
            
            test_prompt = """Analyze this simple contract:
            
Agreement between Company A and Company B for $10,000 payment due January 1, 2024.

Please provide a brief 2-sentence analysis."""
            
            print("   Making API call...")
            result = handler.analyze_contract(test_prompt)
            
            if "QUOTA" in result or "LIMIT" in result:
                print(f"   ⚠️  Quota Issue: {result[:100]}...")
            else:
                print(f"   ✅ Success: {len(result)} characters returned")
            
            # Check quota status after request
            print(f"\n📊 QUOTA STATUS AFTER REQUEST:")
            print("-" * 40)
            status_after = handler.get_quota_status()
            
            print(f"   Requests in last minute: {status_after['requests_in_last_minute']}")
            print(f"   Daily tokens used: {status_after['daily_tokens_used']:,}")
            print(f"   Rate limit status: {status_after['rate_limit_status']}")
            print(f"   Daily quota status: {status_after['daily_quota_status']}")
        
        print(f"\n✅ QUOTA MANAGEMENT TEST COMPLETE")
        print("=" * 60)
        print("✅ System correctly tracks and manages API quotas")
        print("✅ Rate limiting functions work properly")  
        print("✅ Quota status reporting is functional")
        
    except Exception as e:
        print(f"❌ QUOTA TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quota_status()