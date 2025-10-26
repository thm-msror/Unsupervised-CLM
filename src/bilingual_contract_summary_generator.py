#!/usr/bin/env python3
"""
Enhanced Contract Summary Generator with Translation Support
Handles bilingual contract analysis and summaries with proper RTL support
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys

# Add src path
sys.path.insert(0, str(Path(__file__).parent))

from llm_handler import LLMHandler
from translation_handler import TranslationHandler

class BilingualContractSummaryGenerator:
    """
    Enhanced Contract Summary Generator with Arabic/English translation support
    Creates bilingual summaries with proper RTL formatting
    """
    
    def __init__(self):
        self.handler = None  # Initialize only when needed to save quota
        self.translator = TranslationHandler()
        
        # Get the project root directory (parent of src/)
        project_root = Path(__file__).parent.parent
        
        self.analysis_dir = project_root / "data" / "analysed_documents"
        self.summary_dir = project_root / "data" / "contract_summaries"
        self.prompts_dir = project_root / "prompts"
        
        # Create directories if they don't exist
        self.summary_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_document_language(self, file_path: Path) -> str:
        """Detect the primary language of a document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use translator's language detection
            detected = self.translator.detect_language(content)
            
            # Also check filename for language indicators
            filename_lang = 'ar' if '_arabic_' in file_path.name else 'en'
            
            # Combine detection methods
            if detected == 'ar' or filename_lang == 'ar':
                return 'ar'
            else:
                return 'en'
            
        except Exception as e:
            print(f"⚠️ Language detection failed for {file_path.name}: {e}")
            # Fallback to filename
            return 'ar' if '_arabic_' in file_path.name else 'en'
    
    def create_bilingual_analysis(self, analysis_file: Path, target_language: str = None) -> Dict[str, str]:
        """
        Create or translate analysis to target language
        
        Args:
            analysis_file: Path to analysis file
            target_language: 'ar' or 'en', if None will detect and create opposite
        
        Returns:
            Dict with translated analysis sections
        """
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            source_lang = self.detect_document_language(analysis_file)
            
            if target_language is None:
                # Create opposite language version
                target_language = 'en' if source_lang == 'ar' else 'ar'
            
            if source_lang == target_language:
                # Already in target language, extract sections normally
                return self._extract_analysis_sections(content, target_language)
            
            # Translate the analysis
            print(f"🔄 Translating analysis from {source_lang} to {target_language}...")
            translated_sections = self.translator.translate_contract_analysis(content, target_language)
            
            return translated_sections
            
        except Exception as e:
            print(f"❌ Error creating bilingual analysis: {e}")
            return {
                'basic_info': f'[Translation error: {e}]',
                'dates': f'[Translation error: {e}]',
                'financial': f'[Translation error: {e}]',
                'obligations': f'[Translation error: {e}]',
                'legal': f'[Translation error: {e}]',
                'risks': f'[Translation error: {e}]',
                'recommendations': f'[Translation error: {e}]',
                'full_content': content
            }
    
    def _extract_analysis_sections(self, content: str, language: str) -> Dict[str, str]:
        """Extract sections from analysis content without translation"""
        sections = {
            'language': language,
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
    
    def _extract_section(self, content: str, pattern: str, section_name: str) -> str:
        """Extract specific section from analysis content"""
        try:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                section_text = match.group(0)
                section_text = re.sub(r'\n\n\*\*\d+\..*$', '', section_text)
                return section_text.strip()
            else:
                return f"[{section_name} section not found]"
        except Exception as e:
            return f"[Error extracting {section_name}: {e}]"
    
    def group_related_documents(self) -> Dict[str, Dict[str, List[Path]]]:
        """
        Group analysis files by contract with language separation
        Returns dict mapping contract_name -> {'ar': [files], 'en': [files]}
        """
        print("🔍 GROUPING RELATED CONTRACT DOCUMENTS WITH LANGUAGE DETECTION")
        print("=" * 70)
        
        if not self.analysis_dir.exists():
            print("❌ No analysis directory found")
            return {}
        
        analysis_files = list(self.analysis_dir.glob("*_analysis_*.txt"))
        print(f"📄 Found {len(analysis_files)} analysis files")
        
        # Group files by base contract name and language
        groups = {}
        
        for file_path in analysis_files:
            # Extract base contract name
            filename = file_path.stem
            base_name = re.sub(r'_analysis_\d{8}_\d{6}', '', filename)
            base_name = re.sub(r'_(arabic|english)$', '', base_name, flags=re.IGNORECASE)
            
            # Detect language
            detected_lang = self.detect_document_language(file_path)
            
            if base_name not in groups:
                groups[base_name] = {'ar': [], 'en': []}
            
            groups[base_name][detected_lang].append(file_path)
        
        # Print grouping results
        print(f"📊 Grouped into {len(groups)} contract sets:")
        for contract_name, lang_files in groups.items():
            ar_count = len(lang_files['ar'])
            en_count = len(lang_files['en'])
            print(f"   📋 {contract_name}: {ar_count} Arabic, {en_count} English")
            
            for lang, files in lang_files.items():
                for file in files:
                    lang_name = "العربية" if lang == 'ar' else "English"
                    print(f"      - {lang_name}: {file.name}")
        
        return groups
    
    def create_bilingual_summary_prompt(self, contract_name: str, arabic_analysis: Dict[str, str], english_analysis: Dict[str, str]) -> str:
        """
        Create bilingual summary prompt with both Arabic and English analysis
        """
        # Load the prompt template from file
        prompt_template = self.load_summarization_prompt()
        
        # Build bilingual contract data
        contract_data_text = f"\n### CONTRACT: {contract_name}\n"
        
        # Add Arabic analysis
        if arabic_analysis and arabic_analysis.get('basic_info'):
            contract_data_text += f"\n**النسخة العربية (Arabic Version Analysis):**\n"
            contract_data_text += f"- المعلومات الأساسية: {arabic_analysis.get('basic_info', 'غير متوفر')}\n"
            contract_data_text += f"- التواريخ المهمة: {arabic_analysis.get('dates', 'غير متوفر')}\n"
            contract_data_text += f"- الشؤون المالية: {arabic_analysis.get('financial', 'غير متوفر')}\n"
            contract_data_text += f"- الالتزامات الرئيسية: {arabic_analysis.get('obligations', 'غير متوفر')}\n"
            contract_data_text += f"- الإطار القانوني: {arabic_analysis.get('legal', 'غير متوفر')}\n"
            contract_data_text += f"- تحليل المخاطر: {arabic_analysis.get('risks', 'غير متوفر')}\n"
            contract_data_text += f"- التوصيات: {arabic_analysis.get('recommendations', 'غير متوفر')}\n"
        
        # Add English analysis
        if english_analysis and english_analysis.get('basic_info'):
            contract_data_text += f"\n**English Version Analysis:**\n"
            contract_data_text += f"- Basic Info: {english_analysis.get('basic_info', 'N/A')}\n"
            contract_data_text += f"- Key Dates: {english_analysis.get('dates', 'N/A')}\n"
            contract_data_text += f"- Financial: {english_analysis.get('financial', 'N/A')}\n"
            contract_data_text += f"- Obligations: {english_analysis.get('obligations', 'N/A')}\n"
            contract_data_text += f"- Legal Framework: {english_analysis.get('legal', 'N/A')}\n"
            contract_data_text += f"- Risk Analysis: {english_analysis.get('risks', 'N/A')}\n"
            contract_data_text += f"- Recommendations: {english_analysis.get('recommendations', 'N/A')}\n"
        
        # Replace placeholder in template
        return prompt_template.replace("{CONTRACT_DATA}", contract_data_text)
    
    def load_summarization_prompt(self) -> str:
        """Load the summarization prompt template from file"""
        prompt_file = self.prompts_dir / "summarization_prompt.txt"
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"⚠️  Prompt file not found: {prompt_file}")
            return "Create a comprehensive bilingual executive summary:\n\n{CONTRACT_DATA}"
        except Exception as e:
            print(f"⚠️  Error loading prompt: {e}")
            return "Create a comprehensive bilingual executive summary:\n\n{CONTRACT_DATA}"
    
    def process_bilingual_contracts(self, dry_run: bool = True) -> Dict[str, str]:
        """
        Process contracts with bilingual support
        Creates summaries in both Arabic and English when possible
        """
        print("🚀 BILINGUAL CONTRACT SUMMARY GENERATION")
        print("=" * 70)
        
        if dry_run:
            print("⚠️  DRY RUN MODE - No API calls will be made")
            print("   Use dry_run=False to generate actual summaries")
        
        # Check translation status
        translation_status = self.translator.get_translation_status()
        print(f"\n🔄 Translation Services Status:")
        for service, available in translation_status.items():
            status_icon = "✅" if available else "❌"
            print(f"   {status_icon} {service}")
        
        contract_groups = self.group_related_documents()
        
        if not contract_groups:
            print("❌ No contract groups found")
            return {}
        
        results = {}
        
        for contract_name, lang_files in contract_groups.items():
            print(f"\n📋 PROCESSING BILINGUAL CONTRACT: {contract_name}")
            print("-" * 60)
            
            arabic_analysis = {}
            english_analysis = {}
            
            # Process Arabic files
            if lang_files['ar']:
                print(f"   🔍 Processing Arabic version...")
                ar_file = lang_files['ar'][0]  # Take first Arabic file
                arabic_analysis = self._extract_analysis_sections(
                    open(ar_file, 'r', encoding='utf-8').read(), 'ar'
                )
                print(f"   ✅ Arabic analysis loaded")
            else:
                # Create Arabic version from English if available
                if lang_files['en']:
                    print(f"   🔄 Creating Arabic version from English...")
                    en_file = lang_files['en'][0]
                    arabic_analysis = self.create_bilingual_analysis(en_file, 'ar')
                    print(f"   ✅ Arabic version translated")
            
            # Process English files
            if lang_files['en']:
                print(f"   🔍 Processing English version...")
                en_file = lang_files['en'][0]  # Take first English file
                english_analysis = self._extract_analysis_sections(
                    open(en_file, 'r', encoding='utf-8').read(), 'en'
                )
                print(f"   ✅ English analysis loaded")
            else:
                # Create English version from Arabic if available
                if lang_files['ar']:
                    print(f"   🔄 Creating English version from Arabic...")
                    ar_file = lang_files['ar'][0]
                    english_analysis = self.create_bilingual_analysis(ar_file, 'en')
                    print(f"   ✅ English version translated")
            
            # Generate bilingual summary
            if arabic_analysis or english_analysis:
                summary_prompt = self.create_bilingual_summary_prompt(
                    contract_name, arabic_analysis, english_analysis
                )
                
                if dry_run:
                    print("   🔍 DRY RUN - Bilingual prompt generated (no API call)")
                    print(f"   📊 Prompt length: {len(summary_prompt)} characters")
                    results[contract_name] = f"BILINGUAL_PROMPT_READY ({len(summary_prompt)} chars)"
                else:
                    # Make API call for actual summary
                    print("   🤖 Generating bilingual AI summary...")
                    try:
                        if not self.handler:
                            self.handler = LLMHandler()
                        
                        summary_response = self.handler.analyze_contract(summary_prompt)
                        
                        # Save bilingual summary
                        summary_path = self.save_bilingual_summary(
                            contract_name, summary_response, 
                            list(lang_files['ar'] + lang_files['en'])
                        )
                        results[contract_name] = str(summary_path)
                        print("   ✅ Bilingual summary generated and saved")
                        
                    except Exception as e:
                        print(f"   ❌ Error generating summary: {e}")
                        results[contract_name] = f"ERROR: {e}"
            else:
                print("   ⚠️  No analysis data available")
                results[contract_name] = "NO_DATA"
        
        print(f"\n📊 PROCESSING COMPLETE")
        print(f"   📋 Contracts processed: {len(results)}")
        
        if dry_run:
            print(f"   🔍 Ready for API calls - set dry_run=False when satisfied")
        else:
            print(f"   💾 Summaries saved to: {self.summary_dir}")
        
        return results
    
    def save_bilingual_summary(self, contract_name: str, summary_content: str, source_files: List[Path]):
        """Save bilingual summary with proper formatting and metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create metadata
        metadata = {
            'contract_name': contract_name,
            'generated_at': timestamp,
            'source_files': [f.name for f in source_files],
            'languages': [],
            'type': 'bilingual_summary'
        }
        
        # Detect languages from source files
        for file in source_files:
            if '_arabic_' in file.name:
                metadata['languages'].append('العربية')
            else:
                metadata['languages'].append('English')
        
        # Create summary header with RTL support
        header = f"""CONTRACT EXECUTIVE SUMMARY | ملخص تنفيذي للعقد
{'=' * 80}
Contract | العقد: {contract_name}
Generated | تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source Files | الملفات المصدر: {len(source_files)} analysis files
Languages | اللغات: {', '.join(set(metadata['languages']))}
Type | النوع: Bilingual Analysis | تحليل ثنائي اللغة
{'=' * 80}

"""
        
        full_summary = header + summary_content
        
        # Save summary file
        summary_filename = f"{contract_name}_bilingual_executive_summary_{timestamp}.txt"
        summary_path = self.summary_dir / summary_filename
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(full_summary)
        
        print(f"   💾 Bilingual summary saved: {summary_filename}")
        return summary_path

def main():
    """Test the bilingual summary generation system"""
    generator = BilingualContractSummaryGenerator()
    
    # Run in dry mode first to test without using quota
    print("🧪 TESTING BILINGUAL SUMMARY GENERATION (DRY RUN)")
    results = generator.process_bilingual_contracts(dry_run=True)
    
    print("\n📋 RESULTS:")
    for contract, status in results.items():
        print(f"   📄 {contract}: {status}")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Install translation libraries: pip install googletrans==4.0.0rc1 deep-translator")
    print(f"   2. Review the bilingual prompts generated above")
    print(f"   3. When ready, run: generator.process_bilingual_contracts(dry_run=False)")
    print(f"   4. Check output in: {generator.summary_dir}")

if __name__ == "__main__":
    main()