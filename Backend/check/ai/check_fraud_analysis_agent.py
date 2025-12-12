"""
Check Fraud Analysis AI Agent using LangChain
Uses LangChain + OpenAI to analyze check fraud and make final decisions
Completely independent from Money Order AI agent - follows same LangChain pattern
"""

import json
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import LangChain components
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"LangChain not available: {e}")

from .check_prompts import (
    SYSTEM_PROMPT,
    RECOMMENDATION_GUIDELINES,
    format_analysis_template
)
from .check_tools import CheckDataAccessTools

logger = logging.getLogger(__name__)


class CheckFraudAnalysisAgent:
    """
    AI-powered fraud analysis agent for checks using LangChain
    Uses LangChain + ChatOpenAI to make final fraud determination decisions
    """

    def __init__(self, api_key: str, model: str = "gpt-4", data_tools: Optional[CheckDataAccessTools] = None):
        """
        Initialize the check fraud analysis agent with LangChain

        Args:
            api_key: OpenAI API key
            model: Model to use (default: o4-mini)
            data_tools: Data access tools for querying customer history, etc.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model
        self.data_tools = data_tools or CheckDataAccessTools()
        self.llm = None

        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                # For newer models (o4, o1), don't set max tokens (they have their own defaults)
                # For older models (gpt-4), use max_tokens
                llm_kwargs = {
                    'model': self.model_name,
                    'openai_api_key': self.api_key,
                }
                
                # Newer models (o4, o1) only support temperature=1 (default)
                # Older models support custom temperature values
                if self.model_name.startswith('o4') or self.model_name.startswith('o1'):
                    llm_kwargs['temperature'] = 1  # o4/o1 only support default temperature
                else:
                    llm_kwargs['max_tokens'] = 1500
                    llm_kwargs['temperature'] = 0.7  # Custom temperature for older models
                
                self.llm = ChatOpenAI(**llm_kwargs)
                logger.info(f"Initialized CheckFraudAnalysisAgent with LangChain model: {model}")
            except Exception as e:
                logger.warning(f"Could not initialize LangChain: {e}")
                self.llm = None
        else:
            if not LANGCHAIN_AVAILABLE:
                logger.warning("LangChain not available - AI analysis will be skipped")
            elif not self.api_key:
                logger.warning("OPENAI_API_KEY not set - AI analysis will be skipped")
            self.llm = None

    def analyze_fraud(
        self,
        extracted_data: Dict,
        ml_analysis: Dict,
        customer_id: Optional[str] = None,
        payer_name: Optional[str] = None
    ) -> Dict:
        """
        Analyze check for fraud using AI with LangChain

        Args:
            extracted_data: Extracted check data from Mindee
            ml_analysis: ML fraud analysis results
            customer_id: Customer ID if known
            payer_name: Payer name for customer lookup

        Returns:
            AI analysis dict with recommendation, confidence, reasoning, etc.
        """
        if not payer_name:
            payer_name = extracted_data.get('payer_name')

        customer_info: Dict = {}
        if payer_name:
            customer_info = self.data_tools.get_customer_history(payer_name)
            logger.info(f"Retrieved customer history for: {payer_name}")

        policy_decision = self._apply_policy_rules(payer_name, customer_info, ml_analysis)
        if policy_decision:
            return policy_decision

        if self.llm is None:
            raise ValueError("AI Agent not initialized. OpenAI API key missing or invalid.")

        return self._llm_analysis(
            extracted_data,
            ml_analysis,
            customer_id,
            payer_name,
            customer_info
        )

    def _apply_policy_rules(self, payer_name: Optional[str], customer_info: Optional[Dict], ml_analysis: Optional[Dict] = None) -> Optional[Dict]:
        """Enforce mandatory payer-history policy before any LLM call."""
        if not payer_name:
            logger.warning("Payer name missing; defaulting to ESCALATE per policy.")
            return self._create_first_time_escalation("Unknown Payer", is_new_customer=True)

        customer_info = customer_info or {}
        fraud_count = customer_info.get('fraud_count', 0) or 0
        escalate_count = customer_info.get('escalate_count', 0) or 0
        
        # Get fraud score from ML analysis
        ml_analysis = ml_analysis or {}
        fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)

        # REPEAT OFFENDER: fraud_count > 0 → Auto-reject
        if fraud_count > 0:
            logger.warning(
                f"REPEAT OFFENDER DETECTED: {payer_name} has fraud_count={fraud_count}. Auto-rejecting."
            )
            return self._create_repeat_offender_rejection(payer_name, fraud_count)

        # FIRST TIME: escalate_count = 0
        if escalate_count == 0:
            # Check fraud score: < 30% → APPROVE, >= 30% → ESCALATE
            if fraud_risk_score < 0.30:
                logger.info(
                    f"FIRST TIME CUSTOMER: {payer_name} has escalate_count=0 and fraud_score={fraud_risk_score:.1%} < 30%. Auto-approving."
                )
                return self._create_approval(payer_name, fraud_risk_score)
            else:
                logger.info(
                    f"FIRST TIME CUSTOMER: {payer_name} has escalate_count=0 and fraud_score={fraud_risk_score:.1%} >= 30%. Auto-escalating for manual review."
                )
                return self._create_first_time_escalation(payer_name, is_new_customer=True)

        # PREVIOUSLY ESCALATED: escalate_count > 0, fraud_count = 0 → Proceed to LLM for decision
        logger.info(f"Previously escalated customer {payer_name}; proceeding to LLM analysis.")
        return None

    def _llm_analysis(
        self,
        extracted_data: Dict,
        ml_analysis: Dict,
        customer_id: Optional[str] = None,
        payer_name: Optional[str] = None,
        customer_info: Optional[Dict] = None
    ) -> Dict:
        """
        Perform fraud analysis using LangChain and OpenAI
        """
        try:
            # Get customer information
            if not payer_name:
                payer_name = extracted_data.get('payer_name')

            if customer_info is None:
                customer_info = {}
                if payer_name:
                    customer_info = self.data_tools.get_customer_history(payer_name)
                    logger.info(f"Retrieved customer history for: {payer_name}")

            # MANDATORY REPEAT OFFENDER CHECK - BEFORE ANY LLM ANALYSIS
            # If fraud_count > 0, this MUST trigger automatic rejection (per policy)
            fraud_count = customer_info.get('fraud_count', 0)
            if fraud_count > 0:
                logger.warning(f"REPEAT OFFENDER DETECTED: {payer_name} has fraud_count={fraud_count}. Auto-rejecting.")
                return self._create_repeat_offender_rejection(payer_name, fraud_count)

            # Check for duplicates - but don't return early, pass to AI for analysis
            check_number = extracted_data.get('check_number')
            is_duplicate = False
            if check_number and payer_name:
                is_duplicate = self.data_tools.check_duplicate(check_number, payer_name)
                if is_duplicate:
                    logger.warning(f"Duplicate check detected: {check_number} from {payer_name} - will be flagged in AI analysis")
                    # Add duplicate flag to customer_info so AI can consider it
                    customer_info['is_duplicate'] = True
                    customer_info['duplicate_check_number'] = check_number

            # Format the analysis prompt
            analysis_prompt = format_analysis_template(
                check_data=extracted_data,
                ml_analysis=ml_analysis,
                customer_info=customer_info
            )

            # Add recommendation guidelines
            full_prompt = f"{analysis_prompt}\n\n{RECOMMENDATION_GUIDELINES}"

            # Create LangChain prompt - full_prompt is already formatted, so pass it directly
            # Don't use .from_template() since full_prompt already has { } in JSON schema
            from langchain_core.messages import SystemMessage, HumanMessage

            system_msg = SystemMessage(content=SYSTEM_PROMPT)
            user_msg = HumanMessage(content=full_prompt)
            messages = [system_msg, user_msg]

            # Generate analysis using LangChain
            logger.info("Calling LangChain LLM for check fraud analysis...")
            response = self.llm.invoke(messages)

            # Parse response
            ai_response = response.content
            logger.info("Received LLM response")

            # Try to parse as JSON
            try:
                result = json.loads(ai_response)
            except json.JSONDecodeError:
                # If not JSON, try to extract structured data from text
                result = self._parse_text_response(ai_response)

            # Validate and format result
            final_result = self._validate_and_format_result(result, ml_analysis, customer_info)

            logger.info(f"AI recommendation: {final_result.get('recommendation')}")
            return final_result

        except Exception as e:
            logger.error(f"Error in AI fraud analysis: {e}", exc_info=True)
            # Return safe fallback decision
            return self._create_fallback_decision(ml_analysis)

    def _create_approval(self, payer_name: str, fraud_risk_score: float) -> Dict:
        """Create approval response for first-time customers with low fraud scores."""
        return {
            'recommendation': 'APPROVE',
            'confidence_score': 1.0,
            'summary': f"Automatic approval: {payer_name} is a first-time customer with low fraud risk ({fraud_risk_score:.1%}).",
            'reasoning': [
                f"Payer {payer_name} has no recorded escalations (escalate_count = 0)",
                f"Fraud risk score ({fraud_risk_score:.1%}) is below 30% threshold",
                'First-time customers with low fraud scores are auto-approved'
            ],
            'key_indicators': [
                'Customer escalation count: 0',
                f'Fraud risk score: {fraud_risk_score:.1%} < 30%',
                'Policy: first-time low-risk uploads are approved'
            ],
            'actionable_recommendations': [
                'Process this check normally',
                'Create a customer record for future tracking',
                'Monitor future uploads for this payer'
            ],
            'fraud_types': [],
            'fraud_explanations': []
        }

    def _create_first_time_escalation(self, payer_name: str, is_new_customer: bool = False) -> Dict:
        """Create escalation response for first-time or clean-history customers."""
        customer_state = "new customer" if is_new_customer else "customer with no prior escalations"
        summary_reason = (
            f"Automatic escalation: {payer_name} is a {customer_state} per payer-based fraud policy."
        )
        return {
            'recommendation': 'ESCALATE',
            'confidence_score': 1.0,
            'summary': summary_reason,
            'reasoning': [
                f"Payer {payer_name} has no recorded escalations (escalate_count = 0)",
                'First-time or clean-history uploads must be escalated for manual review',
                'LLM and ML outputs cannot override this customer-history rule'
            ],
            'key_indicators': [
                'Customer escalation count: 0',
                'Policy: first-time uploads require escalation'
            ],
            'actionable_recommendations': [
                'Route this check to the manual review queue',
                'Create a customer record if one does not exist',
                'Monitor future uploads for this payer to enforce repeat-offender rules'
            ]
        }

    def _create_repeat_offender_rejection(self, payer_name: str, fraud_count: int) -> Dict:
        """Create rejection response for repeat offenders (fraud_count > 0)"""
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Automatic rejection: {payer_name} is a flagged repeat offender',
            'reasoning': [
                f'Payer {payer_name} has fraud_count = {fraud_count}',
                'Per payer-based fraud tracking policy: repeat offenders are automatically rejected',
                'This payer has previous fraud incidents and is now subject to automatic rejection',
                'LLM analysis skipped - mandatory reject rule applies'
            ],
            'key_indicators': [
                'Repeat offender detected',
                f'Previous fraud count: {fraud_count}'
            ],
            'actionable_recommendations': [
                'Block this transaction immediately',
                'Flag customer account for fraud investigation',
                'Contact payer to verify legitimacy of future transactions'
            ],
            'fraud_types': ['REPEAT_OFFENDER'],
            'fraud_explanations': [
                {
                    'type': 'REPEAT_OFFENDER',
                    'explanation': f'Payer {payer_name} has {fraud_count} previous fraud incident(s). Per fraud tracking policy, repeat offenders are automatically rejected.'
                }
            ]
        }

    def _create_duplicate_rejection(self, check_number: str, payer_name: str) -> Dict:
        """Create escalation response for duplicate checks"""
        return {
            'recommendation': 'ESCALATE',  # Duplicates should be escalated, not rejected
            'confidence_score': 1.0,
            'summary': f'Duplicate check submission detected for check #{check_number}',
            'reasoning': [
                f'Check #{check_number} from {payer_name} was previously submitted',
                'Duplicate submissions require manual review to verify legitimacy',
                'This may be a resubmission or potential fraud attempt'
            ],
            'key_indicators': [
                'Duplicate check detected',
                'Same check_number and payer_name combination'
            ],
            'actionable_recommendations': [
                'Review previous submission for this check',
                'Contact payer to verify if this is an intentional resubmission',
                'Investigate for potential fraud if no valid reason for duplicate'
            ],
            'fraud_types': [],  # Duplicate is not a fraud type - it's an escalation reason
            'fraud_explanations': []
        }

    def _parse_text_response(self, text_response: str) -> Dict:
        """Parse text response if JSON parsing fails"""
        # Simple heuristic parsing
        result = {
            'recommendation': 'ESCALATE',  # Default to safe option
            'confidence_score': 0.7,
            'summary': text_response[:200],
            'reasoning': [],
            'key_indicators': [],
            'actionable_recommendations': [],
            'fraud_types': [],
            'fraud_explanations': []
        }

        # Try to extract recommendation
        text_lower = text_response.lower()
        if 'approve' in text_lower and 'reject' not in text_lower:
            result['recommendation'] = 'APPROVE'
        elif 'reject' in text_lower:
            result['recommendation'] = 'REJECT'
        else:
            result['recommendation'] = 'ESCALATE'

        # Extract reasoning (look for bullet points or numbered lists)
        lines = text_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'): 
                result['reasoning'].append(line.lstrip('-*•0123456789.) '))

        return result

    def _validate_and_format_result(self, result: Dict, ml_analysis: Dict, customer_info: Dict) -> Dict:
        """Validate and format the AI result"""
        # Ensure required fields exist
        validated = {
            'recommendation': result.get('recommendation', 'ESCALATE').upper(),
            'confidence_score': float(result.get('confidence_score', 0.7)),
            'summary': result.get('summary', 'AI fraud analysis completed'),
            'reasoning': result.get('reasoning', []),
            'key_indicators': result.get('key_indicators', []),
            'actionable_recommendations': result.get('actionable_recommendations', []),
            'fraud_types': result.get('fraud_types', []),
            'fraud_explanations': result.get('fraud_explanations', [])
        }

        # Validate recommendation value
        if validated['recommendation'] not in ['APPROVE', 'REJECT', 'ESCALATE']:
            logger.warning(f"Invalid recommendation: {validated['recommendation']}, defaulting to ESCALATE")
            validated['recommendation'] = 'ESCALATE'

        # Ensure confidence score is in valid range
        validated['confidence_score'] = max(0.0, min(1.0, validated['confidence_score']))

        # Validate fraud_types is a list
        if not isinstance(validated['fraud_types'], list):
            validated['fraud_types'] = []

        # Validate fraud_explanations is a list
        if not isinstance(validated['fraud_explanations'], list):
            validated['fraud_explanations'] = []

        # Ensure fraud_types are valid
        valid_fraud_types = ['SIGNATURE_FORGERY', 'AMOUNT_ALTERATION', 'COUNTERFEIT_CHECK', 'REPEAT_OFFENDER', 'STALE_CHECK']
        validated['fraud_types'] = [ft for ft in validated['fraud_types'] if ft in valid_fraud_types]

        # Add additional context
        validated['ml_fraud_score'] = ml_analysis.get('fraud_risk_score', 0.0)
        validated['ml_risk_level'] = ml_analysis.get('risk_level', 'UNKNOWN')

        if customer_info.get('customer_id'):
            validated['customer_history'] = {
                'fraud_count': customer_info.get('fraud_count', 0),
                'escalate_count': customer_info.get('escalate_count', 0),
                'has_fraud_history': customer_info.get('has_fraud_history', False)
            }

        return validated

    def _create_fallback_decision(self, ml_analysis: Dict) -> Dict:
        """Create safe fallback decision if AI analysis fails"""
        fraud_score = ml_analysis.get('fraud_risk_score', 0.5)
        risk_level = ml_analysis.get('risk_level', 'MEDIUM')

        # Conservative fallback logic
        if fraud_score >= 0.7:
            recommendation = 'REJECT'
            summary = 'High fraud risk detected by ML models - automatic rejection'
        elif fraud_score >= 0.3:
            recommendation = 'ESCALATE'
            summary = 'Moderate fraud risk - requires human review'
        else:
            recommendation = 'APPROVE'
            summary = 'Low fraud risk detected'

        return {
            'recommendation': recommendation,
            'confidence_score': 0.6,
            'summary': summary,
            'reasoning': [
                'AI analysis unavailable - using ML-based fallback decision',
                f'ML fraud score: {fraud_score:.2%}',
                f'Risk level: {risk_level}'
            ],
            'key_indicators': ml_analysis.get('feature_importance', []),
            'actionable_recommendations': [
                'Review ML fraud indicators',
                'Consider manual verification if needed'
            ],
            'ml_fraud_score': fraud_score,
            'ml_risk_level': risk_level,
            'fallback_mode': True,
            'fraud_types': [],  # Cannot determine fraud types without AI
            'fraud_explanations': []
        }
