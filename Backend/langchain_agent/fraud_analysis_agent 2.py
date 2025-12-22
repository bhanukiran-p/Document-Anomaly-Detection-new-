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
                # For newer models (o4, o1), don't set max tokens (they have their own defaults)
                # For older models (gpt-4), use max_tokens
                llm_kwargs = {
                    'model': self.model_name,
                    'openai_api_key': self.api_key,
                }
                
                # Newer models (o4, o1) only support temperature=1 (default), not custom values
                # Older models support custom temperature
                if self.model_name.startswith('o4') or self.model_name.startswith('o1'):
                    # Don't set temperature - newer models only support default (1)
                    pass
                else:
                    # For older models, set temperature
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
            customer_fraud_history: Dict with fraud history (escalate_count, fraud_count, has_fraud_history)

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
        # Log what we received
        purchaser = extracted_data.get('purchaser', 'Unknown')
        logging.info(f"[FRAUD_ANALYSIS] Analyzing {purchaser}: is_repeat_customer={is_repeat_customer}, customer_fraud_history={customer_fraud_history}")

        # Store escalate_count for later use in recommendation logic
        # Will be used in RECOMMENDATION_GUIDELINES to determine REJECT vs ESCALATE
        escalate_count = 0
        if customer_fraud_history:
            escalate_count = customer_fraud_history.get('escalate_count', 0)
            logging.info(f"[FRAUD_ANALYSIS] Extracted escalate_count={escalate_count} from customer_fraud_history")

        # MANDATORY RULE: If escalate_count >= 1, REJECT immediately
        # Repeat customers with any previous escalation are automatically rejected
        if escalate_count >= 1:
            fraud_risk_score = ml_analysis.get('fraud_score', 0)
            logging.info(f"[FRAUD_ANALYSIS] MANDATORY REJECT: Customer has escalation history (escalate_count={escalate_count})")
            return {
                'recommendation': 'REJECT',
                'confidence_score': 0.95,
                'summary': f'MANDATORY REJECT: Customer has escalation history (count={escalate_count})',
                'reasoning': [
                    f'Customer has been escalated {escalate_count} time(s) in previous uploads',
                    'Per system policy: Repeat customers with any escalation history are automatically rejected',
                    f'Current fraud risk score: {fraud_risk_score:.0%}'
                ],
                'key_indicators': [
                    f'Customer escalation count: {escalate_count}',
                    f'Fraud risk score: {fraud_risk_score:.0%}'
                ],
                'verification_notes': 'Mandatory rejection based on escalation history and current fraud score',
                'actionable_recommendations': [
                    'Block this transaction immediately',
                    'Flag customer account for review',
                    'Consider deactivating customer'
                ],
                'training_insights': 'Customers with escalation history have demonstrated fraud risk patterns',
                'historical_comparison': 'Similar to other repeat fraud cases',
                'analysis_type': 'policy_enforcement',
                'model_used': 'escalation_policy'
            }

        # Store ML analysis and customer status for later validation
        self._current_ml_analysis = ml_analysis
        self._is_repeat_customer = is_repeat_customer

        # Get customer history if ID provided
        customer_history = "No customer ID provided"
        if customer_id and self.data_tools:
            history = self.data_tools.get_customer_history(customer_id)
            if history:
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
        # Determine customer type based on escalate_count
        if is_repeat_customer:
            if escalate_count >= 1:
                customer_type = f"REPEAT CUSTOMER WITH ESCALATION HISTORY (escalate_count={escalate_count}, previously flagged)"
            else:
                customer_type = "REPEAT CUSTOMER WITH CLEAN HISTORY (escalate_count=0, no previous escalations)"
        else:
            customer_type = "NEW CUSTOMER (not in database)"

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
            "payee": get_val(['recipient', 'payee', 'pay_to']),
            "purchaser": get_val(['sender_name', 'purchaser', 'from', 'sender']),
            "date": get_val(['date']),
            "location": get_val(['sender_address', 'location']),
            "signature": get_val(['signature']),
            "fraud_indicators": str(ml_analysis.get('anomalies', [])),
            "customer_id": customer_id or "N/A",
            "customer_type": customer_type,
            "customer_history": customer_history,
            "similar_cases": similar_cases,
            "training_patterns": training_patterns,
            "past_similar_cases": past_similar_cases
        }

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
