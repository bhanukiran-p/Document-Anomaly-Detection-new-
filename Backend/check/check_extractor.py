"""
Check Extractor - Complete Fraud Detection Pipeline
Orchestrates: Mindee OCR → Normalization → ML Detection → AI Analysis → Customer Tracking
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import Mindee - use ClientV2 API (requires mindee>=4.31.0)
try:
    from mindee import ClientV2, InferenceParameters, PathInput
    MINDEE_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).error(f"Mindee library not properly installed: {e}")
    logging.getLogger(__name__).error("Requires mindee>=4.31.0. Install with: pip install --upgrade 'mindee>=4.31.0'")
    MINDEE_AVAILABLE = False
    ClientV2 = None
    InferenceParameters = None
    PathInput = None

# Import check-specific components from local modules
from .normalization.check_normalizer_factory import CheckNormalizerFactory
from .ml.check_fraud_detector import CheckFraudDetector
from .ai.check_fraud_analysis_agent import CheckFraudAnalysisAgent
from .ai.check_tools import CheckDataAccessTools

logger = logging.getLogger(__name__)

# Mindee configuration - read after load_dotenv()
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_CHECK = os.getenv("MINDEE_MODEL_ID_CHECK", "046edc76-e8a4-4e11-a9a3-bb8632250446").strip()
# Endpoint name is the "API name" from Mindee API Builder Settings page
# Try model name first, then model ID as fallback
MINDEE_ENDPOINT_NAME_CHECK = os.getenv("MINDEE_ENDPOINT_NAME_CHECK", "").strip() or "bank-check" or MINDEE_MODEL_ID_CHECK
# Account name is your organization's username on Mindee API Builder
# From screenshot: "Vikram Ramanathan's Organization" - try slugified version
MINDEE_ACCOUNT_NAME = os.getenv("MINDEE_ACCOUNT_NAME", "").strip() or "vikram-ramanathan"

logger.info(f"Mindee API Key loaded: {MINDEE_API_KEY[:20]}..." if MINDEE_API_KEY else "Mindee API Key NOT SET")
logger.info(f"Mindee Model ID: {MINDEE_MODEL_ID_CHECK}")
logger.info(f"Mindee Endpoint Name: {MINDEE_ENDPOINT_NAME_CHECK}")
logger.info(f"Mindee Account Name: {MINDEE_ACCOUNT_NAME or 'Not set (will use default)'}")

if not MINDEE_API_KEY:
    logger.warning("MINDEE_API_KEY is not set - check extraction may fail")
    mindee_client = None
elif not MINDEE_AVAILABLE:
    logger.error("Mindee library not available")
    mindee_client = None
else:
    mindee_client = ClientV2(api_key=MINDEE_API_KEY)
    logger.info("Mindee ClientV2 initialized successfully")


class CheckExtractor:
    """
    Complete check extraction and fraud analysis pipeline
    Mindee-only OCR → Bank-specific normalization → ML fraud detection → AI decision
    """

    def __init__(self):
        """Initialize all components"""
        # ML Fraud Detector
        model_dir = os.getenv("ML_MODEL_DIR", "ml_models")
        self.ml_detector = CheckFraudDetector(model_dir=model_dir)
        logger.info("Initialized CheckFraudDetector")

        # AI Agent
        openai_key = os.getenv('OPENAI_API_KEY')
        self.ai_agent = None
        if openai_key:
            data_tools = CheckDataAccessTools()
            self.ai_agent = CheckFraudAnalysisAgent(
                api_key=openai_key,
                model=os.getenv('AI_MODEL', 'o4-mini'),
                data_tools=data_tools
            )
            logger.info("Initialized CheckFraudAnalysisAgent")
        else:
            logger.warning("OPENAI_API_KEY not set - AI analysis will be skipped")

    def extract_and_analyze(self, image_path: str) -> Dict:
        """
        Complete check analysis pipeline - NO EARLY EXITS
        Always runs full evaluation regardless of missing fields

        Args:
            image_path: Path to check image file

        Returns:
            Complete analysis results dict with all rule outputs, issues, and final decision
        """
        logger.info(f"Starting check analysis for: {image_path}")

        # Stage 1: OCR Extraction (Mindee only)
        extracted_data, raw_text = self._extract_with_mindee(image_path)
        logger.info(f"Extracted data from Mindee: {list(extracted_data.keys())}")

        # Stage 2: Normalization
        bank_name = extracted_data.get('bank_name', '')
        normalized_data = self._normalize_data(extracted_data, bank_name)

        # Stage 3: Validation Rules (collects issues but doesn't exit early)
        validation_issues = self._collect_validation_issues(normalized_data)
        logger.info(f"Validation issues found: {len(validation_issues)}")

        # Stage 4: ML Fraud Detection
        ml_analysis = self._run_ml_fraud_detection(normalized_data, raw_text)
        logger.info(f"ML fraud analysis complete: {ml_analysis.get('risk_level')}")

        # Stage 5: Customer History & Duplicate Detection (continue regardless)
        customer_info = self._get_customer_info(normalized_data)
        duplicate_check = self._check_duplicate(normalized_data)
        if duplicate_check:
            logger.warning("Duplicate check detected - will be included in issues")
            validation_issues.append("Duplicate check submission detected")

        # Stage 6: AI Fraud Analysis (always runs unless initialization failed)
        ai_analysis = self._run_ai_analysis(normalized_data, ml_analysis, customer_info)
        logger.info(f"AI analysis complete: {ai_analysis.get('recommendation') if ai_analysis else 'N/A'}")

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
            anomalies=anomalies,
            confidence_score=confidence_score,
            validation_issues=validation_issues,
            overall_decision=overall_decision,
            duplicate_detected=duplicate_check,
            raw_text=raw_text
        )

    def _extract_with_mindee(self, file_path: str) -> Tuple[Dict, str]:
        """Extract check data using Mindee API only (no fallback)"""
        if not mindee_client:
            raise RuntimeError("Mindee client not initialized. Check API key and installation.")

        try:
            # Use ClientV2 API with InferenceParameters (as shown in Mindee API docs)
            logger.info(f"Extracting with Mindee using model ID: {MINDEE_MODEL_ID_CHECK}")
            
            # Create inference parameters with the model ID (as per API docs)
            params = InferenceParameters(model_id=MINDEE_MODEL_ID_CHECK, raw_text=True)
            input_source = PathInput(file_path)
            
            # Parse document using ClientV2 with model ID (as per API docs)
            logger.info(f"Calling Mindee API with model ID...")
            response = mindee_client.enqueue_and_get_inference(input_source, params)
            
            # Extract fields from the response (as per API docs structure)
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
            
            # Convert to expected format (matching the old format)
            raw_response = {
                'inference': {
                    'result': {
                        'fields': fields
                    }
                }
            }
            
            raw_response_data = raw_response

            # Parse JSON string response if needed
            if isinstance(raw_response_data, str):
                raw_response = json.loads(raw_response_data)
                logger.info(f"Parsed JSON response successfully")
            else:
                raw_response = raw_response_data
                logger.info(f"Response was already a dict")

            logger.info(f"Raw response keys: {list(raw_response.keys()) if isinstance(raw_response, dict) else 'Not a dict'}")
            logger.info(f"Raw response type: {type(raw_response)}")
            if raw_response and isinstance(raw_response, dict):
                logger.info(f"Raw response sample: {str(raw_response)[:1000]}")

            if not raw_response or 'inference' not in raw_response:
                raise ValueError(f"Invalid Mindee API response - no inference in response. Keys: {list(raw_response.keys()) if isinstance(raw_response, dict) else 'unknown'}")

            inference = raw_response['inference']
            if not inference:
                raise ValueError("Invalid Mindee API response - inference is empty")

            logger.info(f"Inference keys: {list(inference.keys()) if isinstance(inference, dict) else 'Not a dict'}")

            # ClientV2 returns fields inside inference.result.fields
            result = inference.get('result', {}) if isinstance(inference, dict) else {}
            logger.info(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            fields = result.get('fields', {}) if isinstance(result, dict) else {}
            logger.info(f"Fields type: {type(fields)}, count: {len(fields) if isinstance(fields, dict) else 'N/A'}")

            if not fields:
                logger.warning(f"No fields found in Mindee response. Result: {result}")

            # Convert Mindee fields to simple dict and normalize field names
            extracted = {}
            field_mapping = {
                'number_amount': 'amount_numeric',
                'word_amount': 'amount_written',
                'pay_to': 'payee_name',
                'signature': 'signature_detected',  # Note: Mindee returns boolean
                'amount_in_words': 'amount_written',
                'sender_name': 'payer_name',
                'sender_address': 'payer_address',
                'recipient': 'payee_name',
            }

            for name, field_data in fields.items():
                logger.debug(f"Processing field {name}: {field_data} (type: {type(field_data)})")

                # Extract the actual value from SimpleField object
                value = None
                if hasattr(field_data, 'value'):
                    # SimpleField object - extract the value
                    value = field_data.value
                elif isinstance(field_data, dict):
                    if 'value' in field_data:
                        value = field_data['value']
                    elif 'values' in field_data:
                        value = field_data['values']
                    elif 'content' in field_data:
                        value = field_data['content']
                    else:
                        logger.warning(f"  → Field {name} has no value/values/content. Keys: {list(field_data.keys())}")
                        continue
                else:
                    # Already a plain value
                    value = field_data

                # Map field name to standard name if needed
                standard_name = field_mapping.get(name, name)
                extracted[standard_name] = value

                if standard_name != name:
                    logger.info(f"  → Extracted {name} → {standard_name}: {value}")
                else:
                    logger.info(f"  → Extracted {name}: {value}")

            # Get raw OCR text (ClientV2 doesn't include OCR in the response)
            raw_text = ""
            # For now, use extracted field values as raw text
            if extracted:
                raw_text = " ".join([str(v) for v in extracted.values() if v])

            logger.info(f"Successfully extracted {len(extracted)} fields from Mindee: {list(extracted.keys())}")
            logger.info(f"Extracted data summary: {extracted}")
            return extracted, raw_text

        except Exception as e:
            logger.error(f"Mindee extraction failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to extract check data: {str(e)}") from e

    def _normalize_data(self, extracted_data: Dict, bank_name: str) -> Dict:
        """Normalize check data using bank-specific normalizer"""
        if not bank_name:
            logger.warning("Bank name not detected - skipping normalization")
            return extracted_data

        normalizer = CheckNormalizerFactory.get_normalizer(bank_name)

        if normalizer:
            logger.info(f"Normalizing data for bank: {bank_name}")
            normalized_obj = normalizer.normalize(extracted_data)
            normalized_data = normalized_obj.to_dict()

            # Add validation flags
            normalized_data['is_supported_bank'] = normalized_obj.is_supported_bank()
            normalized_data['is_valid'] = normalized_obj.is_valid()
            normalized_data['completeness_score'] = normalized_obj.get_completeness_score()
            normalized_data['critical_missing_fields'] = normalized_obj.get_critical_missing_fields()

            logger.info(f"Normalization complete - Completeness: {normalized_data['completeness_score']}")
            return normalized_data
        else:
            logger.warning(f"No normalizer found for bank: {bank_name}")
            # Mark as unsupported bank
            extracted_data['is_supported_bank'] = False
            extracted_data['bank_name'] = bank_name
            return extracted_data

    def _collect_validation_issues(self, data: Dict) -> List[str]:
        """
        Collect all validation issues without early termination
        Returns a list of all issues found - pipeline continues regardless
        """
        issues = []

        # 1. Check signature_detected field (boolean, not detected)
        # Mindee returns 'signature' field which gets mapped to 'signature_detected'
        # Also check 'signature_present' for backwards compatibility
        signature_detected = data.get('signature_detected', data.get('signature_present', False))
        logger.info(f"Signature check: signature_detected={signature_detected}, raw value={data.get('signature_detected', 'NOT FOUND')}")
        if not signature_detected:
            issues.append("Missing signature - required for check validation")
            logger.warning("Signature not detected")

        # 2. Unsupported bank
        if not data.get('is_supported_bank', False):
            bank_name = data.get('bank_name', 'Unknown')
            issues.append(f"Unsupported bank: {bank_name}. Only Bank of America and Chase are accepted.")

        # 3. Missing critical fields
        critical_missing = data.get('critical_missing_fields', [])
        if len(critical_missing) >= 3:
            issues.append(f"Too many critical fields missing: {', '.join(critical_missing)}")
        elif critical_missing:
            issues.append(f"Missing critical fields: {', '.join(critical_missing)}")

        # 4. Missing check number
        if not data.get('check_number'):
            issues.append("Check number missing - required for processing")

        # 5. Missing payer or payee
        if not data.get('payer_name'):
            issues.append("Payer name missing - required field")
        if not data.get('payee_name'):
            issues.append("Payee name missing - required field")

        # 6. Same payer and payee (can't pay yourself)
        payer = str(data.get('payer_name', '')).lower().strip()
        payee = str(data.get('payee_name', '')).lower().strip()
        if payer and payee and payer == payee:
            issues.append("Payer and payee cannot be the same person")

        # 7. Check amount validations
        amount_dict = data.get('amount_numeric', {})
        if isinstance(amount_dict, dict):
            amount = amount_dict.get('value', 0)
        else:
            amount = amount_dict or 0

        if amount > 10000:
            issues.append(f"High amount: ${amount:,.2f} - requires additional verification")

        # Log all issues collected (for debugging)
        if issues:
            logger.info(f"Validation issues collected: {issues}")
        else:
            logger.info("No validation issues found")

        return issues

    def _run_ml_fraud_detection(self, data: Dict, raw_text: str) -> Dict:
        """Run ML fraud detection"""
        try:
            ml_analysis = self.ml_detector.predict_fraud(data, raw_text)
            return ml_analysis
        except Exception as e:
            logger.error(f"ML fraud detection failed: {e}", exc_info=True)
            return {
                'fraud_risk_score': 0.5,
                'risk_level': 'UNKNOWN',
                'model_confidence': 0.0,
                'error': str(e),
                'anomalies': []
            }

    def _get_customer_info(self, data: Dict) -> Dict:
        """Get customer history from database"""
        payer_name = data.get('payer_name')
        if not payer_name:
            return {}

        try:
            data_tools = CheckDataAccessTools()
            customer_info = data_tools.get_customer_history(payer_name)
            return customer_info
        except Exception as e:
            logger.error(f"Failed to get customer info: {e}")
            return {}

    def _check_duplicate(self, data: Dict) -> bool:
        """Check for duplicate check submission"""
        check_number = data.get('check_number')
        payer_name = data.get('payer_name')

        if not check_number or not payer_name:
            return False

        try:
            data_tools = CheckDataAccessTools()
            is_duplicate = data_tools.check_duplicate(check_number, payer_name)
            return is_duplicate
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False

    def _run_ai_analysis(self, data: Dict, ml_analysis: Dict, customer_info: Dict) -> Optional[Dict]:
        """Run AI fraud analysis"""
        if not self.ai_agent:
            logger.info("AI agent not available - skipping AI analysis")
            return None

        try:
            payer_name = data.get('payer_name')
            ai_analysis = self.ai_agent.analyze_fraud(
                extracted_data=data,
                ml_analysis=ml_analysis,
                payer_name=payer_name
            )
            return ai_analysis
        except Exception as e:
            logger.error(f"AI analysis failed: {e}", exc_info=True)
            return None

    def _generate_anomalies(self, data: Dict, ml_analysis: Dict, ai_analysis: Optional[Dict]) -> List[str]:
        """Generate comprehensive anomaly list"""
        anomalies = []

        # From ML analysis
        ml_anomalies = ml_analysis.get('anomalies', [])
        anomalies.extend(ml_anomalies)

        # From AI analysis
        if ai_analysis:
            ai_factors = ai_analysis.get('key_indicators', [])
            anomalies.extend(ai_factors)

        # From validation
        if not data.get('is_supported_bank', True):
            anomalies.append(f"Unsupported bank: {data.get('bank_name')}")

        critical_missing = data.get('critical_missing_fields', [])
        if critical_missing:
            anomalies.append(f"Missing critical fields: {', '.join(critical_missing)}")

        # Amount checks
        amount_dict = data.get('amount_numeric', {})
        if isinstance(amount_dict, dict):
            amount = amount_dict.get('value', 0)
        else:
            amount = amount_dict or 0

        if amount > 10000:
            anomalies.append(f"High amount: ${amount:,.2f} - requires additional verification")

        return list(set(anomalies))  # Remove duplicates

    def _calculate_confidence(self, data: Dict, ml_analysis: Dict, ai_analysis: Optional[Dict]) -> float:
        """Calculate overall confidence score"""
        confidence = 0.5

        # Factor 1: Data completeness (30%)
        completeness = data.get('completeness_score', 0.5)
        confidence += completeness * 0.3

        # Factor 2: ML model confidence (30%)
        ml_confidence = ml_analysis.get('model_confidence', 0.5)
        confidence += ml_confidence * 0.3

        # Factor 3: AI confidence (40%)
        if ai_analysis:
            ai_confidence = ai_analysis.get('confidence_score', 0.7)
            confidence += ai_confidence * 0.4
        else:
            confidence += 0.2  # Partial credit if AI not available

        return min(1.0, max(0.0, confidence))

    def _determine_final_decision(
        self,
        validation_issues: List[str],
        ml_analysis: Dict,
        ai_analysis: Optional[Dict],
        normalized_data: Dict
    ) -> str:
        """
        Determine final decision based on all collected issues
        - REJECT if signature missing or critical issues exist
        - Otherwise defer to AI or ML analysis
        """
        # Check for signature (most critical)
        has_signature = normalized_data.get('signature_detected', False)
        if not has_signature:
            logger.warning("Decision: REJECT due to missing signature")
            return "REJECT"

        # Check for other critical issues
        critical_keywords = [
            "unsupported bank",
            "missing check number",
            "missing payer name",
            "missing payee name",
            "cannot be the same person",
            "too many critical fields missing"
        ]

        for issue in validation_issues:
            if any(keyword in issue.lower() for keyword in critical_keywords):
                logger.warning(f"Decision: REJECT due to critical issue: {issue}")
                return "REJECT"

        # Check for duplicate
        if "duplicate check" in " ".join(validation_issues).lower():
            logger.warning("Decision: REJECT due to duplicate check")
            return "REJECT"

        # Defer to AI analysis if available
        if ai_analysis:
            recommendation = ai_analysis.get('recommendation', 'ESCALATE').upper()
            logger.info(f"Decision: {recommendation} (from AI analysis)")
            return recommendation

        # Fall back to ML analysis
        fraud_score = ml_analysis.get('fraud_risk_score', 0.5)
        if fraud_score >= 0.7:
            logger.info(f"Decision: REJECT (ML fraud score: {fraud_score})")
            return "REJECT"
        elif fraud_score >= 0.3:
            logger.info(f"Decision: ESCALATE (ML fraud score: {fraud_score})")
            return "ESCALATE"
        else:
            logger.info(f"Decision: APPROVE (ML fraud score: {fraud_score})")
            return "APPROVE"

    def _build_complete_response(self, **kwargs) -> Dict:
        """
        Build complete response with ALL analysis results, issues, and decision
        No data is excluded or hidden
        """
        validation_issues = kwargs.get('validation_issues', [])
        overall_decision = kwargs.get('overall_decision', 'UNKNOWN')
        duplicate_detected = kwargs.get('duplicate_detected', False)

        response = {
            'status': 'success',
            'extracted_data': kwargs['extracted_data'],
            'normalized_data': kwargs['normalized_data'],
            'ml_analysis': kwargs['ml_analysis'],
            'ai_analysis': kwargs['ai_analysis'],
            'anomalies': kwargs['anomalies'],
            'confidence_score': kwargs['confidence_score'],
            'timestamp': datetime.now().isoformat(),
            # NEW: Include all validation issues
            'validation_issues': validation_issues,
            # NEW: Include overall decision
            'overall_decision': overall_decision,
            # NEW: Flag if duplicate
            'duplicate_detected': duplicate_detected,
            # Raw text for audit trail
            'raw_text': kwargs.get('raw_text', '')
        }

        return response


# Legacy function for backward compatibility
def extract_check(file_path: str) -> Dict:
    """
    Extract and analyze check (legacy function)

    Args:
        file_path: Path to check image

    Returns:
        Analysis results dict
    """
    extractor = CheckExtractor()
    return extractor.extract_and_analyze(file_path)
