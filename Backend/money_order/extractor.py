"""
Money Order extraction using Mindee API
"""
import os
import logging
import re
from typing import Any, Dict, Optional
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


def _extract_from_raw_text(raw_text: str, field_name: str) -> Optional[str]:
    """
    Fallback extraction from raw text using regex patterns for money order fields
    
    Args:
        raw_text: Raw OCR text from the document
        field_name: Name of the field to extract
        
    Returns:
        Extracted value or None
    """
    if not raw_text:
        return None
    
    patterns = {
        'issuer': [
            r'western\s+union',
            r'moneygram',
            r'usps|u\.s\.\s+postal\s+service|united\s+states\s+postal\s+service',
            r'american\s+express',
            r'postal\s+service',
            r'walmart\s+money\s+order|walmart',
            r'kroger\s+money\s+order|kroger',
            r'7-eleven|7eleven|seven\s+eleven',
            r'cvs\s+pharmacy|cvs',
            r'walgreens',
            r'rite\s+aid',
            r'giant\s+eagle',
            r'publix',
            r'safeway',
            r'k\s+mart|kmart',
        ],
        'date': [
            r'date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'issue\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'purchase\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'issued[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Generic date pattern
        ],
        'location': [
            r'location[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'purchased\s+at[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'issued\s+at[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'agent\s+location[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'agent[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'store[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
        ],
        'amount_in_words': [
            r'amount\s+in\s+words[:\s]+([A-Z][A-Za-z\s-]+)',
            r'pay\s+the\s+sum\s+of[:\s]+([A-Z][A-Za-z\s-]+)',
            r'([A-Z][A-Za-z\s-]+\s+dollars?\s+and\s+[A-Z][A-Za-z\s-]+\s+cents?)',
            r'([A-Z][A-Za-z\s-]+\s+dollars?)',
        ],
        'receipt_number': [
            r'receipt\s+number[:\s]+([A-Z0-9-]+)',
            r'receipt\s+no[:\s]+([A-Z0-9-]+)',
            r'receipt[:\s]+([A-Z0-9-]+)',
        ],
        'signature': [
            r'signature[:\s]+([A-Z][A-Za-z\s]+)',
            r'signed[:\s]+([A-Z][A-Za-z\s]+)',
            r'purchaser\s+signature[:\s]+([A-Z][A-Za-z\s]+)',
        ],
    }
    
    if field_name not in patterns:
        return None
    
    # Special handling for issuer (case-insensitive brand name matching)
    if field_name == 'issuer':
        text_lower = raw_text.lower()
        for pattern in patterns[field_name]:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Capitalize the issuer name properly
                issuer_name = match.group(0).strip()
                # Format common issuers
                if 'western union' in issuer_name:
                    return 'Western Union'
                elif 'moneygram' in issuer_name:
                    return 'MoneyGram'
                elif 'usps' in issuer_name or 'u.s. postal service' in issuer_name or 'postal service' in issuer_name:
                    return 'USPS'
                elif 'american express' in issuer_name:
                    return 'American Express'
                elif 'walmart' in issuer_name:
                    return 'Walmart'
                elif 'kroger' in issuer_name:
                    return 'Kroger'
                elif '7-eleven' in issuer_name or '7eleven' in issuer_name:
                    return '7-Eleven'
                elif 'cvs' in issuer_name:
                    return 'CVS'
                elif 'walgreens' in issuer_name:
                    return 'Walgreens'
                elif 'rite aid' in issuer_name:
                    return 'Rite Aid'
                elif 'giant eagle' in issuer_name:
                    return 'Giant Eagle'
                elif 'publix' in issuer_name:
                    return 'Publix'
                elif 'safeway' in issuer_name:
                    return 'Safeway'
                elif 'k mart' in issuer_name or 'kmart' in issuer_name:
                    return 'Kmart'
                return issuer_name.title()
        return None
    
    # For other fields, use standard pattern matching
    for pattern in patterns[field_name]:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip() if match.lastindex else match.group(0).strip()
            logger.info(f"Extracted {field_name} from raw text: {value}")
            return value
    
    return None


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
    raw_text = out.get("raw_text", "")
    
    # Extract fields with fallback to raw text extraction
    issuer = fields.get("issuer")
    if not issuer:
        issuer = _extract_from_raw_text(raw_text, "issuer")
    
    date = fields.get("issue_date") or fields.get("date")
    if not date:
        date = _extract_from_raw_text(raw_text, "date")
    
    location = fields.get("location") or fields.get("address")
    if not location:
        location = _extract_from_raw_text(raw_text, "location")
        # If location extraction failed, try to construct from city/state
        if not location:
            city = fields.get("city")
            state = fields.get("state")
            if city or state:
                location = ", ".join(filter(None, [city, state]))
    
    amount_in_words = fields.get("amount_in_words") or fields.get("word_amount")
    if not amount_in_words:
        amount_in_words = _extract_from_raw_text(raw_text, "amount_in_words")
    
    receipt_number = fields.get("receipt_number")
    if not receipt_number:
        receipt_number = _extract_from_raw_text(raw_text, "receipt_number")
    
    signature = fields.get("signature")
    if not signature:
        signature = _extract_from_raw_text(raw_text, "signature")
    
    extracted = {
        "issuer": issuer or "",
        # Mindee uses 'payer' instead of 'purchaser'
        "purchaser": fields.get("payer") or fields.get("purchaser"),
        "payee": fields.get("payee"),
        "amount": fields.get("amount"),
        "date": date,
        # Mindee uses 'money_order_number' instead of 'serial_number'
        "serial_number": fields.get("money_order_number") or fields.get("serial_number"),
        "location": location,
        "amount_in_words": amount_in_words,
        "receipt_number": receipt_number,
        "signature": signature,
        # Additional Mindee fields
        "money_order_number": fields.get("money_order_number"),
        "address": fields.get("address"),
        "city": fields.get("city"),
        "state": fields.get("state"),
        "zip_code": fields.get("zip_code"),
        "raw_ocr_text": raw_text,
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}
