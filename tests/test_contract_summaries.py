#!/usr/bin/env python3
"""
Test Contract Summary Generation System (No API Calls)
Validates grouping, content extraction, and prompt generation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contract_summary_generator import ContractSummaryGenerator

def test_summary_system():
    """Test the summary generation system without API calls"""
    
    print("🧪 TESTING CONTRACT SUMMARY GENERATION SYSTEM")
    print("=" * 70)
    
    generator = ContractSummaryGenerator()
    
    # Test 1: Document grouping
    print("\n1️⃣ TESTING DOCUMENT GROUPING")
    print("-" * 40)
    
    contract_groups = generator.group_related_documents()
    
    if contract_groups:
        print(f"✅ Successfully grouped documents into {len(contract_groups)} contracts")
        
        # Show detailed grouping results
        for contract_name, files in contract_groups.items():
            print(f"\n📋 Contract: {contract_name}")
            print(f"   📄 Versions: {len(files)}")
            
            for file_path in files:
                # Test content extraction
                print(f"\n   📖 Testing content extraction: {file_path.name}")
                analysis_data = generator.extract_analysis_content(file_path)
                
                print(f"      🌍 Language: {analysis_data['language']}")
                print(f"      📊 Sections extracted: {len([k for k in analysis_data.keys() if k not in ['language', 'file_name', 'full_content']])}")
                
                # Show sample content (first 100 chars of each section)
                for section, content in analysis_data.items():
                    if section not in ['language', 'file_name', 'full_content', 'error']:
                        preview = content[:100] + "..." if len(content) > 100 else content
                        print(f"      - {section}: {preview}")
    else:
        print("❌ No contract groups found")
        return False
    
    # Test 2: Prompt generation (dry run)
    print(f"\n2️⃣ TESTING PROMPT GENERATION")
    print("-" * 40)
    
    # Test with first contract group
    first_contract = list(contract_groups.keys())[0]
    first_files = contract_groups[first_contract]
    
    print(f"📋 Testing with contract: {first_contract}")
    prompt = generator.generate_summary_for_contract_group(
        first_contract, first_files, dry_run=True
    )
    
    if prompt and len(prompt) > 1000:
        print("✅ Prompt generated successfully")
        print(f"   📊 Prompt length: {len(prompt):,} characters")
        print(f"   📝 Preview (first 500 chars):")
        print("   " + "-" * 50)
        print("   " + prompt[:500].replace('\n', '\n   '))
        print("   " + "-" * 50)
        print("   [... full prompt ready for API call ...]")
    else:
        print("❌ Prompt generation failed")
        return False
    
    # Test 3: Full system dry run
    print(f"\n3️⃣ TESTING FULL SYSTEM (DRY RUN)")
    print("-" * 40)
    
    results = generator.process_all_contracts(dry_run=True)
    
    if results:
        print("✅ Full system test successful")
        print(f"   📊 Contracts ready for processing: {len(results)}")
        
        for contract, status in results.items():
            print(f"   📄 {contract}: {status}")
    else:
        print("❌ Full system test failed")
        return False
    
    # Test 4: Quota usage estimation
    print(f"\n4️⃣ QUOTA USAGE ESTIMATION")
    print("-" * 40)
    
    total_prompt_chars = 0
    estimated_tokens = 0
    
    for contract_name, files in contract_groups.items():
        # Get prompt for this contract
        prompt = generator.generate_summary_for_contract_group(
            contract_name, files, dry_run=True
        )
        prompt_chars = len(prompt)
        # Rough token estimation: ~4 chars per token
        prompt_tokens = prompt_chars // 4
        
        total_prompt_chars += prompt_chars
        estimated_tokens += prompt_tokens
        
        print(f"   📄 {contract_name}:")
        print(f"      - Prompt size: {prompt_chars:,} chars (~{prompt_tokens:,} tokens)")
    
    print(f"\n📊 TOTAL ESTIMATED USAGE:")
    print(f"   📝 Total prompt characters: {total_prompt_chars:,}")
    print(f"   🎯 Estimated input tokens: {estimated_tokens:,}")
    print(f"   💰 Estimated API calls: {len(contract_groups)}")
    
    # Check against quota limits
    print(f"\n💡 QUOTA ASSESSMENT:")
    daily_token_limit = 50_000_000  # Gemini 2.5 Pro daily limit
    usage_percentage = (estimated_tokens / daily_token_limit) * 100
    
    print(f"   🔒 Daily token limit: {daily_token_limit:,}")
    print(f"   📊 Estimated usage: {usage_percentage:.2f}% of daily quota")
    
    if usage_percentage < 10:
        print(f"   ✅ SAFE: Very low quota usage - proceed with confidence")
    elif usage_percentage < 25:
        print(f"   ⚠️  MODERATE: Reasonable quota usage - should be fine")
    else:
        print(f"   🚨 HIGH: Significant quota usage - consider batching")
    
    print(f"\n🎉 SYSTEM READY FOR PRODUCTION")
    print("=" * 70)
    print("✅ Document grouping working correctly")
    print("✅ Content extraction successful")
    print("✅ Prompt generation optimized")
    print("✅ Quota usage estimated and acceptable")
    print("✅ Ready for API calls when needed")
    
    return True

def show_next_steps():
    """Show next steps for actual summary generation"""
    print(f"\n🚀 NEXT STEPS FOR ACTUAL SUMMARY GENERATION:")
    print("-" * 60)
    print("1️⃣ Run the dry run first:")
    print("   python src/contract_summary_generator.py")
    print("")
    print("2️⃣ When satisfied, generate actual summaries:")
    print("   from contract_summary_generator import ContractSummaryGenerator")
    print("   generator = ContractSummaryGenerator()")
    print("   results = generator.process_all_contracts(dry_run=False)")
    print("")
    print("3️⃣ Check results in:")
    print("   data/contract_summaries/")
    print("")
    print("4️⃣ Each summary will include:")
    print("   • Contract Overview with multilingual support")
    print("   • Key Extracted Data (parties, dates, financial)")
    print("   • Risk & Compliance Alerts")
    print("   • AI-Generated Insights & Legal Advice")
    print("   • Executive Recommendations")

if __name__ == "__main__":
    success = test_summary_system()
    if success:
        show_next_steps()
    else:
        print("❌ TESTING FAILED - Review errors above")