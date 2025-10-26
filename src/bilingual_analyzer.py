#!/usr/bin/env python3
"""
Bilingual Contract Analysis System
Processes contracts in both Arabic and English, providing translated analysis and summaries
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

# Add src path
sys.path.insert(0, str(Path(__file__).parent))

from translation_handler import TranslationHandler
from contract_summary_generator import ContractSummaryGenerator
from analysis import analyze_document
from analysis_metrics import ContractAnalysisMetrics
from llm_handler import LLMHandler

class BilingualContractAnalyzer:
    """
    Enhanced contract analyzer that supports bilingual analysis and translation
    """
    
    def __init__(self):
        self.translator = TranslationHandler()
        self.llm_handler = LLMHandler()
        self.metrics = ContractAnalysisMetrics()
        self.summarizer = ContractSummaryGenerator()
        self.output_dir = Path("../data/bilingual_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_contract_language(self, contract_text: str) -> str:
        """
        Detect the primary language of the contract
        Returns: 'ar', 'en', 'mixed', or 'unknown'
        """
        return self.translator.detect_language(contract_text)
    
    def analyze_contract_bilingual(self, contract_path: Path, target_languages: List[str] = ['ar', 'en']) -> Dict[str, Dict]:
        """
        Analyze a contract and provide results in multiple languages
        
        Args:
            contract_path: Path to the contract file
            target_languages: Languages to provide analysis in (['ar', 'en'])
        
        Returns:
            Dict with analysis in each requested language
        """
        results = {}
        
        # First, perform the standard analysis
        print(f"📄 Analyzing contract: {contract_path.name}")
        
        # Load the analysis prompt
        prompt_file = Path("../prompts/analysis_prompt.txt")
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        else:
            prompt_template = "Analyze this contract and provide a comprehensive analysis."
        
        # Get the original analysis using the analyze_document function
        analysis_result = analyze_document(
            contract_path, 
            self.llm_handler, 
            prompt_template, 
            self.output_dir,
            self.metrics
        )
        
        original_analysis = analysis_result.get('analysis_content', '')
        
        if not original_analysis:
            print(f"❌ Failed to analyze {contract_path.name}")
            return {}
        
        # Detect source language
        source_lang = self.detect_contract_language(original_analysis)
        print(f"🔍 Detected language: {source_lang}")
        
        # Store original analysis
        results[source_lang] = {
            'analysis': original_analysis,
            'language': source_lang,
            'is_original': True,
            'translation_quality': 'original'
        }
        
        # Translate to other requested languages
        for target_lang in target_languages:
            if target_lang != source_lang:
                print(f"🔄 Translating to {target_lang}...")
                
                try:
                    translated_sections = self.translator.translate_contract_analysis(
                        original_analysis, target_lang
                    )
                    
                    # Reconstruct full analysis from translated sections
                    translated_analysis = self._reconstruct_analysis(translated_sections)
                    
                    results[target_lang] = {
                        'analysis': translated_analysis,
                        'language': target_lang,
                        'is_original': False,
                        'translation_quality': 'machine_translated',
                        'sections': translated_sections
                    }
                    
                    print(f"✅ Translation to {target_lang} completed")
                    
                except Exception as e:
                    print(f"❌ Translation to {target_lang} failed: {e}")
                    results[target_lang] = {
                        'analysis': f"Translation failed: {e}",
                        'language': target_lang,
                        'is_original': False,
                        'translation_quality': 'failed'
                    }
        
        return results
    
    def _reconstruct_analysis(self, sections: Dict[str, str]) -> str:
        """
        Reconstruct a full analysis from translated sections
        """
        analysis_parts = []
        
        section_headers = {
            'basic_info': '**1. BASIC INFO**',
            'dates': '**2. KEY DATES**',
            'financial': '**3. MONEY MATTERS**', 
            'obligations': '**4. MAIN OBLIGATIONS**',
            'legal': '**5. LEGAL FRAMEWORK**',
            'risks': '**6. RISK ANALYSIS**',
            'recommendations': '**7. RECOMMENDATIONS**'
        }
        
        for section_key, header in section_headers.items():
            if section_key in sections and sections[section_key]:
                # Clean up the section (remove duplicate headers)
                section_content = sections[section_key]
                if not section_content.startswith(header):
                    section_content = f"{header}\n{section_content}"
                analysis_parts.append(section_content)
        
        return "\n\n".join(analysis_parts)
    
    def save_bilingual_analysis(self, contract_name: str, bilingual_results: Dict[str, Dict]) -> Dict[str, Path]:
        """
        Save bilingual analysis results to files
        """
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for lang, result in bilingual_results.items():
            # Create filename
            quality_suffix = "_original" if result.get('is_original') else "_translated"
            filename = f"{contract_name}_{lang}_analysis{quality_suffix}_{timestamp}.txt"
            file_path = self.output_dir / filename
            
            # Create file content with metadata
            content = f"""BILINGUAL CONTRACT ANALYSIS
