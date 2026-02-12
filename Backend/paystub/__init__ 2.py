"""
Paystub Analysis Module
Complete self-contained paystub analysis pipeline
Includes: Mindee OCR, Normalization, ML Fraud Detection, AI Analysis
Completely independent from other document analysis modules
"""

from .paystub_extractor import PaystubExtractor

# Main entry point
def extract_paystub(file_path: str) -> dict:
    """
    Extract and analyze paystub - main entry point
    
    Args:
        file_path: Path to paystub image/PDF file
        
    Returns:
        Complete analysis results dict
    """
    extractor = PaystubExtractor()
    return extractor.extract_and_analyze(file_path)

__all__ = ['extract_paystub', 'PaystubExtractor']
