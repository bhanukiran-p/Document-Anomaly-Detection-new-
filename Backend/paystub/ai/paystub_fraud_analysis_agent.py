"""
Paystub Fraud Analysis AI Agent using LangChain
Uses LangChain + OpenAI to analyze paystub fraud and make final decisions
Completely independent from other document type AI agents
"""

import json
import logging
from typing import Dict, Optional
import os

# Load environment variables (if not already loaded)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv already loaded by api_server.py or not available
    pass

# Import LangChain components
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"LangChain not available: {e}")

from .paystub_prompts import (
    SYSTEM_PROMPT,
    RECOMMENDATION_GUIDELINES,
    format_analysis_template
)
from .paystub_tools import PaystubDataAccessTools

logger = logging.getLogger(__name__)


class PaystubFraudAnalysisAgent:
    """
    AI-powered fraud analysis agent for paystubs using LangChain
    Uses LangChain + ChatOpenAI to make final fraud determination decisions
    """

    def __init__(self, api_key: str, model: str = "o4-mini", data_tools: Optional[PaystubDataAccessTools] = None):
        """
        Initialize the paystub fraud analysis agent with LangChain

        Args:
            api_key: OpenAI API key
            model: Model to use (default: o4-mini)
            data_tools: Data access tools for querying employee history, etc.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model
        self.data_tools = data_tools or PaystubDataAccessTools()
        self.llm = None

        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                # For newer models (o4, o1), don't set max tokens (they have their own defaults)
                # For older models (gpt-4), use max_tokens
                llm_kwargs = {
                    'model': self.model_name,
                    'openai_api_key': self.api_key,
                    'temperature': 1,  # Explicitly set to 1 for all models (required for o4, o1)
                }
                
                # Only set max_tokens for older models that support it
                if not (self.model_name.startswith('o4') or self.model_name.startswith('o1')):
                    llm_kwargs['max_tokens'] = 1500
                
                self.llm = ChatOpenAI(**llm_kwargs)
                logger.info(f"Initialized PaystubFraudAnalysisAgent with LangChain model: {model}")
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
        employee_name: Optional[str] = None
    ) -> Dict:
        """
        Analyze paystub for fraud using AI with LangChain

        Args:
            extracted_data: Extracted paystub data from OCR
            ml_analysis: ML fraud analysis results
            employee_name: Employee name for employee lookup

        Returns:
            AI analysis dict with recommendation, confidence, reasoning, etc.
        """
        # Try multiple sources for employee name
        if not employee_name:
            employee_name = (
                extracted_data.get('employee_name') or
                extracted_data.get('employee') or
                (extracted_data.get('employee_names', [])[0] if isinstance(extracted_data.get('employee_names'), list) and len(extracted_data.get('employee_names', [])) > 0 else None)
            )

        employee_info: Dict = {}
        if employee_name:
            employee_info = self.data_tools.get_employee_history(employee_name)
            logger.info(f"Retrieved employee history for: {employee_name}")
            logger.info(f"Employee history: escalate_count={employee_info.get('escalate_count', 0)}, fraud_count={employee_info.get('fraud_count', 0)}")
        else:
            logger.warning("Employee name not found in extracted_data")

        policy_decision = self._apply_policy_rules(employee_name, employee_info, ml_analysis, extracted_data)
        if policy_decision:
            return policy_decision

        if self.llm is None:
            raise ValueError("AI Agent not initialized. OpenAI API key missing or invalid.")

        return self._llm_analysis(
            extracted_data,
            ml_analysis,
            employee_name,
            employee_info
        )

    def _apply_policy_rules(self, employee_name: Optional[str], employee_info: Optional[Dict], ml_analysis: Optional[Dict] = None, extracted_data: Optional[Dict] = None) -> Optional[Dict]:
        """Enforce mandatory employee-history policy before any LLM call."""
        if not employee_name:
            raise ValueError("Employee name is required for fraud analysis. Cannot proceed without employee identification.")

        employee_info = employee_info or {}
        escalate_count = employee_info.get('escalate_count', 0) or 0
        fraud_count = employee_info.get('fraud_count', 0) or 0

        # Check for duplicates BEFORE repeat offender check
        if employee_name and extracted_data:
            pay_date = extracted_data.get('pay_date')
            pay_period_start = extracted_data.get('pay_period_start')
            if pay_date and pay_period_start:
                is_duplicate = self.data_tools.check_duplicate(employee_name, pay_date, pay_period_start)
                if is_duplicate:
                    logger.warning(f"Duplicate paystub detected: {pay_date} from {employee_name}")
                    return self._create_duplicate_rejection(pay_date, employee_name)

        # UPDATED POLICY: Repeat offenders always go to LLM for decision
        # No auto-reject for repeat offenders - LLM will make the decision based on risk score
        if escalate_count > 0:
            fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0) if ml_analysis else 0.0
            fraud_risk_percent = fraud_risk_score * 100
            logger.info(
                f"REPEAT OFFENDER DETECTED: {employee_name} has escalate_count={escalate_count} "
                f"and fraud_risk_score={fraud_risk_percent:.1f}%. Proceeding to LLM for decision."
            )
            # Don't auto-reject, let the LLM make the decision based on risk score

        # Proceed to LLM for decision
        logger.info(f"Proceeding to LLM analysis for employee: {employee_name}")
        return None

    def _llm_analysis(
        self,
        extracted_data: Dict,
        ml_analysis: Dict,
        employee_name: Optional[str] = None,
        employee_info: Optional[Dict] = None
    ) -> Dict:
        """
        Perform fraud analysis using LangChain and OpenAI
        """
        try:
            # Get employee information
            if not employee_name:
                employee_name = extracted_data.get('employee_name')

            if employee_info is None:
                employee_info = {}
                if employee_name:
                    employee_info = self.data_tools.get_employee_history(employee_name)
                    logger.info(f"Retrieved employee history for: {employee_name}")

            # Format the analysis prompt
            analysis_prompt = format_analysis_template(
                paystub_data=extracted_data,
                ml_analysis=ml_analysis,
                employee_info=employee_info
            )

            # Add recommendation guidelines
            full_prompt = f"{analysis_prompt}\n\n{RECOMMENDATION_GUIDELINES}"

            # Create LangChain prompt
            system_msg = SystemMessage(content=SYSTEM_PROMPT)
            user_msg = HumanMessage(content=full_prompt)
            messages = [system_msg, user_msg]

            # Generate analysis using LangChain
            logger.info("Calling LangChain LLM for paystub fraud analysis...")
            response = self.llm.invoke(messages)

            # Parse response
            ai_response = response.content
            logger.info("Received LLM response")

            # Strip markdown code blocks if present (LLM sometimes wraps JSON in ```json ... ```)
            ai_response_cleaned = ai_response.strip()
            if ai_response_cleaned.startswith('```json'):
                ai_response_cleaned = ai_response_cleaned[7:]  # Remove ```json
            elif ai_response_cleaned.startswith('```'):
                ai_response_cleaned = ai_response_cleaned[3:]  # Remove ```
            if ai_response_cleaned.endswith('```'):
                ai_response_cleaned = ai_response_cleaned[:-3]  # Remove trailing ```
            ai_response_cleaned = ai_response_cleaned.strip()

            # Sanitize common LLM JSON errors (e.g., "0. ninety" -> "0.90")
            import re
            ai_response_cleaned = re.sub(r'"confidence_score":\s*0\.\s*ninety', '"confidence_score":0.90', ai_response_cleaned)
            ai_response_cleaned = re.sub(r'"confidence_score":\s*0\.\s*eighty', '"confidence_score":0.80', ai_response_cleaned)
            ai_response_cleaned = re.sub(r'"confidence_score":\s*0\.\s*seventy', '"confidence_score":0.70', ai_response_cleaned)

            # Try to parse as JSON
            try:
                result = json.loads(ai_response_cleaned)
            except json.JSONDecodeError:
                # If not JSON, try to extract structured data from text
                result = self._parse_text_response(ai_response_cleaned)

            # Validate and format result
            final_result = self._validate_and_format_result(result, ml_analysis, employee_info)

            # CRITICAL: Post-LLM validation - Force ESCALATE for new employees if LLM returns REJECT
            # This matches money order logic: new employees should NEVER get REJECT on first upload
            is_new_employee = not employee_info.get('employee_id')
            if is_new_employee and final_result.get('recommendation') == 'REJECT':
                logger.warning(
                    f"LLM returned REJECT for new employee {employee_name}. "
                    f"Overriding to ESCALATE per policy (new employees must be escalated, not rejected)."
                )
                final_result = self._create_first_time_escalation(employee_name, is_new_employee=True)
                final_result['reasoning'].append(
                    f"Original LLM recommendation was REJECT, but overridden to ESCALATE because this is a new employee. "
                    f"New employees require manual review before rejection."
                )

            logger.info(f"AI recommendation: {final_result.get('recommendation')}")
            return final_result

        except Exception as e:
            logger.error(f"Error in AI fraud analysis: {e}", exc_info=True)
            raise RuntimeError(
                f"AI analysis failed: {str(e)}. "
                f"Please check OpenAI API key and network connectivity."
            ) from e

    def _create_first_time_escalation(self, employee_name: str, is_new_employee: bool = False) -> Dict:
        """Create escalation response for first-time or clean-history employees."""
        employee_state = "new employee" if is_new_employee else "employee with no prior escalations"
        summary_reason = (
            f"Automatic escalation: {employee_name} is a {employee_state} per employee-based fraud policy."
        )
        return {
            'recommendation': 'ESCALATE',
            'confidence_score': 1.0,
            'summary': summary_reason,
            'reasoning': [
                f"Employee {employee_name} has no recorded escalations (escalate_count = 0)",
                'First-time or clean-history uploads must be escalated for manual review',
                'LLM and ML outputs cannot override this employee-history rule'
            ],
            'key_indicators': [
                'Employee escalation count: 0',
                'Policy: first-time uploads require escalation'
            ],
            'actionable_recommendations': [
                'Route this paystub to the manual review queue',
                'Create an employee record if one does not exist',
                'Monitor future uploads for this employee to enforce repeat-offender rules'
            ],
            'fraud_types': [],
            'fraud_explanations': []
        }

    def _create_repeat_offender_rejection(self, employee_name: str, escalate_count: int, fraud_count: int = 0) -> Dict:
        """Create rejection response for repeat offenders (escalate_count > 0 and fraud risk >= 40%)"""
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Automatic rejection: {employee_name} is a flagged repeat offender with fraud risk >= 40%',
            'reasoning': [
                f'Employee {employee_name} has escalate_count = {escalate_count}',
                f'Employee has fraud_count = {fraud_count}',
                'Per updated policy: repeat offenders with fraud risk >= 40% are automatically rejected',
                'This employee was previously escalated and current paystub shows elevated fraud risk',
                'LLM analysis skipped - mandatory reject rule applies'
            ],
            'key_indicators': [
                'Repeat offender detected',
                f'Escalation count: {escalate_count}',
                f'Fraud count: {fraud_count}'
            ],
            'actionable_recommendations': [
                'Block this transaction immediately',
                'Flag employee account for fraud investigation',
                'Contact employee to verify legitimacy of future submissions'
            ],
            'fraud_types': ['REPEAT_OFFENDER'],  # Separate classification for repeat offenders
            'fraud_explanations': [{
                'type': 'REPEAT_OFFENDER',
                'reasons': [
                    f'Employee has {escalate_count} previous escalation{"s" if escalate_count != 1 else ""}',
                    f'Employee has {fraud_count} previous fraud incident{"s" if fraud_count != 1 else ""}',
                    'Employee status: Repeat Employee with documented fraud history'
                ]
            }]
        }

    def _create_duplicate_rejection(self, pay_date: str, employee_name: str) -> Dict:
        """Create rejection response for duplicate paystubs"""
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Duplicate paystub submission detected for employee {employee_name}',
            'reasoning': [
                f'Paystub for {pay_date} from {employee_name} was previously submitted',
                'Duplicate submissions are automatically rejected per fraud policy',
                'This is a critical fraud indicator'
            ],
            'key_indicators': [
                'Duplicate paystub detected',
                'Same employee_name, pay_date, and pay_period_start combination'
            ],
            'actionable_recommendations': [
                'Block this transaction immediately',
                'Flag employee account for review',
                'Investigate potential fraud attempt'
            ],
            'fraud_types': ['FABRICATED_DOCUMENT'],  # Duplicate submission is a form of fabrication
            'fraud_explanations': [{
                'type': 'FABRICATED_DOCUMENT',
                'reasons': [f'Duplicate paystub detected for {pay_date} from {employee_name}. This paystub was previously submitted.']
            }]
        }

    def _parse_text_response(self, text_response: str) -> Dict:
        """Parse text response if JSON parsing fails - NO FALLBACKS"""
        raise RuntimeError(
            f"LLM response could not be parsed as JSON. This is a critical error. "
            f"Response was: {text_response[:500]}"
        )

    def _validate_and_format_result(self, result: Dict, ml_analysis: Dict, employee_info: Dict) -> Dict:
        """Validate and format the AI result"""
        # Ensure required fields exist
        validated = {
            'recommendation': result.get('recommendation', 'ESCALATE').upper(),
            'confidence_score': float(result.get('confidence_score', 0.7)),
            'summary': result.get('summary', 'AI fraud analysis completed'),
            'reasoning': result.get('reasoning', []),
            'key_indicators': result.get('key_indicators', []),
            'actionable_recommendations': result.get('actionable_recommendations', [])
        }

        # Validate recommendation value - NO FALLBACKS
        if validated['recommendation'] not in ['APPROVE', 'REJECT', 'ESCALATE']:
            raise ValueError(
                f"Invalid recommendation from LLM: {validated['recommendation']}. "
                f"Must be one of: APPROVE, REJECT, ESCALATE. This is a critical error."
            )

        # Ensure reasoning is a list
        if not isinstance(validated['reasoning'], list):
            validated['reasoning'] = [str(validated['reasoning'])]

        # Ensure key_indicators is a list
        if not isinstance(validated['key_indicators'], list):
            validated['key_indicators'] = [str(validated['key_indicators'])]

        # Ensure actionable_recommendations is a list
        if not isinstance(validated['actionable_recommendations'], list):
            validated['actionable_recommendations'] = [str(validated['actionable_recommendations'])]

        # Handle fraud_types and fraud_explanations
        fraud_types = result.get('fraud_types') or ml_analysis.get('fraud_types') or []
        fraud_explanations = result.get('fraud_explanations') or []

        # Normalize fraud_explanations into list[{type, reasons[list]}]
        normalized_explanations = []
        if isinstance(fraud_explanations, list):
            for item in fraud_explanations:
                if isinstance(item, dict):
                    fraud_type = item.get('type')
                    reasons = item.get('reasons', [])
                    if fraud_type and isinstance(reasons, list):
                        normalized_explanations.append({
                            'type': fraud_type,
                            'reasons': [str(r) for r in reasons if r]
                        })

        # If no explanations but we have types, backfill using ml_analysis.fraud_reasons
        if not normalized_explanations and fraud_types:
            base_reasons = ml_analysis.get('fraud_reasons', [])
            for fraud_type in fraud_types:
                normalized_explanations.append({
                    'type': fraud_type,
                    'reasons': base_reasons if base_reasons else [f"Flagged as {fraud_type.replace('_', ' ').title()} by the ML rules."]
                })

        # Ensure fraud_types is a list
        if not isinstance(fraud_types, list):
            fraud_types = [str(fraud_types)] if fraud_types else []

        validated['fraud_types'] = fraud_types
        validated['fraud_explanations'] = normalized_explanations

        return validated



