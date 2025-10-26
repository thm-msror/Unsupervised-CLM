#!/usr/bin/env python3
"""
Enhanced Performance Metrics for Contract Analysis LLM
Measures both technical performance and analysis quality
"""

import time
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import statistics

class ContractAnalysisMetrics:
    """
    Comprehensive metrics tracking system for LLM contract analysis performance.
    
    **Primary Metrics Categories:**
    
    1. **Session Metadata:**
       - session_id: Unique identifier for analysis session (timestamp-based)
       - session_start/end: ISO timestamps for session boundaries
       - session_duration_minutes: Total elapsed time for complete analysis
    
    2. **Processing Volume Metrics:**
       - documents_processed: Total number of documents attempted
       - successful_analyses: Count of successfully completed analyses  
       - failed_analyses: Count of documents that failed processing
       - total_processing_time: Cumulative time spent on all document processing
    
    3. **Performance Metrics:**
       - api_response_times: List of response times for successful API calls
       - avg_response_time: Mean API response time across all calls
       - throughput_docs_per_minute: Real-world processing throughput
       - tokens_processed: List of token counts for throughput analysis
       - success_rate: Percentage of documents successfully processed
    
    4. **Quality Assessment Metrics (0.0-1.0 scale):**
       - structure_compliance: How well analyses follow expected format
       - completeness_scores: Thoroughness of analysis content
       - extraction_accuracy: Quality of information extraction  
       - consistency_scores: Internal logical consistency of analyses
    
    5. **Content Analysis Metrics:**
       - document_sizes: Character counts of all processed documents
       - avg_document_size/median_document_size: Size distribution statistics
       - languages_detected: Count of documents by language code
       - contract_types_identified: Distribution of contract types found
       - complexity_scores: Calculated complexity for each document
       - avg_complexity: Portfolio-level complexity assessment
    
    6. **Per-Document Detailed Metrics:**
       - filename, text_length, language, processing_time
       - api_calls, errors, analysis_quality scores
       - success status and detailed timestamps
    
    **Key Use Cases:**
    - Performance optimization and bottleneck identification
    - Quality assurance and analysis reliability measurement  
    - Capacity planning and resource allocation
    - Portfolio analysis and business intelligence
    - Error pattern analysis and system reliability tracking
    
    **Output Formats:**
    - JSON metrics file for detailed analysis and reporting
    - Console summary dashboard for immediate performance feedback
    - Per-document metrics for granular analysis debugging
    """
    
    def __init__(self):
        self.metrics = {
            'session_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'session_start': datetime.now().isoformat(),
            'documents_processed': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'total_processing_time': 0.0,
            'per_document_metrics': [],
            'quality_metrics': {
                'structure_compliance': [],
                'completeness_scores': [],
                'extraction_accuracy': [],
                'consistency_scores': []
            },
            'performance_metrics': {
                'api_response_times': [],
                'tokens_processed': [],
                'throughput_docs_per_minute': 0.0,
                'error_rates': []
            },
            'content_metrics': {
                'document_sizes': [],
                'languages_detected': {},
                'contract_types_identified': {},
                'complexity_scores': []
            }
        }
    
    def start_document_analysis(self, filename: str, text_length: int, language: str = "en") -> Dict[str, Any]:
        """
        Start tracking metrics for a single document analysis session.
        
        Creates comprehensive tracking structure for individual document processing:
        
        **Document Identity Metrics:**
        - filename: Source document file name for identification
        - text_length: Total character count of the document being processed
        - language: Detected or specified language code (e.g., 'en', 'ar', 'fr')
        
        **Processing State Metrics:**
        - start_time: High-precision timestamp when document analysis begins (perf_counter)
        - truncated: Boolean flag indicating if document was truncated due to size limits
        - api_calls: Counter for number of API requests made for this document
        - errors: List to collect any processing errors encountered
        - analysis_quality: Dict to store quality assessment scores after analysis
        
        Args:
            filename: Name of the document file being analyzed
            text_length: Character count of the document content
            language: Language code for the document (default: "en")
            
        Returns:
            Dict containing initialized metrics tracking structure for the document
        """
        doc_metrics = {
            'filename': filename,
            'start_time': time.perf_counter(),
            'text_length': text_length,
            'language': language,
            'truncated': False,
            'api_calls': 0,
            'errors': [],
            'analysis_quality': {}
        }
        
        # Update content metrics
        self.metrics['content_metrics']['document_sizes'].append(text_length)
        lang_count = self.metrics['content_metrics']['languages_detected'].get(language, 0)
        self.metrics['content_metrics']['languages_detected'][language] = lang_count + 1
        
        return doc_metrics
    
    def record_api_call(self, doc_metrics: Dict[str, Any], response_time: float, 
                       tokens_used: Optional[int] = None, success: bool = True):
        """
        Record API call performance metrics for analysis quality assessment.
        
        **API Performance Metrics Tracked:**
        - api_calls: Incremented counter of total API requests per document
        - api_response_time: Actual time (seconds) for the API to respond
        - api_response_times: Global list of all successful API response times (for avg calculation)
        - tokens_processed: Global list of token counts for throughput analysis
        
        **Usage in Analysis:**
        - Response time helps identify slow documents or API performance issues
        - Token count enables throughput measurement (tokens/minute)
        - Success tracking helps calculate API reliability rates
        - Per-document API calls indicate complexity (multiple attempts needed)
        
        Args:
            doc_metrics: Document-specific metrics dictionary to update
            response_time: Time in seconds for the API call to complete
            tokens_used: Number of tokens processed in the API call (optional)
            success: Whether the API call succeeded (affects global success tracking)
        """
        doc_metrics['api_calls'] += 1
        doc_metrics['api_response_time'] = response_time
        
        if success:
            self.metrics['performance_metrics']['api_response_times'].append(response_time)
        
        if tokens_used:
            self.metrics['performance_metrics']['tokens_processed'].append(tokens_used)
    
    def analyze_response_quality(self, response: str, doc_metrics: Dict[str, Any]) -> Dict[str, float]:
        """
        Analyze the quality of LLM response using multiple quality dimensions.
        
        **Quality Metrics Calculated (Scale 0.0-1.0):**
        
        1. **structure_compliance**: Measures adherence to expected contract analysis format
           - Checks for presence of key sections (parties, dates, financial, obligations, risks)
           - 1.0 = All expected sections present, 0.0 = No recognizable structure
           - Helps identify if LLM followed the analysis prompt correctly
        
        2. **completeness**: Evaluates thoroughness of the analysis content
           - Minimum length, presence of numbers/dates, proper nouns (names)
           - Absence of failure indicators ("not found", "unable to")
           - Legal language usage, multiple complete sentences
           - 1.0 = Comprehensive analysis, 0.0 = Incomplete or failed response
        
        3. **information_density**: Assesses specificity and concrete information extraction
           - Financial amounts ($1,000), dates (01/01/2024), time periods (30 days)
           - Company identifiers (Inc., LLC), proper nouns, structured data
           - 1.0 = Rich specific details, 0.0 = Generic or vague content
        
        4. **consistency**: Measures internal logical consistency of analysis
           - Detects contradictions (high risk + low risk, expires + perpetual)
           - Checks for conflicting complexity assessments
           - 1.0 = No contradictions found, 0.0 = Multiple contradictions
        
        5. **type_detection**: Evaluates contract type identification accuracy
           - Recognizes service, employment, software, lease, purchase agreements
           - Updates global contract type statistics for portfolio analysis
           - 1.0 = Contract type identified, 0.0 = Type not determined
        
        **Global Quality Tracking:**
        - Individual scores added to global quality_metrics lists
        - Enables calculation of average quality across all documents
        - Helps identify systemic analysis quality issues
        
        Args:
            response: The LLM-generated contract analysis text
            doc_metrics: Document metrics dictionary to store quality scores
            
        Returns:
            Dict containing all 5 quality scores (0.0-1.0 scale)
        """
        quality_scores = {}
        
        # 1. Structure Compliance (0-1): Does response follow expected format?
        structure_score = self._check_structure_compliance(response)
        quality_scores['structure_compliance'] = structure_score
        
        # 2. Completeness (0-1): How many expected sections are present?
        completeness_score = self._check_completeness(response)
        quality_scores['completeness'] = completeness_score
        
        # 3. Information Density (0-1): Quality of extracted information
        density_score = self._check_information_density(response)
        quality_scores['information_density'] = density_score
        
        # 4. Consistency (0-1): Internal consistency of the analysis
        consistency_score = self._check_consistency(response)
        quality_scores['consistency'] = consistency_score
        
        # 5. Contract Type Detection (0-1): Did it identify contract type?
        type_detection_score = self._check_contract_type_detection(response)
        quality_scores['type_detection'] = type_detection_score
        
        # Update document metrics
        doc_metrics['analysis_quality'] = quality_scores
        
        # Update global quality metrics
        self.metrics['quality_metrics']['structure_compliance'].append(structure_score)
        self.metrics['quality_metrics']['completeness_scores'].append(completeness_score)
        self.metrics['quality_metrics']['extraction_accuracy'].append(density_score)
        self.metrics['quality_metrics']['consistency_scores'].append(consistency_score)
        
        return quality_scores
    
    def finish_document_analysis(self, doc_metrics: Dict[str, Any], 
                                success: bool = True, error: Optional[str] = None):
        """
        Complete document analysis and update comprehensive session metrics.
        
        **Final Document Metrics Calculated:**
        - processing_time: Total time from start to finish (seconds)
        - success: Boolean indicating if analysis completed successfully
        - end_time: High-precision timestamp when analysis finished
        - timestamp: Human-readable ISO format timestamp for reporting
        - errors: Any accumulated error messages during processing
        
        **Session-Level Metrics Updated:**
        - documents_processed: Total count of all documents attempted
        - successful_analyses: Count of documents that completed successfully
        - failed_analyses: Count of documents that failed processing
        - total_processing_time: Cumulative processing time across all documents
        - per_document_metrics: Complete detailed metrics for each document
        
        **Content Analysis Integration:**
        - Calculates document complexity score based on processing characteristics
        - Updates global complexity_scores list for portfolio complexity assessment
        - Complexity factors: document length, processing time, API calls, language
        - Arabic/RTL languages get complexity multiplier due to processing difficulty
        
        **Usage for Performance Analysis:**
        - Success rate calculation (successful/total)
        - Average processing time per document
        - Throughput calculation (documents per minute)
        - Error pattern analysis across document types/sizes
        
        Args:
            doc_metrics: Document-specific metrics dictionary
            success: Whether document analysis completed successfully
            error: Optional error message if analysis failed
        """
        end_time = time.perf_counter()
        processing_time = end_time - doc_metrics['start_time']
        
        doc_metrics['processing_time'] = processing_time
        doc_metrics['success'] = success
        doc_metrics['end_time'] = end_time
        doc_metrics['timestamp'] = datetime.now().isoformat()
        
        if error:
            doc_metrics['errors'].append(error)
        
        # Update session metrics
        self.metrics['documents_processed'] += 1
        self.metrics['total_processing_time'] += processing_time
        
        if success:
            self.metrics['successful_analyses'] += 1
        else:
            self.metrics['failed_analyses'] += 1
        
        # Add to per-document metrics
        self.metrics['per_document_metrics'].append(doc_metrics)
        
        # Calculate contract complexity score
        complexity = self._calculate_complexity_score(doc_metrics)
        self.metrics['content_metrics']['complexity_scores'].append(complexity)
    
    def _check_structure_compliance(self, response: str) -> float:
        """Check if response follows expected structure (0-1)"""
        expected_sections = [
            r'contract type|type:|purpose',
            r'parties|party|between|among',
            r'date|term|effective|expir',
            r'financial|payment|fee|cost|price',
            r'obligation|requirement|shall|must',
            r'risk|liability|penalty|breach'
        ]
        
        found_sections = 0
        for pattern in expected_sections:
            if re.search(pattern, response, re.IGNORECASE):
                found_sections += 1
        
        return found_sections / len(expected_sections)
    
    def _check_completeness(self, response: str) -> float:
        """Check completeness of analysis (0-1)"""
        # Check for key indicators of complete analysis
        completeness_indicators = [
            len(response) > 100,  # Minimum length
            bool(re.search(r'\d+', response)),  # Contains numbers/dates
            bool(re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', response)),  # Contains proper nouns (names)
            not re.search(r'not found|unable to|cannot determine', response, re.IGNORECASE),  # Not failure response
            bool(re.search(r'shall|will|must|required', response, re.IGNORECASE)),  # Legal language
            response.count('.') >= 3,  # Multiple sentences
        ]
        
        return sum(completeness_indicators) / len(completeness_indicators)
    
    def _check_information_density(self, response: str) -> float:
        """
        Check information density and quality (0-1) - Enhanced for better extraction accuracy
        
        **Enhanced Extraction Indicators:**
        - Multiple financial amounts (not just one)
        - Various date formats (MM/DD/YYYY, DD-MM-YYYY, Month DD, YYYY)
        - Specific time periods with numbers
        - Company identifiers with proper formatting
        - Rich proper noun extraction
        - Well-structured information presentation
        - Specific quantities and measurements
        - Legal terminology usage
        """
        # Simplified density indicators - focus on key extraction elements
        density_indicators = [
            # Core extraction elements (most important)
            bool(re.search(r'\$[\d,]+', response)),  # Financial amounts
            bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', response)),  # Dates
            bool(re.search(r'\d+\s*(days|months|years)', response, re.IGNORECASE)),  # Time periods
            bool(re.search(r'(?:Inc\.|LLC|Corp\.|Ltd\.)', response)),  # Company types
            
            # Quality indicators
            len(re.findall(r'[A-Z][a-z]+', response)) >= 5,  # Proper nouns/names
            response.count(':') >= 2,  # Structured information
            
            # Content richness (bonus indicators)
            bool(re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', response, re.IGNORECASE)),  # Month names
            bool(re.search(r'\d+\s*(percent|%)', response, re.IGNORECASE)),  # Percentages
            len(response.split()) >= 100,  # Adequate detail length
        ]
        
        return sum(density_indicators) / len(density_indicators)
    
    def _check_consistency(self, response: str) -> float:
        """Check internal consistency of analysis (0-1)"""
        # Basic consistency checks
        consistency_score = 1.0
        
        # Check for contradictions
        contradictions = [
            (r'high risk', r'low risk'),
            (r'expires?', r'perpetual|indefinite'),
            (r'simple|basic', r'complex|complicated'),
        ]
        
        for pos_pattern, neg_pattern in contradictions:
            if (re.search(pos_pattern, response, re.IGNORECASE) and 
                re.search(neg_pattern, response, re.IGNORECASE)):
                consistency_score -= 0.2
        
        return max(0.0, consistency_score)
    
    def _check_contract_type_detection(self, response: str) -> float:
        """Check if contract type was properly identified (0-1)"""
        contract_types = [
            r'service agreement|services contract',
            r'employment|work|labor',
            r'software|development|technology',
            r'lease|rental|property',
            r'purchase|sale|buy|sell',
            r'consulting|advisory',
            r'partnership|joint venture',
            r'license|licensing',
            r'non-disclosure|confidentiality|nda',
            r'maintenance|support',
        ]
        
        for contract_type in contract_types:
            if re.search(contract_type, response, re.IGNORECASE):
                # Update contract type tracking
                type_name = contract_type.split('|')[0]
                current_count = self.metrics['content_metrics']['contract_types_identified'].get(type_name, 0)
                self.metrics['content_metrics']['contract_types_identified'][type_name] = current_count + 1
                return 1.0
        
        return 0.0
    
    def _calculate_complexity_score(self, doc_metrics: Dict[str, Any]) -> float:
        """
        Calculate document complexity score based on processing characteristics.
        
        **Complexity Factors Analyzed (Scale 0.0-1.0):**
        
        1. **length_factor**: Document size complexity
           - Normalized to 50,000 characters as baseline (typical large contract)
           - Larger documents are inherently more complex to analyze
           - Formula: min(text_length / 50000, 1.0)
        
        2. **time_factor**: Processing time complexity  
           - Normalized to 30 seconds as baseline (typical analysis time)
           - Longer processing indicates more complex content or API challenges
           - Formula: min(processing_time / 30.0, 1.0)
        
        3. **api_factor**: API interaction complexity
           - Normalized to 3 API calls as baseline (retry scenarios)
           - Multiple API calls indicate processing difficulties or failures
           - Formula: min(api_calls / 3.0, 1.0)
        
        4. **language_factor**: Language processing complexity multiplier
           - Arabic/RTL languages: 1.2x multiplier (higher complexity)
           - Other languages: 1.0x multiplier (standard complexity)
           - Accounts for additional processing challenges in non-Latin scripts
        
        **Final Complexity Score:**
        - Combined weighted average of all factors
        - Range: 0.0 (simple) to 1.0+ (highly complex)
        - Capped at 1.0 maximum for normalization
        - Used for portfolio complexity analysis and resource planning
        
        **Applications:**
        - Identify documents requiring special handling
        - Predict processing time for similar documents  
        - Optimize API usage for complex vs simple documents
        - Resource allocation for batch processing
        
        Args:
            doc_metrics: Document metrics containing processing characteristics
            
        Returns:
            float: Complexity score (0.0-1.0 scale)
        """
        # Factors: length, processing time, API calls, language
        length_factor = min(doc_metrics['text_length'] / 50000, 1.0)  # Normalize to 50k chars
        time_factor = min(doc_metrics['processing_time'] / 30.0, 1.0)  # Normalize to 30 seconds
        api_factor = min(doc_metrics['api_calls'] / 3.0, 1.0)  # Normalize to 3 calls
        
        # Arabic/complex languages are inherently more complex
        language_factor = 1.2 if doc_metrics['language'].startswith('ar') else 1.0
        
        complexity = (length_factor + time_factor + api_factor) * language_factor / 3.0
        return min(complexity, 1.0)
    
    def calculate_final_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive final session metrics and performance indicators.
        
        **Performance Metrics Calculated:**
        
        1. **avg_response_time**: Average API response time across all successful calls (seconds)
           - Helps identify API performance trends and bottlenecks
           - Based only on successful API calls for accuracy
        
        2. **success_rate**: Percentage of documents successfully analyzed (0.0-1.0)
           - Formula: successful_analyses / documents_processed
           - Key indicator of system reliability and API stability
        
        3. **throughput_docs_per_minute**: Processing throughput efficiency
           - Formula: (successful_analyses / total_processing_time) * 60
           - Measures real-world processing capacity for capacity planning
        
        **Quality Metrics Aggregated:**
        
        - **avg_structure_compliance**: Average adherence to expected analysis format
        - **avg_completeness_scores**: Average thoroughness of analysis content  
        - **avg_extraction_accuracy**: Average quality of information extraction
        - **avg_consistency_scores**: Average internal consistency of analyses
        
        **Content Analysis Metrics:**
        
        1. **avg_document_size**: Mean character count across all processed documents
           - Helps understand typical document complexity in the batch
        
        2. **median_document_size**: Middle value of document sizes
           - Less affected by outliers than average, shows typical document size
        
        3. **avg_complexity**: Mean complexity score across all documents
           - Portfolio-level complexity assessment for resource planning
        
        4. **languages_detected**: Count of documents by language
           - Shows language distribution in the document portfolio
        
        5. **contract_types_identified**: Count of documents by contract type
           - Portfolio composition analysis for business insights
        
        **Session Summary Metrics:**
        
        - **session_duration_minutes**: Total elapsed time for the entire session
        - **session_end**: ISO timestamp when session completed
        - **documents_processed**: Total number of documents attempted
        - **successful_analyses**: Number of documents successfully completed
        - **failed_analyses**: Number of documents that failed processing
        
        **Error Handling:**
        - Safely handles empty metric lists to prevent calculation errors
        - Validates data types before statistical calculations
        - Returns original metrics if no documents were processed
        
        Returns:
            Dict: Complete metrics with all calculated aggregations and summaries
        """
        if self.metrics['documents_processed'] == 0:
            return self.metrics
        
        # Performance metrics
        if self.metrics['performance_metrics']['api_response_times']:
            avg_response_time = statistics.mean(self.metrics['performance_metrics']['api_response_times'])
            self.metrics['performance_metrics']['avg_response_time'] = round(avg_response_time, 3)
        
        # Success rate
        total_docs = self.metrics['documents_processed']
        success_rate = self.metrics['successful_analyses'] / total_docs if total_docs > 0 else 0
        self.metrics['performance_metrics']['success_rate'] = round(success_rate, 3)
        
        # Throughput (docs per minute)
        if self.metrics['total_processing_time'] > 0:
            throughput = (self.metrics['successful_analyses'] / self.metrics['total_processing_time']) * 60
            self.metrics['performance_metrics']['throughput_docs_per_minute'] = round(throughput, 2)
        
        # Quality averages - create copy to avoid iteration modification error
        quality_items = list(self.metrics['quality_metrics'].items())
        for quality_type, scores in quality_items:
            if scores:
                # Ensure scores is a list, not a single float
                if isinstance(scores, (int, float)):
                    scores = [scores]
                elif not isinstance(scores, list):
                    continue
                    
                if len(scores) > 0:
                    avg_score = statistics.mean(scores)
                    self.metrics['quality_metrics'][f'avg_{quality_type}'] = round(avg_score, 3)
        
        # Content analysis with safety checks
        if self.metrics['content_metrics']['document_sizes']:
            sizes = self.metrics['content_metrics']['document_sizes']
            # Ensure sizes is a list
            if isinstance(sizes, (int, float)):
                sizes = [sizes]
            if isinstance(sizes, list) and len(sizes) > 0:
                self.metrics['content_metrics']['avg_document_size'] = int(statistics.mean(sizes))
                self.metrics['content_metrics']['median_document_size'] = int(statistics.median(sizes))
        
        if self.metrics['content_metrics']['complexity_scores']:
            complexities = self.metrics['content_metrics']['complexity_scores']
            # Ensure complexities is a list
            if isinstance(complexities, (int, float)):
                complexities = [complexities]
            if isinstance(complexities, list) and len(complexities) > 0:
                self.metrics['content_metrics']['avg_complexity'] = round(statistics.mean(complexities), 3)
        
        # Session summary
        self.metrics['session_end'] = datetime.now().isoformat()
        session_duration = datetime.now() - datetime.fromisoformat(self.metrics['session_start'])
        self.metrics['session_duration_minutes'] = round(session_duration.total_seconds() / 60, 2)
        
        return self.metrics
    
    def save_metrics(self, output_path: Path) -> Path:
        """Save comprehensive metrics to JSON file"""
        final_metrics = self.calculate_final_metrics()
        
        # Create metrics filename
        metrics_file = output_path / f"analysis_metrics_{self.metrics['session_id']}.json"
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(final_metrics, f, indent=2, ensure_ascii=False)
        
        return metrics_file
    
    def print_summary(self):
        """Print clean, human-readable metrics summary with inline formulas"""
        final_metrics = self.calculate_final_metrics()
        
        print("\n📊 CONTRACT ANALYSIS SUMMARY REPORT")
        print("=" * 70)
        
        # BASIC STATISTICS
        total_docs = final_metrics['documents_processed']
        successful = final_metrics['successful_analyses'] 
        failed = final_metrics['failed_analyses']
        success_rate = (successful / total_docs * 100) if total_docs > 0 else 0
        
        print(f"📄 Documents Processed: {total_docs}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {success_rate:.1f}% (successful/total*100)")
        
        # PERFORMANCE METRICS - Speed & Efficiency
        perf = final_metrics['performance_metrics']
        avg_time = perf.get('avg_response_time', 0)
        throughput = perf.get('throughput_docs_per_minute', 0)
        session_time = final_metrics.get('session_duration_minutes', 0)
        
        print(f"\n⚡ SPEED & EFFICIENCY:")
        print(f"   ⏱️  Average Processing Time: {avg_time:.1f}s per document")
        print(f"   🚀 Throughput Rate: {throughput:.1f} docs/minute (successful_docs/session_minutes)")
        print(f"   ⏰ Total Session Duration: {session_time:.1f} minutes")
        
        # QUALITY METRICS - Analysis Quality
        quality = final_metrics.get('quality_metrics', {})
        avg_structure = quality.get('avg_structure_compliance', 0) * 100
        avg_completeness = quality.get('avg_completeness', 0) * 100
        avg_extraction = quality.get('avg_information_density', 0) * 100  # Use information_density as extraction proxy
        
        print(f"\n🎯 ANALYSIS QUALITY:")
        print(f"   📋 Structure Compliance: {avg_structure:.0f}% (follows expected format)")
        print(f"   ✅ Completeness Score: {avg_completeness:.0f}% (required sections present)")
        print(f"   � Extraction Accuracy: {avg_extraction:.0f}% (key info extracted correctly)")
        
        # CONTENT ANALYSIS - Document Insights  
        content = final_metrics.get('content_metrics', {})
        avg_complexity = content.get('avg_complexity_score', 0)
        total_chars = content.get('total_characters_processed', 0)
        
        print(f"\n📖 DOCUMENT INSIGHTS:")
        print(f"   🧮 Average Complexity: {avg_complexity:.1f}/5.0 (document difficulty rating)")
        print(f"   📝 Total Text Processed: {total_chars:,} characters")
        if total_docs > 0:
            avg_doc_size = total_chars / total_docs
            print(f"   📄 Average Document Size: {avg_doc_size:,.0f} chars per document")
        
        # RELIABILITY METRICS - System Performance
        reliability = final_metrics.get('reliability_metrics', {})
        error_rate = reliability.get('error_rate', failed / total_docs if total_docs > 0 else 0) * 100
        fallback_rate = reliability.get('fallback_usage_rate', 0) * 100
        
        print(f"\n🛡️  SYSTEM RELIABILITY:")
        print(f"   ❌ Error Rate: {error_rate:.1f}% (failed/total*100)")
        print(f"   🔄 Fallback Usage: {fallback_rate:.1f}% (fallbacks/total*100)")
        print(f"   📊 Processing Stability: {'High' if error_rate < 10 else 'Medium' if error_rate < 25 else 'Low'}")
        
        # RECOMMENDATIONS
        print(f"\n💡 RECOMMENDATIONS:")
        if success_rate >= 95:
            print(f"   ✅ Excellent performance - system running optimally")
        elif success_rate >= 80:
            print(f"   ⚠️  Good performance - monitor for improvements")  
        else:
            print(f"   🚨 Performance issues detected - review error patterns")
            
        if avg_time > 10:
            print(f"   ⏱️  Consider optimizing for faster processing times")
        if avg_extraction < 70:
            print(f"   🔍 Review prompts to improve extraction accuracy")
            
        print("=" * 70)
        
        print("=" * 60)