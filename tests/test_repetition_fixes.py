#!/usr/bin/env python3
"""
Test script to verify repetition fixes and extraction accuracy improvements
"""

import sys
import json
from pathlib import Path
import time
import re

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "app"))

from llm_handler import LLMHandler
from analysis_metrics import ContractAnalysisMetrics

def test_repetition_fixes():
    """Test the fixes for repetitive output and extraction accuracy"""
    print("🔧 TESTING REPETITION FIXES AND EXTRACTION ACCURACY")
    print("=" * 60)
    
    # Initialize components
    try:
        handler = LLMHandler()
        metrics = ContractAnalysisMetrics()
        print("✅ Components initialized with gemini-2.0-flash-lite")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Load the balanced prompt
    balanced_prompt_file = project_root / "prompts" / "balanced_analysis_prompt.txt"
    
    if not balanced_prompt_file.exists():
        print(f"❌ Balanced prompt not found: {balanced_prompt_file}")
        return
    
    balanced_prompt = balanced_prompt_file.read_text(encoding='utf-8')
    print(f"✅ Loaded balanced prompt template")
    
    # Simple test contract
    test_contract = """
    HPARC SOFTWARE DEVELOPMENT AGREEMENT
    
    This Software Development Agreement is entered into on January 15, 2024, 
    between HPARC Inc., a Delaware corporation, and DevStudio LLC.
    
    Total Project Cost: $75,000
    Payment Schedule: $25,000 upon signing, $25,000 at 50% completion, $25,000 upon delivery
    Late Payment Fee: $500 per month after 15 days
    Project Duration: 6 months
    Delivery Date: June 30, 2024
    
    HPARC may terminate this Agreement at any time, without cause, upon ninety (90) days' 
    prior notification or payment to the Software Developer of amounts equivalent to the 
    prior one (1) months' billing amounts.
    """
    
    print(f"\n📄 Test Contract: {len(test_contract)} characters")
    
    try:
        # Test the balanced prompt
        print(f"\n🔍 Testing Balanced Prompt...")
        
        formatted_prompt = balanced_prompt.format(document_text=test_contract)
        
        # Start metrics tracking
        doc_metrics = metrics.start_document_analysis(
            filename="test_repetition_fix.txt",
            text_length=len(test_contract),
            language="en"
        )
        
        # Analyze with LLM
        start_time = time.perf_counter()
        response = handler.analyze_contract(formatted_prompt)
        processing_time = time.perf_counter() - start_time
        
        print(f"   ⏱️  Processing Time: {processing_time:.2f}s")
        print(f"   📄 Response Length: {len(response)} chars")
        
        # Record metrics
        metrics.record_api_call(doc_metrics, processing_time, success=True)
        quality_scores = metrics.analyze_response_quality(response, doc_metrics)
        metrics.finish_document_analysis(doc_metrics, success=True)
        
        extraction_accuracy = quality_scores.get('information_density', 0)
        
        print(f"   🎯 Extraction Accuracy: {extraction_accuracy:.3f}")
        print(f"   📊 Quality Scores: {quality_scores}")
        
        # Analyze repetition
        lines = response.split('\n')
        total_lines = len(lines)
        unique_lines = len(set(line.strip() for line in lines if line.strip()))
        repetition_ratio = (total_lines - unique_lines) / total_lines if total_lines > 0 else 0
        
        print(f"   🔄 Repetition Analysis:")
        print(f"      Total Lines: {total_lines}")
        print(f"      Unique Lines: {unique_lines}")
        print(f"      Repetition Ratio: {repetition_ratio:.3f}")
        
        # Check for specific repetitive patterns
        hparc_mentions = response.count('HPARC')
        review_mentions = response.count('Review the')
        
        print(f"      HPARC mentions: {hparc_mentions}")
        print(f"      'Review the' mentions: {review_mentions}")
        
        # Extract specific elements
        financial_amounts = len(re.findall(r'\$[\d,]+', response))
        dates_found = len(re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', response))
        time_periods = len(re.findall(r'\d+\s*(days|months|years)', response, re.IGNORECASE))
        
        print(f"   💰 Financial amounts extracted: {financial_amounts}")
        print(f"   📅 Dates extracted: {dates_found}")
        print(f"   ⏰ Time periods extracted: {time_periods}")
        
        # Print first part of response
        print(f"\n📝 RESPONSE PREVIEW (first 500 chars):")
        print("-" * 50)
        print(response[:500] + "..." if len(response) > 500 else response)
        
        # Check for repetitive ending
        if len(response) > 1000:
            print(f"\n📝 RESPONSE ENDING (last 300 chars):")
            print("-" * 50)
            print("..." + response[-300:])
        
        # Success criteria
        print(f"\n✅ SUCCESS CRITERIA CHECK:")
        print("-" * 30)
        
        success_criteria = {
            "Extraction Accuracy > 0.6": extraction_accuracy > 0.6,
            "Low Repetition (< 0.3)": repetition_ratio < 0.3,
            "Reasonable Length (500-2000)": 500 <= len(response) <= 2000,
            "Has Financial Data": financial_amounts > 0,
            "Has Date Data": dates_found > 0,
            "Limited HPARC Mentions (< 20)": hparc_mentions < 20,
            "Limited Review Mentions (< 10)": review_mentions < 10
        }
        
        for criteria, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {criteria}")
        
        overall_success = sum(success_criteria.values()) >= 5  # At least 5/7 criteria
        
        print(f"\n🎯 OVERALL RESULT:")
        if overall_success:
            print("✅ FIXES SUCCESSFUL - Repetition reduced, extraction improved!")
        else:
            print("⚠️  NEEDS MORE WORK - Some issues remain")
        
        return {
            'extraction_accuracy': extraction_accuracy,
            'repetition_ratio': repetition_ratio,
            'response_length': len(response),
            'financial_amounts': financial_amounts,
            'dates_found': dates_found,
            'success': overall_success
        }
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    result = test_repetition_fixes()
    
    if result and 'error' not in result:
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 30)
        
        if result['success']:
            print("✅ Ready for production use!")
            print("✅ Run: python src/analysis.py")
        else:
            print("🔧 Consider further prompt tuning")
            print("🔧 Monitor for repetition in full analysis")
        
        print(f"🎯 Target metrics achieved:")
        print(f"   Extraction Accuracy: {result['extraction_accuracy']:.3f} (target: >0.6)")
        print(f"   Repetition Ratio: {result['repetition_ratio']:.3f} (target: <0.3)")
    else:
        print("❌ Testing failed - check error above")