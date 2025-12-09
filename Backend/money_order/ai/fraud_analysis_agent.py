"""
Fraud Analysis Agent using LangChain and OpenAI GPT-4
Provides intelligent fraud recommendations based on ML scores and extracted data
"""

import os
import re
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import sys
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"Warning: LangChain not installed. Error: {e}")

from .prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_TEMPLATE,
    RECOMMENDATION_GUIDELINES
)
from .tools import DataAccessTools


class FraudAnalysisAgent:
    """
    AI-powered fraud analysis agent using OpenAI GPT-4
    """

    def __init__(self, api_key: Optional[str] = None, model: str = 'gpt-4', data_tools: Optional[DataAccessTools] = None):
        """
        Initialize the fraud analysis agent
        
        Args:
            api_key: OpenAI API key (optional, falls back to env var)
            model: Model name to use (default: gpt-4)
            data_tools: Tools for accessing historical data
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model
        self.data_tools = data_tools
        self.llm = None

        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                # For newer models (o4, o1), explicitly set temperature=1 (required, not optional)
                # For older models (gpt-4), use max_tokens and optional temperature
                is_newer_model = self.model_name.startswith('o4') or self.model_name.startswith('o1')
                
                llm_kwargs = {
                    'model': self.model_name,
                    'openai_api_key': self.api_key,
                }
                
                # Newer models (o4, o1) ONLY support temperature=1 (must be explicitly set)
                # If we don't set it, LangChain defaults to 0.7 which causes an error
                if is_newer_model:
                    llm_kwargs['temperature'] = 1  # Required for newer models
                else:
                    # For older models, set temperature and max_tokens
                    llm_kwargs['temperature'] = 1
                    llm_kwargs['max_tokens'] = 1500
                
                self.llm = ChatOpenAI(**llm_kwargs)
            except Exception as e:
                print(f"Warning: Could not initialize LangChain: {e}")
                self.llm = None
        else:
            if not LANGCHAIN_AVAILABLE:
                print("LangChain not available - using fallback analysis")
            elif not self.api_key:
                print("OpenAI API key not found - using fallback analysis")
            self.llm = None

    def analyze_fraud(self,
                      ml_analysis: Dict,
                      extracted_data: Dict,
                      customer_id: Optional[str] = None,
                      is_repeat_customer: bool = False,
                      customer_fraud_history: Optional[Dict] = None) -> Dict:
        """
        Perform AI-powered fraud analysis

        Args:
            ml_analysis: ML model fraud analysis results
            extracted_data: Extracted money order fields
            customer_id: Customer ID for history lookup
            is_repeat_customer: Whether this is a repeat customer from database
            customer_fraud_history: Dict with fraud history from database

        Returns:
            Dictionary with AI analysis and recommendation
        """
        if self.llm is None:
            raise ValueError("AI Agent not initialized. OpenAI API key missing or invalid.")

        return self._llm_analysis(ml_analysis, extracted_data, customer_id, is_repeat_customer, customer_fraud_history)

    def _llm_analysis(self, ml_analysis: Dict, extracted_data: Dict, customer_id: Optional[str] = None, is_repeat_customer: bool = False, customer_fraud_history: Optional[Dict] = None) -> Dict:
        """
        Perform fraud analysis using LangChain and OpenAI

        Payer-Based Fraud Logic:
        - If customer has escalate_count > 0 (previous ESCALATE recommendations), force REJECT
        - This means second and subsequent uploads by same payer always get REJECT
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Log input parameters for debugging
        purchaser = extracted_data.get('purchaser', 'Unknown')
        logger.info(f"[FRAUD_ANALYSIS] Starting analysis for {purchaser}")
        logger.info(f"[FRAUD_ANALYSIS] Input params: is_repeat_customer={is_repeat_customer}, customer_id={customer_id}")
        logger.info(f"[FRAUD_ANALYSIS] customer_fraud_history={customer_fraud_history}")

        # PRIORITY #1: MANDATORY SIGNATURE VALIDATION CHECK
        # This is the HIGHEST priority check - enforced before ALL other rules
        signature = extracted_data.get('signature')
        
        # Check both the signature field AND ML fraud indicators for missing signature
        # ML stores fraud indicators in 'fraud_indicators' list
        ml_fraud_indicators = ml_analysis.get('fraud_indicators', []) if ml_analysis else []
        ml_detected_missing_sig = any('missing signature' in str(indicator).lower() for indicator in ml_fraud_indicators)
        
        # Log signature status for debugging
        logger.info(f"[FRAUD_ANALYSIS] Signature field value: {signature}")
        logger.info(f"[FRAUD_ANALYSIS] ML fraud_indicators: {ml_fraud_indicators}")
        logger.info(f"[FRAUD_ANALYSIS] ML detected missing signature: {ml_detected_missing_sig}")
        
        # Check if signature is missing (either field is empty OR ML detected it)
        if (not signature or signature == '' or signature is None) or ml_detected_missing_sig:
            logger.warning(f"[FRAUD_ANALYSIS] ⚠️ MISSING SIGNATURE DETECTED")
            logger.warning(f"[FRAUD_ANALYSIS] Signature field: {signature}, ML detected: {ml_detected_missing_sig}")
            
            # Check if this is a repeat customer with previous escalations
            escalate_count = 0
            if customer_fraud_history:
                escalate_count = customer_fraud_history.get('escalate_count', 0)
            
            logger.info(f"[FRAUD_ANALYSIS] Customer escalate_count: {escalate_count}")
            
            # FIRST TIME (escalate_count == 0): ESCALATE for human review
            # SECOND TIME (escalate_count > 0): REJECT automatically
            if escalate_count > 0:
                logger.warning(f"[FRAUD_ANALYSIS] ⚠️ REPEAT OFFENDER: REJECT triggered (escalate_count={escalate_count})")
                
                # Repeat attempt with missing signature - force REJECT
                reject_result = {
                    'recommendation': 'REJECT',
                    'confidence_score': 1.0,
                    'summary': f'Missing signature detected on repeat upload (escalate_count={escalate_count}). Automatic rejection per strict signature validation policy.',
                    'reasoning': [
                        'Signature field is missing or empty' if not signature else 'ML fraud detector identified missing signature',
                        f'Customer has {escalate_count} previous escalation(s) - this is a repeat attempt',
                        'Per system policy: First missing signature → ESCALATE, repeat attempts → REJECT',
                        'Automatic rejection enforced to prevent repeat fraud attempts'
                    ],
                    'key_indicators': [
                        'No signature detected in OCR extraction' if not signature else 'ML fraud detector flagged missing signature',
                        f'Repeat offender (escalate_count={escalate_count})',
                        'Mandatory signature policy violation'
                    ],
                    'verification_notes': 'Document rejected due to missing signature on repeat upload. Customer was previously escalated for same issue.',
                    'actionable_recommendations': (
                        [
                            'Reject this transaction immediately - policy enforcement overrides low fraud score',
                            'Signature policy takes precedence over normal approval thresholds',
                            'Flag customer account for potential fraud pattern (repeat missing signature attempts)',
                            'Consider blocking future uploads from this customer'
                        ] if ml_analysis.get("fraud_risk_score", 0) < 0.30 else [
                            'Reject this transaction immediately - signature not present on repeat upload',
                            'Flag customer account for potential fraud pattern (repeat missing signature attempts)',
                            'Consider blocking future uploads from this customer'
                        ]
                    ),
                    'fraud_types': ['SIGNATURE_FORGERY', 'REPEAT_OFFENDER'],
                    'fraud_explanations': [
                        {
                            'type': 'SIGNATURE_FORGERY',
                            'reasons': [
                                'Signature field is missing or empty' if not signature else 'ML fraud detector identified missing signature',
                                'Mandatory signature validation failed',
                                'Signature is required for all money orders per policy'
                            ]
                        },
                        {
                            'type': 'REPEAT_OFFENDER',
                            'reasons': [
                                f'Customer has {escalate_count} previous escalation(s)',
                                'Repeat attempt with missing signature indicates fraud pattern',
                                'Per payer-based fraud tracking policy: repeat offenders are automatically rejected'
                            ]
                        }
                    ],
                    'training_insights': 'Repeat missing signature attempts indicate potential fraud pattern',
                    'historical_comparison': 'Consistent with repeat offender policy',
                    'analysis_type': 'policy_enforcement',
                    'model_used': 'mandatory_signature_policy'
                }
                
                logger.info(f"[FRAUD_ANALYSIS] Returning REJECT result: {reject_result}")
                return reject_result
            else:
                logger.warning(f"[FRAUD_ANALYSIS] ⚠️ FIRST TIME OFFENDER: ESCALATE triggered")
                
                # First time missing signature - force ESCALATE for human review
                escalate_result = {
                    'recommendation': 'ESCALATE',
                    'confidence_score': 1.0,
                    'summary': 'Missing signature detected on first upload. Escalating for human review per signature validation policy.',
                    'reasoning': [
                        'Signature field is missing or empty' if not signature else 'ML fraud detector identified missing signature',
                        'This is the first upload from this payer (escalate_count=0)',
                        'Per system policy: First missing signature → ESCALATE for human review',
                        'Escalation allows verification of potential OCR error or legitimate missing signature'
                    ],
                    'key_indicators': [
                        'No signature detected in OCR extraction' if not signature else 'ML fraud detector flagged missing signature',
                        'First-time payer',
                        'Mandatory signature policy - requires human verification'
                    ],
                    'verification_notes': 'Document escalated due to missing signature on first upload. Verify if signature is truly missing or if OCR failed to detect it.',
                    'actionable_recommendations': [
                        'Manually verify if signature is present on the physical document',
                        'If signature is present, approve and note OCR limitation',
                        'If signature is truly missing, reject and flag customer for future uploads'
                    ],
                    'fraud_types': ['SIGNATURE_FORGERY'],
                    'fraud_explanations': [
                        {
                            'type': 'SIGNATURE_FORGERY',
                            'reasons': [
                                'Signature field is missing or empty' if not signature else 'ML fraud detector identified missing signature',
                                'Mandatory signature validation failed',
                                'First-time upload requires human verification to rule out OCR error'
                            ]
                        }
                    ],
                    'training_insights': 'First-time missing signatures may be OCR errors or legitimate issues requiring human judgment',
                    'historical_comparison': 'Consistent with first-time escalation policy',
                    'analysis_type': 'policy_enforcement',
                    'model_used': 'mandatory_signature_policy'
                }
                
                logger.info(f"[FRAUD_ANALYSIS] Returning ESCALATE result: {escalate_result}")
                return escalate_result


        # Store ML analysis and customer status for later validation
        self._current_ml_analysis = ml_analysis
        self._is_repeat_customer = is_repeat_customer

        # Check if this payer already has escalate history - if so, force REJECT
        # This is critical for payer-based fraud tracking
        escalate_count = 0
        if customer_fraud_history:
            raw_escalate_count = customer_fraud_history.get('escalate_count', 0)
            # CRITICAL: Convert to int to handle string/None values
            try:
                if raw_escalate_count is None:
                    escalate_count = 0
                else:
                    escalate_count = int(raw_escalate_count)
            except (ValueError, TypeError) as e:
                logger.error(f"[FRAUD_ANALYSIS] Error converting escalate_count to int: {raw_escalate_count}, error: {e}")
                escalate_count = 0
            
            logger.info(f"[FRAUD_ANALYSIS] Extracted escalate_count={escalate_count} (raw={raw_escalate_count}, type={type(raw_escalate_count)}) from customer_fraud_history")
            logger.info(f"[FRAUD_ANALYSIS] Full customer_fraud_history dict: {customer_fraud_history}")
        else:
            logger.info(f"[FRAUD_ANALYSIS] No customer_fraud_history provided, escalate_count=0")

        # CRITICAL CHECK: MANDATORY REJECT if escalate_count > 0 AND fraud_risk_score >= 30%
        # This MUST happen before any LLM analysis
        # If fraud score is low (< 30%), allow normal analysis even for repeat customers
        # Double-check with explicit comparison to handle edge cases
        fraud_risk_score = ml_analysis.get('fraud_risk_score', 0) if ml_analysis else 0
        
        if escalate_count is not None and int(escalate_count) > 0:
            logger.info(f"[FRAUD_ANALYSIS] Repeat customer detected: escalate_count={escalate_count}, fraud_risk_score={fraud_risk_score:.1%}")
            
            # Check if fraud score warrants rejection
            if fraud_risk_score >= 0.30:
                logger.warning(f"[FRAUD_ANALYSIS] ⚠️ MANDATORY REJECT TRIGGERED: escalate_count={escalate_count} > 0 AND fraud_risk_score={fraud_risk_score:.1%} >= 30%")
                logger.warning(f"[FRAUD_ANALYSIS] Customer has previous ESCALATE records AND high fraud score - forcing REJECT recommendation")
                
                # Customer has previous ESCALATE records AND high fraud score - force REJECT recommendation
                reject_result = {
                    'recommendation': 'REJECT',
                    'confidence_score': 1.0,
                    'summary': f'Payer has escalate_count={escalate_count} from previous uploads and fraud score of {fraud_risk_score:.1%}. Forcing REJECT per payer-based fraud tracking rules.',
                    'reasoning': [
                        f'Customer escalate_count is {escalate_count} (> 0)',
                        f'Fraud risk score is {fraud_risk_score:.1%} (>= 30% threshold)',
                        'Per system policy: repeat customers with high fraud scores are automatically REJECTED',
                        'This overrides AI scoring to enforce strict repeat customer fraud policy'
                    ],
                    'key_indicators': [
                        f'Repeat payer detected with {escalate_count} previous escalation(s)',
                        f'High fraud risk score: {fraud_risk_score:.1%}',
                        'Policy: Force REJECT on repeat offenders with elevated risk'
                    ],
                    'verification_notes': 'Forced rejection based on customer fraud history combined with high fraud score',
                    'actionable_recommendations': [
                        'Block this transaction immediately - repeat customer with high fraud score',
                        'Flag customer account for review',
                        'Consider deactivating customer'
                    ],
                    'fraud_types': ['REPEAT_OFFENDER'],
                    'fraud_explanations': [
                        {
                            'type': 'REPEAT_OFFENDER',
                            'reasons': [
                                f'Customer has {escalate_count} previous escalation(s)',
                                f'Fraud risk score is {fraud_risk_score:.1%} (>= 30% threshold)',
                                'Per payer-based fraud tracking policy: repeat offenders with elevated risk are automatically rejected'
                            ]
                        }
                    ],
                    'training_insights': 'Repeat customers with escalation history and high fraud scores have very high fraud probability',
                    'historical_comparison': 'Similar to other repeat fraud cases',
                    'analysis_type': 'policy_enforcement',
                    'model_used': 'payer_fraud_policy'
                }
                
                logger.info(f"[FRAUD_ANALYSIS] Returning REJECT result: {reject_result}")
                return reject_result
            else:
                logger.info(f"[FRAUD_ANALYSIS] Repeat customer with LOW fraud score ({fraud_risk_score:.1%} < 30%) - allowing normal analysis to proceed")
                # Low fraud score - allow normal analysis even though escalate_count > 0
        else:
            logger.info(f"[FRAUD_ANALYSIS] escalate_count={escalate_count}, proceeding with LLM analysis")

        # Get fraud risk score to determine if we should hide escalate_count from AI
        fraud_risk_score = ml_analysis.get('fraud_risk_score', 0) if ml_analysis else 0
        hide_escalate_count = fraud_risk_score < 0.30
        
        if hide_escalate_count:
            logger.info(f"[FRAUD_ANALYSIS] Fraud score ({fraud_risk_score:.1%}) < 30% - hiding escalate_count from AI to allow approval")

        # Get customer history if ID provided
        customer_history = "No customer ID provided"
        if customer_id and self.data_tools:
            history = self.data_tools.get_customer_history(customer_id)
            if history:
                # If fraud score is low, remove escalate_count from history to prevent AI from seeing it
                if hide_escalate_count and isinstance(history, dict):
                    history_copy = history.copy()
                    history_copy.pop('escalate_count', None)
                    history_copy.pop('last_recommendation', None)  # Also remove last recommendation
                    customer_history = str(history_copy)
                    logger.info(f"[FRAUD_ANALYSIS] Sanitized customer history (removed escalate_count): {customer_history}")
                else:
                    customer_history = str(history)

        # Search for similar fraud cases
        similar_cases = "No similar cases found"
        if self.data_tools:
            cases = self.data_tools.search_similar_fraud_cases(
                issuer=extracted_data.get('issuer'),
                amount_range=(
                    extracted_data.get('amount', 0) * 0.9,
                    extracted_data.get('amount', 0) * 1.1
                )
            )
            if cases:
                similar_cases = str(cases)

        # Get training insights (mocked for now, but would come from vector DB or stats)
        training_patterns = "High correlation between amount mismatch and fraud (45% of cases)."

        # Get historical analysis results
        past_similar_cases = "No past analysis found."
        if self.data_tools:
            past_results = self.data_tools.search_stored_analyses(
                issuer=extracted_data.get('issuer'),
                amount_range=(
                    extracted_data.get('amount', 0) * 0.9,
                    extracted_data.get('amount', 0) * 1.1
                )
            )
            if past_results:
                past_similar_cases = str(past_results[:3])

        # Helper to get value from multiple keys
        def get_val(keys, default='Unknown'):
            for key in keys:
                val = extracted_data.get(key)
                if val:
                    return val
            return default

        # Helper to format amount
        def format_amount(val):
            if isinstance(val, dict):
                return f"{val.get('currency', '$')} {val.get('value', 0)}"
            return val

        # Prepare prompt variables
        # Check if repeat customer has fraud history from database
        has_fraud_history = False
        if is_repeat_customer and customer_fraud_history:
            # Use the fraud flag from database (more reliable than string search)
            has_fraud_history = customer_fraud_history.get('has_fraud_history', False)

        if is_repeat_customer and has_fraud_history:
            customer_type = "REPEAT CUSTOMER WITH FRAUD HISTORY (known fraudster in database)"
        elif is_repeat_customer:
            customer_type = "REPEAT CUSTOMER WITH CLEAN HISTORY (no fraud incidents)"
        else:
            customer_type = "NEW CUSTOMER (not in database)"

        # Extract escalation tracking info for LLM context
        escalate_count = 0
        fraud_count = 0
        if customer_fraud_history:
            escalate_count = customer_fraud_history.get('escalate_count', 0)
            fraud_count = customer_fraud_history.get('fraud_count', 0)

        # Format escalation status for clear LLM understanding
        # Only show escalation warning if fraud score >= 30%
        if hide_escalate_count:
            # Low fraud score - hide escalation details from AI
            escalation_status = "No escalation history"
        else:
            # High fraud score - show full escalation details
            escalation_status = f"Escalate Count: {escalate_count} | Fraud Count: {fraud_count}"
            if escalate_count > 0:
                escalation_status += " | ⚠️ PAYER HAS BEEN ESCALATED BEFORE - MUST REJECT"

        prompt_vars = {
            "fraud_risk_score": ml_analysis.get('fraud_score', 0),
            "risk_level": ml_analysis.get('risk_level', 'UNKNOWN'),
            "model_confidence": ml_analysis.get('confidence_score', 0),
            "rf_score": ml_analysis.get('model_scores', {}).get('random_forest', 0),
            "xgb_score": ml_analysis.get('model_scores', {}).get('xgboost', 0),
            "issuer": get_val(['issuer_name', 'issuer']),
            "serial_number": get_val(['serial_primary', 'serial_number']),
            "amount": format_amount(get_val(['amount_numeric', 'amount'])),
            "amount_in_words": get_val(['amount_written', 'amount_in_words']),
            "raw_ocr_text": extracted_data.get('raw_text', 'N/A'),
            "payee": get_val(['recipient', 'payee', 'pay_to']),
            "purchaser": get_val(['sender_name', 'purchaser', 'from', 'sender']),
            "date": get_val(['date']),
            "location": get_val(['sender_address', 'location']),
            "signature": get_val(['signature']),
            "fraud_indicators": str(ml_analysis.get('anomalies', [])),
            "customer_id": customer_id or "N/A",
            "customer_type": customer_type,
            "escalation_status": escalation_status,
            "customer_history": customer_history,
            "similar_cases": similar_cases,
            "training_patterns": training_patterns,
            "past_similar_cases": past_similar_cases
        }

        # DEBUG: Log raw_text availability
        logger.info(f"[FRAUD_ANALYSIS] DEBUG: extracted_data keys: {list(extracted_data.keys())}")
        logger.info(f"[FRAUD_ANALYSIS] DEBUG: raw_text in extracted_data: {'raw_text' in extracted_data}")
        logger.info(f"[FRAUD_ANALYSIS] DEBUG: raw_text value: {extracted_data.get('raw_text', 'MISSING')[:100] if extracted_data.get('raw_text') else 'NULL'}")
        logger.info(f"[FRAUD_ANALYSIS] DEBUG: raw_ocr_text for prompt: {prompt_vars.get('raw_ocr_text', 'NOT SET')[:100] if prompt_vars.get('raw_ocr_text') != 'N/A' else 'N/A'}")

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(ANALYSIS_TEMPLATE)
        ])

        # Generate analysis
        messages = prompt.format_messages(**prompt_vars)
        response = self.llm.invoke(messages)

        # Parse response
        return self._parse_llm_response(response.content)

    def _parse_llm_response(self, content: str) -> Dict:
        """
        Parse the structured response from LLM
        """
        result = {
            'recommendation': 'ESCALATE',
            'confidence_score': 0.0,
            'summary': '',
            'reasoning': [],
            'key_indicators': [],
            'verification_notes': '',
            'actionable_recommendations': [],
            'fraud_types': [],
            'fraud_explanations': [],
            'training_insights': '',
            'historical_comparison': '',
            'analysis_type': 'ai_enhanced',
            'model_used': self.model_name
        }
        
        try:
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.split(':', 1)[1].strip().upper()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        score_str = line.split(':', 1)[1].strip().replace('%', '')
                        result['confidence_score'] = float(score_str) / 100.0
                    except:
                        result['confidence_score'] = 0.5
                elif line.startswith('SUMMARY:'):
                    result['summary'] = line.split(':', 1)[1].strip()
                elif line.startswith('REASONING:'):
                    current_section = 'reasoning'
                    if ':' in line and len(line.split(':', 1)[1].strip()) > 0:
                         result['reasoning'].append(line.split(':', 1)[1].strip())
                elif line.startswith('KEY_INDICATORS:'):
                    current_section = 'key_indicators'
                    if ':' in line and len(line.split(':', 1)[1].strip()) > 0:
                         result['key_indicators'].append(line.split(':', 1)[1].strip())
                elif line.startswith('VERIFICATION_NOTES:'):
                    result['verification_notes'] = line.split(':', 1)[1].strip()
                    current_section = 'verification_notes'
                elif line.startswith('ACTIONABLE_RECOMMENDATIONS:'):
                    current_section = 'actionable_recommendations'
                elif line.startswith('FRAUD_TYPES:'):
                    # Parse comma-separated fraud types
                    fraud_types_str = line.split(':', 1)[1].strip()
                    if fraud_types_str and fraud_types_str.lower() not in ['none', 'n/a', '']:
                        result['fraud_types'] = [ft.strip() for ft in fraud_types_str.split(',') if ft.strip()]
                    current_section = None
                elif line.startswith('FRAUD_EXPLANATIONS:'):
                    current_section = 'fraud_explanations'
                    current_fraud_type = None
                elif line.startswith('TRAINING_INSIGHTS:'):
                    result['training_insights'] = line.split(':', 1)[1].strip()
                    current_section = 'training_insights'
                elif line.startswith('HISTORICAL_COMPARISON:'):
                    result['historical_comparison'] = line.split(':', 1)[1].strip()
                    current_section = 'historical_comparison'
                elif line.startswith('- '):
                    item = line[2:].strip()
                    if current_section == 'reasoning':
                        result['reasoning'].append(item)
                    elif current_section == 'key_indicators':
                        result['key_indicators'].append(item)
                    elif current_section == 'actionable_recommendations':
                        result['actionable_recommendations'].append(item)
                    elif current_section == 'fraud_explanations':
                        # Check if this is a fraud type header (ends with colon)
                        if item.endswith(':'):
                            current_fraud_type = item[:-1].strip()
                            # Initialize fraud explanation entry
                            result['fraud_explanations'].append({
                                'type': current_fraud_type,
                                'reasons': []
                            })
                elif line.startswith('* ') and current_section == 'fraud_explanations':
                    # This is a reason for the current fraud type
                    reason = line[2:].strip()
                    if result['fraud_explanations'] and current_fraud_type:
                        result['fraud_explanations'][-1]['reasons'].append(reason)
                elif current_section == 'verification_notes' and not line.isupper():
                     result['verification_notes'] += " " + line
                elif current_section == 'training_insights' and not line.isupper():
                     result['training_insights'] += " " + line
                elif current_section == 'historical_comparison' and not line.isupper():
                     result['historical_comparison'] += " " + line

        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            result['summary'] = "Error parsing AI analysis results."
            
        return result

    def _fallback_analysis(self, ml_analysis: Dict, extracted_data: Dict) -> Dict:
        """
        DEPRECATED: Rule-based fallback analysis.
        Now raises exception to enforce strict error handling.
        """
        raise ValueError("Fallback analysis is disabled. System requires active AI Agent.")
