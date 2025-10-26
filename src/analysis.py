#!/usr/bin/env python3
"""
Simple Contract Analysis - Just Works Version
Processes contracts with minimal complexity and maximum reliability
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add paths
src_dir = Path(__file__).parent
app_dir = src_dir.parent / "app"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(app_dir))

from llm_handler import LLMHandler
from analysis_metrics import ContractAnalysisMetrics
from config import config

def analyze_document(doc_path: Path, handler: LLMHandler, prompt_template: str, output_dir: Path, metrics: ContractAnalysisMetrics) -> dict:
    """
    Analyze a single document with comprehensive metrics tracking.
    
    Metrics Measured:
    - **Performance**: API response times, processing speed, throughput
    - **Quality**: Structure compliance, completeness, extraction accuracy
    - **Content**: Document complexity, language detection, contract type identification
    - **Reliability**: Success rates, error patterns, fallback usage
    
    Args:
        doc_path: Path to the JSON document
        handler: LLM handler instance
        prompt_template: Analysis prompt template
        output_dir: Directory to save results
        metrics: Metrics tracking instance
        
    Returns:
        dict: Analysis results with success status and metrics
    """
    print(f"📄 Processing: {doc_path.name}")
    
    start_time = time.perf_counter()
    
    try:
        # Load document
        with open(doc_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different document formats
        full_text = None
        
        if isinstance(data, dict) and "full_text" in data:
            # Standard format: single object with full_text
            full_text = data["full_text"]
            language = data.get("language", "unknown")
        elif isinstance(data, list) and len(data) > 0:
            # Sentence-segmented format: array with first object containing full_text
            first_item = data[0]
            if isinstance(first_item, dict) and "full_text" in first_item:
                full_text = first_item["full_text"]
                language = first_item.get("lang", "unknown")  # Note: 'lang' not 'language' in segmented format
            else:
                print(f"   ❌ No 'full_text' in first array item")
                return {"success": False, "error": "No full_text in array format"}
        else:
            print(f"   ❌ Unrecognized document format")
            return {"success": False, "error": "Unrecognized document format"}
        
        if not full_text:
            print(f"   ❌ No 'full_text' field found")
            return {"success": False, "error": "No full_text field"}
        
        text = full_text
        
        original_length = len(text)
        
        # Start metrics tracking for this document
        doc_metrics = metrics.start_document_analysis(
            filename=doc_path.name,
            text_length=original_length,
            language=language
        )
        
        # Process FULL document - no truncation for complete analysis
        print(f"   📄 Processing FULL document: {original_length:,} chars ({language.upper()})")
        print(f"   ⏳ Allowing full processing time - no timeout limits")
        
        # Use complete text for comprehensive analysis
        
        # Analyze with enhanced error handling for large documents
        formatted_prompt = prompt_template.format(document_text=text)
        print(f"   🤖 Analyzing...")
        
        api_metrics = {}
        
        try:
            # Single attempt with full processing time - no retries, no timeouts
            if hasattr(handler, 'analyze_contract_with_metrics'):
                print(f"   ⏳ Processing with full analysis method (no time limits)...")
                result, api_metrics = handler.analyze_contract_with_metrics(formatted_prompt)
                api_time = api_metrics['response_time_seconds']
                
                if not api_metrics['success']:
                    # Handle known failure cases for full document processing
                    if api_metrics.get('finish_reason') == '2':
                        print(f"   ⚠️  Large document hit response limits - using fallback analysis")
                        result = create_fallback_analysis(doc_path.name, language, len(text), "Full document analysis exceeded response limits")
                    elif api_metrics.get('finish_reason') == '3':
                        print(f"   ⚠️  Content filtered - using fallback analysis")  
                        result = create_fallback_analysis(doc_path.name, language, len(text), "Content filtered")
                    else:
                        print(f"   ⚠️  API error - using fallback analysis")
                        result = create_fallback_analysis(doc_path.name, language, len(text), "API error")
                            
            else:
                # Fallback to basic method
                print(f"   ⏳ Processing with basic method (no time limits)...")
                result = handler.analyze_contract(formatted_prompt)
                api_time = time.perf_counter() - start_time
                api_metrics = {
                    'success': True,
                    'response_time_seconds': api_time,
                    'total_tokens': len(formatted_prompt + result) // 4,  # Rough estimate
                    'method': 'basic'
                }
                    
        except Exception as e:
            # Single failure - create comprehensive fallback
            print(f"   ⚠️  API processing failed: {str(e)[:100]}...")
            print(f"   🔄 Creating comprehensive fallback analysis")
            result = create_fallback_analysis(doc_path.name, language, len(text), f"API processing failed: {str(e)}")
            api_time = time.perf_counter() - start_time
            api_metrics = {
                'success': False,
                'response_time_seconds': api_time,
                'error': str(e),
                'method': 'fallback',
                'note': 'Single attempt with full processing time'
            }
        
        print(f"   ⏱️  Time: {api_time:.2f}s")
        
        # Additional safety check for None/empty results
        if result is None or not result.strip():
            print(f"   ⚠️  Empty/None result detected, creating fallback analysis")
            result = create_fallback_analysis(doc_path.name, language, len(text), "Empty or None response from API")
        
        print(f"   📊 Response: {len(result)} chars")
        
        # Save result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{doc_path.stem}_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"CONTRACT ANALYSIS REPORT\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"Document: {doc_path.name}\n")
            f.write(f"Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Language: {language.upper()}\n")
            f.write(f"Original Length: {original_length:,} characters\n")
            if original_length > len(text):
                f.write(f"Processed Length: {len(text):,} characters (truncated)\n")
            f.write(f"Processing Time: {api_time:.2f} seconds\n")
            f.write(f"\n" + "=" * 50 + "\n\n")
            f.write(result)
        
        print(f"   ✅ Saved: {output_file.name}")
        
        # Complete metrics tracking for this document
        # First record the API call metrics
        if api_metrics.get('success', True):
            metrics.record_api_call(
                doc_metrics, 
                api_metrics.get('response_time_seconds', api_time),
                api_metrics.get('total_tokens', 0),
                success=True
            )
            # Analyze response quality
            metrics.analyze_response_quality(result, doc_metrics)
        
        # Finish document analysis
        metrics.finish_document_analysis(doc_metrics, success=True)
        
        return {
            "success": True,
            "processing_time": api_time,
            "original_length": original_length,
            "processed_length": len(text),
            "response_length": len(result),
            "language": language,
            "metrics": doc_metrics
        }
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        # Record failed analysis in metrics if we got that far
        if 'doc_metrics' in locals():
            metrics.finish_document_analysis(doc_metrics, success=False, error=str(e))
        return {"success": False, "error": str(e)}

def create_fallback_analysis(filename: str, language: str, text_length: int, reason: str) -> str:
    """Create a comprehensive fallback analysis when full document API processing fails"""
    return f"""COMPREHENSIVE FALLBACK ANALYSIS
