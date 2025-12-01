"""
Paystub extraction using Mindee API with ML Fraud Detection and AI Analysis
"""
import os
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from mindee import ClientV2, InferenceParameters, PathInput
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

logger = logging.getLogger(__name__)


def convert_to_json_serializable(obj: Any) -> Any:
    """
    Recursively convert NumPy types and other non-JSON-serializable types to native Python types

    Args:
        obj: Object to convert (can be dict, list, or primitive type)

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, (np.integer, np.int_)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_json_serializable(item) for item in obj)
    else:
        return obj


def _parse_currency_value(value: Any) -> Optional[float]:
    """Best-effort conversion of currency-like strings to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value_str = str(value).strip()
    if not value_str:
        return None
    # Remove currency symbols and commas
    cleaned = re.sub(r'[^0-9.\-]', '', value_str)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


ONES = [
    "ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE",
    "SIX", "SEVEN", "EIGHT", "NINE", "TEN", "ELEVEN",
    "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN",
    "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"
]
TENS = [
    "", "", "TWENTY", "THIRTY", "FORTY", "FIFTY",
    "SIXTY", "SEVENTY", "EIGHTY", "NINETY"
]
SCALES = [
    (1_000_000, "MILLION"),
    (1_000, "THOUSAND"),
    (100, "HUNDRED"),
]


