#!/usr/bin/env python3
"""
Configuration settings for CLM system
Centralized path management and settings
"""

from pathlib import Path
import os

class Config:
    """Configuration class for CLM paths and settings"""
    
    # Base paths
    PROJECT_ROOT = Path(__file__).parent.parent
    APP_ROOT = PROJECT_ROOT / "app"
    SRC_ROOT = PROJECT_ROOT / "src"
    
    # Data paths
    DATA_ROOT = PROJECT_ROOT / "data"
    DOCUMENTS_INPUT = DATA_ROOT / "parsed"
    DOCUMENTS_OUTPUT = DATA_ROOT / "analysed_documents"
    
    # Prompt and template paths
    PROMPTS_ROOT = PROJECT_ROOT / "prompts"
    ANALYSIS_PROMPT = PROMPTS_ROOT / "analysis_prompt.txt"
    
    # Supported file types
    SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt']
    
    # AI Configuration
    MAX_DOCUMENT_LENGTH = 40000  # Characters
    
    # Output file patterns
    OUTPUT_BULLETS_SUFFIX = "_bullets.txt"
    OUTPUT_JSON_SUFFIX = "_analysis.json"
    OUTPUT_SUMMARY_SUFFIX = "_summary.txt"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_ROOT,
            cls.DOCUMENTS_OUTPUT,
            cls.PROMPTS_ROOT
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_data_path(cls) -> Path:
        """Get data folder path"""
        return cls.DATA_ROOT
    
    @classmethod
    def get_output_path(cls) -> Path:
        """Get output folder path for analyzed documents"""
        return cls.DOCUMENTS_OUTPUT
    
    @classmethod
    def get_input_documents(cls) -> list:
        """Get list of all input documents to process"""
        documents = []
        for ext in cls.SUPPORTED_EXTENSIONS:
            documents.extend(cls.DATA_ROOT.glob(f"*{ext}"))
        return documents
    
    @classmethod
    def get_parsed_documents(cls) -> list:
        """Get list of all parsed JSON documents from data/parsed folder"""
        parsed_documents = []
        if cls.DOCUMENTS_INPUT.exists():
            parsed_documents.extend(cls.DOCUMENTS_INPUT.glob("*.json"))
        return parsed_documents
    
    @classmethod
    def get_parsed_documents_path(cls) -> Path:
        """Get the parsed documents folder path"""
        return cls.DOCUMENTS_INPUT
    
    @classmethod
    def is_supported_file(cls, file_path: Path) -> bool:
        """Check if file extension is supported"""
        return file_path.suffix.lower() in cls.SUPPORTED_EXTENSIONS

# Create global config instance
config = Config()

# Ensure directories exist when module is imported
config.ensure_directories()