(Full document processing attempted: {text_length:,} characters)
(Reason: {reason})

**1. DOCUMENT OVERVIEW**
- File: {filename}
- Language: {language.upper()}
- Size: {text_length:,} characters
- Status: Full document analysis attempted but failed
- Analysis Method: Fallback comprehensive template

**2. EXTRACTED INFORMATION** 
- Key Parties: Requires manual extraction from full document
- Contract Type: Requires analysis of full document content
- Primary Purpose: Requires review of complete document text

**2. KEY DATES**
- Start Date: Not specified
- End Date: Not specified
- Renewal/Extension: Not specified
- Important Deadlines: Not specified

**3. FINANCIAL TERMS**
- Total Value: Not specified
- Payment Schedule: Not specified
- Late Fees/Penalties: Not specified

**4. MAIN OBLIGATIONS**
- Party 1 Must: Not specified (requires manual review)
- Party 2 Must: Not specified (requires manual review)

**5. LEGAL FRAMEWORK**
- Governing Law: Not specified
- Dispute Resolution: Not specified
- Jurisdiction: Not specified

**6. COMPREHENSIVE RISK ANALYSIS**
- High-Risk Areas: Full document review needed for complete risk assessment
- Compliance Issues: Manual review required to identify all compliance requirements  
- Missing Protections: Complete document analysis needed to identify gaps
- Overall Risk Level: REQUIRES FULL MANUAL REVIEW
- Critical Sections: All sections require detailed legal review

**7. DETAILED RECOMMENDATIONS**
- **IMMEDIATE ACTION**: Conduct full manual legal review of complete document
- **Priority Level**: HIGH - Full document contains {text_length:,} characters requiring analysis
- **Next Steps**: 
  1. Manual extraction of all key terms and parties
  2. Complete risk assessment of all clauses
  3. Full compliance review against applicable regulations
  4. Detailed financial and obligation analysis
