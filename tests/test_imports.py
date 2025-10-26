#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add the current directory to the path
ROOT = Path(__file__).parent
SRC = ROOT / "src"
sys.path.append(str(SRC))
sys.path.append(str(ROOT))

print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")
print(f"Root directory: {ROOT}")
print(f"SRC directory: {SRC}")
print(f"SRC exists: {SRC.exists()}")

try:
    print("Testing imports...")
    from src.translation_handler import detect_language
    print("✅ translation_handler imported")
    
    from src.contract_summary_generator import ContractSummaryGenerator
    print("✅ contract_summary_generator imported")
    
    from src.doc_reader import read_docu
    print("✅ doc_reader imported")
    
    from src.analysis import analyze_document
    print("✅ analysis imported")
    
    from src.llm_handler import LLMHandler
    print("✅ llm_handler imported")
    
    from src.analysis_metrics import ContractAnalysisMetrics
    print("✅ analysis_metrics imported")
    
    print("🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()