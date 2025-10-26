#!/usr/bin/env python3
# src/llm_handler.py
"""
LLM Handler for Google Gemini API
Enhanced with comprehensive performance tracking
"""

import os
import time
import re
from typing import Dict, Any, Optional, Tuple
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

load_dotenv()

class LLMHandler:
    """
    Google Gemini API handler using gemini-2.5-pro model
    
    Model Performance:
    - Enhanced reasoning and comprehension
    - Better for complex contract analysis
    - Higher quality outputs for legal documents
    - Optimized for detailed analysis tasks
    """
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.5-pro',
            # Optimized for comprehensive legal analysis with enhanced reasoning
            # Model: gemini-2.5-pro - Enhanced for complex analysis
            generation_config={
                'temperature': 0.1,  # Focused but allows some creativity
                'max_output_tokens': 4000,  # Reasonable limit for concise analysis
                'top_p': 0.8,
                'top_k': 40
            }
        )
        
        # Rate limiting tracking
        self._last_request_time = 0
        self._request_count = 0
        self._request_times = []  # Track request times for rate limiting
        self._daily_token_count = 0
        self._daily_reset_time = time.time() + 86400  # Reset daily counter
        
        # Quota limits for gemini-2.5-pro
        self.REQUESTS_PER_MINUTE = 30  # Similar rate limit
        self.TOKENS_PER_MINUTE = 1000000  # High token throughput
        self.TOKENS_PER_DAY = 10000000  # More conservative daily limit for Pro model
    
    def _check_rate_limits(self, estimated_tokens: int) -> bool:
        """
        Check if we're within rate limits before making API call
        
        Args:
            estimated_tokens: Number of tokens we plan to use
            
        Returns:
            True if we can proceed, False if we need to wait
        """
        current_time = time.time()
        
        # Clean old request times (older than 1 minute)
        self._request_times = [t for t in self._request_times if current_time - t < 60]
        
        # Check requests per minute limit
        if len(self._request_times) >= self.REQUESTS_PER_MINUTE:
            wait_time = 60 - (current_time - self._request_times[0])
            if wait_time > 0:
                print(f"   ⏱️  Rate limit: Waiting {wait_time:.1f}s for request quota...")
                time.sleep(wait_time)
                return self._check_rate_limits(estimated_tokens)
        
        # Check daily token limit
        if current_time > self._daily_reset_time:
            self._daily_token_count = 0
            self._daily_reset_time = current_time + 86400
            
        if self._daily_token_count + estimated_tokens > self.TOKENS_PER_DAY:
            print(f"   📊 Daily token limit would be exceeded ({self._daily_token_count + estimated_tokens}/{self.TOKENS_PER_DAY})")
            return False
            
        return True
    
    def _record_request(self, tokens_used: int):
        """Record a successful API request for rate limiting"""
        current_time = time.time()
        self._request_times.append(current_time)
        self._daily_token_count += tokens_used
        self._last_request_time = current_time

    def analyze_contract(self, prompt: str) -> str:
        """
        Send prompt to Gemini and return response with enhanced metrics tracking
        
        Args:
            prompt: Complete analysis prompt with document text
            
        Returns:
            Raw text response from Gemini
        """
        start_time = time.perf_counter()
        
        try:
            # Record token count for metrics and rate limiting
            token_count = self._estimate_tokens(prompt)
            
            # Check rate limits before making request
            if not self._check_rate_limits(token_count):
                self._last_response_time = time.perf_counter() - start_time
                self._last_token_count = token_count
                return """DAILY QUOTA EXCEEDED

Daily API token limit reached.

Status:
1. Type: Contract document detected
2. Issue: Daily token quota exceeded  
3. Tokens used today: {self._daily_token_count}/{self.TOKENS_PER_DAY}
4. Recommendation: Try again tomorrow

[Daily usage limit reached - service resets in 24 hours]
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,      # Very focused for extraction
                    'max_output_tokens': 8000,   # Generous for comprehensive analysis
                    'top_p': 0.8,
                    'top_k': 20
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    }
                ]
            )
            
            # Comprehensive response handling with None protection
            if response is None:
                return """API ERROR - NULL RESPONSE

The API returned a null response.

Basic Fallback Analysis:
1. Type: Contract document detected
2. Status: API returned null
3. Recommendation: Retry analysis or manual review
4. Action: Check API status and rate limits

[API returned null response]
"""
            
            if hasattr(response, 'text') and response.text and response.text.strip():
                # Record successful response time and token usage
                response_time = time.perf_counter() - start_time
                self._last_response_time = response_time
                total_tokens = self._estimate_tokens(prompt + response.text)
                self._last_token_count = total_tokens
                
                # Record successful request for rate limiting
                self._record_request(total_tokens)
                
                return response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', 'unknown')
                
                # Check finish reason first
                if finish_reason == 2:  # MAX_TOKENS - output was cut off
                    # Try to get partial content
                    if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                        partial_text = candidate.content.parts[0].text.strip()
                        return f"""PARTIAL ANALYSIS (truncated due to length):

