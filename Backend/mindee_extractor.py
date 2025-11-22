"""
Mindee-powered extractors for each supported document type.
"""

import os
from typing import Any, Dict

from mindee import ClientV2, InferenceParameters, PathInput

MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_GLOBAL = os.getenv("MINDEE_MODEL_ID_GLOBAL", "").strip()
MINDEE_MODEL_ID_CHECK = os.getenv("MINDEE_MODEL_ID_CHECK", "").strip()
MINDEE_MODEL_ID_PAYSTUB = os.getenv("MINDEE_MODEL_ID_PAYSTUB", "").strip()
MINDEE_MODEL_ID_BANK_STATEMENT = os.getenv("MINDEE_MODEL_ID_BANK_STATEMENT", "").strip()
MINDEE_MODEL_ID_MONEY_ORDER = os.getenv("MINDEE_MODEL_ID_MONEY_ORDER", "").strip()

_DEFAULT_MODELS = {
    "global": "7ecd4b47-c7a0-430c-ac68-a68b04960a39",
    "check": "046edc76-e8a4-4e11-a9a3-bb8632250446",
    "paystub": "ba548707-66d2-48c3-83f3-599484b078c8",
    "bank_statement": "2b6cc7a4-6b0b-4178-a8f8-00c626965d87",
    "money_order": "7ecd4b47-c7a0-430c-ac68-a68b04960a39",
}

MINDEE_MODEL_ID_GLOBAL = MINDEE_MODEL_ID_GLOBAL or _DEFAULT_MODELS["global"]
MINDEE_MODEL_ID_CHECK = MINDEE_MODEL_ID_CHECK or _DEFAULT_MODELS["check"]
MINDEE_MODEL_ID_PAYSTUB = MINDEE_MODEL_ID_PAYSTUB or _DEFAULT_MODELS["paystub"]
MINDEE_MODEL_ID_BANK_STATEMENT = MINDEE_MODEL_ID_BANK_STATEMENT or _DEFAULT_MODELS["bank_statement"]
MINDEE_MODEL_ID_MONEY_ORDER = MINDEE_MODEL_ID_MONEY_ORDER or _DEFAULT_MODELS["money_order"]

if not MINDEE_API_KEY:
    raise RuntimeError("MINDEE_API_KEY is not set")

mindee_client = ClientV2(MINDEE_API_KEY)


def _run_model(file_path: str, model_id: str) -> Dict[str, Any]:
    import logging
    logger = logging.getLogger(__name__)

    params = InferenceParameters(model_id=model_id or MINDEE_MODEL_ID_GLOBAL, raw_text=True, confidence=True)
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


def extract_paystub(file_path: str) -> Dict[str, Any]:
    out = _run_model(file_path, MINDEE_MODEL_ID_PAYSTUB)
    fields = out["fields"]

    # Mindee returns first_name and last_name separately, combine them for employee_name
    first_name = fields.get("first_name", "")
    last_name = fields.get("last_name", "")
    employee_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else fields.get("employee_name")

    extracted = {
        "employer_name": fields.get("employer_name") or fields.get("company_name"),
        "employee_name": employee_name,
        "employee_id": fields.get("employee_id"),
        # Mindee uses 'pay_period_start_date' and 'pay_period_end_date'
        "pay_period_start": fields.get("pay_period_start_date") or fields.get("pay_period_start"),
        "pay_period_end": fields.get("pay_period_end_date") or fields.get("pay_period_end"),
        "pay_date": fields.get("pay_date"),
        "gross_pay": fields.get("gross_pay"),
        "net_pay": fields.get("net_pay"),
        "taxes": fields.get("taxes"),
        "deductions": fields.get("deductions"),
        "ytd_gross": fields.get("ytd_gross"),
        "ytd_net": fields.get("ytd_net"),
        # Additional Mindee fields
        "first_name": first_name,
        "last_name": last_name,
        "employee_address": fields.get("employee_address"),
        "employer_address": fields.get("employer_address"),
        "social_security_number": fields.get("social_security_number"),
        "raw_ocr_text": out["raw_text"],
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}


def extract_money_order(file_path: str) -> Dict[str, Any]:
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


def extract_bank_statement(file_path: str) -> Dict[str, Any]:
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
