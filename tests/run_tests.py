#!/usr/bin/env python3
"""
Test Runner for CLM System
Runs all tests from the tests/ directory
"""

import os
import sys
from pathlib import Path

def run_tests():
    """Run all available tests"""
    print("🧪 CLM SYSTEM TEST RUNNER")
    print("=" * 40)
    
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    
    print(f"📁 Tests Directory: {tests_dir}")
    print(f"📁 Project Root: {project_root}")
    
    # Change to tests directory
    os.chdir(tests_dir)
    
    available_tests = {
        "1": ("test_env.py", "Test .env configuration and API key"),
        "2": ("check_quota.py", "Check API quota for different models"),
        "3": ("test_models.py", "Compare different Gemini models"),
        "4": ("update_api_key.py", "Update API key interactively"),
        "5": ("test_imports.py", "Test all Python imports"),
    }
    
    print(f"\n🔍 AVAILABLE TESTS:")
    for key, (filename, description) in available_tests.items():
        status = "✅" if (tests_dir / filename).exists() else "❌"
        print(f"   {key}. {status} {description}")
    
    print(f"\n   0. Run all tests sequentially")
    print(f"   q. Quit")
    
    while True:
        choice = input(f"\nSelect test to run (0-5, q): ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == '0':
            print(f"\n🚀 Running all tests...")
            for key, (filename, description) in available_tests.items():
                if (tests_dir / filename).exists():
                    print(f"\n" + "="*50)
                    print(f"Running: {description}")
                    print(f"="*50)
                    os.system(f"python {filename}")
                    input(f"\nPress Enter to continue to next test...")
            break
        elif choice in available_tests:
            filename, description = available_tests[choice]
            if (tests_dir / filename).exists():
                print(f"\n🚀 Running: {description}")
                print(f"="*50)
                os.system(f"python {filename}")
            else:
                print(f"❌ Test file not found: {filename}")
        else:
            print(f"❌ Invalid choice. Please select 0-5 or q.")

if __name__ == "__main__":
    run_tests()