"""
<<<<<<< Updated upstream
Check Analysis Package
Provides check extraction, normalization, ML fraud detection, and AI analysis.
=======
Check Analysis Module
Complete self-contained check analysis pipeline
Includes: OCR, Normalization, ML Fraud Detection, AI Analysis, Database Operations
>>>>>>> Stashed changes
"""

from .check_extractor import CheckExtractor

<<<<<<< Updated upstream
__all__ = ['CheckExtractor']
=======
# Main entry point
def extract_check(file_path: str) -> dict:
    """
    Extract and analyze check - main entry point
    
    Args:
        file_path: Path to check image/PDF file
        
    Returns:
        Complete analysis results dict
    """
    extractor = CheckExtractor()
    return extractor.extract_and_analyze(file_path)

__all__ = ['extract_check', 'CheckExtractor']
>>>>>>> Stashed changes
