"""
Check Normalizer Factory
Automatically selects and returns the appropriate normalizer for a given bank
Uses generic normalizer for all banks by default
"""

from typing import Optional
from .check_base_normalizer import CheckBaseNormalizer
from .normalise_generic import GenericCheckNormalizer


class CheckNormalizerFactory:
    """
    Factory class to create appropriate check normalizer based on bank name
    Uses generic normalizer for all banks by default
    """

    # Registry of bank-specific normalizers (optional - for special cases)
    BANK_SPECIFIC_NORMALIZERS = {
        # Commented out - using generic normalizer for all banks now
        # 'bank of america': BankOfAmericaNormalizer,
        # 'bofa': BankOfAmericaNormalizer,
        # 'boa': BankOfAmericaNormalizer,
        # 'bankofamerica': BankOfAmericaNormalizer,
        # 'chase': ChaseNormalizer,
        # 'chase bank': ChaseNormalizer,
        # 'jpmorgan chase': ChaseNormalizer,
        # 'jp morgan chase': ChaseNormalizer,
    }

    @classmethod
    def get_normalizer(cls, bank_name: str) -> Optional[CheckBaseNormalizer]:
        """
        Get appropriate normalizer for the given bank

        Now uses GenericCheckNormalizer for ALL banks by default.
        Mindee provides standardized field names, so we don't need bank-specific logic.

        Args:
            bank_name: Name of the bank (case-insensitive)

        Returns:
            GenericCheckNormalizer instance (works for all banks)

        Examples:
            >>> normalizer = CheckNormalizerFactory.get_normalizer('Bank of America')
            >>> normalizer = CheckNormalizerFactory.get_normalizer('Chase')
            >>> normalizer = CheckNormalizerFactory.get_normalizer('Wells Fargo')
            # All return GenericCheckNormalizer
        """
        if not bank_name:
            # Return generic normalizer even if bank name is unknown
            return GenericCheckNormalizer(bank_name='Unknown Bank')

        # Normalize bank name (lowercase, strip whitespace, remove special chars)
        bank_key = bank_name.lower().strip().replace('-', '').replace('_', '')

        # Check if there's a bank-specific normalizer (for special cases)
        normalizer_class = cls.BANK_SPECIFIC_NORMALIZERS.get(bank_key)

        if normalizer_class:
            return normalizer_class()

        # Default: Use generic normalizer for all banks
        return GenericCheckNormalizer(bank_name=bank_name)

    @classmethod
    def is_supported_bank(cls, bank_name: str) -> bool:
        """
        Check if a bank is supported

        Since we now use generic normalizer, ALL banks are supported.

        Args:
            bank_name: Name of the bank

        Returns:
            Always True (generic normalizer works for all banks)
        """
        # Generic normalizer supports all banks
        return True

    @classmethod
    def get_supported_banks(cls) -> list:
        """
        Get list of all supported banks

        Returns:
            List indicating all banks are supported via generic normalizer
        """
        return ['All Banks (using generic normalizer)']

    @classmethod
    def register_normalizer(cls, bank_name: str, normalizer_class):
        """
        Register a bank-specific normalizer for a bank (optional)

        Only needed if a bank requires special handling beyond generic normalization.

        Args:
            bank_name: Bank name (will be lowercased)
            normalizer_class: Normalizer class (must inherit from CheckBaseNormalizer)
        """
        if not issubclass(normalizer_class, CheckBaseNormalizer):
            raise ValueError(f"{normalizer_class} must inherit from CheckBaseNormalizer")

        bank_key = bank_name.lower().strip().replace('-', '').replace('_', '')
        cls.BANK_SPECIFIC_NORMALIZERS[bank_key] = normalizer_class

    @classmethod
    def normalize_data(cls, bank_name: str, ocr_data: dict):
        """
        Convenience method to normalize check data in one call

        Args:
            bank_name: Bank name
            ocr_data: OCR-extracted data from Mindee

        Returns:
            NormalizedCheck instance or None if bank not supported
        """
        normalizer = cls.get_normalizer(bank_name)
        if normalizer:
            return normalizer.normalize(ocr_data)
        return None
