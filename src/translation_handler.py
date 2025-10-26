#!/usr/bin/env python3
"""
Translation Handler for Contract Analysis
Handles English ↔ Arabic translation with RTL support for contract processing
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

# Translation options (in order of preference)
TRANSLATION_LIBRARIES = []

# Try Google Translate API (most accurate)
try:
    from googletrans import Translator as GoogleTranslator
    TRANSLATION_LIBRARIES.append('googletrans')
except ImportError:
    pass

# Try Deep Translator (multiple providers)
try:
    from deep_translator import GoogleTranslator as DeepGoogleTranslator
    from deep_translator import MyMemoryTranslator, PonsTranslator
    TRANSLATION_LIBRARIES.append('deep_translator')
except ImportError:
    pass

# Try Azure Translator (if API key available)
try:
    import requests
    if os.getenv('AZURE_TRANSLATOR_KEY'):
        TRANSLATION_LIBRARIES.append('azure_translator')
except ImportError:
    pass

class TranslationHandler:
    """
    Handles translation between English and Arabic with RTL support
    Supports multiple translation providers with fallback
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.primary_translator = None
        self.fallback_translators = []
        self._setup_translators()
    
    def _setup_translators(self):
        """Initialize available translation services"""
        if 'googletrans' in TRANSLATION_LIBRARIES:
            try:
                self.primary_translator = GoogleTranslator()
                self.logger.info("✅ Google Translate initialized as primary")
            except Exception as e:
                self.logger.warning(f"⚠️ Google Translate failed: {e}")
        
        if 'deep_translator' in TRANSLATION_LIBRARIES:
            try:
                self.fallback_translators.append(('deep_google', DeepGoogleTranslator(source='auto', target='arabic')))
                self.fallback_translators.append(('mymemory', MyMemoryTranslator(source='english', target='arabic')))
                self.logger.info("✅ Deep Translator services added as fallback")
            except Exception as e:
                self.logger.warning(f"⚠️ Deep Translator failed: {e}")
        
        if 'azure_translator' in TRANSLATION_LIBRARIES:
            self.azure_key = os.getenv('AZURE_TRANSLATOR_KEY')
            self.azure_endpoint = os.getenv('AZURE_TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com')
            if self.azure_key:
                self.logger.info("✅ Azure Translator configured")
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is Arabic or English
        Returns: 'ar' for Arabic, 'en' for English, 'unknown' for uncertain
        """
        if not text.strip():
            return 'unknown'
        
        # Count Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        
        if total_chars == 0:
            return 'unknown'
        
        arabic_ratio = arabic_chars / total_chars
        
        if arabic_ratio > 0.7:
            return 'ar'
        elif arabic_ratio < 0.1:
            return 'en'
        else:
            return 'mixed'
    
    def translate_text(self, text: str, source_lang: str = 'auto', target_lang: str = 'ar') -> Optional[str]:
        """
        Translate text between languages with fallback support
        """
        if not text.strip():
            return text
        
        # Try primary translator first
        if self.primary_translator:
            try:
                if hasattr(self.primary_translator, 'translate'):
                    result = self.primary_translator.translate(text, src=source_lang, dest=target_lang)
                    return result.text
            except Exception as e:
                self.logger.warning(f"Primary translator failed: {e}")
        
        # Try fallback translators
        for name, translator in self.fallback_translators:
            try:
                if target_lang == 'ar' and source_lang in ['en', 'auto']:
                    result = translator.translate(text)
                    return result
                elif target_lang == 'en' and source_lang == 'ar':
                    # Create English translator - Deep Translator requires full language names
                    if name == 'deep_google':
                        en_translator = DeepGoogleTranslator(source='arabic', target='english')
                        return en_translator.translate(text)
                    elif name == 'mymemory':
                        en_translator = MyMemoryTranslator(source='arabic', target='english')
                        return en_translator.translate(text)
            except Exception as e:
                self.logger.warning(f"Fallback translator {name} failed: {e}")
        
        # Try Azure Translator as last resort
        if hasattr(self, 'azure_key') and self.azure_key:
            try:
                return self._azure_translate(text, source_lang, target_lang)
            except Exception as e:
                self.logger.warning(f"Azure translator failed: {e}")
        
        self.logger.error("All translation methods failed")
        return None
    
    def _azure_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Azure Translator API call"""
        headers = {
            'Ocp-Apim-Subscription-Key': self.azure_key,
            'Ocp-Apim-Subscription-Region': os.getenv('AZURE_TRANSLATOR_REGION', 'global'),
            'Content-type': 'application/json',
        }
        
        params = {
            'api-version': '3.0',
            'to': target_lang
        }
        if source_lang != 'auto':
            params['from'] = source_lang
        
        body = [{'text': text}]
        
        response = requests.post(
            f"{self.azure_endpoint}/translate",
            params=params,
            headers=headers,
            json=body
        )
        
        if response.status_code == 200:
            result = response.json()
            return result[0]['translations'][0]['text']
        else:
            raise Exception(f"Azure API error: {response.status_code}")
    
    def format_rtl_text(self, arabic_text: str) -> str:
        """
        Format Arabic text with proper RTL markers for display
        Clean approach that respects RTL directionality without forcing overrides
        """
        if not arabic_text:
            return arabic_text
        
        # Clean any existing directional formatting characters
        cleaned_text = arabic_text
        directional_chars = ['\u202A', '\u202B', '\u202C', '\u202D', '\u202E', '\u200E', '\u200F', '\u061C']
        for char in directional_chars:
            cleaned_text = cleaned_text.replace(char, '')
        
        # Simply add RTL mark at the beginning to indicate RTL context
        # This is less invasive and lets the text flow naturally
        rtl_mark = '\u200F'  # Right-to-Left Mark (less aggressive than override)
        
        return f"{rtl_mark}{cleaned_text}"
    
    def translate_contract_analysis(self, analysis_text: str, target_language: str = 'ar') -> Dict[str, str]:
        """
        Translate a complete contract analysis maintaining structure
        
        Args:
            analysis_text: The full analysis text
            target_language: 'ar' for Arabic, 'en' for English
        
        Returns:
            Dict with translated sections
        """
        sections = {
            'basic_info': '',
            'dates': '',
            'financial': '',
            'obligations': '',
            'legal': '',
            'risks': '',
            'recommendations': '',
            'full_content': ''
        }
        
        # Extract sections using the same patterns as contract_summary_generator
        section_patterns = {
            'basic_info': r'\*\*1\. BASIC INFO\*\*.*?\n\n\*\*2\.',
            'dates': r'\*\*2\. KEY DATES\*\*.*?\n\n\*\*3\.',
            'financial': r'\*\*3\. MONEY MATTERS\*\*.*?\n\n\*\*4\.',
            'obligations': r'\*\*4\. MAIN OBLIGATIONS\*\*.*?\n\n\*\*5\.',
            'legal': r'\*\*5\. LEGAL FRAMEWORK\*\*.*?\n\n\*\*6\.',
            'risks': r'\*\*6\. RISK ANALYSIS\*\*.*?\n\n\*\*7\.',
            'recommendations': r'\*\*7\. RECOMMENDATIONS\*\*.*'
        }
        
        for section_name, pattern in section_patterns.items():
            try:
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                if match:
                    section_text = match.group(0)
                    # Remove the next section header
                    section_text = re.sub(r'\n\n\*\*\d+\..*$', '', section_text)
                    
                    # Translate the section
                    source_lang = 'en' if target_language == 'ar' else 'ar'
                    translated = self.translate_text(section_text, source_lang, target_language)
                    
                    if translated:
                        if target_language == 'ar':
                            sections[section_name] = self.format_rtl_text(translated)
                        else:
                            sections[section_name] = translated
                    else:
                        sections[section_name] = f"[Translation failed for {section_name}]"
                else:
                    sections[section_name] = f"[{section_name} section not found]"
            except Exception as e:
                sections[section_name] = f"[Error translating {section_name}: {e}]"
        
        # Translate full content
        try:
            source_lang = 'en' if target_language == 'ar' else 'ar'
            translated_full = self.translate_text(analysis_text, source_lang, target_language)
            if translated_full:
                if target_language == 'ar':
                    sections['full_content'] = self.format_rtl_text(translated_full)
                else:
                    sections['full_content'] = translated_full
            else:
                sections['full_content'] = "[Full content translation failed]"
        except Exception as e:
            sections['full_content'] = f"[Error translating full content: {e}]"
        
        return sections
    
    def get_translation_status(self) -> Dict[str, bool]:
        """Get status of available translation services"""
        return {
            'googletrans': 'googletrans' in TRANSLATION_LIBRARIES,
            'deep_translator': 'deep_translator' in TRANSLATION_LIBRARIES,
            'azure_translator': 'azure_translator' in TRANSLATION_LIBRARIES and hasattr(self, 'azure_key'),
            'primary_ready': self.primary_translator is not None,
            'fallback_count': len(self.fallback_translators)
        }

