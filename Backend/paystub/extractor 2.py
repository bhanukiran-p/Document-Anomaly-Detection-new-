"""
Paystub Extractor Module - Legacy file
This file is kept for backward compatibility but redirects to paystub_extractor.py
All new code should use PaystubExtractor from paystub_extractor.py
"""

# Import the new Mindee-based extractor
from .paystub_extractor import PaystubExtractor

# For backward compatibility, export the class
__all__ = ['PaystubExtractor']


