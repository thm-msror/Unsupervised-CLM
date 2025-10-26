#!/usr/bin/env python3
"""
Intelligent Contract Summary Generator
Creates comprehensive summaries from analyzed documents with multilingual support
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys

# Add src path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_handler import LLMHandler

class ContractSummaryGenerator:
    """
    Generates intelligent contract summaries by consolidating multiple analysis files
    Supports multilingual documents and provides dashboard-ready outputs
    """
    
    def __init__(self):
        self.handler = None  # Initialize only when needed to save quota
        
        # Get the project root directory (parent of src/)
        project_root = Path(__file__).parent.parent
        
        self.analysis_dir = project_root / "data" / "analysed_documents"
        self.summary_dir = project_root / "data" / "contract_summaries"
        self.prompts_dir = project_root / "prompts"
        
        # Create directories if they don't exist
        self.summary_dir.mkdir(parents=True, exist_ok=True)
    
    def group_related_documents(self) -> Dict[str, List[Path]]:
        """
        Group analysis files by contract (Arabic + English versions)
        Returns dict mapping contract_name -> list of analysis files
        """
        print("🔍 GROUPING RELATED CONTRACT DOCUMENTS")
        print("=" * 60)
        
        if not self.analysis_dir.exists():
            print("❌ No analysis directory found")
            return {}
        
        analysis_files = list(self.analysis_dir.glob("*_analysis_*.txt"))
        print(f"📄 Found {len(analysis_files)} analysis files")
        
        # Group files by base contract name
        groups = {}
        
        for file_path in analysis_files:
            # Extract base contract name (remove language suffix and analysis timestamp)
            filename = file_path.stem
            
            # Remove analysis timestamp pattern: _analysis_YYYYMMDD_HHMMSS
            base_name = re.sub(r'_analysis_\d{8}_\d{6}', '', filename)
            
            # Remove language indicators
            base_name = re.sub(r'_(arabic|english)$', '', base_name, flags=re.IGNORECASE)
            
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append(file_path)
        
        print(f"📊 Grouped into {len(groups)} contract sets:")
        for contract_name, files in groups.items():
            print(f"   📋 {contract_name}: {len(files)} versions")
            for file in files:
                lang = "Arabic" if "_arabic_" in file.name else "English"
                print(f"      - {lang}: {file.name}")
        
        return groups
    
    def extract_analysis_content(self, file_path: Path) -> Dict[str, str]:
        """
        Extract structured content from analysis file
        Returns dict with sections and their content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect language
            language = "Arabic" if "_arabic_" in file_path.name else "English"
            
            # Extract key sections using regex patterns
            sections = {
                'language': language,
                'file_name': file_path.name,
                'basic_info': self._extract_section(content, r'\*\*1\. BASIC INFO\*\*.*?\n\n\*\*2\.', 'Basic Information'),
                'dates': self._extract_section(content, r'\*\*2\. KEY DATES\*\*.*?\n\n\*\*3\.', 'Key Dates'),  
                'financial': self._extract_section(content, r'\*\*3\. MONEY MATTERS\*\*.*?\n\n\*\*4\.', 'Financial Terms'),
                'obligations': self._extract_section(content, r'\*\*4\. MAIN OBLIGATIONS\*\*.*?\n\n\*\*5\.', 'Obligations'),
                'legal': self._extract_section(content, r'\*\*5\. LEGAL FRAMEWORK\*\*.*?\n\n\*\*6\.', 'Legal Framework'),
                'risks': self._extract_section(content, r'\*\*6\. RISK ANALYSIS\*\*.*?\n\n\*\*7\.', 'Risk Analysis'),
                'recommendations': self._extract_section(content, r'\*\*7\. RECOMMENDATIONS\*\*.*', 'Recommendations'),
                'full_content': content
            }
            
            return sections
            
        except Exception as e:
            print(f"⚠️  Error reading {file_path.name}: {e}")
            return {
                'language': 'Unknown',
                'file_name': file_path.name,
                'error': str(e),
                'full_content': ''
            }
    
    def _extract_section(self, content: str, pattern: str, section_name: str) -> str:
        """Extract specific section from analysis content"""
        try:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                # Clean up the extracted content
                section_text = match.group(0)
                # Remove the next section header
                section_text = re.sub(r'\n\n\*\*\d+\..*$', '', section_text)
                return section_text.strip()
            else:
                return f"[{section_name} section not found]"
        except Exception as e:
            return f"[Error extracting {section_name}: {e}]"
    
    def load_summarization_prompt(self) -> str:
        """Load the summarization prompt template from file"""
        prompt_file = self.prompts_dir / "summarization_prompt.txt"
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"⚠️  Prompt file not found: {prompt_file}")
            # Fallback to basic prompt
            return "Create a comprehensive executive summary of the following contract analysis:\n\n{CONTRACT_DATA}"
        except Exception as e:
            print(f"⚠️  Error loading prompt: {e}")
            return "Create a comprehensive executive summary of the following contract analysis:\n\n{CONTRACT_DATA}"
    
    def create_summary_prompt(self, contract_data: Dict[str, List[Dict]]) -> str:
        """
        Create optimized prompt for AI summary generation using template from file
        """
        # Load the prompt template from file
        prompt_template = self.load_summarization_prompt()
        
        # Build the contract data section
        contract_data_text = ""
        for contract_name, versions in contract_data.items():
            contract_data_text += f"\n### CONTRACT: {contract_name}\n"
            
            for version in versions:
                lang = version['language']
                contract_data_text += f"\n**{lang} Version Analysis:**\n"
                contract_data_text += f"- Basic Info: {version.get('basic_info', 'N/A')}\n"
                contract_data_text += f"- Key Dates: {version.get('dates', 'N/A')}\n" 
                contract_data_text += f"- Financial: {version.get('financial', 'N/A')}\n"
                contract_data_text += f"- Obligations: {version.get('obligations', 'N/A')}\n"
                contract_data_text += f"- Legal Framework: {version.get('legal', 'N/A')}\n"
                contract_data_text += f"- Risk Analysis: {version.get('risks', 'N/A')}\n"
        
        # Replace the placeholder with actual contract data
        final_prompt = prompt_template.replace("{CONTRACT_DATA}", contract_data_text)
        
        return final_prompt
    
    def generate_summary_for_contract_group(self, contract_name: str, analysis_files: List[Path], dry_run: bool = True) -> str:
        """
        Generate AI summary for a group of related contract analyses
        
        Args:
            contract_name: Base name of the contract
            analysis_files: List of analysis file paths
            dry_run: If True, return prompt without API call
        """
        print(f"\n📋 PROCESSING CONTRACT GROUP: {contract_name}")
        print("-" * 50)
        
        # Extract content from all analysis files
        contract_versions = []
        for file_path in analysis_files:
            print(f"   📄 Reading: {file_path.name}")
            analysis_data = self.extract_analysis_content(file_path)
            contract_versions.append(analysis_data)
        
        # Create consolidated data structure
        contract_data = {contract_name: contract_versions}
        
        # Generate summary prompt
        summary_prompt = self.create_summary_prompt(contract_data)
        
        if dry_run:
            print("   🔍 DRY RUN - Prompt generated (no API call)")
            print(f"   📊 Prompt length: {len(summary_prompt)} characters")
            return summary_prompt
        
        # Make API call (only when not in dry run)
        print("   🤖 Generating AI summary...")
        try:
            if not self.handler:
                self.handler = LLMHandler()
            
            summary_response = self.handler.analyze_contract(summary_prompt)
            print("   ✅ Summary generated successfully")
            return summary_response
            
        except Exception as e:
            print(f"   ❌ Error generating summary: {e}")
            return f"ERROR: Could not generate summary - {e}"
    
    def save_contract_summary(self, contract_name: str, summary_content: str, analysis_files: List[Path]):
        """Save the generated summary to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create summary metadata
        metadata = {
            'contract_name': contract_name,
            'generated_at': timestamp,
            'source_files': [f.name for f in analysis_files],
            'languages': []
        }
        
        # Detect languages from source files
        for file in analysis_files:
            if "_arabic_" in file.name:
                metadata['languages'].append('Arabic')
            else:
                metadata['languages'].append('English')
        
        # Create summary file content
        summary_header = f"""CONTRACT EXECUTIVE SUMMARY
