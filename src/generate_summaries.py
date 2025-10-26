#!/usr/bin/env python3
"""
Generate actual contract summaries (not dry run)
This will make API calls and save summaries to data/contract_summaries/
"""

import sys
from pathlib import Path

# Import from same directory
from contract_summary_generator import ContractSummaryGenerator

def generate_actual_summaries():
    """Generate real contract summaries using API calls"""
    print("🚀 GENERATING ACTUAL CONTRACT SUMMARIES")
    print("=" * 60)
    print("⚠️  This will make API calls and use quota")
    print("✅ Proceeding with actual summary generation...")
    
    try:
        generator = ContractSummaryGenerator()
        
        # Generate actual summaries (dry_run=False)
        results = generator.process_all_contracts(dry_run=False)
        
        print(f"\n🎉 SUMMARY GENERATION COMPLETE!")
        print(f"📁 Output directory: {generator.summary_dir}")
        print(f"📊 Generated summaries: {len(results)}")
        
        print(f"\n📋 GENERATED FILES:")
        for contract_name, file_path in results.items():
            print(f"   📄 {contract_name}")
            print(f"      💾 Saved to: {Path(file_path).name}")
        
        # List all files in the directory
        summary_files = list(generator.summary_dir.glob("*.txt"))
        print(f"\n📁 ALL SUMMARY FILES ({len(summary_files)} total):")
        for file in summary_files:
            print(f"   📄 {file.name}")
        
    except Exception as e:
        print(f"❌ Error generating summaries: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_actual_summaries()