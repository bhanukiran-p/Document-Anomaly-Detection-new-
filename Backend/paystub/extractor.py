"""
Paystub extraction using Mindee API
"""
import os
import logging
from typing import Any, Dict
from mindee import ClientV2, InferenceParameters, PathInput

logger = logging.getLogger(__name__)

# Load configuration from environment
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_PAYSTUB = os.getenv("MINDEE_MODEL_ID_PAYSTUB", "ba548707-66d2-48c3-83f3-599484b078c8").strip()

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
    if raw_text and not isinstance(raw_text, str):
        raw_text = str(raw_text)
    return {"fields": simple_fields, "raw_text": raw_text}


def extract_paystub(file_path: str) -> Dict[str, Any]:
    """
    Extract paystub data using Mindee API

    Args:
        file_path: Path to the paystub image/PDF file

    Returns:
        Dictionary containing extracted paystub data
    """
    try:
        out = _run_model(file_path, MINDEE_MODEL_ID_PAYSTUB)
        fields = out["fields"]
    except Exception as e:
        logger.error(f"Paystub extraction error: {e}", exc_info=True)
        raise

    # Mindee returns first_name and last_name separately, combine them for employee_name
    first_name = fields.get("first_name", "")
    last_name = fields.get("last_name", "")
    employee_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else fields.get("employee_name")

    extracted = {
        "employer_name": fields.get("employer_name") or fields.get("company_name"),
        "company_name": fields.get("employer_name") or fields.get("company_name"),
        "employee_name": employee_name,
        "employee_id": fields.get("employee_id"),
        "pay_period_start": fields.get("pay_period_start_date") or fields.get("pay_period_start"),
        "pay_period_end": fields.get("pay_period_end_date") or fields.get("pay_period_end"),
        "pay_date": fields.get("pay_date"),
        "gross_pay": fields.get("gross_pay"),
        "net_pay": fields.get("net_pay"),
        "taxes": fields.get("taxes"),
        "deductions": fields.get("deductions"),
        "ytd_gross": fields.get("ytd_gross") or fields.get("ytd_gross_pay") or fields.get("year_to_date_gross"),
        "ytd_net": fields.get("ytd_net") or fields.get("ytd_net_pay") or fields.get("year_to_date_net"),
        "first_name": first_name,
        "last_name": last_name,
        "employee_address": fields.get("employee_address"),
        "employer_address": fields.get("employer_address"),
        "social_security_number": fields.get("social_security_number"),
        "raw_ocr_text": out.get("raw_text", ""),
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}

