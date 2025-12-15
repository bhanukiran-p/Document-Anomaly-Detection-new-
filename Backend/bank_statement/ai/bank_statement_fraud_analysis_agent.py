"""
Bank Statement Fraud Analysis AI Agent using LangChain
Uses LangChain + OpenAI to analyze bank statement fraud and make final decisions
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

from .bank_statement_prompts import (
    SYSTEM_PROMPT,
    RECOMMENDATION_GUIDELINES,
    format_analysis_template
)
from .bank_statement_tools import BankStatementDataAccessTools

logger = logging.getLogger(__name__)


class BankStatementFraudAnalysisAgent:
    """
    AI-powered fraud analysis agent for bank statements using LangChain
    Uses LangChain + ChatOpenAI to make final fraud determination decisions
    """

    def __init__(self, api_key: str, model: str = "o4-mini", data_tools: Optional[BankStatementDataAccessTools] = None):
        """
        Initialize the bank statement fraud analysis agent with LangChain

        Args:
            api_key: OpenAI API key
            model: Model to use (default: o4-mini)
            data_tools: Data access tools for querying customer history, etc.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model
        self.data_tools = data_tools or BankStatementDataAccessTools()
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
                logger.info(f"Initialized BankStatementFraudAnalysisAgent with LangChain model: {model}")
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
        account_holder_name: Optional[str] = None
    ) -> Dict:
        """
        Analyze bank statement for fraud using AI with LangChain

        Args:
            extracted_data: Extracted bank statement data from Mindee
            ml_analysis: ML fraud analysis results
            account_holder_name: Account holder name for customer lookup

        Returns:
            AI analysis dict with recommendation, confidence, reasoning, etc.
        """
        # Try multiple sources for account holder name
        if not account_holder_name:
            account_holder_name = (
                extracted_data.get('account_holder_name') or
                extracted_data.get('account_holder') or
                (extracted_data.get('account_holder_names', [])[0] if isinstance(extracted_data.get('account_holder_names'), list) and len(extracted_data.get('account_holder_names', [])) > 0 else None)
            )

        customer_info: Dict = {}
        if account_holder_name:
            customer_info = self.data_tools.get_customer_history(account_holder_name)
            logger.info(f"Retrieved customer history for: {account_holder_name}")
            logger.info(f"Customer history: escalate_count={customer_info.get('escalate_count', 0)}, fraud_count={customer_info.get('fraud_count', 0)}")
        else:
            logger.warning("Account holder name not found in extracted_data")

        policy_decision = self._apply_policy_rules(account_holder_name, customer_info)
        if policy_decision:
            return policy_decision

        if self.llm is None:
            raise ValueError("AI Agent not initialized. OpenAI API key missing or invalid.")

        return self._llm_analysis(
            extracted_data,
            ml_analysis,
            account_holder_name,
            customer_info
        )

    def _apply_policy_rules(self, account_holder_name: Optional[str], customer_info: Optional[Dict]) -> Optional[Dict]:
        """Enforce mandatory account-holder-history policy before any LLM call."""
        if not account_holder_name:
            logger.warning("Account holder name missing; defaulting to ESCALATE per policy.")
            return self._create_first_time_escalation("Unknown Account Holder", is_new_customer=True)

        customer_info = customer_info or {}
        fraud_count = customer_info.get('fraud_count', 0) or 0

        # Check for repeat offenders: if fraud_count > 0, auto-reject with REPEAT_OFFENDER
        # REPEAT_OFFENDER only applies to customers who have been REJECTED before (fraud_count > 0)
        # Customers who were only ESCALATED (escalate_count > 0, fraud_count = 0) should go through LLM analysis
        if fraud_count > 0:
            logger.warning(
                f"REPEAT OFFENDER DETECTED: {account_holder_name} has fraud_count={fraud_count}. Auto-rejecting."
            )
            return self._create_repeat_offender_rejection(account_holder_name, fraud_count)

        # If we reach here, account holder has no fraud history → proceed to LLM for decision
        logger.info(f"Customer {account_holder_name} has no fraud history; proceeding to LLM analysis.")
        return None

    def _llm_analysis(
        self,
        extracted_data: Dict,
        ml_analysis: Dict,
        account_holder_name: Optional[str] = None,
        customer_info: Optional[Dict] = None
    ) -> Dict:
        """
        Perform fraud analysis using LangChain and OpenAI
        """
        try:
            # Get customer information
            if not account_holder_name:
                account_holder_name = extracted_data.get('account_holder_name')

            if customer_info is None:
                customer_info = {}
                if account_holder_name:
                    customer_info = self.data_tools.get_customer_history(account_holder_name)
                    logger.info(f"Retrieved customer history for: {account_holder_name}")

            # MANDATORY REPEAT OFFENDER CHECK - BEFORE ANY LLM ANALYSIS
            # REPEAT_OFFENDER only applies to customers who have been REJECTED before (fraud_count > 0)
            # Customers who were only ESCALATED (escalate_count > 0, fraud_count = 0) should go through LLM analysis
            fraud_count = customer_info.get('fraud_count', 0) or 0
            escalate_count = customer_info.get('escalate_count', 0) or 0
            if fraud_count > 0:
                logger.warning(f"REPEAT OFFENDER DETECTED: {account_holder_name} has fraud_count={fraud_count}. Auto-rejecting.")
                return self._create_repeat_offender_rejection(account_holder_name, fraud_count)
            
            # CRITICAL: Upload-based decision logic BEFORE LLM
            # First upload (escalate_count = 0): >30% → ESCALATE, ≤30% → APPROVE
            # Second+ upload (escalate_count > 0): >30% → REJECT, ≤30% → Continue to LLM
            fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)
            is_first_upload = escalate_count == 0
            is_new_customer = not customer_info.get('customer_id')
            
            if is_first_upload:
                # First upload logic
                if fraud_risk_score > 0.30:
                    logger.info(f"First upload with fraud_risk_score={fraud_risk_score:.1%} > 30% → ESCALATE")
                    return self._create_first_time_escalation(account_holder_name, is_new_customer=is_new_customer, fraud_risk_score=fraud_risk_score)
                else:
                    logger.info(f"First upload with fraud_risk_score={fraud_risk_score:.1%} ≤ 30% → APPROVE")
                    return self._create_first_time_approval(account_holder_name, fraud_risk_score)
            else:
                # Second+ upload logic
                # For second+ uploads with >30% risk, we still need to call LLM to get fraud types
                # Then we'll override recommendation to REJECT but keep LLM-provided fraud types
                # And add REPEAT_OFFENDER only if fraud_count > 0
                if fraud_risk_score > 0.30:
                    logger.warning(f"Second+ upload (escalate_count={escalate_count}, fraud_count={fraud_count}) with fraud_risk_score={fraud_risk_score:.1%} > 30% → Will REJECT after LLM analysis")
                    # Continue to LLM to get fraud types, then override to REJECT
                    # Don't return early - let LLM analyze and provide fraud types
                else:
                    logger.info(f"Second+ upload (escalate_count={escalate_count}) with fraud_risk_score={fraud_risk_score:.1%} ≤ 30% → Continue to LLM for analysis")
                    # Continue to LLM analysis for second+ uploads with low risk

            # Check for duplicates - CRITICAL: Only mark as duplicate if previous submission was REJECTED
            # If previous was ESCALATED, NEVER mark as duplicate - allow resubmission even if current upload is fraud
            # Duplicate = same document uploaded again AFTER it was already REJECTED (confirmed fraud)
            account_number = extracted_data.get('account_number')
            statement_period_start = extracted_data.get('statement_period_start_date')
            if account_number and statement_period_start and account_holder_name:
                duplicate_check = self.data_tools.check_duplicate(account_number, statement_period_start, account_holder_name)
                is_duplicate = duplicate_check.get('is_duplicate', False)
                previous_recommendation = duplicate_check.get('previous_recommendation')
                
                # Log duplicate check results for debugging
                logger.info(f"Duplicate check result: is_duplicate={is_duplicate}, previous_recommendation={previous_recommendation}")
                
                if is_duplicate:
                    # CRITICAL LOGIC: Only reject as duplicate if previous submission was REJECTED (confirmed fraud)
                    # If previous was ESCALATED, APPROVE, or None - allow resubmission (not considered duplicate)
                    # This means: escalated documents can be resubmitted even if they turn out to be fraud
                    previous_rec_upper = previous_recommendation.upper() if previous_recommendation else None
                    if previous_recommendation and previous_rec_upper == 'REJECT':
                        logger.warning(f"Duplicate bank statement detected (previous was REJECTED/fraud): {account_number} from {account_holder_name}, previous_recommendation={previous_recommendation}")
                        return self._create_duplicate_rejection(account_number, account_holder_name)
                    else:
                        # Previous was ESCALATED, APPROVE, or no recommendation - NOT a duplicate
                        # Allow resubmission and continue with normal analysis (even if current upload is fraud)
                        logger.info(f"Same statement found but previous was '{previous_recommendation}' (not REJECTED) - NOT treating as duplicate, allowing resubmission: {account_number} from {account_holder_name}")
                        # Continue with normal analysis flow - this will be analyzed normally
                        # IMPORTANT: Do NOT mark as duplicate - let it go through normal analysis

            # Format the analysis prompt
            analysis_prompt = format_analysis_template(
                bank_statement_data=extracted_data,
                ml_analysis=ml_analysis,
                customer_info=customer_info
            )

            # Add recommendation guidelines
            full_prompt = f"{analysis_prompt}\n\n{RECOMMENDATION_GUIDELINES}"

            # Create LangChain prompt
            system_msg = SystemMessage(content=SYSTEM_PROMPT)
            user_msg = HumanMessage(content=full_prompt)
            messages = [system_msg, user_msg]

            # Generate analysis using LangChain
            logger.info("Calling LangChain LLM for bank statement fraud analysis...")
            response = self.llm.invoke(messages)

            # Parse response
            ai_response = response.content
            logger.info(f"Received LLM response (length: {len(ai_response)} chars)")
            logger.info(f"LLM raw response: {ai_response[:500]}...")  # Log first 500 chars for debugging

            # Try to parse as JSON - NO FALLBACK, error if invalid
            # But try harder to extract JSON from common LLM response formats
            result = self._parse_json_response(ai_response)
            
            # Log what LLM returned for fraud_types and fraud_explanations
            logger.info(f"LLM returned fraud_types: {result.get('fraud_types', [])}")
            logger.info(f"LLM returned fraud_explanations: {result.get('fraud_explanations', [])}")
            logger.info(f"LLM returned actionable_recommendations: {result.get('actionable_recommendations', [])}")

            # Validate and format result
            final_result = self._validate_and_format_result(result, ml_analysis, customer_info)

            # CRITICAL: Post-LLM override for second+ uploads with >30% risk
            # We let LLM analyze to get fraud types, but then override recommendation to REJECT
            # And add REPEAT_OFFENDER only if fraud_count > 0
            # Get customer info again to ensure we have latest values
            escalate_count_post = customer_info.get('escalate_count', 0) or 0
            fraud_count_post = customer_info.get('fraud_count', 0) or 0
            fraud_risk_score_post = ml_analysis.get('fraud_risk_score', 0.0)
            is_second_upload = escalate_count_post > 0
            
            if is_second_upload and fraud_risk_score_post > 0.30:
                logger.warning(f"Overriding LLM recommendation to REJECT for second+ upload with >30% risk (escalate_count={escalate_count_post}, fraud_count={fraud_count_post})")
                original_recommendation = final_result.get('recommendation')
                
                # Get fraud types from LLM (document-based analysis) - use LLM fraud types only
                llm_fraud_types = final_result.get('fraud_types', []) or []
                llm_fraud_explanations = final_result.get('fraud_explanations', []) or []
                
                # Add REPEAT_OFFENDER only if fraud_count > 0 (not based on escalate_count)
                fraud_types = list(llm_fraud_types)  # Copy LLM fraud types
                fraud_explanations = list(llm_fraud_explanations)  # Copy LLM explanations
                
                if fraud_count_post > 0:
                    # Only add REPEAT_OFFENDER if customer has previous fraud (fraud_count > 0)
                    if 'REPEAT_OFFENDER' not in fraud_types:
                        fraud_types.append('REPEAT_OFFENDER')
                        fraud_explanations.append({
                            'type': 'REPEAT_OFFENDER',
                            'reasons': [
                                f'Customer has {fraud_count_post} previous fraud incident(s)',
                                f'Current fraud risk score ({fraud_risk_score_post:.1%}) exceeds 30% threshold for repeat customers',
                                'Second+ uploads with elevated risk from a customer with fraud history indicate potential fraud pattern'
                            ]
                        })
                        logger.info(f"Added REPEAT_OFFENDER fraud type because fraud_count={fraud_count_post} > 0")
                else:
                    logger.info(f"NOT adding REPEAT_OFFENDER because fraud_count={fraud_count_post} (only escalate_count={escalate_count_post})")
                
                # Override to REJECT but keep LLM/ML fraud types and add REPEAT_OFFENDER if applicable
                final_result['recommendation'] = 'REJECT'
                final_result['confidence_score'] = 1.0
                final_result['summary'] = f'Second+ upload rejected: {account_holder_name} has fraud risk score {fraud_risk_score_post:.1%} > 30%'
                final_result['fraud_types'] = fraud_types
                final_result['fraud_explanations'] = fraud_explanations
                
                # Update reasoning to reflect override
                if original_recommendation != 'REJECT':
                    final_result['reasoning'].insert(0, f'Original LLM recommendation was {original_recommendation}, but overridden to REJECT because this is a second+ upload with fraud risk > 30%')
                final_result['reasoning'].insert(0, f'Account holder {account_holder_name} has {escalate_count_post} previous escalation(s)')
                final_result['reasoning'].insert(1, f'Fraud risk score ({fraud_risk_score_post:.1%}) exceeds 30% threshold for second+ uploads')
                final_result['reasoning'].insert(2, 'Second and subsequent uploads with risk > 30% are automatically rejected per policy')

            logger.info(f"AI recommendation: {final_result.get('recommendation')}")
            logger.info(f"Fraud types: {final_result.get('fraud_types', [])}")
            return final_result

        except Exception as e:
            logger.error(f"Error in AI fraud analysis: {e}", exc_info=True)
            # No fallback - raise error if LLM is not available
            raise RuntimeError(
                f"AI analysis failed: {str(e)}. "
                f"Please check OpenAI API key and network connectivity. "
                f"LLM analysis is required - no fallback available."
            ) from e

    def _create_first_time_approval(self, account_holder_name: str, fraud_risk_score: float) -> Dict:
        """Create approval response for first-time uploads with fraud risk score ≤ 30%"""
        return {
            'recommendation': 'APPROVE',
            'confidence_score': 1.0,
            'summary': f'First upload approved: {account_holder_name} has fraud risk score {fraud_risk_score:.1%} ≤ 30%',
            'reasoning': [
                f'Account holder {account_holder_name} is a first-time uploader (escalate_count = 0)',
                f'Fraud risk score ({fraud_risk_score:.1%}) is ≤ 30% threshold for first uploads',
                'First uploads with low risk scores are automatically approved per policy'
            ],
            'key_indicators': [
                'Customer escalation count: 0',
                f'Fraud risk score: {fraud_risk_score:.1%}',
                'Policy: first uploads with ≤30% risk are approved'
            ],
            'actionable_recommendations': [],
            'fraud_types': [],
            'fraud_explanations': []
        }

    def _create_second_upload_rejection(self, account_holder_name: str, fraud_risk_score: float, escalate_count: int, fraud_count: int) -> Dict:
        """Create rejection response for second+ uploads with fraud risk score > 30%
        
        CRITICAL: REPEAT_OFFENDER fraud type is ONLY set if fraud_count > 0 (previous fraud).
        If only escalate_count > 0 (previous escalation but no fraud), do NOT set REPEAT_OFFENDER.
        However, we still include fraud_types array - it will just be empty or contain other fraud types.
        """
        # REPEAT_OFFENDER logic: Only set if fraud_count > 0 (previous fraud/rejection)
        # If only escalate_count > 0 (previous escalation), don't set REPEAT_OFFENDER
        fraud_types = []
        fraud_explanations = []
        
        if fraud_count > 0:
            # Customer has previous fraud - set REPEAT_OFFENDER
            fraud_types.append('REPEAT_OFFENDER')
            fraud_explanations.append({
                'type': 'REPEAT_OFFENDER',
                'reasons': [
                    f'Customer has {fraud_count} previous fraud incident(s)',
                    f'Current fraud risk score ({fraud_risk_score:.1%}) exceeds 30% threshold for repeat customers',
                    'Second+ uploads with elevated risk from a customer with fraud history indicate potential fraud pattern'
                ]
            })
        # If fraud_count = 0, fraud_types remains empty (no REPEAT_OFFENDER)
        # The rejection still happens, but without REPEAT_OFFENDER fraud type
        
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Second+ upload rejected: {account_holder_name} has fraud risk score {fraud_risk_score:.1%} > 30%',
            'reasoning': [
                f'Account holder {account_holder_name} has {escalate_count} previous escalation(s)',
                f'Fraud risk score ({fraud_risk_score:.1%}) exceeds 30% threshold for second+ uploads',
                'Second and subsequent uploads with risk > 30% are automatically rejected per policy',
                'This customer was previously escalated, indicating ongoing risk concerns'
            ],
            'key_indicators': [
                f'Customer escalation count: {escalate_count}',
                f'Fraud risk score: {fraud_risk_score:.1%}',
                'Policy: second+ uploads with >30% risk are rejected'
            ],
            'actionable_recommendations': [
                'Block this transaction immediately',
                'Flag customer account for fraud investigation',
                'Review previous escalation history for patterns'
            ],
            'fraud_types': fraud_types,  # Empty if fraud_count = 0, contains REPEAT_OFFENDER if fraud_count > 0
            'fraud_explanations': fraud_explanations  # Empty if fraud_count = 0, contains REPEAT_OFFENDER explanation if fraud_count > 0
        }

    def _create_first_time_escalation(self, account_holder_name: str, is_new_customer: bool = False, fraud_risk_score: float = None) -> Dict:
        """Create escalation response for first-time uploads with fraud risk score > 30%"""
        customer_state = "new customer" if is_new_customer else "customer with no prior escalations"
        risk_text = f" with fraud risk score {fraud_risk_score:.1%}" if fraud_risk_score else ""
        summary_reason = (
            f"Automatic escalation: {account_holder_name} is a {customer_state}{risk_text} > 30%."
        )
        return {
            'recommendation': 'ESCALATE',
            'confidence_score': 1.0,
            'summary': summary_reason,
            'reasoning': [
                f"Account holder {account_holder_name} has no recorded escalations (escalate_count = 0)",
                f'Fraud risk score ({fraud_risk_score:.1%}) exceeds 30% threshold for first uploads' if fraud_risk_score else 'First-time uploads must be escalated for manual review',
                'First-time uploads with fraud risk > 30% must be escalated for manual review',
                'LLM and ML outputs cannot override this customer-history rule'
            ],
            'key_indicators': [
                'Customer escalation count: 0',
                f'Fraud risk score: {fraud_risk_score:.1%}' if fraud_risk_score else 'Policy: first-time uploads require escalation',
                'Policy: first-time uploads with >30% risk require escalation'
            ],
            # For new customers: exclude actionable_recommendations and fraud_types (empty lists)
            'actionable_recommendations': [] if is_new_customer else [
                'Route this bank statement to the manual review queue',
                'Create a customer record if one does not exist',
                'Monitor future uploads for this account holder to enforce repeat-offender rules'
            ],
            'fraud_types': [],  # Always empty for new customers
            'fraud_explanations': []  # Always empty for new customers
        }

    def _create_repeat_offender_rejection(self, account_holder_name: str, fraud_count: int) -> Dict:
        """Create rejection response for repeat offenders (fraud_count > 0)
        
        REPEAT_OFFENDER only applies to customers who have been REJECTED before.
        Customers who were only ESCALATED should go through LLM analysis to identify actual fraud types.
        """
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Automatic rejection: {account_holder_name} is a flagged repeat offender',
            'reasoning': [
                f'Account holder {account_holder_name} has fraud_count = {fraud_count}',
                'Per account-holder-based fraud tracking policy: repeat offenders are automatically rejected',
                'This account holder was previously rejected and is now subject to automatic rejection',
                'LLM analysis skipped - mandatory reject rule applies'
            ],
            'key_indicators': [
                'Repeat offender detected',
                f'Fraud count: {fraud_count}'
            ],
            'actionable_recommendations': [
                'Block this transaction immediately',
                'Flag customer account for fraud investigation',
                'Contact account holder to verify legitimacy of future transactions'
            ],
            'fraud_types': ['REPEAT_OFFENDER'],  # Set fraud type for repeat offenders
            'fraud_explanations': [
                {
                    'type': 'REPEAT_OFFENDER',
                    'reasons': [
                        f'Account holder {account_holder_name} has been rejected {fraud_count} time(s) previously',
                        'Per account-holder-based fraud tracking policy: customers with fraud history (previous rejections) are automatically rejected on subsequent submissions',
                        'This account holder was previously flagged for fraud and is now subject to automatic rejection'
                    ]
                }
            ]
        }

    def _create_fraud_history_rejection(self, account_holder_name: str, fraud_count: int) -> Dict:
        """Create rejection response for customers with fraud history (fraud_count > 0)"""
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Automatic rejection: {account_holder_name} has fraud history',
            'reasoning': [
                f'Account holder {account_holder_name} has fraud_count = {fraud_count}',
                'Per account-holder-based fraud tracking policy: customers with fraud history are automatically rejected',
                'This account holder was previously rejected and is now subject to automatic rejection',
                'LLM analysis skipped - mandatory reject rule applies'
            ],
            'key_indicators': [
                'Fraud history detected',
                f'Fraud count: {fraud_count}'
            ],
            'actionable_recommendations': [
                'Block this transaction immediately',
                'Flag customer account for fraud investigation',
                'Contact account holder to verify legitimacy of future transactions'
            ],
            'fraud_types': [],  # Only LLM provides fraud_types - automatic rejections skip LLM
            'fraud_explanations': []  # Only LLM provides fraud_explanations - automatic rejections skip LLM
        }

    def _create_duplicate_rejection(self, account_number: str, account_holder_name: str) -> Dict:
        """Create rejection response for duplicate bank statements
        
        CRITICAL: This is ONLY called when:
        - Same statement (account_number + statement_period_start) was previously submitted
        - AND the previous submission was REJECTED (confirmed fraud)
        
        If previous was ESCALATED, this method is NOT called - resubmission is allowed.
        """
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Duplicate bank statement submission detected for account {account_number} - previous submission was REJECTED',
            'reasoning': [
                f'Bank statement for account {account_number} from {account_holder_name} was previously submitted and REJECTED (confirmed fraud)',
                'Resubmitting a statement that was already rejected as fraud is a duplicate violation',
                'Duplicate submissions after fraud rejection are automatically rejected per fraud policy',
                'This is a critical fraud indicator - attempting to resubmit a fraudulent document'
            ],
            'key_indicators': [
                'Duplicate statement detected',
                'Previous submission was REJECTED (confirmed fraud)',
                'Same account_number and statement_period_start combination',
                'Resubmission of fraudulent document'
            ],
            'actionable_recommendations': [
                'Block this transaction immediately',
                'Flag customer account for fraud investigation',
                'Investigate potential fraud attempt - resubmitting rejected fraudulent document'
            ],
            'fraud_types': ['FABRICATED_DOCUMENT'],  # Resubmitting a REJECTED statement is a form of document fabrication
            'fraud_explanations': [
                {
                    'type': 'FABRICATED_DOCUMENT',
                    'reasons': [
                        f'Bank statement for account {account_number} from {account_holder_name} was previously submitted and REJECTED as fraud',
                        'Resubmitting a statement that was already rejected as fraudulent violates duplicate policy',
                        'This statement has already been processed and rejected - resubmission indicates deliberate fraud attempt',
                        'Only statements previously REJECTED (confirmed fraud) are considered duplicates - escalated statements can be resubmitted'
                    ]
                }
            ]
        }

    def _parse_json_response(self, ai_response: str) -> Dict:
        """
        Parse JSON from LLM response, handling common formats.
        Tries multiple strategies but raises error if JSON cannot be extracted.
        NO FALLBACK - must return valid JSON or raise error.
        
        Args:
            ai_response: Raw response from LLM
            
        Returns:
            Parsed JSON dict
            
        Raises:
            ValueError: If JSON cannot be parsed from response
        """
        import re
        
        if not ai_response or not ai_response.strip():
            raise ValueError(
                "LLM returned empty response. "
                "LLM must return valid JSON format. "
                "Please check OpenAI API key and network connectivity."
            )
        
        # Strategy 1: Try direct JSON parse
        try:
            return json.loads(ai_response.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from markdown code blocks (```json ... ```)
        json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_block_pattern, ai_response, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Find JSON object in response (look for { ... })
        # Try to find the first complete JSON object
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(ai_response):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found complete JSON object
                    json_str = ai_response[start_idx:i+1]
                    try:
                        return json.loads(json_str.strip())
                    except json.JSONDecodeError:
                        # Try next JSON object
                        start_idx = -1
                        brace_count = 0
                        continue
        
        # Strategy 4: Try to fix common JSON issues (trailing commas, etc.)
        # Remove trailing commas before closing braces/brackets
        cleaned = re.sub(r',\s*}', '}', ai_response)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass
        
        # All strategies failed - raise error with helpful message
        response_preview = ai_response[:1000] if len(ai_response) > 1000 else ai_response
        raise ValueError(
            f"LLM returned invalid JSON response. "
            f"LLM must return valid JSON format. "
            f"Response length: {len(ai_response)} chars. "
            f"Response preview: {response_preview}... "
            f"Please check OpenAI API key and network connectivity. "
            f"LLM analysis is required - no fallback available."
        )

    def _validate_and_format_result(self, result: Dict, ml_analysis: Dict, customer_info: Dict) -> Dict:
        """Validate and format the AI result"""
        # Check if this is a new customer
        is_new_customer = not customer_info.get('customer_id')
        
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
        
        # For new customers: clear fraud_types and actionable_recommendations
        # Only LLM provides these - no fallback to ML
        if is_new_customer:
            validated['fraud_types'] = []
            validated['fraud_explanations'] = []
            validated['actionable_recommendations'] = []
            # Clean up reasoning to remove confusing messages about fraud history
            validated['reasoning'] = [
                reason for reason in validated['reasoning'] 
                if 'fraud history' not in reason.lower() and 'documented fraud' not in reason.lower()
            ]
        
        # For repeat customers: Validate that LLM provided fraud_types and fraud_explanations for REJECT/ESCALATE
        is_repeat_customer = not is_new_customer
        recommendation = validated.get('recommendation', 'UNKNOWN')
        if is_repeat_customer and recommendation in ['REJECT', 'ESCALATE']:
            # LLM MUST provide fraud_types and fraud_explanations for repeat customers with REJECT/ESCALATE
            fraud_types = validated.get('fraud_types', [])
            fraud_explanations = validated.get('fraud_explanations', [])
            
            logger.info(f"Validating LLM response for repeat customer with {recommendation} recommendation:")
            logger.info(f"  - fraud_types provided: {len(fraud_types)} items - {fraud_types}")
            logger.info(f"  - fraud_explanations provided: {len(fraud_explanations)} items - {fraud_explanations}")
            
            if not fraud_types or len(fraud_types) == 0:
                logger.error(
                    f"❌ LLM did not provide fraud_types for repeat customer with {recommendation} recommendation. "
                    f"This is REQUIRED - LLM must identify fraud types for repeat customers. "
                    f"Full result keys: {list(result.keys())}"
                )
            if not fraud_explanations or len(fraud_explanations) == 0:
                logger.error(
                    f"❌ LLM did not provide fraud_explanations for repeat customer with {recommendation} recommendation. "
                    f"This is REQUIRED - LLM must provide fraud explanations for repeat customers. "
                    f"Full result keys: {list(result.keys())}"
                )

        # Validate recommendation value
        if validated['recommendation'] not in ['APPROVE', 'REJECT', 'ESCALATE']:
            logger.warning(f"Invalid recommendation: {validated['recommendation']}, defaulting to ESCALATE")
            validated['recommendation'] = 'ESCALATE'

        # Ensure confidence score is in valid range
        validated['confidence_score'] = max(0.0, min(1.0, validated['confidence_score']))

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


