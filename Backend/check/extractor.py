"""
Check extraction using Mindee API
"""
import os
import logging
from typing import Any, Dict
from mindee import ClientV2, InferenceParameters, PathInput

logger = logging.getLogger(__name__)

# Load configuration from environment
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_CHECK = os.getenv("MINDEE_MODEL_ID_CHECK", "046edc76-e8a4-4e11-a9a3-bb8632250446").strip()

if not MINDEE_API_KEY:
    raise RuntimeError("MINDEE_API_KEY is not set")

mindee_client = ClientV2(MINDEE_API_KEY)


def _run_model(file_path: str, model_id: str) -> Dict[str, Any]:
    """Run Mindee model inference on a document"""
    params = InferenceParameters(model_id=model_id, raw_text=True, confidence=True)
    input_source = PathInput(file_path)
    response = mindee_client.enqueue_and_get_inference(input_source, params)
    result = response.inference.result
    fields = result.fields or {}

    logger.info(f"=== MINDEE RAW RESPONSE DEBUG ===")
    logger.info(f"Available field names: {list(fields.keys())}")

    simple_fields: Dict[str, Any] = {}
    for name, field in fields.items():
        if hasattr(field, "value"):
            simple_fields[name] = field.value
            logger.info(f"  {name}: {field.value}")
        elif hasattr(field, "items"):
            values = []
            for item in field.items:
                if hasattr(item, "value"):
                    values.append(item.value)
                elif hasattr(item, "fields"):
                    values.append({k: v.value for k, v in item.fields.items()})
            simple_fields[name] = values
            logger.info(f"  {name} (list): {values}")
        elif hasattr(field, "fields"):
            simple_fields[name] = {k: v.value for k, v in field.fields.items()}
            logger.info(f"  {name} (dict): {simple_fields[name]}")

    logger.info(f"=== END DEBUG ===")

    raw_text = getattr(result, "raw_text", "") or ""
    # Convert RawText object to string if it's not already a string
    if raw_text and not isinstance(raw_text, str):
        raw_text = str(raw_text)
    return {"fields": simple_fields, "raw_text": raw_text}


def extract_check(file_path: str) -> Dict[str, Any]:
    """
    Extract check data using Mindee API

    Args:
        file_path: Path to the check image/PDF file

    Returns:
        Dictionary containing extracted check data
    """
    out = _run_model(file_path, MINDEE_MODEL_ID_CHECK)
    fields = out["fields"]
    extracted = {
        "bank_name": fields.get("bank_name"),
        "country": fields.get("country"),
        "check_type": fields.get("check_type"),
        # Mindee uses 'pay_to' instead of 'payee_name'
        "payee_name": fields.get("pay_to") or fields.get("payee_name") or fields.get("payee"),
        # Mindee uses 'number_amount' instead of 'amount_numeric'
        "amount_numeric": fields.get("number_amount") or fields.get("amount_numeric") or fields.get("amount"),
        # Mindee uses 'word_amount' instead of 'amount_words'
        "amount_words": fields.get("word_amount") or fields.get("amount_words"),
        # Mindee uses 'check_date' instead of 'date'
        "date": fields.get("check_date") or fields.get("date"),
        "check_number": fields.get("check_number"),
        "routing_number": fields.get("routing_number"),
        "account_number": fields.get("account_number"),
        "memo": fields.get("memo"),
        # Mindee uses 'signature' (boolean) instead of 'signature_detected'
        "signature_detected": fields.get("signature") or fields.get("signature_detected"),
        "currency": fields.get("currency"),
        # Additional Mindee fields
        "payer_name": fields.get("payer_name"),
        "payer_address": fields.get("payer_address"),
        "raw_ocr_text": out["raw_text"],
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}