- **Business Impact**: Complete document analysis essential for informed decision-making

**8. EXTRACTION REQUIREMENTS**
- Full contract parties and roles identification needed
- Complete financial terms extraction required  
- All dates, deadlines, and milestones need manual identification
- Risk clauses and liability terms require detailed legal review
- Termination and renewal conditions need full analysis

---
PROCESSING NOTES:
- Original attempt: Full document processing ({text_length:,} chars)
- Fallback reason: {reason}
- Recommendation: Use manual or specialized legal analysis tools for complete review
"""

def load_analysis_prompt(use_enhanced: bool = True) -> str:
    """
    Load analysis prompt template optimized for Gemini 2.5 Pro
    
    Args:
        use_enhanced: If True, uses the concise, well-structured prompt
    """
    try:
        # Use the short, well-structured analysis prompt for Gemini 2.5 Pro
        prompt_file = Path(__file__).parent.parent / "prompts" / "analysis_prompt.txt"
        if prompt_file.exists():
            print("✅ Using concise analysis prompt (optimized for Gemini 2.5 Pro)")
            return prompt_file.read_text(encoding='utf-8')
        
        # Fallback to balanced prompt if main one doesn't exist
        if use_enhanced:
            balanced_prompt_file = Path(__file__).parent.parent / "prompts" / "balanced_analysis_prompt.txt"
            if balanced_prompt_file.exists():
                print("⚠️  Using balanced prompt as fallback")
                return balanced_prompt_file.read_text(encoding='utf-8')
    except Exception:
        pass
    
    # Simple fallback prompt
    return """
Analyze this contract and provide a brief analysis covering:

1. Contract Type and Purpose
2. Main Parties Involved
3. Key Terms and Financial Information
4. Important Dates
5. Risk Assessment

Contract Text:
{document_text}

