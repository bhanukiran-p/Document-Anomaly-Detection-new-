"""
Check extraction using Mindee API with ML Fraud Detection and AI Analysis
"""
import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from mindee import ClientV2, InferenceParameters, PathInput
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

logger = logging.getLogger(__name__)


def convert_to_json_serializable(obj: Any) -> Any:
    """Recursively convert NumPy types and other non-JSON-serializable types to native Python types."""
    if isinstance(obj, (np.integer, np.int_)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float_)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(convert_to_json_serializable(item) for item in obj)
    return obj


# Import ML models and AI agent
try:
    from ml_models.fraud_detector import MoneyOrderFraudDetector

    ML_AVAILABLE = True
except ImportError as e:
    logger.warning("ML fraud detector not available: %s", e)
    ML_AVAILABLE = False
    MoneyOrderFraudDetector = None

try:
    from langchain_agent.fraud_analysis_agent import FraudAnalysisAgent
    from langchain_agent.tools import DataAccessTools

    AI_AVAILABLE = True
except ImportError as e:
    logger.warning("AI fraud analysis agent not available: %s", e)
    AI_AVAILABLE = False
    FraudAnalysisAgent = None
    DataAccessTools = None

# Import Check Normalization
try:
    from check_normalization.check_normalizer_factory import CheckNormalizerFactory

    NORMALIZATION_AVAILABLE = True
except ImportError as e:
    logger.warning("Check normalization not available: %s", e)
    NORMALIZATION_AVAILABLE = False
    CheckNormalizerFactory = None

MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_CHECK = os.getenv("MINDEE_MODEL_ID_CHECK", "046edc76-e8a4-4e11-a9a3-bb8632250446").strip()

if not MINDEE_API_KEY:
    raise RuntimeError("MINDEE_API_KEY is not set")

mindee_client = ClientV2(MINDEE_API_KEY)


def _run_model(file_path: str) -> Dict[str, Any]:
    """Run Mindee model inference on a document."""
    try:
        params = InferenceParameters(model_id=MINDEE_MODEL_ID_CHECK, raw_text=True)
        input_source = PathInput(file_path)
        response = mindee_client.enqueue_and_get_inference(input_source, params)

        if not response or not hasattr(response, 'inference'):
            raise ValueError("Invalid response from Mindee API: missing inference object")
        
        if not response.inference or not hasattr(response.inference, 'result'):
            raise ValueError("Invalid response from Mindee API: missing result object")
            
        result = response.inference.result
        if not result:
            raise ValueError("Invalid response from Mindee API: result is None")
            
        fields = result.fields or {}
    except Exception as e:
        logger.error(f"Mindee API call failed: {e}", exc_info=True)
        raise RuntimeError(f"Failed to process document with Mindee API: {str(e)}") from e

    logger.info("=== MINDEE RAW RESPONSE DEBUG ===")
    logger.info("Available field names: %s", list(fields.keys()))

    simple_fields: Dict[str, Any] = {}
    for name, field in fields.items():
        if hasattr(field, "value"):
            simple_fields[name] = field.value
            logger.info("  %s: %s", name, field.value)
        elif hasattr(field, "items"):
            values = []
            for item in field.items:
                if hasattr(item, "value"):
                    values.append(item.value)
                elif hasattr(item, "fields"):
                    values.append({k: v.value for k, v in item.fields.items()})
            simple_fields[name] = values
            logger.info("  %s (list): %s", name, values)
        elif hasattr(field, "fields"):
            simple_fields[name] = {k: v.value for k, v in field.fields.items()}
            logger.info("  %s (dict): %s", name, simple_fields[name])

    logger.info("=== END DEBUG ===")

    raw_text = getattr(result, "raw_text", "") or ""
    if raw_text and not isinstance(raw_text, str):
        raw_text = str(raw_text)
    return {"fields": simple_fields, "raw_text": raw_text}


