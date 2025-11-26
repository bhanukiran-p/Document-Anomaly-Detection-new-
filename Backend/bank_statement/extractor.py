"""
Bank Statement extraction using Mindee API
"""
import os
import logging
import re
from typing import Any, Dict, Optional
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
    params = InferenceParameters(model_id=model_id, raw_text=True)
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


def _extract_from_raw_text(raw_text: str, field_name: str) -> Optional[str]:
    """
    Fallback extraction from raw text using regex patterns for bank statement fields
    
    Args:
        raw_text: Raw OCR text from the document
        field_name: Name of the field to extract
        
    Returns:
        Extracted value or None
    """
    if not raw_text:
        return None
    
    patterns = {
        'bank_name': [
            r'bank[:\s]+([A-Z][A-Za-z\s&,\.]+(?:Bank|National|Banking|Credit\s+Union)?)',
            r'([A-Z][A-Za-z\s&,\.]+(?:Bank|National|Banking|Credit\s+Union))',
            r'chase',
            r'bank\s+of\s+america|bofa',
            r'wells\s+fargo',
            r'citibank|citi',
            r'us\s+bank',
            r'pnc\s+bank',
            r'td\s+bank',
            r'capital\s+one',
        ],
        'account_holder': [
            r'account\s+holder[:\s]+([A-Z][A-Za-z\s,]+)',
            r'customer\s+name[:\s]+([A-Z][A-Za-z\s,]+)',
            r'name[:\s]+([A-Z][A-Z][A-Za-z\s,]+)',  # At least 2 capital letters (first and last name)
            r'account\s+owner[:\s]+([A-Z][A-Za-z\s,]+)',
        ],
        'account_number': [
            r'account\s+number[:\s]+([\d-]+)',
            r'account\s+no[:\s]+([\d-]+)',
            r'acct[:\s]+([\d-]+)',
            r'account[:\s]+([\d-]+)',
            r'account\s+ending[:\s]+([\d]+)',
        ],
        'statement_period_start': [
            r'statement\s+period[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'period[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'from[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'beginning[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ],
        'statement_period_end': [
            r'through[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'to[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'ending[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'statement\s+period[:\s]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+through\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ],
        'opening_balance': [
            r'beginning\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'opening\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'starting\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'previous\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'balance\s+forward[:\s$]*([\d,]+\.?\d{2})',
        ],
        'closing_balance': [
            r'ending\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'closing\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'final\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'current\s+balance[:\s$]*([\d,]+\.?\d{2})',
            r'new\s+balance[:\s$]*([\d,]+\.?\d{2})',
        ],
    }
    
    if field_name not in patterns:
        return None
    
    # Special handling for bank_name (case-insensitive brand name matching)
    if field_name == 'bank_name':
        text_lower = raw_text.lower()
        for pattern in patterns[field_name]:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                bank_name = match.group(1).strip() if match.lastindex else match.group(0).strip()
                # Format common banks
                if 'chase' in bank_name.lower():
                    return 'Chase'
                elif 'bank of america' in bank_name.lower() or 'bofa' in bank_name.lower():
                    return 'Bank of America'
                elif 'wells fargo' in bank_name.lower():
                    return 'Wells Fargo'
                elif 'citibank' in bank_name.lower() or 'citi' in bank_name.lower():
                    return 'Citibank'
                elif 'us bank' in bank_name.lower():
                    return 'U.S. Bank'
                elif 'pnc' in bank_name.lower():
                    return 'PNC Bank'
                elif 'td bank' in bank_name.lower():
                    return 'TD Bank'
                elif 'capital one' in bank_name.lower():
                    return 'Capital One'
                return bank_name.title()
        return None
    
    # For other fields, use standard pattern matching
    for pattern in patterns[field_name]:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip() if match.lastindex else match.group(0).strip()
            # Clean up numeric values (remove commas, ensure proper format)
            if field_name in ['opening_balance', 'closing_balance']:
                value = value.replace(',', '').replace('$', '')
            logger.info(f"Extracted {field_name} from raw text: {value}")
            return value
    
    return None


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
    raw_text = out.get("raw_text", "")

    # Extract fields with fallback to raw text extraction
    bank_name = fields.get("bank_name")
    if not bank_name:
        bank_name = _extract_from_raw_text(raw_text, "bank_name")
    
    # Mindee returns account_holder_names as a list, extract first name
    account_holder_names = fields.get("account_holder_names", [])
    account_holder = account_holder_names[0] if account_holder_names and len(account_holder_names) > 0 else fields.get("account_holder")
    if not account_holder:
        account_holder = _extract_from_raw_text(raw_text, "account_holder")
    
    account_number = fields.get("account_number")
    if not account_number:
        account_number = _extract_from_raw_text(raw_text, "account_number")
    
    statement_period_start = fields.get("statement_period_start_date") or fields.get("statement_period_start")
    if not statement_period_start:
        statement_period_start = _extract_from_raw_text(raw_text, "statement_period_start")
    
    statement_period_end = fields.get("statement_period_end_date") or fields.get("statement_period_end")
    if not statement_period_end:
        statement_period_end = _extract_from_raw_text(raw_text, "statement_period_end")
    
    opening_balance = fields.get("beginning_balance") or fields.get("opening_balance")
    if not opening_balance:
        opening_balance = _extract_from_raw_text(raw_text, "opening_balance")
    
    closing_balance = fields.get("ending_balance") or fields.get("closing_balance")
    if not closing_balance:
        closing_balance = _extract_from_raw_text(raw_text, "closing_balance")

    extracted = {
        "bank_name": bank_name,
        # Mindee uses 'account_holder_names' (list) instead of 'account_holder'
        "account_holder": account_holder,
        "account_number": account_number,
        # Mindee uses 'statement_period_start_date' and 'statement_period_end_date'
        "statement_period_start": statement_period_start,
        "statement_period_end": statement_period_end,
        # Mindee uses 'beginning_balance' instead of 'opening_balance'
        "opening_balance": opening_balance,
        # Mindee uses 'ending_balance' instead of 'closing_balance'
        "closing_balance": closing_balance,
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
        "raw_ocr_text": raw_text,
        "fields": fields,
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}
