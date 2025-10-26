#!/usr/bin/env python3
"""
Model Testing and Comparison Tool for Contract Analysis
Tests different Gemini models to find the best performance/quality balance
"""

import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env from parent directory
load_dotenv(Path("../.env"))

class ModelTester:
    """Test different Gemini models for contract analysis performance"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Available models to test
        self.models_to_test = {
            'gemini-2.5-flash': {
                'name': 'Gemini 2.5 Flash (Current)',
                'rate_limit_rpm': 10,
                'rate_limit_tpm': 250000,
                'description': 'Current model - balanced speed and quality'
            },
            'gemini-2.5-pro': {
                'name': 'Gemini 2.5 Pro (Higher Quality)',
                'rate_limit_rpm': 5,
                'rate_limit_tpm': 125000,
                'description': 'Higher quality analysis, better for complex contracts'
            },
            'gemini-2.0-flash': {
                'name': 'Gemini 2.0 Flash (Faster)',
                'rate_limit_rpm': 15,
                'rate_limit_tpm': 1000000,
                'description': 'Higher rate limit, massive token allowance'
            },
            'gemini-2.0-flash-lite': {
                'name': 'Gemini 2.0 Flash-Lite (Fastest)',
                'rate_limit_rpm': 30,
                'rate_limit_tpm': 1000000,
                'description': 'Highest rate limit, very fast processing'
            }
        }
        
        # Simple test prompt for contract analysis
        self.test_prompt = """
        Analyze this sample contract clause and provide a brief analysis:
        
        "This Software Development Agreement is entered into between TechCorp Inc. (Client) and DevStudio LLC (Developer) for the development of a mobile application. The total project cost is $50,000, payable in 3 installments. The project shall be completed within 6 months from the effective date. Developer shall provide 30 days warranty on all deliverables."
        
        Provide analysis covering:
        1. Contract Type
        2. Parties
        3. Financial Terms
        4. Timeline
        5. Risk Assessment
        """
    
    def test_model(self, model_name: str) -> dict:
        """Test a specific model and return performance metrics"""
        print(f"\n🔄 Testing {self.models_to_test[model_name]['name']}...")
        
        try:
            # Initialize model
            model = genai.GenerativeModel(
                model_name,
                generation_config={
                    'temperature': 0.0,
                    'max_output_tokens': 2000,
                    'top_p': 0.8,
                    'top_k': 20
                }
            )
            
            # Test API call
            start_time = time.perf_counter()
            response = model.generate_content(self.test_prompt)
            end_time = time.perf_counter()
            
            response_time = end_time - start_time
            response_text = response.text if response.text else "No response generated"
            
            # Calculate basic quality metrics
            quality_score = self.calculate_quality_score(response_text)
            
            result = {
                'model': model_name,
                'success': True,
                'response_time': round(response_time, 2),
                'response_length': len(response_text),
                'word_count': len(response_text.split()),
                'quality_score': quality_score,
                'rate_limit_rpm': self.models_to_test[model_name]['rate_limit_rpm'],
                'rate_limit_tpm': self.models_to_test[model_name]['rate_limit_tpm'],
                'response_preview': response_text[:200] + "..." if len(response_text) > 200 else response_text
            }
            
            print(f"   ✅ Success: {response_time:.2f}s, {len(response_text)} chars, Quality: {quality_score:.2f}")
            return result
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            return {
                'model': model_name,
                'success': False,
                'error': str(e),
                'rate_limit_rpm': self.models_to_test[model_name]['rate_limit_rpm'],
                'rate_limit_tpm': self.models_to_test[model_name]['rate_limit_tpm']
            }
    
    def calculate_quality_score(self, response: str) -> float:
        """Calculate basic quality score for response"""
        if not response or len(response) < 50:
            return 0.0
        
        quality_indicators = [
            'contract' in response.lower(),
            'parties' in response.lower() or 'client' in response.lower(),
            '$' in response or 'cost' in response.lower() or 'price' in response.lower(),
            'month' in response.lower() or 'time' in response.lower(),
            'risk' in response.lower() or 'warranty' in response.lower(),
            len(response.split()) > 50,  # Adequate length
            response.count('.') >= 3,    # Multiple sentences
        ]
        
        return sum(quality_indicators) / len(quality_indicators)
    
    def run_comparison(self) -> dict:
        """Run comparison across all available models"""
        print("🚀 GEMINI MODEL COMPARISON FOR CONTRACT ANALYSIS")
        print("=" * 60)
        
        results = {}
        
        for model_name in self.models_to_test.keys():
            try:
                result = self.test_model(model_name)
                results[model_name] = result
                
                # Wait between tests to respect rate limits
                print("   ⏳ Waiting 10 seconds between tests...")
                time.sleep(10)
                
            except Exception as e:
                print(f"   ❌ Critical error testing {model_name}: {e}")
                results[model_name] = {
                    'model': model_name,
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def print_comparison_results(self, results: dict):
        """Print detailed comparison results"""
        print(f"\n📊 MODEL COMPARISON RESULTS")
        print("=" * 80)
        
        successful_models = [r for r in results.values() if r.get('success', False)]
        failed_models = [r for r in results.values() if not r.get('success', False)]
        
        if successful_models:
            print(f"\n✅ SUCCESSFUL MODELS ({len(successful_models)}):")
            print("-" * 80)
            
            # Sort by quality score then response time
            successful_models.sort(key=lambda x: (-x.get('quality_score', 0), x.get('response_time', 999)))
            
            for i, result in enumerate(successful_models, 1):
                model_info = self.models_to_test[result['model']]
                print(f"\n{i}. {model_info['name']}")
                print(f"   Model: {result['model']}")
                print(f"   Response Time: {result['response_time']}s")
                print(f"   Quality Score: {result['quality_score']:.2f}/1.0")
                print(f"   Response Length: {result['response_length']} chars ({result['word_count']} words)")
                print(f"   Rate Limits: {result['rate_limit_rpm']} RPM, {result['rate_limit_tpm']:,} TPM")
                print(f"   Description: {model_info['description']}")
                
                if i == 1:
                    print(f"   🏆 RECOMMENDED: Best overall performance")
        
        if failed_models:
            print(f"\n❌ FAILED MODELS ({len(failed_models)}):")
            print("-" * 40)
            for result in failed_models:
                model_info = self.models_to_test[result['model']]
                print(f"   {model_info['name']}: {result.get('error', 'Unknown error')}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        print("-" * 40)
        
        if successful_models:
            best_model = successful_models[0]
            print(f"✅ Best Overall: {best_model['model']}")
            print(f"   Quality: {best_model['quality_score']:.2f}, Speed: {best_model['response_time']}s")
            
            # Find fastest model
            fastest_model = min(successful_models, key=lambda x: x.get('response_time', 999))
            if fastest_model != best_model:
                print(f"⚡ Fastest: {fastest_model['model']} ({fastest_model['response_time']}s)")
            
            # Find highest rate limit
            highest_rpm = max(successful_models, key=lambda x: x.get('rate_limit_rpm', 0))
            if highest_rpm != best_model:
                print(f"🚀 Highest Rate Limit: {highest_rpm['model']} ({highest_rpm['rate_limit_rpm']} RPM)")
    
    def save_results(self, results: dict):
        """Save comparison results to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"model_comparison_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Run model comparison"""
    try:
        tester = ModelTester()
        results = tester.run_comparison()
        tester.print_comparison_results(results)
        tester.save_results(results)
        
    except Exception as e:
        print(f"❌ Error running model comparison: {e}")

if __name__ == "__main__":
    main()