def _parse_amount_fields(fields: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    """Return numeric + formatted amount from raw fields."""
    amount_value = fields.get("number_amount") or fields.get("amount_numeric") or fields.get("amount")
    amount_numeric: Optional[float] = None

    if isinstance(amount_value, (int, float)):
        amount_numeric = float(amount_value)
    elif isinstance(amount_value, str):
        import re

        amount_str = re.sub(r"[^\d.]", "", amount_value)
        if amount_str:
            try:
                amount_numeric = float(amount_str)
            except ValueError:
                pass

    if amount_numeric is not None:
        return amount_numeric, f"${amount_numeric:,.2f}"
    return None, str(amount_value) if amount_value is not None else None


def _build_extracted(fields: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    """Normalize Mindee fields into the structure expected by the frontend/ML layer."""
    amount_numeric, amount_formatted = _parse_amount_fields(fields)
    return {
        "bank_name": fields.get("bank_name"),
        "country": fields.get("country"),
        "check_type": fields.get("check_type"),
        "payee_name": fields.get("pay_to") or fields.get("payee_name") or fields.get("payee"),
        "amount_numeric": amount_numeric,
        "amount": amount_formatted,
        "amount_words": fields.get("word_amount") or fields.get("amount_words"),
        "date": fields.get("check_date") or fields.get("date"),
        "check_number": fields.get("check_number"),
        "routing_number": fields.get("routing_number"),
        "account_number": fields.get("account_number"),
        "memo": fields.get("memo"),
        "signature_detected": fields.get("signature") or fields.get("signature_detected"),
        "currency": fields.get("currency"),
        "payer_name": fields.get("payer_name"),
        "payer_address": fields.get("payer_address"),
        "raw_ocr_text": raw_text,
    }


def _ml_not_available_reason() -> Dict[str, Any]:
    return {
        "fraud_risk_score": 0.0,
        "risk_level": "UNKNOWN",
        "model_confidence": 0.0,
        "error": "ML detection not available",
    }


def _run_ml_analysis(extracted: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    """Invoke the fraud detector if available."""
    if not (ML_AVAILABLE and MoneyOrderFraudDetector):
        logger.warning("ML fraud detection not available - ML_AVAILABLE: %s", ML_AVAILABLE)
        return _ml_not_available_reason()

    try:
        logger.info("Starting ML fraud detection for check...")
        model_dir = os.getenv("ML_MODEL_DIR", "ml_models")
        fraud_detector = MoneyOrderFraudDetector(model_dir=model_dir)
        logger.info("Fraud detector initialized, models loaded: %s", fraud_detector.models_loaded)

        check_data_for_ml = {
            **extracted,
            "issuer": extracted.get("bank_name") or "Unknown Bank",
            "payee": extracted.get("payee_name"),
            "purchaser": extracted.get("payer_name"),
        }

        analysis = fraud_detector.predict_fraud(check_data_for_ml, raw_text)
        logger.info(
            "ML fraud detection completed: risk_score=%s, risk_level=%s",
            analysis.get("fraud_risk_score"),
            analysis.get("risk_level"),
        )
        return analysis
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("ML fraud detection failed: %s", exc, exc_info=True)
        return {
            "error": str(exc),
            "fraud_risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "model_confidence": 0.0,
        }


def _run_ai_analysis(ml_analysis: Dict[str, Any], extracted: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Invoke the LangChain-based AI agent when configured."""
    if not (AI_AVAILABLE and FraudAnalysisAgent and DataAccessTools):
        logger.info("AI analysis not available (LangChain not installed or OpenAI key not set)")
        return None

    try:
        ml_scores_path = os.getenv("ML_SCORES_CSV", "ml_models/mock_data/ml_scores.csv")
        customer_history_path = os.getenv("CUSTOMER_HISTORY_CSV", "ml_models/mock_data/customer_history.csv")
        fraud_cases_path = os.getenv("FRAUD_CASES_CSV", "ml_models/mock_data/fraud_cases.csv")

        data_tools = DataAccessTools(
            ml_scores_path=ml_scores_path,
            customer_history_path=customer_history_path,
            fraud_cases_path=fraud_cases_path,
        )

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            logger.info("AI analysis skipped (OPENAI_API_KEY missing)")
            return None

        ai_agent = FraudAnalysisAgent(
            api_key=openai_key,
            model=os.getenv("AI_MODEL", "gpt-4"),
            data_tools=data_tools,
        )
        analysis = ai_agent.analyze_fraud(ml_analysis, extracted, customer_id=None)
        logger.info("AI fraud analysis completed: recommendation=%s", analysis.get("recommendation"))
        return analysis
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("AI fraud analysis failed: %s", exc, exc_info=True)
        return None


def _generate_anomalies(extracted: Dict[str, Any], ml_analysis: Optional[Dict], ai_analysis: Optional[Dict]) -> List[str]:
    """Generate list of anomalies based on ML, AI analysis, and normalization validation."""
    anomalies: List[str] = []

    # Add specific check fraud indicators (MICR mismatch, font signature, etc.)
    try:
        from utils.check_fraud_indicators import detect_check_fraud_indicators
        raw_text = extracted.get('raw_ocr_text', '')
        fraud_indicators = detect_check_fraud_indicators(extracted, raw_text)
        anomalies.extend(fraud_indicators)
    except ImportError:
        logger.warning("Check fraud indicators module not available")
    except Exception as e:
        logger.warning(f"Failed to detect check fraud indicators: {e}")

    # Check normalization-based fraud indicators
    if NORMALIZATION_AVAILABLE and CheckNormalizerFactory:
        try:
            bank_name = extracted.get("bank_name")
            normalizer = CheckNormalizerFactory.get_normalizer(bank_name)
            normalized_check = normalizer.normalize(extracted)

            # Get fraud indicators from normalized check
            fraud_indicators = normalized_check.get_fraud_indicators()
            anomalies.extend(fraud_indicators)

            # Log normalization info
            logger.info(f"Check normalized using {normalizer.__class__.__name__}")
            logger.info(f"Completeness score: {normalized_check.get_completeness_score()}")
        except Exception as e:
            logger.warning(f"Check normalization validation failed: {e}")

    if ml_analysis:
        risk_level = ml_analysis.get("risk_level", "LOW")
        fraud_score = ml_analysis.get("fraud_risk_score", 0)

        if risk_level in {"HIGH", "CRITICAL"}:
            anomalies.append(f"High fraud risk detected: {risk_level} (score: {fraud_score:.2%})")

        feature_importance = ml_analysis.get("feature_importance", {})
        if isinstance(feature_importance, dict):
            items = feature_importance.items()
        else:
            items = []
            for item in feature_importance or []:
                if isinstance(item, dict) and "feature" in item and "importance" in item:
                    items.append((item["feature"], item["importance"]))

        for feature, importance in list(items)[:5]:
            try:
                weight = float(importance)
            except (TypeError, ValueError):
                continue
            if weight > 0.1:
                anomalies.append(f"Fraud indicator: {feature} (importance: {weight:.2%})")

    if ai_analysis:
        recommendation = ai_analysis.get("recommendation")
        if recommendation and recommendation != "APPROVE":
            anomalies.append(f"AI recommendation: {recommendation}")
        anomalies.extend(ai_analysis.get("risk_factors", []))

    amount = extracted.get("amount_numeric")
    if amount:
        if amount > 10_000:
            anomalies.append("Amount exceeds $10,000 - requires additional verification")
        if amount < 1:
            anomalies.append("Amount is suspiciously low")

    return anomalies


def _calculate_confidence_score(extracted: Dict[str, Any], ml_analysis: Optional[Dict[str, Any]]) -> float:
    """Calculate overall confidence score based on extraction and ML analysis."""
    confidence = 0.5
    required_fields = ["bank_name", "payee_name", "amount_numeric", "date", "check_number"]
    present_fields = sum(1 for field in required_fields if extracted.get(field))
    confidence += (present_fields / len(required_fields)) * 0.3

    if ml_analysis:
        confidence += ml_analysis.get("model_confidence", 0.5) * 0.2
    else:
        confidence += 0.2

    return min(1.0, max(0.0, confidence))


def _build_response(
    extracted: Dict[str, Any],
    fields: Dict[str, Any],
    raw_text: str,
    ml_analysis: Optional[Dict[str, Any]],
    ai_analysis: Optional[Dict[str, Any]],
    anomalies: List[str],
    confidence_score: float,
    normalized_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the final payload returned to the API layer."""
    result = {
        "status": "success",
        "extracted_data": extracted,
        "raw_fields": fields,
        "raw_text": raw_text,
        "timestamp": datetime.now().isoformat(),
        "anomalies": anomalies,
        "confidence_score": confidence_score,
    }

    # Add normalized data if available
    if normalized_data:
        result["normalized_data"] = normalized_data
        # Extract missing fields and key factors
        missing_fields = [k for k, v in normalized_data.items() if v is None or v == '']
        result["missing_fields"] = missing_fields
        logger.info(f"Normalized data added with {len(missing_fields)} missing fields")

    if ml_analysis:
        serializable_ml = convert_to_json_serializable(ml_analysis)
        result["ml_analysis"] = serializable_ml
        result["ml_fraud_analysis"] = serializable_ml
        if isinstance(serializable_ml, dict):
            logger.info("ML analysis added to response: %s", list(serializable_ml.keys()))
    else:
        logger.warning("ML analysis is None - adding default structure")
        result["ml_analysis"] = _ml_not_available_reason()
        result["ml_fraud_analysis"] = result["ml_analysis"]

    if ai_analysis:
        result["ai_analysis"] = convert_to_json_serializable(ai_analysis)
        logger.info("AI analysis added to response")

    logger.info("Final result keys: %s", list(result.keys()))
    return result


def extract_check(file_path: str) -> Dict[str, Any]:
    """
    Extract check data using Mindee API with ML Fraud Detection and AI Analysis.

    Args:
        file_path: Path to the check image/PDF file
    """
    mindee_out = _run_model(file_path)
    fields = mindee_out["fields"]
    raw_text = mindee_out.get("raw_text", "")

    extracted = _build_extracted(fields, raw_text)

    # Normalize check data
    normalized_data = None
    if NORMALIZATION_AVAILABLE and CheckNormalizerFactory:
        try:
            bank_name = extracted.get("bank_name")
            normalizer = CheckNormalizerFactory.get_normalizer(bank_name)
            normalized_check = normalizer.normalize(extracted)
            normalized_data = normalized_check.to_dict()
            logger.info(f"Check normalized using {normalizer.__class__.__name__}")
        except Exception as e:
            logger.warning(f"Check normalization failed: {e}")

    ml_analysis = _run_ml_analysis(extracted, raw_text)
    ai_analysis = _run_ai_analysis(ml_analysis, extracted)

    anomalies = _generate_anomalies(extracted, ml_analysis, ai_analysis)
    confidence_score = float(_calculate_confidence_score(extracted, ml_analysis or {}))

    result = _build_response(extracted, fields, raw_text, ml_analysis, ai_analysis, anomalies, confidence_score, normalized_data)

    # Save analysis result for feedback system
    try:
        from langchain_agent.result_storage import save_analysis_result
        check_number = extracted.get("check_number", "unknown")
        analysis_id = save_analysis_result(result, check_number)
        if analysis_id:
            result["analysis_id"] = analysis_id
            logger.info(f"Analysis saved with ID: {analysis_id}")
    except Exception as e:
        logger.warning(f"Failed to save analysis result: {e}")

    return result
