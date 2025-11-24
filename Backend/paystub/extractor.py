"""
Paystub extraction using Mindee API
"""
import os
import logging
import re
from typing import Any, Dict, Optional
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


def _extract_ytd_value(raw_text: str, field_type: str) -> Optional[str]:
    """
    Specialized extraction for YTD values with multiple strategies
    
    Args:
        raw_text: Raw OCR text from the document
        field_type: 'gross' or 'net'
        
    Returns:
        Extracted YTD value or None
    """
    if not raw_text:
        return None
    
    # Strategy 0: Direct table format extraction (most reliable for structured paystubs)
    # Look for the exact format: "YTD GROSS:" or "YTD NET PAY:" followed by value
    if field_type == 'gross':
        # Try exact format first: "YTD GROSS: 7,500.00"
        direct_patterns = [
            r'ytd\s+gross[:\s]+([\d,]+\.\d{2})',  # YTD GROSS: 7,500.00
            r'ytd\s+gross\s+([\d,]+\.\d{2})',  # YTD GROSS 7,500.00
        ]
        for pattern in direct_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip().replace(',', '')
                logger.info(f"Extracted YTD {field_type} via direct pattern: {value}")
                return value
    else:  # net
        # Try exact format first: "YTD NET PAY: 5,017.52"
        direct_patterns = [
            r'ytd\s+net\s+pay[:\s]+([\d,]+\.\d{2})',  # YTD NET PAY: 5,017.52
            r'ytd\s+net\s+pay\s+([\d,]+\.\d{2})',  # YTD NET PAY 5,017.52
            r'ytd\s+net[:\s]+([\d,]+\.\d{2})',  # YTD NET: 5,017.52
        ]
        for pattern in direct_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip().replace(',', '')
                # Validate it's different from gross
                gross_match = re.search(r'ytd\s+gross[:\s]+([\d,]+\.\d{2})', raw_text, re.IGNORECASE)
                if gross_match:
                    gross_value = gross_match.group(1).strip().replace(',', '')
                    if value == gross_value:
                        logger.warning(f"YTD Net value ({value}) matches Gross, skipping")
                        continue
                logger.info(f"Extracted YTD {field_type} via direct pattern: {value}")
                return value
    
    # Strategy 1: Look for specific patterns with negative lookahead to avoid confusion
    if field_type == 'gross':
        # For gross, make sure we don't match "net"
        patterns = [
            r'ytd\s+gross[:\s]+\$?\s*([\d,]+\.\d{2})',  # YTD GROSS: 7,500.00 (with colon)
            r'ytd\s+gross(?!\s+net)(?!\s+pay)[:\s]*\$?\s*([\d,]+\.?\d{2})',  # YTD GROSS (not NET)
            r'ytd\s+gross[:\s]*\$?\s*([\d,]+\.?\d{2})',
            r'ytd\s+gross[:\s]*([\d,]+\.?\d{2})',
            r'year\s+to\s+date\s+gross[:\s]*\$?\s*([\d,]+\.?\d{2})',
            r'gross\s+ytd[:\s]*\$?\s*([\d,]+\.?\d{2})',
        ]
    else:  # net
        # For net, look specifically for "YTD NET PAY" or "YTD NET" but not "YTD GROSS"
        patterns = [
            r'ytd\s+net\s+pay[:\s]+\$?\s*([\d,]+\.\d{2})',  # YTD NET PAY: 5,017.52 (with colon, most specific)
            r'ytd\s+net\s+pay[:\s]*\$?\s*([\d,]+\.?\d{2})',  # YTD NET PAY (most specific)
            r'ytd\s+net(?!\s+gross)[:\s]+\$?\s*([\d,]+\.\d{2})',  # YTD NET: (with colon, not GROSS)
            r'ytd\s+net(?!\s+gross)[:\s]*\$?\s*([\d,]+\.?\d{2})',  # YTD NET (not GROSS)
            r'ytd\s+net[:\s]*\$?\s*([\d,]+\.?\d{2})',
            r'ytd\s+net[:\s]*([\d,]+\.?\d{2})',
            r'year\s+to\s+date\s+net[:\s]*\$?\s*([\d,]+\.?\d{2})',
            r'net\s+pay\s+ytd[:\s]*\$?\s*([\d,]+\.?\d{2})',
            r'net\s+ytd[:\s]*\$?\s*([\d,]+\.?\d{2})',
        ]
    
    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip().replace(',', '')
            logger.info(f"Extracted YTD {field_type} via pattern: {value}")
            return value
    
    # Strategy 2: Look for table-like structures with YTD in one column and value in next
    # Use more specific patterns to avoid confusion
    if field_type == 'gross':
        ytd_pattern = r'ytd\s+gross(?!\s+net)(?!\s+pay)'
    else:  # net
        ytd_pattern = r'ytd\s+net\s+pay|ytd\s+net(?!\s+gross)'
    
    match = re.search(ytd_pattern, raw_text, re.IGNORECASE)
    if match:
        # Look for number after YTD GROSS/NET (within 100 chars, but stop at next YTD field)
        start_pos = match.end()
        remaining_text = raw_text[start_pos:start_pos + 150]
        # Stop if we encounter another YTD field
        next_ytd = re.search(r'\bytd\s+', remaining_text, re.IGNORECASE)
        if next_ytd:
            remaining_text = remaining_text[:next_ytd.start()]
        
        # Look for dollar amount pattern (prefer 2 decimal places)
        amount_match = re.search(r'[:\s]*\$?\s*([\d,]+\.\d{2})', remaining_text)
        if amount_match:
            value = amount_match.group(1).strip().replace(',', '')
            logger.info(f"Extracted YTD {field_type} via proximity: {value}")
            return value
        # Look for number without dollar sign
        amount_match = re.search(r'[:\s]*([\d,]+\.\d{2})', remaining_text)
        if amount_match:
            value = amount_match.group(1).strip().replace(',', '')
            logger.info(f"Extracted YTD {field_type} via proximity (no $): {value}")
            return value
    
    # Strategy 3: Look for "YTD:" followed by gross/net in summary section
    summary_pattern = rf'ytd[:\s]+{field_type}[:\s]*\$?\s*([\d,]+\.?\d{{2}})'
    match = re.search(summary_pattern, raw_text, re.IGNORECASE)
    if match:
        value = match.group(1).strip().replace(',', '')
        logger.info(f"Extracted YTD {field_type} via summary pattern: {value}")
        return value
    
    # Strategy 4: Look for YTD and field_type separately but close together (within 30 chars)
    # This handles cases where they might be on different lines or separated
    ytd_positions = []
    for match in re.finditer(r'ytd', raw_text, re.IGNORECASE):
        ytd_positions.append(match.start())
    
    # For net, look specifically for "net pay" or just "net" (but not "gross")
    if field_type == 'net':
        field_pattern = r'\bnet\s+pay\b|\bnet\b(?!\s+gross)'
    else:
        field_pattern = r'\bgross\b(?!\s+net)'
    
    field_positions = []
    for match in re.finditer(field_pattern, raw_text, re.IGNORECASE):
        field_positions.append(match.start())
    
    # Check if YTD and field_type are close together
    for ytd_pos in ytd_positions:
        for field_pos in field_positions:
            distance = abs(ytd_pos - field_pos)
            if distance < 40:  # Within 40 characters
                # Look for number after the field_type, but stop at next YTD field
                search_start = max(ytd_pos, field_pos)
                search_text = raw_text[search_start:search_start + 80]
                # Stop if we encounter another YTD field
                next_ytd = re.search(r'\bytd\s+', search_text, re.IGNORECASE)
                if next_ytd:
                    search_text = search_text[:next_ytd.start()]
                
                amount_match = re.search(r'[:\s]*\$?\s*([\d,]+\.\d{2})', search_text)
                if amount_match:
                    value = amount_match.group(1).strip().replace(',', '')
                    logger.info(f"Extracted YTD {field_type} via proximity search: {value}")
                    return value
    
    # Strategy 5: Look for common paystub summary patterns with context validation
    if field_type == 'gross':
        summary_patterns = [
            r'ytd\s+gross(?!\s+net)(?!\s+pay)[:\s]+([\d,]{1,10}\.\d{2})',
            r'ytd\s+gross\s+([\d,]{1,10}\.\d{2})',
        ]
    else:  # net
        summary_patterns = [
            r'ytd\s+net\s+pay[:\s]+([\d,]{1,10}\.\d{2})',  # Most specific first
            r'ytd\s+net(?!\s+gross)[:\s]+([\d,]{1,10}\.\d{2})',
            r'ytd\s+net\s+([\d,]{1,10}\.\d{2})',
        ]
    
    for pattern in summary_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip().replace(',', '')
            # Validate: for net, make sure the value is different from gross (if gross was found)
            if field_type == 'net':
                gross_match = re.search(r'ytd\s+gross[:\s]*\$?\s*([\d,]+\.?\d{2})', raw_text, re.IGNORECASE)
                if gross_match:
                    gross_value = gross_match.group(1).strip().replace(',', '')
                    if value == gross_value:
                        logger.warning(f"YTD Net value matches YTD Gross ({value}), skipping to avoid duplicate")
                        continue  # Skip this match, try next pattern
            logger.info(f"Extracted YTD {field_type} via summary pattern: {value}")
            return value
    
    # Strategy 6: For net specifically, try to find it in a table structure after gross
    if field_type == 'net':
        # Find YTD GROSS first, then look for NET PAY after it
        gross_match = re.search(r'ytd\s+gross[:\s]*\$?\s*([\d,]+\.?\d{2})', raw_text, re.IGNORECASE)
        if gross_match:
            # Look for YTD NET PAY after the gross value (not just NET PAY)
            search_start = gross_match.end()
            search_text = raw_text[search_start:search_start + 300]
            # Stop at next section or end
            next_section = re.search(r'\n\s*(?:total|deductions|current)', search_text, re.IGNORECASE)
            if next_section:
                search_text = search_text[:next_section.start()]
            
            # Look for "YTD NET PAY" specifically (most specific)
            net_match = re.search(r'ytd\s+net\s+pay[:\s]*\$?\s*([\d,]+\.\d{2})', search_text, re.IGNORECASE)
            if net_match:
                value = net_match.group(1).strip().replace(',', '')
                gross_value = gross_match.group(1).strip().replace(',', '')
                if value != gross_value:  # Make sure they're different
                    logger.info(f"Extracted YTD net via table structure: {value}")
                    return value
            
            # Fallback: Look for "NET PAY" after YTD section
            net_match = re.search(r'net\s+pay[:\s]*\$?\s*([\d,]+\.\d{2})', search_text, re.IGNORECASE)
            if net_match:
                value = net_match.group(1).strip().replace(',', '')
                gross_value = gross_match.group(1).strip().replace(',', '')
                if value != gross_value:  # Make sure they're different
                    logger.info(f"Extracted YTD net via table structure (fallback): {value}")
                    return value
    
    logger.warning(f"Could not extract YTD {field_type} from raw text")
    return None


