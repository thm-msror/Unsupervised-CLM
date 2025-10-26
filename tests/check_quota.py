#!/usr/bin/env python3
"""
Quick quota checker for different models with Qatar time zone support
"""
import os
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env from parent directory
load_dotenv(Path("../.env"))

def test_model_quota(model_name: str) -> bool:
    """Test if a model has remaining quota"""
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel(model_name)
        
        # Simple test prompt
        response = model.generate_content("Hello, test message.")
        print(f"✅ {model_name}: Quota available")
        return True
        
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            print(f"❌ {model_name}: Quota exceeded")
        else:
            print(f"⚠️  {model_name}: Other error - {str(e)[:100]}")
        return False

def get_reset_times():
    """Calculate quota reset times in different time zones"""
    # Google's quotas typically reset at midnight Pacific Time
    pst_tz = timezone(timedelta(hours=-8))  # Pacific Standard Time
    qatar_tz = timezone(timedelta(hours=3))  # Qatar Standard Time (UTC+3)
    utc_tz = timezone.utc
    
    now_utc = datetime.now(utc_tz)
    now_pst = now_utc.astimezone(pst_tz)
    now_qatar = now_utc.astimezone(qatar_tz)
    
    # Calculate next midnight PST
    next_pst_midnight = now_pst.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    next_pst_midnight_utc = next_pst_midnight.astimezone(utc_tz)
    next_pst_midnight_qatar = next_pst_midnight_utc.astimezone(qatar_tz)
    
    # Calculate time remaining
    time_until_reset = next_pst_midnight_utc - now_utc
    hours_remaining = int(time_until_reset.total_seconds() // 3600)
    minutes_remaining = int((time_until_reset.total_seconds() % 3600) // 60)
    
    return {
        'current_qatar_time': now_qatar.strftime("%Y-%m-%d %H:%M:%S"),
        'current_pst_time': now_pst.strftime("%Y-%m-%d %H:%M:%S"),
        'reset_qatar_time': next_pst_midnight_qatar.strftime("%Y-%m-%d %H:%M:%S"),
        'reset_pst_time': next_pst_midnight.strftime("%Y-%m-%d %H:%M:%S"),
        'hours_remaining': hours_remaining,
        'minutes_remaining': minutes_remaining
    }

def main():
    print("🔍 CHECKING QUOTA FOR DIFFERENT MODELS")
    print("=" * 60)
    
    # Show current time information
    time_info = get_reset_times()
    print(f"🇶🇦 Current Qatar Time: {time_info['current_qatar_time']}")
    print(f"🇺🇸 Current PST Time: {time_info['current_pst_time']}")
    print("=" * 60)
    
    models_to_check = [
        'gemini-2.5-pro',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite'
    ]
    
    available_models = []
    quota_exceeded_models = []
    
    for model in models_to_check:
        if test_model_quota(model):
            available_models.append(model)
        else:
            quota_exceeded_models.append(model)
        time.sleep(2)  # Small delay between tests
    
    print(f"\n📊 QUOTA STATUS RESULTS:")
    print("-" * 40)
    
    if available_models:
        print(f"✅ Available models ({len(available_models)}):")
        for model in available_models:
            print(f"   🟢 {model}")
        print(f"\n🎯 Recommended: {available_models[0]}")
    
    if quota_exceeded_models:
        print(f"\n❌ Quota exceeded models ({len(quota_exceeded_models)}):")
        for model in quota_exceeded_models:
            print(f"   🔴 {model}")
    
    if quota_exceeded_models:
        print(f"\n⏰ QUOTA RESET INFORMATION:")
        print("-" * 40)
        print(f"🇶🇦 Reset in Qatar: {time_info['reset_qatar_time']}")
        print(f"🇺🇸 Reset in PST: {time_info['reset_pst_time']}")
        print(f"⏱️  Time remaining: {time_info['hours_remaining']}h {time_info['minutes_remaining']}m")
        
    if not available_models:
        print(f"\n🚨 ALL MODELS QUOTA EXCEEDED!")
        print(f"💤 Wait {time_info['hours_remaining']}h {time_info['minutes_remaining']}m for reset")

if __name__ == "__main__":
    main()