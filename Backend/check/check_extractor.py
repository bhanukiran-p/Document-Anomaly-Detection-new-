"""
Check Extractor - Complete Fraud Detection Pipeline
Orchestrates: Mindee OCR → Normalization → ML Detection → AI Analysis → Customer Tracking
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import Mindee - use new API
try:
    from mindee import Client
    from mindee.product import CustomV1
    MINDEE_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).error(f"Mindee library not properly installed: {e}")
    MINDEE_AVAILABLE = False
    Client = None
    CustomV1 = None

# Import check-specific components
from normalization.check_normalizer_factory import CheckNormalizerFactory
from ml_models.check_fraud_detector import CheckFraudDetector
from check.ai.check_fraud_analysis_agent import CheckFraudAnalysisAgent
from check.ai.check_tools import CheckDataAccessTools

logger = logging.getLogger(__name__)

# Mindee configuration
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_CHECK = os.getenv("MINDEE_MODEL_ID_CHECK", "046edc76-e8a4-4e11-a9a3-bb8632250446").strip()

if not MINDEE_API_KEY:
    logger.warning("MINDEE_API_KEY is not set - check extraction may fail")
    mindee_client = None
elif not MINDEE_AVAILABLE:
    logger.error("Mindee library not available")
    mindee_client = None
else:
    mindee_client = Client(api_key=MINDEE_API_KEY)


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
                model=os.getenv('AI_MODEL', 'gpt-4'),
                data_tools=data_tools
            )
            logger.info("Initialized CheckFraudAnalysisAgent")
        else:
            logger.warning("OPENAI_API_KEY not set - AI analysis will be skipped")

    def extract_and_analyze(self, image_path: str) -> Dict:
        """
        Complete check analysis pipeline

        Args:
            image_path: Path to check image file

        Returns:
            Complete analysis results dict
        """
        logger.info(f"Starting check analysis for: {image_path}")

        # Stage 1: OCR Extraction (Mindee only)
        extracted_data, raw_text = self._extract_with_mindee(image_path)
        logger.info(f"Extracted data from Mindee: {list(extracted_data.keys())}")

        # Stage 2: Normalization
        bank_name = extracted_data.get('bank_name', '')
        normalized_data = self._normalize_data(extracted_data, bank_name)

        # Stage 3: Validation & Auto-Reject Checks
        auto_reject_reason = self._check_auto_reject_conditions(normalized_data)
        if auto_reject_reason:
            logger.warning(f"Auto-reject triggered: {auto_reject_reason}")
            return self._create_auto_reject_response(
                extracted_data, normalized_data, auto_reject_reason
            )

        # Stage 4: ML Fraud Detection
        ml_analysis = self._run_ml_fraud_detection(normalized_data, raw_text)
        logger.info(f"ML fraud analysis complete: {ml_analysis.get('risk_level')}")

        # Stage 5: Customer History & Duplicate Detection
        customer_info = self._get_customer_info(normalized_data)
        duplicate_check = self._check_duplicate(normalized_data)

        if duplicate_check:
            logger.warning("Duplicate check detected")
            return self._create_duplicate_response(extracted_data, normalized_data, ml_analysis)

        # Stage 6: AI Fraud Analysis
        ai_analysis = self._run_ai_analysis(normalized_data, ml_analysis, customer_info)
        logger.info(f"AI analysis complete: {ai_analysis.get('recommendation') if ai_analysis else 'N/A'}")

        # Stage 7: Generate Anomalies
        anomalies = self._generate_anomalies(normalized_data, ml_analysis, ai_analysis)

        # Stage 8: Calculate Confidence Score
        confidence_score = self._calculate_confidence(normalized_data, ml_analysis, ai_analysis)

        # Stage 9: Build Final Response
        return self._build_final_response(
            extracted_data=extracted_data,
            normalized_data=normalized_data,
            ml_analysis=ml_analysis,
            ai_analysis=ai_analysis,
            anomalies=anomalies,
            confidence_score=confidence_score,
            raw_text=raw_text
        )

    def _extract_with_mindee(self, file_path: str) -> Tuple[Dict, str]:
        """Extract check data using Mindee API only (no fallback)"""
        if not mindee_client:
            raise RuntimeError("Mindee client not initialized. Check API key and installation.")

        try:
            # Use new Mindee API
            input_source = mindee_client.source_from_path(file_path)

            # Create custom endpoint
            custom_endpoint = mindee_client.create_endpoint(
                endpoint_name=MINDEE_MODEL_ID_CHECK,
                account_name="xforia",  # Replace with your account name if different
                version="1"
            )

            # Parse document using custom model
            result = mindee_client.enqueue_and_parse(
                product_class=CustomV1,
                input_source=input_source,
                endpoint=custom_endpoint
            )

            # Extract fields from the result
            doc = result.document
            if not doc or not doc.inference or not doc.inference.prediction:
                raise ValueError("Invalid Mindee API response")

            fields = doc.inference.prediction.fields if hasattr(doc.inference.prediction, 'fields') else {}

            # Convert Mindee fields to simple dict
            extracted = {}
            for name, field in fields.items():
                if hasattr(field, "value"):
                    extracted[name] = field.value
                    logger.debug(f"Mindee field {name}: {field.value}")
                elif hasattr(field, "values"):
                    # Handle list fields
                    extracted[name] = [v.value if hasattr(v, 'value') else v for v in field.values]
                elif hasattr(field, "content"):
                    # Some fields use 'content' instead of 'value'
                    extracted[name] = field.content

            # Get raw OCR text
            raw_text = ""
            if hasattr(doc, 'ocr') and doc.ocr:
                raw_text = str(doc.ocr)

            logger.info(f"Successfully extracted {len(extracted)} fields from Mindee")
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

    def _check_auto_reject_conditions(self, data: Dict) -> Optional[str]:
        """Check for auto-reject conditions"""

        # 1. Unsupported bank
        if not data.get('is_supported_bank', False):
            bank_name = data.get('bank_name', 'Unknown')
            return f"Unsupported bank: {bank_name}. Only Bank of America and Chase are accepted."

        # 2. Missing critical fields
        critical_missing = data.get('critical_missing_fields', [])
        if len(critical_missing) >= 3:
            return f"Too many critical fields missing: {', '.join(critical_missing)}"

        # 3. Missing signature
        if not data.get('signature_detected'):
            return "Signature not detected - required for check validation"

        # 4. Missing check number
        if not data.get('check_number'):
            return "Check number missing - required for processing"

        # 5. Missing payer or payee
        if not data.get('payer_name'):
            return "Payer name missing - required field"
        if not data.get('payee_name'):
            return "Payee name missing - required field"

        # 6. Same payer and payee (can't pay yourself)
        payer = str(data.get('payer_name', '')).lower().strip()
        payee = str(data.get('payee_name', '')).lower().strip()
        if payer and payee and payer == payee:
            return "Payer and payee cannot be the same person"

        return None

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

    def _create_auto_reject_response(self, extracted: Dict, normalized: Dict, reason: str) -> Dict:
        """Create response for auto-rejected checks"""
        return {
            'status': 'rejected',
            'extracted_data': extracted,
            'normalized_data': normalized,
            'ml_analysis': {
                'fraud_risk_score': 1.0,
                'risk_level': 'CRITICAL',
                'model_confidence': 1.0,
                'auto_reject': True
            },
            'ai_analysis': {
                'recommendation': 'REJECT',
                'confidence_score': 1.0,
                'summary': f'Auto-rejected: {reason}',
                'reasoning': [reason, 'Auto-reject policy triggered'],
                'key_indicators': ['Auto-reject condition met'],
                'actionable_recommendations': ['Transaction blocked - do not process']
            },
            'anomalies': [reason],
            'confidence_score': 1.0,
            'timestamp': datetime.now().isoformat(),
            'auto_reject_reason': reason
        }

    def _create_duplicate_response(self, extracted: Dict, normalized: Dict, ml_analysis: Dict) -> Dict:
        """Create response for duplicate checks"""
        check_number = normalized.get('check_number')
        payer_name = normalized.get('payer_name')

        return {
            'status': 'rejected',
            'extracted_data': extracted,
            'normalized_data': normalized,
            'ml_analysis': ml_analysis,
            'ai_analysis': {
                'recommendation': 'REJECT',
                'confidence_score': 1.0,
                'summary': f'Duplicate check detected: #{check_number} from {payer_name}',
                'reasoning': [
                    f'Check #{check_number} from {payer_name} was previously submitted',
                    'Duplicate submissions are automatically rejected'
                ],
                'key_indicators': ['Duplicate check detected'],
                'actionable_recommendations': ['Block transaction', 'Investigate potential fraud']
            },
            'anomalies': ['Duplicate check submission'],
            'confidence_score': 1.0,
            'timestamp': datetime.now().isoformat(),
            'duplicate_detected': True
        }

    def _build_final_response(self, **kwargs) -> Dict:
        """Build final response with all analysis data"""
        return {
            'status': 'success',
            'extracted_data': kwargs['extracted_data'],
            'normalized_data': kwargs['normalized_data'],
            'ml_analysis': kwargs['ml_analysis'],
            'ai_analysis': kwargs['ai_analysis'],
            'anomalies': kwargs['anomalies'],
            'confidence_score': kwargs['confidence_score'],
            'raw_text': kwargs['raw_text'],
            'timestamp': datetime.now().isoformat()
        }


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
