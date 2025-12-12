"""
Utility modules for PDF validation
"""
try:
    from .pdf_statement_validator import validate_pdf_statement
    PDF_VALIDATOR_AVAILABLE = True
except ImportError:
    PDF_VALIDATOR_AVAILABLE = False
    validate_pdf_statement = None

__all__ = [
    'validate_pdf_statement',
    'PDF_VALIDATOR_AVAILABLE'
]