==================================================
Contract: {contract_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source Files: {len(analysis_files)} analysis files
Languages: {', '.join(set(metadata['languages']))}
==================================================

"""
        
        full_summary = summary_header + summary_content
        
        # Save summary file
        summary_filename = f"{contract_name}_executive_summary_{timestamp}.txt"
        summary_path = self.summary_dir / summary_filename
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(full_summary)
        
        print(f"   💾 Summary saved: {summary_filename}")
        return summary_path
    
    def process_all_contracts(self, dry_run: bool = True) -> Dict[str, str]:
        """
        Process all contract groups and generate summaries
        
        Args:
            dry_run: If True, generate prompts without API calls
        """
        print("🚀 INTELLIGENT CONTRACT SUMMARY GENERATION")
        print("=" * 70)
        
        if dry_run:
            print("⚠️  DRY RUN MODE - No API calls will be made")
            print("   Use dry_run=False to generate actual summaries")
        
        contract_groups = self.group_related_documents()
        
        if not contract_groups:
            print("❌ No contract groups found")
            return {}
        
        results = {}
        
        for contract_name, analysis_files in contract_groups.items():
            summary_content = self.generate_summary_for_contract_group(
                contract_name, analysis_files, dry_run=dry_run
            )
            
            if not dry_run:
                # Save the actual summary
                summary_path = self.save_contract_summary(contract_name, summary_content, analysis_files)
                results[contract_name] = str(summary_path)
            else:
                # Store the prompt for review
                results[contract_name] = f"PROMPT_READY ({len(summary_content)} chars)"
        
        print(f"\n📊 PROCESSING COMPLETE")
        print(f"   📋 Contracts processed: {len(results)}")
        
        if dry_run:
            print(f"   🔍 Ready for API calls - set dry_run=False when satisfied")
        else:
            print(f"   💾 Summaries saved to: {self.summary_dir}")
        
        return results

def main():
    """Test the summary generation system"""
    generator = ContractSummaryGenerator()
    
    # Run in dry mode first to test without using quota
    print("🧪 TESTING SUMMARY GENERATION (DRY RUN)")
    results = generator.process_all_contracts(dry_run=True)
    
    print("\n📋 RESULTS:")
    for contract, status in results.items():
        print(f"   📄 {contract}: {status}")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Review the prompts generated above")
    print(f"   2. When ready, run: generator.process_all_contracts(dry_run=False)")
    print(f"   3. Check output in: {generator.summary_dir}")

if __name__ == "__main__":
    main()