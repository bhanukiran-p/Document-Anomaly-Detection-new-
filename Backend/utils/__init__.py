"""
Utility modules for fraud detection and PDF validation
"""
try:
    from .fraud_detection_service import get_fraud_detection_service
    FRAUD_DETECTION_AVAILABLE = True
except ImportError:
    FRAUD_DETECTION_AVAILABLE = False
    get_fraud_detection_service = None

try:
    from .pdf_statement_validator import validate_pdf_statement
    PDF_VALIDATOR_AVAILABLE = True
except ImportError:
    PDF_VALIDATOR_AVAILABLE = False
    validate_pdf_statement = None

__all__ = [
    'get_fraud_detection_service',
    'validate_pdf_statement',
    'FRAUD_DETECTION_AVAILABLE',
    'PDF_VALIDATOR_AVAILABLE'
]
