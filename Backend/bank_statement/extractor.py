"""
Bank Statement extraction using Mindee API
"""
import os
import logging
from typing import Any, Dict
from mindee import ClientV2, InferenceParameters, PathInput

logger = logging.getLogger(__name__)

# Load configuration from environment
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_BANK_STATEMENT = os.getenv("MINDEE_MODEL_ID_BANK_STATEMENT", "2b6cc7a4-6b0b-4178-a8f8-00c626965d87").strip()

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


def extract_bank_statement(file_path: str) -> Dict[str, Any]:
    """
    Extract bank statement data using Mindee API

    Args:
        file_path: Path to the bank statement image/PDF file

    Returns:
        Dictionary containing extracted bank statement data
    """
    out = _run_model(file_path, MINDEE_MODEL_ID_BANK_STATEMENT)
    fields = out["fields"]

    # Mindee returns account_holder_names as a list, extract first name
    account_holder_names = fields.get("account_holder_names", [])
    account_holder = account_holder_names[0] if account_holder_names and len(account_holder_names) > 0 else fields.get("account_holder")

    extracted = {
        "bank_name": fields.get("bank_name"),
        # Mindee uses 'account_holder_names' (list) instead of 'account_holder'
        "account_holder": account_holder,
        "account_number": fields.get("account_number"),
        # Mindee uses 'statement_period_start_date' and 'statement_period_end_date'
        "statement_period_start": fields.get("statement_period_start_date") or fields.get("statement_period_start"),
        "statement_period_end": fields.get("statement_period_end_date") or fields.get("statement_period_end"),
        # Mindee uses 'beginning_balance' instead of 'opening_balance'
        "opening_balance": fields.get("beginning_balance") or fields.get("opening_balance"),
        # Mindee uses 'ending_balance' instead of 'closing_balance'
        "closing_balance": fields.get("ending_balance") or fields.get("closing_balance"),
        # Additional Mindee fields
        "statement_date": fields.get("statement_date"),
        "account_type": fields.get("account_type"),
        "currency": fields.get("currency"),
        "total_credits": fields.get("total_credits"),
        "total_debits": fields.get("total_debits"),
        "transactions": fields.get("list_of_transactions", []),
        "account_holder_names": account_holder_names,
        "account_holder_address": fields.get("account_holder_address"),
        "bank_address": fields.get("bank_address"),
        "raw_ocr_text": out["raw_text"],
        "fields": fields,
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}
