#!/usr/bin/env python3
"""
Simple test to check RAG Q&A functionality without Streamlit
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_gemini_models():
    """Check available Gemini models"""
    print("🔍 Checking available Gemini models...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found in .env")
            return False
        
        genai.configure(api_key=api_key)
        
        # List all models
        models = list(genai.list_models())
        print(f"✅ Found {len(models)} total models")
        
        # Filter for generative models
        gen_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
        print(f"📋 {len(gen_models)} models support generateContent:")
        
        for model in gen_models[:10]:  # Show first 10
            print(f"   - {model.name}")
        
        # Check specific models
        model_names = [m.name for m in gen_models]
        
        checks = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash-exp",
            "models/gemini-1.5-flash",
            "models/gemini-2.5-pro-preview-03-25"
        ]
        
        print("\n🔎 Checking specific models:")
        for check in checks:
            if check in model_names:
                print(f"   ✅ {check} - Available")
            else:
                print(f"   ❌ {check} - Not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_rag_qa():
    """Test RAG Q&A with sample text"""
    print("\n" + "="*50)
    print("🧪 Testing RAG Q&A System")
    print("="*50)
    
    try:
        from src.rag_model import TfidfIndex
        import google.generativeai as genai
        
        # Sample contract text
        sample_text = """
        CONSULTING AGREEMENT
        
        This Agreement is entered into on January 15, 2025, between ABC Corporation 
        ("Company") and John Smith ("Consultant").
        
        1. SERVICES: Consultant shall provide software development services.
        2. TERM: This Agreement begins February 1, 2025 and ends July 31, 2025.
        3. COMPENSATION: Company shall pay $150 per hour.
        4. GOVERNING LAW: This Agreement shall be governed by the laws of California.
        5. TERMINATION: Either party may terminate with 30 days written notice.
        """
        
        print("\n📄 Sample Contract:")
        print("-" * 50)
        print(sample_text)
        
        # Build RAG index
        print("\n🔨 Building RAG index...")
        
        # Create segments in expected format
        sections_list = [s.strip() for s in sample_text.split('\n') if s.strip()]
        segments = []
        for i, text in enumerate(sections_list):
            segments.append({
                "id": str(i),
                "text": text,
                "title": f"Section {i}"
            })
        
        index = TfidfIndex(segments)
        print(f"✅ Index built with {len(segments)} segments")
        
        # Test questions
        questions = [
            "What is the governing law?",
            "When does the agreement start?",
            "What is the hourly rate?"
        ]
        
        print("\n💬 Testing Questions:")
        print("-" * 50)
        
        for q in questions:
            print(f"\n❓ Q: {q}")
            
            # Search relevant sections
            results = index.search(q, k=3)
            print(f"   📊 Found {len(results)} relevant sections")
            
            if results:
                best_id, best_score, best_match = results[0]
                print(f"   ✅ Best match (score: {best_score:.3f}): {best_match[:100]}...")
        
        # Test generative answer (with Gemini)
        print("\n🤖 Testing Generative Answers:")
        print("-" * 50)
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("⚠️  GEMINI_API_KEY not set - skipping generative test")
            return True
        
        genai.configure(api_key=api_key)
        
        # Try different model names
        model_attempts = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        
        model = None
        for model_name in model_attempts:
            try:
                print(f"\n   Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                test_response = model.generate_content("test")
                print(f"   ✅ {model_name} works!")
                break
            except Exception as e:
                print(f"   ❌ {model_name} failed: {str(e)[:50]}")
        
        if not model:
            print("   ❌ No working model found")
            return False
        
        # Generate answer
        question = "What is the governing law?"
        results = index.search(question, k=3)
        context = "\n".join([text for id, score, text in results])
        
        prompt = f"""Based on the following contract context, answer the question:

Context:
{context}

Question: {question}

Provide a clear, concise answer based only on the context provided."""

        response = model.generate_content(prompt)
        print(f"\n   ❓ Q: {question}")
        print(f"   💡 A: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ RAG Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 RAG Q&A System Test")
    print("="*50)
    
    # Test 1: Check available models
    if not test_gemini_models():
        print("\n❌ Failed to check models")
        return
    
    # Test 2: Test RAG Q&A
    if test_rag_qa():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")

if __name__ == "__main__":
    main()
