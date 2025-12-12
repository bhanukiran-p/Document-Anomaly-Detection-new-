"""
Money Order Normalizer Factory
Automatically selects and returns the appropriate normalizer for a given issuer
"""

from typing import Optional
from .base_normalizer import BaseNormalizer
from .western_union import WesternUnionNormalizer
from .moneygram import MoneyGramNormalizer


class MoneyOrderNormalizerFactory:
    """
    Factory class to create appropriate normalizer based on issuer
    """

    # Registry of supported normalizers
    NORMALIZERS = {
        'western union': WesternUnionNormalizer,
        'moneygram': MoneyGramNormalizer,
        'money gram': MoneyGramNormalizer,  # Handle spacing variation
    }

    @classmethod
    def get_normalizer(cls, issuer: str) -> Optional[BaseNormalizer]:
        """
        Get appropriate normalizer for the given issuer

        Args:
            issuer: Name of the money order issuer (case-insensitive)

        Returns:
            Appropriate normalizer instance or None if issuer not supported

        Examples:
            >>> normalizer = MoneyOrderNormalizerFactory.get_normalizer('Western Union')
            >>> normalizer = MoneyOrderNormalizerFactory.get_normalizer('MoneyGram')
        """
        if not issuer:
            return None

        # Normalize issuer name (lowercase, strip whitespace)
        issuer_key = issuer.lower().strip()

        # Get normalizer class from registry
        normalizer_class = cls.NORMALIZERS.get(issuer_key)

        if normalizer_class:
            return normalizer_class()

        return None

    @classmethod
    def is_supported_issuer(cls, issuer: str) -> bool:
        """
        Check if an issuer is supported

        Since we now use generic normalizer, ALL issuers are supported.

        Args:
            issuer: Name of the money order issuer

        Returns:
            Always True (generic normalizer works for all issuers)
        """
        # Generic normalizer supports all issuers
        return True

    @classmethod
    def get_supported_issuers(cls) -> list:
        """
        Get list of all supported issuers

        Returns:
            List indicating all issuers are supported via generic normalizer
        """
        return ['All Issuers (using generic normalizer)']

    @classmethod
    def register_normalizer(cls, issuer: str, normalizer_class):
        """
        Register an issuer-specific normalizer for an issuer (optional)

        Only needed if an issuer requires special handling beyond generic normalization.

        Args:
            issuer: Issuer name (will be lowercased)
            normalizer_class: Normalizer class (must inherit from BaseNormalizer)
        """
        if not issubclass(normalizer_class, BaseNormalizer):
            raise ValueError(f"{normalizer_class} must inherit from BaseNormalizer")

        issuer_key = issuer.lower().strip()
        cls.ISSUER_SPECIFIC_NORMALIZERS[issuer_key] = normalizer_class

    @classmethod
    def normalize_data(cls, issuer: str, ocr_data: dict):
        """
        Convenience method to normalize data in one call

        Args:
            issuer: Issuer name
            ocr_data: OCR-extracted data

        Returns:
            NormalizedMoneyOrder instance or None if issuer not supported
        """
        normalizer = cls.get_normalizer(issuer)
        if normalizer:
            return normalizer.normalize(ocr_data)
        return None