def _extract_from_raw_text(raw_text: str, field_name: str) -> Optional[str]:
    """
    Fallback extraction from raw text using regex patterns
    
    Args:
        raw_text: Raw OCR text from the document
        field_name: Name of the field to extract
        
    Returns:
        Extracted value or None
    """
    if not raw_text:
        return None
    
    # Use specialized extraction for YTD values
    if field_name == 'ytd_gross':
        return _extract_ytd_value(raw_text, 'gross')
    elif field_name == 'ytd_net':
        return _extract_ytd_value(raw_text, 'net')
    
    patterns = {
        'pay_date': [
            r'pay\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'date\s+paid[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'check\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'pay\s+date[:\s]+(\d{4}-\d{2}-\d{2})',  # ISO format
        ],
        'company_name': [
            r'company[:\s]+([A-Z][A-Za-z\s&,\.]+(?:Corporation|Corp|Inc|LLC|Ltd|Company)?)',
            r'employer[:\s]+([A-Z][A-Za-z\s&,\.]+(?:Corporation|Corp|Inc|LLC|Ltd|Company)?)',
            r'^([A-Z][A-Za-z\s&,\.]+(?:Corporation|Corp|Inc|LLC|Ltd|Company))',  # Company name at start of line
            r'^([A-Z][A-Za-z\s&,\.]+(?:Corporation|Corp|Inc|LLC|Ltd|Company|Finance|Financial|Group))',  # More flexible pattern
        ],
    }
    
    if field_name not in patterns:
        return None
    
    for pattern in patterns[field_name]:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            # Clean up the value
            if field_name in ['ytd_gross', 'ytd_net']:
                # Remove commas and return as number string
                value = value.replace(',', '')
            return value
    
    return None


def extract_paystub(file_path: str) -> Dict[str, Any]:
    """
    Extract paystub data using Mindee API

    Args:
        file_path: Path to the paystub image/PDF file

    Returns:
        Dictionary containing extracted paystub data
    """
    out = _run_model(file_path, MINDEE_MODEL_ID_PAYSTUB)
    fields = out["fields"]

    # Mindee returns first_name and last_name separately, combine them for employee_name
    first_name = fields.get("first_name", "")
    last_name = fields.get("last_name", "")
    employee_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else fields.get("employee_name")

    raw_text = out.get("raw_text", "")
    
    # Extract fields with fallback to raw text extraction
    employer_name = fields.get("employer_name") or fields.get("company_name")
    if not employer_name:
        employer_name = _extract_from_raw_text(raw_text, "company_name")
    
    pay_date = fields.get("pay_date")
    if not pay_date:
        pay_date = _extract_from_raw_text(raw_text, "pay_date")
    
    # Extract YTD values - check multiple possible field names and formats
    ytd_gross = fields.get("ytd_gross") or fields.get("ytd_gross_pay") or fields.get("year_to_date_gross")
    # Check if value is meaningful (not empty string, None, or "N/A")
    if not ytd_gross or str(ytd_gross).strip().upper() in ['', 'N/A', 'NONE', 'NULL']:
        logger.info("YTD Gross not found in Mindee fields, attempting raw text extraction...")
        ytd_gross = _extract_from_raw_text(raw_text, "ytd_gross")
        if ytd_gross:
            logger.info(f"Successfully extracted YTD Gross from raw text: {ytd_gross}")
        else:
            logger.warning("YTD Gross extraction failed from both Mindee and raw text")
    
    ytd_net = fields.get("ytd_net") or fields.get("ytd_net_pay") or fields.get("year_to_date_net")
    # Check if value is meaningful
    if not ytd_net or str(ytd_net).strip().upper() in ['', 'N/A', 'NONE', 'NULL']:
        logger.info("YTD Net not found in Mindee fields, attempting raw text extraction...")
        ytd_net = _extract_from_raw_text(raw_text, "ytd_net")
        if ytd_net:
            logger.info(f"Successfully extracted YTD Net from raw text: {ytd_net}")
        else:
            logger.warning("YTD Net extraction failed from both Mindee and raw text")

    extracted = {
        "employer_name": employer_name,
        "company_name": employer_name,  # Add alias for frontend compatibility
        "employee_name": employee_name,
        "employee_id": fields.get("employee_id"),
        # Mindee uses 'pay_period_start_date' and 'pay_period_end_date'
        "pay_period_start": fields.get("pay_period_start_date") or fields.get("pay_period_start"),
        "pay_period_end": fields.get("pay_period_end_date") or fields.get("pay_period_end"),
        "pay_date": pay_date,
        "gross_pay": fields.get("gross_pay"),
        "net_pay": fields.get("net_pay"),
        "taxes": fields.get("taxes"),
        "deductions": fields.get("deductions"),
        "ytd_gross": ytd_gross,
        "ytd_net": ytd_net,
        # Additional Mindee fields
        "first_name": first_name,
        "last_name": last_name,
        "employee_address": fields.get("employee_address"),
        "employer_address": fields.get("employer_address"),
        "social_security_number": fields.get("social_security_number"),
        "raw_ocr_text": raw_text,
    }
    return {"status": "success", "extracted_data": extracted, "raw_fields": fields}
