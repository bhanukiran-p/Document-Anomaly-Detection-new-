"""
Paystub Normalizer Factory
Automatically selects and returns the appropriate normalizer for paystubs
Completely independent from money order normalizers
"""

from typing import Optional
from .paystub_base_normalizer import PaystubBaseNormalizer
from .paystub_normalizer import PaystubNormalizer


class PaystubNormalizerFactory:
    """
    Factory class to create appropriate paystub normalizer
    """

    # Registry of supported paystub normalizers
    NORMALIZERS = {
        'paystub': PaystubNormalizer,
        'generic': PaystubNormalizer,
    }

    @classmethod
    def get_normalizer(cls, company_name: Optional[str] = None) -> Optional[PaystubBaseNormalizer]:
        """
        Get appropriate normalizer for paystub

        Args:
            company_name: Name of the company (optional, defaults to generic)

        Returns:
            Appropriate normalizer instance or None if not supported
        """
        if not company_name:
            return PaystubNormalizer()
        
        # Normalize company name (lowercase, strip whitespace)
        company_key = company_name.lower().strip()
        
        # Get normalizer class from registry
        normalizer_class = cls.NORMALIZERS.get(company_key)
        
        if normalizer_class:
            return normalizer_class()
        
        # Default to generic paystub normalizer
        return PaystubNormalizer()

    @classmethod
    def is_supported_company(cls, company_name: str) -> bool:
        """
        Check if a company is supported

        Args:
            company_name: Name of the company

        Returns:
            True if supported, False otherwise
        """
        if not company_name:
            return False
        
        company_key = company_name.lower().strip()
        return company_key in cls.NORMALIZERS

    @classmethod
    def get_supported_companies(cls) -> list:
        """
        Get list of all supported companies

        Returns:
            List of supported company names
        """
        return list(set(cls.NORMALIZERS.keys()))

