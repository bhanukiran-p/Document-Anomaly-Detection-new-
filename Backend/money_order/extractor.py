"""
Money Order extraction using Mindee API
"""
import os
import logging
from typing import Any, Dict
from mindee import ClientV2, InferenceParameters, PathInput

logger = logging.getLogger(__name__)

# Load configuration from environment
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_MONEY_ORDER = os.getenv("MINDEE_MODEL_ID_MONEY_ORDER", "7ecd4b47-c7a0-430c-ac68-a68b04960a39").strip()

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


def extract_money_order(file_path: str) -> Dict[str, Any]:
    """
    Extract money order data using Mindee API

    Args:
        file_path: Path to the money order image/PDF file

    Returns:
        Dictionary containing extracted money order data
    """
    out = _run_model(file_path, MINDEE_MODEL_ID_MONEY_ORDER)
    fields = out["fields"]
    extracted = {
        # Mindee doesn't return issuer field for money orders, use empty string as default
        "issuer": fields.get("issuer") or "",
        # Mindee uses 'payer' instead of 'purchaser'
        "purchaser": fields.get("payer") or fields.get("purchaser"),
        "payee": fields.get("payee"),
        "amount": fields.get("amount"),
        # Mindee uses 'issue_date' instead of 'date'
        "date": fields.get("issue_date") or fields.get("date"),
        # Mindee uses 'money_order_number' instead of 'serial_number'
        "serial_number": fields.get("money_order_number") or fields.get("serial_number"),
        # Additional Mindee fields
        "money_order_number": fields.get("money_order_number"),
        "address": fields.get("address"),
        "city": fields.get("city"),
        "state": fields.get("state"),
        "zip_code": fields.get("zip_code"),
        "raw_ocr_text": out["raw_text"],
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}
