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
    try:
        params = InferenceParameters(model_id=model_id, raw_text=True, confidence=True)
        input_source = PathInput(file_path)
        response = mindee_client.enqueue_and_get_inference(input_source, params)
        result = response.inference.result
        fields = result.fields or {}
    except Exception as e:
        logger.error(f"Mindee API error: {e}", exc_info=True)
        raise RuntimeError(f"Failed to process document with Mindee API: {str(e)}")

    logger.info(f"=== MINDEE RAW RESPONSE DEBUG ===")
    logger.info(f"Available field names: {list(fields.keys())}")

    simple_fields: Dict[str, Any] = {}
    for name, field in fields.items():
        if hasattr(field, "value"):
            simple_fields[name] = field.value
            logger.info(f"  {name}: {field.value} (type: {type(field.value).__name__})")
        elif hasattr(field, "items"):
            values = []
            for item in field.items:
                if hasattr(item, "value"):
                    values.append(item.value)
                elif hasattr(item, "fields"):
                    nested_dict = {k: v.value for k, v in item.fields.items()}
                    values.append(nested_dict)
                    logger.info(f"    Nested in {name}: {nested_dict}")
            simple_fields[name] = values
            logger.info(f"  {name} (list): {values}")
        elif hasattr(field, "fields"):
            simple_fields[name] = {k: v.value for k, v in field.fields.items()}
            logger.info(f"  {name} (dict): {simple_fields[name]}")

    logger.info(f"=== END DEBUG ===")
    logger.info(f"Extracted fields summary: {simple_fields}")

    raw_text = getattr(result, "raw_text", "") or ""
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
    try:
        out = _run_model(file_path, MINDEE_MODEL_ID_MONEY_ORDER)
        fields = out["fields"]
    except Exception as e:
        logger.error(f"Money order extraction error: {e}", exc_info=True)
        raise
    
    # Construct comprehensive location from available address components
    address_parts = []
    if fields.get("address"):
        address_parts.append(str(fields.get("address")))
    
    city_state_parts = []
    if fields.get("city"):
        city_state_parts.append(str(fields.get("city")))
    if fields.get("state"):
        city_state_parts.append(str(fields.get("state")))
    if fields.get("zip_code"):
        city_state_parts.append(str(fields.get("zip_code")))
    
    if address_parts:
        if city_state_parts:
            location = ", ".join(address_parts) + ", " + ", ".join(city_state_parts)
        else:
            location = ", ".join(address_parts)
    elif city_state_parts:
        location = ", ".join(city_state_parts)
    else:
        location = fields.get("location")
    
    # Format amount with proper currency formatting if available
    amount = fields.get("amount")
    if amount is not None:
        try:
            if isinstance(amount, (int, float)):
                amount = float(amount)
        except (ValueError, TypeError):
            amount = None
    
    # Try multiple field name variations for each field
    extracted = {
        "issuer": fields.get("issuer") or fields.get("issuer_name") or fields.get("company") or fields.get("company_name") or "",
        "purchaser": fields.get("payer") or fields.get("purchaser") or fields.get("buyer") or fields.get("sender"),
        "payee": fields.get("payee") or fields.get("recipient") or fields.get("pay_to"),
        "amount": amount,
        "date": fields.get("issue_date") or fields.get("date") or fields.get("purchase_date") or fields.get("issued_date") or fields.get("transaction_date"),
        "serial_number": fields.get("money_order_number") or fields.get("serial_number") or fields.get("control_number") or fields.get("tracking_number"),
        "location": location,
        "amount_in_words": fields.get("amount_in_words") or fields.get("word_amount") or fields.get("amount_words") or fields.get("written_amount") or fields.get("amount_text"),
        "receipt_number": fields.get("receipt_number") or fields.get("receipt_no") or fields.get("receipt") or fields.get("confirmation_number") or fields.get("transaction_id"),
        "signature": fields.get("signature") or fields.get("signature_detected") or fields.get("signed") or fields.get("signer"),
        "money_order_number": fields.get("money_order_number"),
        "address": fields.get("address"),
        "city": fields.get("city"),
        "state": fields.get("state"),
        "zip_code": fields.get("zip_code"),
        "payer": fields.get("payer"),
        "issue_date": fields.get("issue_date"),
        "raw_ocr_text": out.get("raw_text", ""),
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}