def _convert_hundreds(number: int) -> str:
    """Convert number < 1000 to words."""
    words = []
    if number >= 100:
        words.append(f"{ONES[number // 100]} HUNDRED")
        number %= 100
    if number >= 20:
        words.append(TENS[number // 10])
        number %= 10
    if 0 < number < 20:
        words.append(ONES[number])
    if not words:
        words.append("ZERO")
    return " ".join(words)


def _number_to_words(amount: Optional[float]) -> Optional[str]:
    """Convert numeric amount to check-style words (uppercase)."""
    if amount is None:
        return None
    amount = round(float(amount), 2)
    dollars = int(amount)
    cents = int(round((amount - dollars) * 100))

    if dollars == 0:
        dollar_words = "ZERO"
    else:
        parts = []
        remainder = dollars
        for scale_value, scale_name in SCALES:
            if remainder >= scale_value:
                chunk = remainder // scale_value
                parts.append(f"{_convert_hundreds(chunk)} {scale_name}")
                remainder %= scale_value
        if remainder:
            parts.append(_convert_hundreds(remainder))
        dollar_words = " ".join(parts)

    return f"{dollar_words} AND {cents:02d}/100 DOLLARS"


def _normalize_pay_date(pay_date: str) -> str:
    """Normalize pay date to MM/DD/YYYY if possible."""
    if not pay_date:
        return ""
    pay_date = pay_date.strip()
    # Known paystub format like 03/01/14 or 03/01/2014
    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y", "%m-%d-%y"):
        try:
            dt = datetime.strptime(pay_date, fmt)
            # If 2-digit year parsed (year < 2000), assume 2000s
            if dt.year < 2000:
                dt = dt.replace(year=dt.year + 2000)
            return dt.strftime("%m/%d/%Y")
        except ValueError:
            continue
    return pay_date  # Fallback to original string


def _prepare_paystub_for_fraud_ml(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Map paystub fields into the structure expected by the fraud detector."""
    amount_numeric = (
        _parse_currency_value(extracted.get("net_pay"))
        or _parse_currency_value(extracted.get("gross_pay"))
    )
    amount_formatted = f"${amount_numeric:,.2f}" if amount_numeric is not None else None
    amount_words = _number_to_words(amount_numeric) if amount_numeric is not None else None

    serial_seed = (
        extracted.get("employee_id")
        or extracted.get("social_security_number")
        or extracted.get("pay_period_start")
        or "0000"
    )
    serial_clean = re.sub(r'[^A-Z0-9]', '', str(serial_seed).upper())
    serial_value = f"PAYROLL-{serial_clean or '0000'}"

    normalized_date = _normalize_pay_date(extracted.get("pay_date", ""))
    employer = extracted.get("company_name") or extracted.get("employer_name") or "Payroll"

    ml_ready = {
        **extracted,
        "issuer": "Payroll",
        "issuer_name": "Payroll",
        "serial_number": serial_value,
        "serial_primary": serial_value,
        "amount": amount_formatted or extracted.get("net_pay") or extracted.get("gross_pay"),
        "amount_numeric": amount_numeric or 0.0,
        "amount_in_words": amount_words,
        "amount_written": amount_words,
        "payee": extracted.get("employee_name"),
        "recipient": extracted.get("employee_name"),
        "purchaser": employer,
        "sender_name": employer,
        "sender_address": extracted.get("employer_address") or extracted.get("employee_address"),
        "signature": extracted.get("employee_name") or "PAYROLL SIGNATURE",
        "date": normalized_date,
        "location": extracted.get("employer_address"),
        "document_type": "paystub",
    }
    return ml_ready


def _evaluate_paystub_risk(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Heuristic risk evaluation tailored for paystubs."""
    score = 0.15  # base risk
    indicators: List[str] = []

    def add(weight: float, message: str):
        nonlocal score
        score += weight
        indicators.append(message)

    gross = _parse_currency_value(extracted.get("gross_pay"))
    net = _parse_currency_value(extracted.get("net_pay"))
    ytd_gross = _parse_currency_value(extracted.get("ytd_gross"))
    ytd_net = _parse_currency_value(extracted.get("ytd_net"))

    if not extracted.get("company_name"):
        add(0.2, "Missing employer/company name")
    if not extracted.get("employee_name"):
        add(0.2, "Missing employee name")
    if gross is None:
        add(0.2, "Gross pay not detected")
    if net is None:
        add(0.2, "Net pay not detected")
    if gross is not None and net is not None:
        if net >= gross:
            add(0.35, "Net pay is greater than or equal to gross pay")
        if net <= 0 or gross <= 0:
            add(0.2, "Pay amounts look invalid (non-positive)")
    if ytd_gross is not None and gross is not None and ytd_gross < gross:
        add(0.2, "Year-to-date gross is less than current gross amount")
    if ytd_net is not None and net is not None and ytd_net < net:
        add(0.15, "Year-to-date net is less than current net amount")

    normalized_date = _normalize_pay_date(extracted.get("pay_date", ""))
    try:
        pay_date_obj = datetime.strptime(normalized_date, "%m/%d/%Y")
        age_days = (datetime.now() - pay_date_obj).days
        if age_days > 365:
            add(0.05, "Pay date is older than 12 months")
    except ValueError:
        if normalized_date:
            add(0.05, "Pay date format could not be validated")

    missing_fields = [field for field in ["employee_id", "social_security_number"] if not extracted.get(field)]
    if missing_fields:
        add(0.05, f"Missing identifiers: {', '.join(missing_fields)}")

    score = max(0.0, min(1.0, score))
    if score < 0.3:
        level = "LOW"
    elif score < 0.6:
        level = "MEDIUM"
    elif score < 0.85:
        level = "HIGH"
    else:
        level = "CRITICAL"

    return {
        "fraud_risk_score": round(score, 3),
        "risk_level": level,
        "model_confidence": 0.65,
        "feature_importance": indicators,
        "prediction_type": "paystub_rules"
    }


# Import ML models and AI agent
try:
    from ml_models.fraud_detector import MoneyOrderFraudDetector
    ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML fraud detector not available: {e}")
    ML_AVAILABLE = False
    MoneyOrderFraudDetector = None

# Import AI analysis agent
try:
    from langchain_agent.fraud_analysis_agent import FraudAnalysisAgent
    from langchain_agent.tools import DataAccessTools
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI fraud analysis agent not available: {e}")
    AI_AVAILABLE = False
    FraudAnalysisAgent = None
    DataAccessTools = None

# Load configuration from environment
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_PAYSTUB = os.getenv("MINDEE_MODEL_ID_PAYSTUB", "ba548707-66d2-48c3-83f3-599484b078c8").strip()

# Initialize Mindee client lazily to avoid import-time errors
mindee_client: Optional[ClientV2] = None

def get_mindee_client() -> ClientV2:
    """Get or create Mindee client"""
    global mindee_client
    if mindee_client is None:
        if not MINDEE_API_KEY:
            raise RuntimeError("MINDEE_API_KEY is not set in environment variables")
        mindee_client = ClientV2(MINDEE_API_KEY)
    return mindee_client


def _run_model(file_path: str, model_id: str) -> Dict[str, Any]:
    """Run Mindee model inference on a document"""
    try:
        client = get_mindee_client()
        params = InferenceParameters(model_id=model_id, raw_text=True)
        input_source = PathInput(file_path)
        response = client.enqueue_and_get_inference(input_source, params)
        
        if not response or not hasattr(response, 'inference'):
            raise ValueError("Invalid response from Mindee API: missing inference object")
        
        if not response.inference or not hasattr(response.inference, 'result'):
            raise ValueError("Invalid response from Mindee API: missing result object")
            
        result = response.inference.result
        if not result:
            raise ValueError("Invalid response from Mindee API: result is None")
            
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
        logger.info(f"Extracted fields summary: {simple_fields}")

        raw_text = getattr(result, "raw_text", "") or ""
        # Convert RawText object to string if it's not already a string
        if raw_text and not isinstance(raw_text, str):
            raw_text = str(raw_text)
        return {"fields": simple_fields, "raw_text": raw_text}
    except Exception as e:
        logger.error(f"Mindee API error: {e}", exc_info=True)
        raise RuntimeError(f"Failed to process document with Mindee API: {str(e)}")


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
    Extract paystub data using Mindee API with ML Fraud Detection and AI Analysis

    Args:
        file_path: Path to the paystub image/PDF file

    Returns:
        Dictionary containing extracted paystub data with ML and AI analysis
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        out = _run_model(file_path, MINDEE_MODEL_ID_PAYSTUB)
        fields = out["fields"]
    except Exception as e:
        logger.error(f"Paystub extraction error: {e}", exc_info=True)
        raise

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
        "employer_name": employer_name or "",
        "company_name": employer_name or "",  # Add alias for frontend compatibility
        "employee_name": employee_name or "",
        "employee_id": fields.get("employee_id") or "",
        # Mindee uses 'pay_period_start_date' and 'pay_period_end_date'
        "pay_period_start": fields.get("pay_period_start_date") or fields.get("pay_period_start") or "",
        "pay_period_end": fields.get("pay_period_end_date") or fields.get("pay_period_end") or "",
        "pay_date": pay_date or "",
        "gross_pay": fields.get("gross_pay") or "",
        "net_pay": fields.get("net_pay") or "",
        "taxes": fields.get("taxes") or "",
        "deductions": fields.get("deductions") or "",
        "ytd_gross": ytd_gross or "",
        "ytd_net": ytd_net or "",
        # Additional Mindee fields
        "first_name": first_name or "",
        "last_name": last_name or "",
        "employee_address": fields.get("employee_address") or "",
        "employer_address": fields.get("employer_address") or "",
        "social_security_number": fields.get("social_security_number") or "",
        "raw_ocr_text": raw_text,
    }

    # Perform ML fraud detection
    ml_analysis = None
    if ML_AVAILABLE and MoneyOrderFraudDetector:
        try:
            use_generic_ml = os.getenv('PAYSTUB_USE_GENERIC_ML', 'false').lower() == 'true'
            if use_generic_ml:
                logger.info("Starting ML fraud detection for paystub (generic model)...")
                model_dir = os.getenv('ML_MODEL_DIR', 'ml_models')
                fraud_detector = MoneyOrderFraudDetector(model_dir=model_dir)
                logger.info(f"Fraud detector initialized, models loaded: {fraud_detector.models_loaded}")

                paystub_data_for_ml = _prepare_paystub_for_fraud_ml(extracted)
                ml_analysis = fraud_detector.predict_fraud(paystub_data_for_ml, raw_text)
                logger.info("Generic ML fraud detection completed for paystub")
            else:
                logger.info("Using paystub-specific heuristic risk evaluation")
                ml_analysis = _evaluate_paystub_risk(extracted)
                logger.info(
                    "Paystub heuristic risk completed: risk_score=%s, risk_level=%s",
                    ml_analysis.get('fraud_risk_score'),
                    ml_analysis.get('risk_level')
                )
        except Exception as e:
            logger.error(f"ML fraud detection failed: {e}", exc_info=True)
            ml_analysis = {
                "error": str(e),
                "fraud_risk_score": 0.0,
                "risk_level": "UNKNOWN",
                "model_confidence": 0.0
            }
    else:
        logger.warning(f"ML fraud detection not available - ML_AVAILABLE: {ML_AVAILABLE}")
        ml_analysis = {
            "fraud_risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "model_confidence": 0.0,
            "error": "ML detection not available"
        }

    # Perform AI fraud analysis
    ai_analysis = None
    if AI_AVAILABLE and FraudAnalysisAgent and DataAccessTools:
        try:
            # Initialize data access tools for LangChain agent
            ml_scores_path = os.getenv('ML_SCORES_CSV', 'ml_models/mock_data/ml_scores.csv')
            customer_history_path = os.getenv('CUSTOMER_HISTORY_CSV', 'ml_models/mock_data/customer_history.csv')
            fraud_cases_path = os.getenv('FRAUD_CASES_CSV', 'ml_models/mock_data/fraud_cases.csv')

            data_tools = DataAccessTools(
                ml_scores_path=ml_scores_path,
                customer_history_path=customer_history_path,
                fraud_cases_path=fraud_cases_path
            )

            # Initialize AI fraud analysis agent
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                ai_agent = FraudAnalysisAgent(
                    api_key=openai_key,
                    model=os.getenv('AI_MODEL', 'gpt-3.5-turbo'),
                    data_tools=data_tools
                )

                ai_analysis = ai_agent.analyze_fraud(ml_analysis, extracted, customer_id=None)
                logger.info(f"AI fraud analysis completed: recommendation={ai_analysis.get('recommendation', 'N/A')}")
        except Exception as e:
            logger.error(f"AI fraud analysis failed: {e}", exc_info=True)

    # Generate anomalies list
    anomalies = _generate_anomalies(extracted, ml_analysis, ai_analysis)

    # Calculate overall confidence score
    confidence_score = _calculate_confidence_score(extracted, ml_analysis)

    # Convert numeric values to native Python types for JSON serialization
    confidence_score = float(confidence_score) if confidence_score is not None else 0.0
    extracted = convert_to_json_serializable(extracted)

    # Build complete response
    result = {
        "status": "success",
        "extracted_data": extracted,
        "raw_fields": convert_to_json_serializable(fields),
        "raw_text": raw_text,
        "timestamp": datetime.now().isoformat(),
        "anomalies": anomalies,
        "confidence_score": confidence_score
    }

    # Always add ML analysis to response (even if None or has error)
    if ml_analysis:
        # Convert NumPy types to JSON-serializable types
        ml_analysis_serializable = convert_to_json_serializable(ml_analysis)
        result["ml_analysis"] = ml_analysis_serializable
        result["ml_fraud_analysis"] = ml_analysis_serializable  # For backward compatibility
        if isinstance(ml_analysis_serializable, dict):
            logger.info(f"ML analysis added to response: {list(ml_analysis_serializable.keys())}")
    else:
        logger.warning("ML analysis is None - adding default structure")
        result["ml_analysis"] = {
            "fraud_risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "model_confidence": 0.0,
            "error": "ML analysis returned None"
        }
        result["ml_fraud_analysis"] = result["ml_analysis"]

    # Add AI analysis if available
    if ai_analysis:
        # Convert NumPy types to JSON-serializable types
        ai_analysis_serializable = convert_to_json_serializable(ai_analysis)
        result["ai_analysis"] = ai_analysis_serializable
        logger.info("AI analysis added to response")
    else:
        logger.info("AI analysis not available (LangChain not installed or OpenAI key not set)")

    logger.info(f"Final result keys: {list(result.keys())}")
    return result


def _generate_anomalies(extracted: Dict, ml_analysis: Optional[Dict], ai_analysis: Optional[Dict]) -> List[str]:
    """Generate list of anomalies based on ML and AI analysis"""
    anomalies = []

    if ml_analysis:
        risk_level = ml_analysis.get('risk_level', 'LOW')
        fraud_score = ml_analysis.get('fraud_risk_score', 0)

        if risk_level in ['HIGH', 'CRITICAL']:
            anomalies.append(f"High fraud risk detected: {risk_level} (score: {fraud_score:.2%})")

        # Check for specific fraud indicators
        feature_importance = ml_analysis.get('feature_importance', {})
        if isinstance(feature_importance, dict):
            for feature, importance in list(feature_importance.items())[:5]:
                if isinstance(importance, (int, float)) and importance > 0.1:
                    anomalies.append(f"Fraud indicator: {feature} (importance: {importance:.2%})")
        elif isinstance(feature_importance, list):
            for item in feature_importance[:5]:
                if isinstance(item, dict) and 'feature' in item and 'importance' in item:
                    importance = item.get('importance', 0)
                    if importance > 0.1:
                        feature = item.get('feature', 'Unknown')
                        anomalies.append(f"Fraud indicator: {feature} (importance: {importance:.2%})")

    if ai_analysis:
        recommendation = ai_analysis.get('recommendation', '')
        if recommendation and recommendation != 'APPROVE':
            anomalies.append(f"AI recommendation: {recommendation}")

        risk_factors = ai_analysis.get('risk_factors', [])
        anomalies.extend(risk_factors)

    # Basic validation checks
    gross_pay = extracted.get('gross_pay')
    net_pay = extracted.get('net_pay')
    
    if gross_pay and net_pay:
        try:
            gross_val = float(str(gross_pay).replace(',', '').replace('$', ''))
            net_val = float(str(net_pay).replace(',', '').replace('$', ''))
            if net_val >= gross_val:
                anomalies.append("Net pay is greater than or equal to gross pay - tax calculation error")
        except (ValueError, TypeError):
            pass

    if not extracted.get('company_name') and not extracted.get('employer_name'):
        anomalies.append("Missing company/employer name")

    if not extracted.get('employee_name'):
        anomalies.append("Missing employee name")

    if not extracted.get('pay_date'):
        anomalies.append("Missing pay date")

    if not extracted.get('gross_pay') or not extracted.get('net_pay'):
        anomalies.append("Missing pay amounts")

    return anomalies


def _calculate_confidence_score(extracted: Dict, ml_analysis: Optional[Dict]) -> float:
    """Calculate overall confidence score based on extraction and ML analysis"""
    confidence = 0.5  # Base confidence

    # Check field completeness
    required_fields = ['company_name', 'employee_name', 'gross_pay', 'net_pay', 'pay_date']
    present_fields = sum(1 for field in required_fields if extracted.get(field))
    field_completeness = present_fields / len(required_fields)
    confidence += field_completeness * 0.3

    # ML confidence if available
    if ml_analysis:
        ml_confidence = ml_analysis.get('model_confidence', 0.5)
        confidence += ml_confidence * 0.2
    else:
        confidence += 0.2  # Default if ML not available

    # Ensure score is between 0 and 1
    return min(1.0, max(0.0, confidence))
