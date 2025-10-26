#!/usr/bin/env python3
"""
Translation utilities for converting English contract analysis to Arabic
"""
from deep_translator import GoogleTranslator
from pathlib import Path
import time

def translate_to_arabic(text: str, chunk_size: int = 4500) -> str:
    """
    Translate English text to Arabic using Deep Translator.
    Splits text into chunks to avoid API limits.
    
    Args:
        text: English text to translate
        chunk_size: Maximum characters per chunk (Google Translate has 5000 char limit)
    
    Returns:
        Translated Arabic text
    """
    if not text or len(text.strip()) == 0:
        return ""
    
    try:
        translator = GoogleTranslator(source='english', target='arabic')
        
        # If text is short enough, translate directly
        if len(text) <= chunk_size:
            return translator.translate(text)
        
        # Split into chunks by paragraphs to preserve structure
        paragraphs = text.split('\n\n')
        translated_chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk size, translate current chunk first
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                translated_chunks.append(translator.translate(current_chunk))
                current_chunk = para
                time.sleep(0.5)  # Rate limiting
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
        
        # Translate remaining chunk
        if current_chunk:
            translated_chunks.append(translator.translate(current_chunk))
        
        return '\n\n'.join(translated_chunks)
    
    except Exception as e:
        print(f"Translation error: {e}")
        return f"[Translation Error: {str(e)}]\n\n{text}"

def save_arabic_translation(original_file_path: str, arabic_content: str) -> str:
    """
    Save Arabic translation alongside the original English file.
    
    Args:
        original_file_path: Path to original English analysis file
        arabic_content: Translated Arabic content
    
    Returns:
        Path to saved Arabic file
    """
    original_path = Path(original_file_path)
    
    # Create Arabic filename: original_name-arabic.txt
    arabic_filename = original_path.stem + "-arabic" + original_path.suffix
    arabic_path = original_path.parent / arabic_filename
    
    # Save Arabic content
    with open(arabic_path, 'w', encoding='utf-8') as f:
        f.write(arabic_content)
    
    return str(arabic_path)

def load_arabic_translation(original_file_path: str) -> str | None:
    """
    Load Arabic translation if it exists.
    
    Args:
        original_file_path: Path to original English analysis file
    
    Returns:
        Arabic content if exists, None otherwise
    """
    original_path = Path(original_file_path)
    arabic_filename = original_path.stem + "-arabic" + original_path.suffix
    arabic_path = original_path.parent / arabic_filename
    
    if arabic_path.exists():
        with open(arabic_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    return None

def has_arabic_translation(original_file_path: str) -> bool:
    """
    Check if Arabic translation exists for a file.
    
    Args:
        original_file_path: Path to original English analysis file
    
    Returns:
        True if Arabic translation exists, False otherwise
    """
    original_path = Path(original_file_path)
    arabic_filename = original_path.stem + "-arabic" + original_path.suffix
    arabic_path = original_path.parent / arabic_filename
    
    return arabic_path.exists()
