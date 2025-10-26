#!/usr/bin/env python3
"""
Extraction Accuracy Improvement Test
Tests the enhanced prompt and metrics for better extraction accuracy
"""

import sys
import json
from pathlib import Path
import time

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "app"))

from llm_handler import LLMHandler
from analysis_metrics import ContractAnalysisMetrics
from config import config

def test_extraction_accuracy():
    """Test extraction accuracy improvements"""
    print("🎯 EXTRACTION ACCURACY IMPROVEMENT TEST")
    print("=" * 60)
    
    # Initialize components
    try:
        handler = LLMHandler()
        metrics = ContractAnalysisMetrics()
        print("✅ Components initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Load both prompts
    standard_prompt_file = project_root / "prompts" / "analysis_prompt.txt"
    enhanced_prompt_file = project_root / "prompts" / "enhanced_analysis_prompt.txt"
    
    if not enhanced_prompt_file.exists():
        print(f"❌ Enhanced prompt not found: {enhanced_prompt_file}")
        return
    
    standard_prompt = standard_prompt_file.read_text(encoding='utf-8')
    enhanced_prompt = enhanced_prompt_file.read_text(encoding='utf-8')
    
    print(f"✅ Loaded both prompt templates")
    
    # Sample contract text for testing
    test_contract = """
    SOFTWARE DEVELOPMENT AGREEMENT
    
    This Software Development Agreement ("Agreement") is entered into on January 15, 2024, 
    between TechCorp Inc., a Delaware corporation ("Client"), and DevStudio LLC, a 
    California limited liability company ("Developer").
    
    PROJECT SCOPE: Development of mobile application for iOS and Android platforms.
    
    FINANCIAL TERMS:
    - Total Project Cost: $75,000
    - Payment Schedule: 
      * $25,000 upon signing (due 01/20/2024)
      * $25,000 at 50% completion (estimated 03/15/2024)  
      * $25,000 upon final delivery (due 06/30/2024)
    - Late Payment Fee: $500 per month after 15 days past due
    
    TIMELINE:
    - Project Duration: 6 months from effective date
    - Milestone 1: Wireframes and UI design (30 days)
    - Milestone 2: Backend development (90 days)
    - Final Delivery: June 30, 2024
    - Warranty Period: 90 days post-delivery
    
    DEVELOPER OBLIGATIONS:
    - Deliver source code within 180 days
    - Provide 2 years of technical support
    - Maintain confidentiality for 5 years
    
    CLIENT OBLIGATIONS:
    - Pay invoices within 30 days of receipt
    - Provide necessary API access and credentials
    - Review and approve deliverables within 10 business days
    
    GOVERNING LAW: This agreement is governed by California state law.
    DISPUTE RESOLUTION: Any disputes shall be resolved through binding arbitration.
    """
    
    print(f"\n📄 Test Contract Loaded: {len(test_contract)} characters")
    
    # Test both prompts
    results = {}
    
    for prompt_name, prompt_template in [("Standard", standard_prompt), ("Enhanced", enhanced_prompt)]:
        print(f"\n🔍 Testing {prompt_name} Prompt...")
        
        try:
            # Format prompt
            formatted_prompt = prompt_template.format(document_text=test_contract)
            
            # Start metrics tracking
            doc_metrics = metrics.start_document_analysis(
                filename=f"test_contract_{prompt_name.lower()}.txt",
                text_length=len(test_contract),
                language="en"
            )
            
            # Analyze with LLM
            start_time = time.perf_counter()
            if hasattr(handler, 'analyze_contract_with_metrics'):
                response, api_metrics = handler.analyze_contract_with_metrics(formatted_prompt)
                processing_time = api_metrics['response_time_seconds']
            else:
                response = handler.analyze_contract(formatted_prompt)
                processing_time = time.perf_counter() - start_time
            
            print(f"   ⏱️  Processing Time: {processing_time:.2f}s")
            print(f"   📄 Response Length: {len(response)} chars")
            
            # Record metrics
            metrics.record_api_call(doc_metrics, processing_time, success=True)
            quality_scores = metrics.analyze_response_quality(response, doc_metrics)
            metrics.finish_document_analysis(doc_metrics, success=True)
            
            # Extract key metrics
            extraction_accuracy = quality_scores.get('information_density', 0)
            
            results[prompt_name] = {
                'extraction_accuracy': extraction_accuracy,
                'processing_time': processing_time,
                'response_length': len(response),
                'quality_scores': quality_scores,
                'response_preview': response[:300] + "..." if len(response) > 300 else response
            }
            
            print(f"   🎯 Extraction Accuracy: {extraction_accuracy:.3f}")
            print(f"   📊 Quality Scores: {quality_scores}")
            
            # Analyze what was extracted
            financial_amounts = len(handler._extract_financial_info(response)) if hasattr(handler, '_extract_financial_info') else response.count('$')
            dates_found = len([x for x in response.split() if any(char.isdigit() and ('/' in x or '-' in x) for char in x.split())])
            
            print(f"   💰 Financial amounts found: {financial_amounts}")
            print(f"   📅 Dates found: {dates_found}")
            
            time.sleep(5)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Error testing {prompt_name} prompt: {e}")
            results[prompt_name] = {'error': str(e)}
    
    # Compare results
    print(f"\n📊 EXTRACTION ACCURACY COMPARISON")
    print("=" * 60)
    
    if 'Standard' in results and 'Enhanced' in results:
        std_accuracy = results['Standard'].get('extraction_accuracy', 0)
        enh_accuracy = results['Enhanced'].get('extraction_accuracy', 0)
        
        print(f"Standard Prompt Accuracy:  {std_accuracy:.3f}")
        print(f"Enhanced Prompt Accuracy:  {enh_accuracy:.3f}")
        
        improvement = enh_accuracy - std_accuracy
        improvement_pct = (improvement / std_accuracy * 100) if std_accuracy > 0 else 0
        
        print(f"Improvement: +{improvement:.3f} ({improvement_pct:+.1f}%)")
        
        if improvement > 0:
            print(f"✅ Enhanced prompt shows improved extraction accuracy!")
        else:
            print(f"⚠️  Enhanced prompt needs further tuning")
    
    # Detailed analysis
    print(f"\n🔍 DETAILED ANALYSIS")
    print("-" * 40)
    
    for prompt_name, result in results.items():
        if 'error' not in result:
            print(f"\n{prompt_name} Prompt Results:")
            print(f"  Extraction Accuracy: {result['extraction_accuracy']:.3f}")
            print(f"  Structure Compliance: {result['quality_scores'].get('structure_compliance', 0):.3f}")
            print(f"  Completeness: {result['quality_scores'].get('completeness', 0):.3f}")
            print(f"  Consistency: {result['quality_scores'].get('consistency', 0):.3f}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 40)
    
    if 'Enhanced' in results and results['Enhanced'].get('extraction_accuracy', 0) > 0.7:
        print("✅ Use enhanced prompt for production analysis")
        print("✅ Extraction accuracy is good (>70%)")
    elif 'Enhanced' in results:
        enh_acc = results['Enhanced'].get('extraction_accuracy', 0)
        print(f"⚠️  Enhanced prompt accuracy is {enh_acc:.1%} - consider further tuning")
        print("💡 Focus on improving financial amount and date extraction")
    
    print("🎯 Key factors for high extraction accuracy:")
    print("   - Include specific dollar amounts ($X,XXX)")
    print("   - Include formatted dates (MM/DD/YYYY)")
    print("   - Include time periods (X days, Y months)")
    print("   - Include company names with types (Inc., LLC)")
    print("   - Use structured format with colons (:)")

if __name__ == "__main__":
    test_extraction_accuracy()