==================================================
Contract: {contract_name}
Language: {lang}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Quality: {result.get('translation_quality', 'unknown')}
Original: {result.get('is_original', False)}
==================================================

{result['analysis']}
"""
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files[lang] = file_path
            print(f"💾 Saved {lang} analysis: {filename}")
        
        return saved_files
    
    def create_bilingual_summary(self, contract_name: str, bilingual_results: Dict[str, Dict]) -> Dict[str, str]:
        """
        Create executive summaries in multiple languages
        """
        summaries = {}
        
        for lang, result in bilingual_results.items():
            print(f"📋 Creating {lang} summary for {contract_name}...")
            
            try:
                # Create contract data structure for summary generation
                contract_data = {
                    contract_name: [{
                        'language': lang,
                        'file_name': f"{contract_name}_{lang}",
                        'full_content': result['analysis']
                    }]
                }
                
                # Extract sections for summary
                if 'sections' in result:
                    sections = result['sections']
                    contract_data[contract_name][0].update({
                        'basic_info': sections.get('basic_info', 'N/A'),
                        'dates': sections.get('dates', 'N/A'),
                        'financial': sections.get('financial', 'N/A'),
                        'obligations': sections.get('obligations', 'N/A'),
                        'legal': sections.get('legal', 'N/A'),
                        'risks': sections.get('risks', 'N/A'),
                        'recommendations': sections.get('recommendations', 'N/A')
                    })
                else:
                    # Extract sections from full analysis for original language
                    extracted = self.summarizer.extract_analysis_content(Path("dummy"))
                    extracted.update({
                        'language': lang,
                        'full_content': result['analysis']
                    })
                    contract_data[contract_name] = [extracted]
                
                # Generate summary prompt
                summary_prompt = self.summarizer.create_summary_prompt(contract_data)
                
                # Get AI summary (would use LLM here in production)  
                handler = LLMHandler()
                summary = handler.analyze_contract(summary_prompt)
                
                summaries[lang] = summary
                print(f"✅ {lang} summary created")
                
            except Exception as e:
                print(f"❌ Failed to create {lang} summary: {e}")
                summaries[lang] = f"Summary generation failed: {e}"
        
        return summaries
    
    def process_contract_full_bilingual(self, contract_path: Path, languages: List[str] = ['ar', 'en']) -> Dict:
        """
        Complete bilingual processing pipeline
        """
        print(f"🚀 BILINGUAL CONTRACT PROCESSING")
        print(f"📄 Contract: {contract_path.name}")
        print(f"🌐 Target languages: {', '.join(languages)}")
        print("=" * 60)
        
        contract_name = contract_path.stem
        
        # Step 1: Bilingual analysis
        bilingual_results = self.analyze_contract_bilingual(contract_path, languages)
        
        if not bilingual_results:
            return {'error': 'Analysis failed'}
        
        # Step 2: Save analysis files
        saved_files = self.save_bilingual_analysis(contract_name, bilingual_results)
        
        # Step 3: Create bilingual summaries
        summaries = self.create_bilingual_summary(contract_name, bilingual_results)
        
        # Step 4: Package results
        final_results = {
            'contract_name': contract_name,
            'languages_processed': list(bilingual_results.keys()),
            'analysis_files': {lang: str(path) for lang, path in saved_files.items()},
            'summaries': summaries,
            'translation_status': self.translator.get_translation_status(),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        print(f"\n🎉 BILINGUAL PROCESSING COMPLETE")
        print(f"📊 Languages processed: {len(bilingual_results)}")
        print(f"📁 Files saved: {len(saved_files)}")
        print(f"📋 Summaries created: {len(summaries)}")
        
        return final_results

def test_bilingual_system():
    """Test the bilingual contract analysis system"""
    print("🧪 TESTING BILINGUAL CONTRACT ANALYSIS SYSTEM")
    print("=" * 60)
    
    analyzer = BilingualContractAnalyzer()
    
    # Check translation status
    status = analyzer.translator.get_translation_status()
    print("📊 Translation Services Status:")
    for service, available in status.items():
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {service}: {available}")
    
    print(f"\n💡 SYSTEM READY FOR BILINGUAL PROCESSING")
    print(f"🔄 Supported translations: English ↔ Arabic")
    print(f"📁 Output directory: {analyzer.output_dir}")
    print(f"🌐 RTL formatting: Enabled for Arabic text")
    
    # Example usage
    print(f"\n📋 USAGE EXAMPLE:")
    print(f"   analyzer = BilingualContractAnalyzer()")
    print(f"   results = analyzer.process_contract_full_bilingual(")
    print(f"       Path('contract.pdf'), ['ar', 'en']")
    print(f"   )")

if __name__ == "__main__":
    test_bilingual_system()