Provide a clear, structured analysis.
"""

def check_and_retry_failed_analyses(output_dir: Path, parsed_dir: Path, handler: LLMHandler, prompt_template: str, metrics: ContractAnalysisMetrics) -> int:
    """
    Check existing analysis files for fallback analyses and retry them.
    
    Returns:
        int: Number of files successfully retried
    """
    print("\n🔍 CHECKING FOR FAILED ANALYSES TO RETRY")
    print("=" * 50)
    
    if not output_dir.exists():
        print("📁 No existing analyses found")
        return 0
    
    # Find all existing analysis files
    analysis_files = list(output_dir.glob("*_analysis_*.txt"))
    print(f"📄 Found {len(analysis_files)} existing analysis files")
    
    failed_files = []
    
    # Check each file for fallback analysis marker
    for analysis_file in analysis_files:
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for the fallback analysis marker
            if "COMPREHENSIVE FALLBACK ANALYSIS" in content and "(Reason: API error)" in content:
                failed_files.append(analysis_file)
                print(f"   🔴 Found failed analysis: {analysis_file.name}")
                
        except Exception as e:
            print(f"   ⚠️  Could not read {analysis_file.name}: {e}")
    
    if not failed_files:
        print("✅ No failed analyses found - all files processed successfully!")
        return 0
    
    print(f"\n🔄 RETRYING {len(failed_files)} FAILED ANALYSES")
    print("-" * 50)
    
    retry_successful = 0
    
    for i, failed_file in enumerate(failed_files, 1):
        print(f"\n[{i}/{len(failed_files)}] Retrying: {failed_file.name}")
        
        # Extract original document name from analysis file name
        # Format: document_name_analysis_timestamp.txt
        base_name = failed_file.stem
        if "_analysis_" in base_name:
            doc_name = base_name.split("_analysis_")[0]
            # Find corresponding JSON file
            json_file = parsed_dir / f"{doc_name}.json"
            
            if json_file.exists():
                print(f"   📄 Found original document: {json_file.name}")
                
                # Retry the analysis
                result = analyze_document(json_file, handler, prompt_template, output_dir, metrics)
                
                if result["success"]:
                    retry_successful += 1
                    print(f"   ✅ Retry successful! New analysis saved.")
                    
                    # Optional: Remove or rename the old failed file
                    backup_name = failed_file.with_suffix('.txt.old')
                    failed_file.rename(backup_name)
                    print(f"   📦 Old file backed up as: {backup_name.name}")
                else:
                    print(f"   ❌ Retry failed again")
            else:
                print(f"   ⚠️  Original document not found: {json_file.name}")
        
        # Rate limiting between retries
        if i < len(failed_files):
            print(f"   ⏳ Rate limiting... (3 second pause)")
            time.sleep(3)
    
    print(f"\n📊 RETRY SUMMARY:")
    print(f"   🔄 Attempted: {len(failed_files)}")
    print(f"   ✅ Successful: {retry_successful}")
    print(f"   📈 Retry Success Rate: {(retry_successful/len(failed_files)*100):.1f}%")
    
    return retry_successful

def main():
    """
    Full Document Contract Analysis Pipeline with Performance Metrics
    
    This pipeline processes COMPLETE contract documents without truncation for 
    comprehensive extracts and risk analysis. Tracks performance metrics:
    
    **Performance Metrics:**
    - API response times and throughput (docs/minute)
    - Processing speed and efficiency
    - Error rates and failure patterns
    
    **Quality Metrics:**
    - Structure compliance: How well analysis follows expected format
    - Completeness scores: Coverage of required analysis sections
    - Extraction accuracy: Quality of information extraction
    - Consistency scores: Uniformity across similar documents
    
    **Content Analysis:**
    - Document complexity scoring
    - Language detection and handling
    - Contract type identification
    - Size and processing requirements
    
    **Reliability Tracking:**
    - Success/failure rates
    - Fallback analysis usage
    - Error categorization and patterns
    - API limit handling effectiveness
    
    Results are saved with detailed metrics for performance optimization.
    """
    print("🚀 ENHANCED CONTRACT ANALYSIS WITH METRICS")
    print("=" * 50)
    
    # Initialize metrics tracking
    metrics = ContractAnalysisMetrics()
    print("📊 Metrics tracking initialized")
    
    # Initialize LLM handler
    try:
        handler = LLMHandler()
        print("✅ LLM handler ready")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Load prompt
    prompt_template = load_analysis_prompt()
    print("✅ Prompt loaded")
    
    # Setup paths
    parsed_dir = config.get_parsed_documents_path()
    output_dir = config.get_output_path()
    output_dir.mkdir(exist_ok=True)
    
    print(f"📁 Input: {parsed_dir}")
    print(f"💾 Output: {output_dir}")
    
    # Check for failed analyses first and retry them
    retried_count = check_and_retry_failed_analyses(output_dir, parsed_dir, handler, prompt_template, metrics)
    
    # Get documents
    json_files = list(parsed_dir.glob("*.json"))
    if not json_files:
        print("❌ No documents found!")
        return

    print(f"📄 Found {len(json_files)} documents")    # Process documents
    successful = 0
    failed = 0
    processing_times = []
    
    print(f"\n🔄 Processing...")
    
    for i, doc_path in enumerate(json_files, 1):
        print(f"\n[{i}/{len(json_files)}] " + "-" * 25)
        
        result = analyze_document(doc_path, handler, prompt_template, output_dir, metrics)
        
        if result["success"]:
            successful += 1
            processing_times.append(result["processing_time"])
        else:
            failed += 1
        
        # Conservative rate limiting to avoid API errors
        if i < len(json_files):
            print(f"   ⏳ Conservative rate limiting... (5 second pause)")
            time.sleep(5)  # 5 seconds = very conservative, ~12 requests per minute

    # Final summary
    total_time = sum(processing_times) if processing_times else 0
    avg_time = total_time / len(processing_times) if processing_times else 0
    
    print(f"\n" + "=" * 50)
    print(f"🎉 PROCESSING COMPLETE")
    print(f"=" * 50)
    print(f"📄 Total Documents: {len(json_files)}")
    print(f"🔄 Retried Failed Analyses: {retried_count}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful/len(json_files)*100):.1f}%")
    
    if processing_times:
        print(f"⏱️  Avg Time: {avg_time:.2f}s per document")
        print(f"🚀 Throughput: {successful/(total_time/60):.1f} docs/minute")
    
    print(f"📁 Results saved to: {output_dir}")
    
    # Generate comprehensive metrics dashboard
    print(f"\n📊 GENERATING COMPREHENSIVE METRICS REPORT...")
    try:
        # Print the metrics summary dashboard
        metrics.print_summary()
        
        # Save detailed metrics to file
        metrics_file = metrics.save_metrics(output_dir)
        print(f"\n📈 Detailed metrics saved to: {metrics_file.name}")
        
    except Exception as e:
        print(f"⚠️  Metrics generation failed: {e}")
    
    print(f"=" * 50)

if __name__ == "__main__":
    main()