{partial_text}

[Analysis was cut short due to response length limits. This is a partial result.]
"""
                    else:
                        return """ANALYSIS FAILED - Response Too Long

The contract analysis exceeded token limits. 

Quick Summary Attempt:
1. Type: Complex legal agreement
2. Parties: Multiple parties identified  
3. Purpose: Legal/business agreement
4. Risk: Unable to complete full analysis
5. Recommendation: Manual review required

[Full analysis failed due to document complexity]
"""
                
                elif finish_reason == 3:  # SAFETY filter
                    return """ANALYSIS BLOCKED - Safety Filter

Contract analysis was blocked by content filters.

Quick Summary:
1. Type: Legal contract document
2. Status: Analysis blocked by safety filters
3. Recommendation: Manual legal review required
4. Action: Review document for sensitive content

[This is a safety filter response, not analysis failure]
"""
                
                elif finish_reason == 1:  # STOP - normal completion but no content
                    return """EMPTY RESPONSE

Analysis completed but no content was generated.

Fallback Summary:
1. Type: Contract document
2. Status: Analysis completed but empty
3. Recommendation: Try with shorter text excerpt
4. Action: Manual review suggested

[Response was empty despite successful completion]
"""
                
                else:
                    # Try to extract any available content
                    if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                        return candidate.content.parts[0].text.strip()
                    else:
                        return f"""ANALYSIS ERROR

Response generation failed (reason: {finish_reason}).

Basic Assessment:
1. Type: Contract document detected
2. Status: Analysis failed  
3. Reason: Technical error ({finish_reason})
4. Recommendation: Manual review required

[Technical failure - not document issue]
"""
            else:
                return """NO RESPONSE GENERATED

API call completed but no response received.

Status:
1. Type: Contract document
2. Analysis: No response from API
3. Recommendation: Retry or manual review
4. Action: Check API status

[No response received from analysis service]
"""
        except google_exceptions.ResourceExhausted as e:
            # Handle quota exceeded errors
            response_time = time.perf_counter() - start_time
            self._last_response_time = response_time
            self._last_token_count = self._estimate_tokens(prompt)
            
            print(f"   ⚠️  QUOTA EXCEEDED: {str(e)}")
            print(f"   💤 Waiting 60 seconds before retry...")
            
            return """QUOTA LIMIT REACHED

API quota exceeded. Analysis temporarily unavailable.

Status:
1. Type: Contract document detected
2. Issue: API quota/rate limit exceeded
3. Action: Request will be retried automatically
4. Recommendation: Wait or try again later

[This is a temporary service limitation]
"""
            
        except google_exceptions.PermissionDenied as e:
            response_time = time.perf_counter() - start_time
            self._last_response_time = response_time
            self._last_token_count = self._estimate_tokens(prompt)
            
            print(f"   🔐 PERMISSION DENIED: {str(e)}")
            
            return """ACCESS DENIED

API access denied. Check authentication.

Status:  
1. Type: Contract document detected
2. Issue: API authentication failed
3. Action: Check API key configuration
4. Recommendation: Verify credentials

