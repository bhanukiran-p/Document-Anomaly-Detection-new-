"""
Document type detection utilities.
"""
import logging

logger = logging.getLogger(__name__)


def detect_document_type(text):
    """
    Detect document type based on text content.

    Args:
        text: OCR text from document

    Returns:
        str: 'check', 'paystub', 'money_order', 'bank_statement', or 'unknown'
    """
    text_lower = text.lower()

    # Priority check: Strong identifiers that definitively indicate document type
    # Check for money order FIRST with strong keywords
    if 'money order' in text_lower or 'western union' in text_lower or 'moneygram' in text_lower:
        return 'money_order'

    # Check for bank statement strong indicators
    if ('statement period' in text_lower or 'account summary' in text_lower or
        'beginning balance' in text_lower or 'transaction detail' in text_lower):
        return 'bank_statement'

    # Check for paystub strong indicators
    if ('gross pay' in text_lower or 'net pay' in text_lower or
        ('ytd' in text_lower and 'earnings' in text_lower)):
        return 'paystub'

    # Check for check strong indicators
    if 'routing number' in text_lower or 'micr' in text_lower or 'check number' in text_lower:
        return 'check'

    # Fallback: Use keyword counting for less obvious cases
    # Check for check-specific keywords
    check_keywords = ['pay to the order of', 'account number', 'memo', 'void', 'dollars']
    check_count = sum(1 for keyword in check_keywords if keyword in text_lower)

    # Check for paystub-specific keywords
    paystub_keywords = ['earnings', 'deductions', 'federal tax', 'state tax', 'social security',
                        'medicare', 'employee', 'employer', 'pay period', 'paycheck']
    paystub_count = sum(1 for keyword in paystub_keywords if keyword in text_lower)

    # Check for money order keywords
    money_order_keywords = ['purchaser', 'serial number', 'receipt', 'remitter']
    money_order_count = sum(1 for keyword in money_order_keywords if keyword in text_lower)

    # Check for bank statement keywords
    bank_statement_keywords = ['ending balance', 'checking summary', 'deposits', 'withdrawals', 'daily balance']
    bank_statement_count = sum(1 for keyword in bank_statement_keywords if keyword in text_lower)

    # Determine document type based on keyword matches
    max_count = max(check_count, paystub_count, money_order_count, bank_statement_count)

    if max_count == 0:
        return 'unknown'

    if check_count == max_count:
        return 'check'
    elif paystub_count == max_count:
        return 'paystub'
    elif bank_statement_count == max_count:
        return 'bank_statement'
    else:
        return 'money_order'


def validate_document_type(raw_text, expected_type):
    """
    Validate that the document matches the expected type.

    Args:
        raw_text: OCR text from document
        expected_type: Expected document type ('check', 'paystub', 'money_order', 'bank_statement')

    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): True if document type matches or is unknown
            - error_message (str): Error message if validation fails, None otherwise
    """
    if not raw_text:
        # Cannot validate without text, allow it to proceed
        return True, None

    detected_type = detect_document_type(raw_text)

    # Allow 'unknown' to pass through
    if detected_type == 'unknown':
        return True, None

    # Check if detected type matches expected type
    if detected_type == expected_type:
        return True, None

    # Validation failed
    error_message = (
        f'Wrong document type detected. This appears to be a {detected_type}, '
        f'not a {expected_type}. Please upload a {expected_type} document.'
    )

    logger.warning(f"Document type mismatch: expected {expected_type}, detected {detected_type}")

    return False, error_message