def test_translation():
    """Test the translation functionality"""
    print("🧪 TESTING TRANSLATION FUNCTIONALITY")
    print("=" * 50)
    
    handler = TranslationHandler()
    status = handler.get_translation_status()
    
    print("📊 Translation Services Status:")
    for service, available in status.items():
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {service}: {available}")
    
    # Test language detection
    english_text = "This is a software development agreement between two parties."
    arabic_text = "هذه اتفاقية تطوير برمجيات بين طرفين"
    
    print(f"\n🔍 Language Detection Test:")
    print(f"   English text detected as: {handler.detect_language(english_text)}")
    print(f"   Arabic text detected as: {handler.detect_language(arabic_text)}")
    
    # Test translation
    if handler.primary_translator or handler.fallback_translators:
        print(f"\n🔄 Translation Test:")
        translated_ar = handler.translate_text(english_text, 'en', 'ar')
        if translated_ar:
            print(f"   EN→AR: {english_text}")
            print(f"   Result: {handler.format_rtl_text(translated_ar)}")
        
        translated_en = handler.translate_text(arabic_text, 'ar', 'en')
        if translated_en:
            print(f"   AR→EN: {arabic_text}")
            print(f"   Result: {translated_en}")
    else:
        print(f"\n⚠️ No translation services available")
        print(f"   Install: pip install googletrans==4.0.0rc1 deep-translator")

if __name__ == "__main__":
    test_translation()