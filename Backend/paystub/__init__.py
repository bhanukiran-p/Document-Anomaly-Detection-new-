"""
Paystub Analysis Module
Complete self-contained paystub analysis pipeline
Includes: OCR, Normalization, ML Fraud Detection, AI Analysis
Completely independent from money order analysis
"""

from .extractor import PaystubExtractor

# Main entry point
def extract_paystub(file_path: str, credentials_path: str = 'google-credentials.json') -> dict:
    """
    Extract and analyze paystub - main entry point
    
    Args:
        file_path: Path to paystub image/PDF file
        credentials_path: Path to Google credentials JSON file
        
    Returns:
        Complete analysis results dict
    """
    extractor = PaystubExtractor(credentials_path)
    return extractor.extract(file_path)

__all__ = ['extract_paystub', 'PaystubExtractor']