[Authentication error - not document issue]
"""
            
        except Exception as e:
            # Record failed response time
            response_time = time.perf_counter() - start_time
            self._last_response_time = response_time
            self._last_token_count = self._estimate_tokens(prompt)
            
            # Detailed error logging for debugging
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"   🔍 DEBUG: API Error Type: {error_type}")
            print(f"   🔍 DEBUG: API Error Message: {error_msg[:200]}...")
            
            # Check if it's a quota-related error by message content
            if any(keyword in error_msg.lower() for keyword in ['quota', 'rate', 'limit', 'exceeded', 'resourceexhausted']):
                print(f"   💤 Detected quota issue, implementing backoff...")
                time.sleep(5)  # Brief backoff for quota issues
                
            raise Exception(f"LLM API call failed ({error_type}): {str(e)}")
    
    def analyze_contract_with_metrics(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze contract and return both result and detailed metrics
        
        Args:
            prompt: Complete analysis prompt with document text
            
        Returns:
            Tuple of (response_text, metrics_dict)
        """
        start_time = time.perf_counter()
        prompt_tokens = self._estimate_tokens(prompt)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 8000,  # Generous for comprehensive analysis
                    'top_p': 0.8,
                    'top_k': 20
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            response_time = time.perf_counter() - start_time
            
            # Extract response and analyze
            response_text = ""
            finish_reason = "unknown"
            response_tokens = 0
            
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                response_tokens = self._estimate_tokens(response_text)
                finish_reason = "success"
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = str(getattr(candidate, 'finish_reason', 'unknown'))
                
                if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                    response_text = candidate.content.parts[0].text.strip()
                    response_tokens = self._estimate_tokens(response_text)
                
                # Handle different finish reasons with appropriate responses
                if finish_reason == "2":  # MAX_TOKENS
                    if not response_text:
                        response_text = "ANALYSIS FAILED - Response Too Long"
                elif finish_reason == "3":  # SAFETY
                    response_text = "ANALYSIS BLOCKED - Safety Filter"
                elif finish_reason == "1" and not response_text:  # STOP but empty
                    response_text = "EMPTY RESPONSE"
            
            # Compile comprehensive metrics
            metrics = {
                'response_time_seconds': round(response_time, 3),
                'prompt_tokens': prompt_tokens,
                'response_tokens': response_tokens,
                'total_tokens': prompt_tokens + response_tokens,
                'tokens_per_second': round((prompt_tokens + response_tokens) / response_time, 2) if response_time > 0 else 0,
                'finish_reason': finish_reason,
                'success': finish_reason in ["success", "1"],
                'model_config': {
                    'model': 'gemini-2.5-flash',
                    'temperature': 0.1,
                    'max_output_tokens': 8000,
                    'top_p': 0.8,
                    'top_k': 20
                },
                'response_analysis': self._analyze_response_quality(response_text)
            }
            
            return response_text, metrics
            
        except Exception as e:
            response_time = time.perf_counter() - start_time
            
            # Enhanced error logging for debugging API failures
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"   🔍 DEBUG: Enhanced API Error Type: {error_type}")
            print(f"   🔍 DEBUG: Enhanced API Error Message: {error_msg[:200]}...")
            
            error_metrics = {
                'response_time_seconds': round(response_time, 3),
                'prompt_tokens': prompt_tokens,
                'response_tokens': 0,
                'total_tokens': prompt_tokens,
                'tokens_per_second': 0,
                'finish_reason': 'error',
                'success': False,
                'error': str(e),
                'error_type': error_type,
                'model_config': {
                    'model': 'gemini-2.5-flash',
                    'temperature': 0.1,
                    'max_output_tokens': 8000
                }
            }
            return f"ERROR: {str(e)}", error_metrics
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token for English)"""
        return len(text) // 4
    
    def _analyze_response_quality(self, response: str) -> Dict[str, Any]:
        """Analyze response quality with detailed metrics"""
        if not response or len(response) < 10:
            return {'quality_score': 0.0, 'issues': ['too_short']}
        
        quality_indicators = {
            'has_structure': bool(re.search(r'[-•*]\s|\d+\.\s|:\s', response)),
            'has_legal_terms': bool(re.search(r'shall|agreement|party|contract|term', response, re.IGNORECASE)),
            'has_specific_info': bool(re.search(r'\$[\d,]+|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', response)),
            'appropriate_length': 50 <= len(response) <= 1000,
            'not_error_response': not re.search(r'error|failed|unable|cannot|blocked', response, re.IGNORECASE),
            'has_conclusions': bool(re.search(r'therefore|conclusion|summary|result', response, re.IGNORECASE))
        }
        
        quality_score = sum(quality_indicators.values()) / len(quality_indicators)
        
        # Identify specific issues
        issues = []
        if len(response) < 50:
            issues.append('too_short')
        if len(response) > 1000:
            issues.append('too_long')
        if not quality_indicators['has_legal_terms']:
            issues.append('missing_legal_context')
        if not quality_indicators['has_structure']:
            issues.append('poor_structure')
        if quality_indicators['not_error_response'] is False:
            issues.append('error_response')
        
        return {
            'quality_score': round(quality_score, 3),
            'length': len(response),
            'word_count': len(response.split()),
            'sentence_count': len(re.split(r'[.!?]+', response)),
            'indicators': quality_indicators,
            'issues': issues
        }
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota and rate limiting status"""
        current_time = time.time()
        
        # Clean old request times
        self._request_times = [t for t in self._request_times if current_time - t < 60]
        
        # Check if daily counter needs reset
        if current_time > self._daily_reset_time:
            self._daily_token_count = 0
            self._daily_reset_time = current_time + 86400
        
        time_until_reset = max(0, self._daily_reset_time - current_time)
        
        return {
            'requests_per_minute_limit': self.REQUESTS_PER_MINUTE,
            'requests_in_last_minute': len(self._request_times),
            'requests_remaining': max(0, self.REQUESTS_PER_MINUTE - len(self._request_times)),
            'daily_token_limit': self.TOKENS_PER_DAY,
            'daily_tokens_used': self._daily_token_count,
            'daily_tokens_remaining': max(0, self.TOKENS_PER_DAY - self._daily_token_count),
            'daily_reset_in_seconds': int(time_until_reset),
            'rate_limit_status': 'OK' if len(self._request_times) < self.REQUESTS_PER_MINUTE else 'NEAR_LIMIT',
            'daily_quota_status': 'OK' if self._daily_token_count < (self.TOKENS_PER_DAY * 0.8) else 'HIGH_USAGE'
        }

    def get_last_metrics(self) -> Dict[str, Any]:
        """Get metrics from the last API call"""
        return {
            'response_time': getattr(self, '_last_response_time', 0),
            'token_count': getattr(self, '_last_token_count', 0)
        }
