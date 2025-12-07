"""
Bank Statement Extractor - Complete Fraud Detection Pipeline
Orchestrates: Mindee OCR → Normalization → ML Detection → AI Analysis → Customer Tracking
Completely self-contained - no dependencies on other document analysis modules
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import centralized config and logging
from config import Config
logger = Config.get_logger(__name__)
from typing import Dict, List, Optional, Tuple

# Load environment variables first (if not already loaded)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv already loaded by api_server.py or not available
    pass

# Import Mindee - use ClientV2 API (requires mindee>=4.31.0)
try:
    from mindee import ClientV2, InferenceParameters, PathInput
    MINDEE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Mindee library not properly installed: {e}")
    logger.error("Requires mindee>=4.31.0. Install with: pip install --upgrade 'mindee>=4.31.0'")
    MINDEE_AVAILABLE = False
    ClientV2 = None
    InferenceParameters = None
    PathInput = None

# Import bank statement-specific components from local modules
from .normalization.bank_statement_normalizer_factory import BankStatementNormalizerFactory

# Mindee configuration - read after load_dotenv()
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_BANK_STATEMENT = os.getenv("MINDEE_MODEL_ID_BANK_STATEMENT", "2b6cc7a4-6b0b-4178-a8f8-00c626965d87").strip()

logger.info(f"Mindee API Key loaded: {MINDEE_API_KEY[:20]}..." if MINDEE_API_KEY else "Mindee API Key NOT SET")
logger.info(f"Mindee Model ID: {MINDEE_MODEL_ID_BANK_STATEMENT}")

if not MINDEE_API_KEY:
    logger.warning("MINDEE_API_KEY is not set - bank statement extraction may fail")
    mindee_client = None
elif not MINDEE_AVAILABLE:
    logger.error("Mindee library not available")
    mindee_client = None
else:
    mindee_client = ClientV2(api_key=MINDEE_API_KEY)
    logger.info("Mindee ClientV2 initialized successfully")


class BankStatementExtractor:
    """
    Complete bank statement extraction and fraud analysis pipeline
    Mindee-only OCR → Bank-specific normalization → ML fraud detection → AI decision
    """

    def __init__(self):
        """Initialize all components"""
        # ML Fraud Detector - will be imported when ml module is ready
        try:
            from .ml.bank_statement_fraud_detector import BankStatementFraudDetector
            model_dir = os.getenv("ML_MODEL_DIR", "models")
            self.ml_detector = BankStatementFraudDetector(model_dir=model_dir)
            logger.info("Initialized BankStatementFraudDetector")
        except ImportError:
            logger.warning("ML fraud detector not available - ML analysis will be skipped")
            self.ml_detector = None

        # AI Agent - will be imported when ai module is ready
        try:
            from .ai.bank_statement_fraud_analysis_agent import BankStatementFraudAnalysisAgent
            from .ai.bank_statement_tools import BankStatementDataAccessTools
            openai_key = os.getenv('OPENAI_API_KEY')
            self.ai_agent = None
            if openai_key:
                data_tools = BankStatementDataAccessTools()
                self.ai_agent = BankStatementFraudAnalysisAgent(
                    api_key=openai_key,
                    model=os.getenv('AI_MODEL', 'o4-mini'),
                    data_tools=data_tools
                )
                logger.info("Initialized BankStatementFraudAnalysisAgent")
            else:
                logger.warning("OPENAI_API_KEY not set - AI analysis will be skipped")
        except ImportError:
            logger.warning("AI agent not available - AI analysis will be skipped")
            self.ai_agent = None

    def extract_and_analyze(self, file_path: str) -> Dict:
        """
        Complete bank statement analysis pipeline - NO EARLY EXITS
        Always runs full evaluation regardless of missing fields

        Args:
            file_path: Path to bank statement image/PDF file

        Returns:
            Complete analysis results dict with all rule outputs, issues, and final decision
        """
        logger.info(f"Starting bank statement analysis for: {file_path}")

        # Stage 1: OCR Extraction (Mindee only)
        extracted_data, raw_text = self._extract_with_mindee(file_path)
        logger.info(f"Extracted data from Mindee: {list(extracted_data.keys())}")

        # Stage 2: Normalization
        bank_name = extracted_data.get('bank_name', '')
        normalized_data = self._normalize_data(extracted_data, bank_name)

        # Stage 3: Validation Rules (collects issues but doesn't exit early)
        validation_issues = self._collect_validation_issues(normalized_data)
        logger.info(f"Validation issues found: {len(validation_issues)}")

        # Stage 4: ML Fraud Detection
        ml_analysis = self._run_ml_fraud_detection(normalized_data, raw_text)
        # Validate ml_analysis is not None before accessing
        if ml_analysis is None:
            raise RuntimeError("ML fraud detection returned None. This should not happen - ML models are required.")
        logger.info(f"ML fraud analysis complete: {ml_analysis.get('risk_level', 'UNKNOWN')}")

        # Stage 5: Customer History & Duplicate Detection (continue regardless)
        customer_info = self._get_customer_info(normalized_data)
        duplicate_check = self._check_duplicate(normalized_data)
        if duplicate_check:
            logger.warning("Duplicate bank statement detected - will be included in issues")
            validation_issues.append("Duplicate bank statement submission detected")

        # Stage 6: AI Fraud Analysis (LLM is required - will raise error if unavailable)
        ai_analysis = self._run_ai_analysis(normalized_data, ml_analysis, customer_info)
        logger.info(f"AI analysis complete: {ai_analysis.get('recommendation', 'UNKNOWN')}")

        # Stage 7: Generate Anomalies
        anomalies = self._generate_anomalies(normalized_data, ml_analysis, ai_analysis)

        # Stage 8: Calculate Confidence Score
        confidence_score = self._calculate_confidence(normalized_data, ml_analysis, ai_analysis)

        # Stage 9: Determine Final Decision Based on All Collected Issues
        overall_decision = self._determine_final_decision(
            validation_issues=validation_issues,
            ml_analysis=ml_analysis,
            ai_analysis=ai_analysis,
            normalized_data=normalized_data
        )

        # Stage 10: Build Final Response with ALL results
        return self._build_complete_response(
            extracted_data=extracted_data,
            normalized_data=normalized_data,
            ml_analysis=ml_analysis,
            ai_analysis=ai_analysis,
            customer_info=customer_info,
            anomalies=anomalies,
            confidence_score=confidence_score,
            validation_issues=validation_issues,
            overall_decision=overall_decision,
            duplicate_detected=duplicate_check,
            raw_text=raw_text
        )

    def _extract_with_mindee(self, file_path: str) -> Tuple[Dict, str]:
        """Extract bank statement data using Mindee API only (no fallback)"""
        if not mindee_client:
            raise RuntimeError("Mindee client not initialized. Check API key and installation.")

        try:
            # Use ClientV2 API with InferenceParameters
            logger.info(f"Extracting with Mindee using model ID: {MINDEE_MODEL_ID_BANK_STATEMENT}")
            
            # Create inference parameters with the model ID
            params = InferenceParameters(model_id=MINDEE_MODEL_ID_BANK_STATEMENT, raw_text=True)
            input_source = PathInput(file_path)
            
            # Parse document using ClientV2 with model ID
            logger.info(f"Calling Mindee API with model ID...")
            response = mindee_client.enqueue_and_get_inference(input_source, params)
            
            # Extract fields from the response
            logger.info(f"Processing Mindee response...")
            
            if not response or not hasattr(response, 'inference'):
                raise ValueError("Invalid Mindee API response: missing inference object")
            
            if not response.inference or not hasattr(response.inference, 'result'):
                raise ValueError("Invalid Mindee API response: missing result object")
            
            result = response.inference.result
            if not result:
                raise ValueError("Invalid Mindee API response: result is None")
            
            fields = result.fields or {}
            logger.info(f"Extracted {len(fields)} fields from Mindee response")
            
            # Get raw text
            raw_text = getattr(result, "raw_text", "") or ""
            if raw_text and not isinstance(raw_text, str):
                raw_text = str(raw_text)
            
            # Convert Mindee fields to simple dict
            extracted = {}
            field_mapping = {
                'account_holder_names': 'account_holder_names',
                'account_holder_name': 'account_holder_name',
                'account_number': 'account_number',
                'account_type': 'account_type',
                'bank_name': 'bank_name',
                'bank_address': 'bank_address',
                'beginning_balance': 'beginning_balance',
                'ending_balance': 'ending_balance',
                'currency': 'currency',
                'list_of_transactions': 'list_of_transactions',
                'statement_date': 'statement_date',
                'statement_period_end_date': 'statement_period_end_date',
                'statement_period_start_date': 'statement_period_start_date',
                'total_credits': 'total_credits',
                'total_debits': 'total_debits',
            }

            for name, field_data in fields.items():
                logger.debug(f"Processing field {name}: {field_data} (type: {type(field_data)})")

                # Extract the actual value from SimpleField object
                value = None
                if hasattr(field_data, 'value'):
                    # SimpleField object - extract the value
                    value = field_data.value
                elif hasattr(field_data, 'items'):
                    # List field - extract items
                    values = []
                    for item in field_data.items:
                        if hasattr(item, 'value'):
                            values.append(item.value)
                        elif hasattr(item, 'fields'):
                            # Nested object (like transaction or address)
                            nested_dict = {}
                            for k, v in item.fields.items():
                                if hasattr(v, 'value'):
                                    nested_dict[k] = v.value
                                else:
                                    nested_dict[k] = v
                            values.append(nested_dict)
                        else:
                            values.append(item)
                    value = values
                elif hasattr(field_data, 'fields'):
                    # Nested object (like address)
                    nested_dict = {}
                    for k, v in field_data.fields.items():
                        if hasattr(v, 'value'):
                            nested_dict[k] = v.value
                        else:
                            nested_dict[k] = v
                    value = nested_dict
                else:
                    # Already a plain value
                    value = field_data

                # Map field name to standard name if needed
                standard_name = field_mapping.get(name, name)
                extracted[standard_name] = value

                logger.info(f"  → Extracted {name}: {value}")

            logger.info(f"Successfully extracted {len(extracted)} fields from Mindee: {list(extracted.keys())}")
            logger.info(f"Extracted data summary: {extracted}")
            return extracted, raw_text

        except Exception as e:
            logger.error(f"Mindee extraction failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to extract bank statement data: {str(e)}") from e

    def _normalize_data(self, extracted_data: Dict, bank_name: str) -> Dict:
        """Normalize bank statement data using bank-specific normalizer"""
        if not bank_name:
            logger.warning("Bank name not detected - skipping normalization")
            return extracted_data

        # Check if bank is in database (case-insensitive)
        try:
            from .utils.bank_list_loader import is_supported_bank
            bank_is_supported = is_supported_bank(bank_name)
        except ImportError:
            # Fallback: check against normalizer factory
            bank_is_supported = BankStatementNormalizerFactory.is_supported_bank(bank_name)

        normalizer = BankStatementNormalizerFactory.get_normalizer(bank_name)

        if normalizer:
            logger.info(f"Normalizing data for bank: {bank_name}")
            normalized_obj = normalizer.normalize(extracted_data)
            normalized_data = normalized_obj.to_dict()

            # Add validation flags (use database check for is_supported_bank)
            normalized_data['is_supported_bank'] = bank_is_supported  # Use database check
            normalized_data['is_valid'] = normalized_obj.is_valid()
            normalized_data['completeness_score'] = normalized_obj.get_completeness_score()
            normalized_data['critical_missing_fields'] = normalized_obj.get_critical_missing_fields()

            logger.info(f"Normalization complete - Completeness: {normalized_data['completeness_score']}")
            return normalized_data
        else:
            # No specific normalizer, but bank might still be in database
            # Use generic normalization (Chase normalizer as template for common fields)
            logger.info(f"No specific normalizer for bank: {bank_name}, using generic normalization")
            
            # Use Chase normalizer as template (it handles common fields)
            from .normalization.chase import ChaseNormalizer
            generic_normalizer = ChaseNormalizer()
            # Override bank name
            generic_normalizer.bank_name = bank_name
            
            normalized_obj = generic_normalizer.normalize(extracted_data)
            normalized_data = normalized_obj.to_dict()
            
            # Use database check for is_supported_bank (not normalizer's check)
            normalized_data['is_supported_bank'] = bank_is_supported
            normalized_data['is_valid'] = normalized_obj.is_valid()
            normalized_data['completeness_score'] = normalized_obj.get_completeness_score()
            normalized_data['critical_missing_fields'] = normalized_obj.get_critical_missing_fields()
            
            logger.info(f"Generic normalization complete - Completeness: {normalized_data['completeness_score']}")
            return normalized_data

    def _collect_validation_issues(self, data: Dict) -> List[str]:
        """
        Collect validation issues without exiting early
        Returns list of issues found
        """
        issues = []

        # Check critical fields
        if not data.get('bank_name'):
            issues.append("Missing bank name")
        if not data.get('account_number'):
            issues.append("Missing account number")
        if not data.get('account_holder_name'):
            issues.append("Missing account holder name")
        if not data.get('statement_period_start_date'):
            issues.append("Missing statement period start date")
        if not data.get('statement_period_end_date'):
            issues.append("Missing statement period end date")
        if not data.get('beginning_balance'):
            issues.append("Missing beginning balance")
        if not data.get('ending_balance'):
            issues.append("Missing ending balance")

        # Check balance consistency
        beginning = data.get('beginning_balance', {})
        ending = data.get('ending_balance', {})
        if isinstance(beginning, dict) and isinstance(ending, dict):
            beg_value = beginning.get('value', 0)
            end_value = ending.get('value', 0)
            
            # Get total_credits and total_debits from data
            total_credits = data.get('total_credits', {}).get('value', 0) if isinstance(data.get('total_credits'), dict) else 0
            total_debits = data.get('total_debits', {}).get('value', 0) if isinstance(data.get('total_debits'), dict) else 0
            
            # ALWAYS calculate total_credits and total_debits from transactions to verify accuracy
            calculated_credits = 0.0
            calculated_debits = 0.0
            
            if data.get('transactions'):
                transactions = data.get('transactions', [])
                
                for txn in transactions:
                    if isinstance(txn, dict):
                        amount = txn.get('amount', {})
                        if isinstance(amount, dict):
                            txn_value = amount.get('value', 0.0)
                        elif isinstance(amount, (int, float)):
                            txn_value = float(amount)
                        else:
                            continue
                        
                        if txn_value > 0:
                            calculated_credits += txn_value
                        elif txn_value < 0:
                            calculated_debits += abs(txn_value)
            
            # Use calculated values if they produce a better balance match
            if calculated_credits > 0 or calculated_debits > 0:
                # Calculate balance with Mindee values
                mindee_expected = beg_value + total_credits - total_debits
                mindee_diff = abs(end_value - mindee_expected)
                
                # Calculate balance with transaction-calculated values
                calc_expected = beg_value + calculated_credits - calculated_debits
                calc_diff = abs(end_value - calc_expected)
                
                # Use calculated values if they produce a better match (smaller difference)
                if calc_diff < mindee_diff:
                    total_credits = calculated_credits
                    total_debits = calculated_debits
            elif total_credits == 0 and calculated_credits > 0:
                # Fallback: use calculated if original is zero
                total_credits = calculated_credits
            elif total_debits == 0 and calculated_debits > 0:
                # Fallback: use calculated if original is zero
                total_debits = calculated_debits
            
            # Check if balances are consistent
            expected_ending = beg_value + total_credits - total_debits
            if abs(end_value - expected_ending) > 0.01:  # Allow small rounding differences
                issues.append(f"Balance inconsistency: Expected ending balance ${expected_ending:,.2f}, found ${end_value:,.2f}")

        # Check transaction count
        transactions = data.get('transactions', [])
        if not transactions or len(transactions) == 0:
            issues.append("No transactions found in statement")

        return issues

    def _run_ml_fraud_detection(self, data: Dict, raw_text: str) -> Dict:
        """Run ML fraud detection - ML detector is REQUIRED, no fallback"""
        if not self.ml_detector:
            raise RuntimeError(
                "ML detector is not available. Bank statement fraud detection requires ML models. "
                "Please ensure ML detector is properly initialized."
            )

        # NO FALLBACK - if ML fails, raise error
        ml_analysis = self.ml_detector.predict_fraud(data, raw_text)
        
        # Validate that ML returned a dict (not None)
        if ml_analysis is None:
            raise RuntimeError(
                "ML fraud detection returned None. ML models must return a valid analysis dict. "
                "Please check ML model initialization and prediction logic."
            )
        
        if not isinstance(ml_analysis, dict):
            raise RuntimeError(
                f"ML fraud detection returned invalid type: {type(ml_analysis)}. "
                f"Expected dict, got {type(ml_analysis)}. "
                f"ML models must return a valid analysis dict."
            )
        
        return ml_analysis

    def _get_customer_info(self, data: Dict) -> Dict:
        """Get customer history from database"""
        # Try multiple sources for account holder name
        account_holder_name = (
            data.get('account_holder_name') or
            data.get('account_holder') or
            (data.get('account_holder_names', [])[0] if isinstance(data.get('account_holder_names'), list) and len(data.get('account_holder_names', [])) > 0 else None)
        )
        
        if not account_holder_name:
            logger.warning("Account holder name not found - cannot lookup customer history")
            return {}

        try:
            from .ai.bank_statement_tools import BankStatementDataAccessTools
            data_tools = BankStatementDataAccessTools()
            customer_info = data_tools.get_customer_history(account_holder_name)
            logger.info(f"Customer lookup for '{account_holder_name}': escalate_count={customer_info.get('escalate_count', 0)}, fraud_count={customer_info.get('fraud_count', 0)}")
            return customer_info
        except Exception as e:
            logger.error(f"Failed to get customer info: {e}")
            return {}

    def _check_duplicate(self, data: Dict) -> bool:
        """Check for duplicate bank statement submission"""
        account_number = data.get('account_number')
        statement_period_start = data.get('statement_period_start_date')
        
        # Try multiple sources for account holder name
        account_holder_name = (
            data.get('account_holder_name') or
            data.get('account_holder') or
            (data.get('account_holder_names', [])[0] if isinstance(data.get('account_holder_names'), list) and len(data.get('account_holder_names', [])) > 0 else None)
        )

        if not account_number or not statement_period_start or not account_holder_name:
            logger.warning(f"Duplicate check skipped - missing data: account_number={bool(account_number)}, statement_period_start={bool(statement_period_start)}, account_holder_name={bool(account_holder_name)}")
            return False

        try:
            from .ai.bank_statement_tools import BankStatementDataAccessTools
            data_tools = BankStatementDataAccessTools()
            is_duplicate = data_tools.check_duplicate(account_number, statement_period_start, account_holder_name)
            if is_duplicate:
                logger.warning(f"Duplicate detected: {account_number} from {account_holder_name} for period {statement_period_start}")
            return is_duplicate
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False

    def _run_ai_analysis(self, data: Dict, ml_analysis: Dict, customer_info: Dict) -> Dict:
        """Run AI fraud analysis - LLM is required, no fallback"""
        if not self.ai_agent:
            raise RuntimeError(
                "AI agent (LLM) not available. "
                "LLM analysis is required for bank statement fraud detection. "
                "Please check OpenAI API key configuration."
            )

        # Try multiple sources for account holder name
        account_holder_name = (
            data.get('account_holder_name') or
            data.get('account_holder') or
            (data.get('account_holder_names', [])[0] if isinstance(data.get('account_holder_names'), list) and len(data.get('account_holder_names', [])) > 0 else None)
        )
        logger.info(f"Using account_holder_name for AI analysis: {account_holder_name}")
        
        # LLM analysis is required - will raise error if it fails
        ai_analysis = self.ai_agent.analyze_fraud(
            extracted_data=data,
            ml_analysis=ml_analysis,
            account_holder_name=account_holder_name
        )
        return ai_analysis

    def _generate_anomalies(self, data: Dict, ml_analysis: Dict, ai_analysis: Dict) -> List[str]:
        """Generate comprehensive anomaly list"""
        anomalies = []

        # From ML analysis
        ml_anomalies = ml_analysis.get('anomalies', [])
        anomalies.extend(ml_anomalies)

        # From AI analysis (LLM is required)
        ai_factors = ai_analysis.get('key_indicators', [])
        anomalies.extend(ai_factors)

        # From validation
        if not data.get('is_supported_bank', True):
            # Only mark as unsupported if not in database (case-insensitive check)
            try:
                from .utils.bank_list_loader import is_supported_bank
                bank_name = data.get('bank_name')
                if bank_name and not is_supported_bank(bank_name):
                    anomalies.append(f"Unsupported bank: {bank_name}")
            except ImportError:
                # Fallback: use is_supported_bank flag
                if not data.get('is_supported_bank', False):
                    anomalies.append(f"Unsupported bank: {data.get('bank_name')}")

        critical_missing = data.get('critical_missing_fields', [])
        if critical_missing:
            anomalies.append(f"Missing critical fields: {', '.join(critical_missing)}")

        # Balance checks
        ending_balance = data.get('ending_balance', {})
        if isinstance(ending_balance, dict):
            balance_value = ending_balance.get('value', 0)
            if balance_value < 0:
                anomalies.append(f"Negative ending balance: ${balance_value:,.2f}")

        # Transaction checks
        transactions = data.get('transactions', [])
        if transactions:
            # Check for suspicious transaction patterns
            # Handle both dict format {'amount': {'value': float}} and direct format {'amount': float}
            def get_amount_value(txn):
                """Safely extract amount value from transaction"""
                if not isinstance(txn, dict):
                    return 0
                amount = txn.get('amount')
                if amount is None:
                    return 0
                # If amount is a dict with 'value' key
                if isinstance(amount, dict):
                    return amount.get('value', 0)
                # If amount is a direct numeric value
                if isinstance(amount, (int, float)):
                    return abs(float(amount))  # Use absolute value for comparison
                return 0
            
            large_transactions = [t for t in transactions if get_amount_value(t) > 10000]
            if large_transactions:
                anomalies.append(f"{len(large_transactions)} large transactions (>$10,000) detected")

        return anomalies

    def _calculate_confidence(self, data: Dict, ml_analysis: Dict, ai_analysis: Dict) -> float:
        """Calculate overall confidence score"""
        scores = []

        # ML confidence
        ml_confidence = ml_analysis.get('model_confidence', 0.0)
        scores.append(ml_confidence)

        # AI confidence (LLM is required)
        ai_confidence = ai_analysis.get('confidence_score', 0.0)
        scores.append(ai_confidence)

        # Data completeness
        completeness = data.get('completeness_score', 0.0)
        scores.append(completeness)

        # Average of all scores
        if scores:
            return round(sum(scores) / len(scores), 2)
        return 0.5

    def _determine_final_decision(
        self,
        validation_issues: List[str],
        ml_analysis: Dict,
        ai_analysis: Dict,
        normalized_data: Dict
    ) -> str:
        """Determine final decision based on all collected information"""
        # Priority: AI recommendation > ML risk level > Validation issues
        # LLM is required, so ai_analysis is always present

        ai_recommendation = ai_analysis.get('recommendation')
        if ai_recommendation in ['APPROVE', 'REJECT', 'ESCALATE']:
            return ai_recommendation

        # Fallback to ML risk level
        risk_level = ml_analysis.get('risk_level', 'UNKNOWN')
        if risk_level == 'CRITICAL':
            return 'REJECT'
        elif risk_level == 'HIGH':
            return 'ESCALATE'
        elif risk_level == 'MEDIUM':
            return 'ESCALATE'
        else:
            # Check validation issues
            if len(validation_issues) > 3:
                return 'ESCALATE'
            return 'APPROVE'

    def _build_complete_response(
        self,
        extracted_data: Dict,
        normalized_data: Dict,
        ml_analysis: Dict,
        ai_analysis: Dict,
        customer_info: Dict,
        anomalies: List[str],
        confidence_score: float,
        validation_issues: List[str],
        overall_decision: str,
        duplicate_detected: bool,
        raw_text: str
    ) -> Dict:
        """Build complete analysis response"""
        # Ensure account_holder_name is in both extracted_data and normalized_data for consistency
        account_holder_name = (
            normalized_data.get('account_holder_name') or
            extracted_data.get('account_holder_name') or
            extracted_data.get('account_holder') or
            (extracted_data.get('account_holder_names', [])[0] if isinstance(extracted_data.get('account_holder_names'), list) and len(extracted_data.get('account_holder_names', [])) > 0 else None)
        )
        
        if account_holder_name:
            extracted_data['account_holder_name'] = account_holder_name
            normalized_data['account_holder_name'] = account_holder_name
        
        return {
            'status': 'success',
            'document_type': 'bank_statement',
            'extracted_data': extracted_data,
            'normalized_data': normalized_data,
            'ml_analysis': ml_analysis,
            'ai_analysis': ai_analysis,  # LLM is required, so always present
            'customer_info': customer_info or {},  # Include customer_info for frontend to determine new vs repeat
            'fraud_risk_score': ml_analysis.get('fraud_risk_score', 0.0),
            'risk_level': ml_analysis.get('risk_level', 'UNKNOWN'),
            'model_confidence': ml_analysis.get('model_confidence', 0.0),
            'ai_recommendation': ai_analysis.get('recommendation', 'UNKNOWN'),  # LLM is required
            'ai_confidence': ai_analysis.get('confidence_score', 0.0),  # LLM is required
            'anomalies': anomalies,
            'validation_issues': validation_issues,
            'confidence_score': confidence_score,
            'overall_decision': overall_decision,
            'duplicate_detected': duplicate_detected,
            'raw_text': raw_text,
            'timestamp': datetime.utcnow().isoformat()
        }

