"""
Bank Statement Normalizer Factory
Automatically selects and returns the appropriate normalizer for a given bank
"""

from typing import Optional
from .bank_statement_base_normalizer import BankStatementBaseNormalizer
from .bank_of_america import BankOfAmericaNormalizer
from .chase import ChaseNormalizer


class BankStatementNormalizerFactory:
    """
    Factory class to create appropriate bank statement normalizer based on bank name
    """

    # Registry of supported bank statement normalizers
    NORMALIZERS = {
        'bank of america': BankOfAmericaNormalizer,
        'bofa': BankOfAmericaNormalizer,
        'boa': BankOfAmericaNormalizer,
        'bankofamerica': BankOfAmericaNormalizer,
        'chase': ChaseNormalizer,
        'chase bank': ChaseNormalizer,
        'jpmorgan chase': ChaseNormalizer,
        'jp morgan chase': ChaseNormalizer,
        'wells fargo': ChaseNormalizer,  # Using Chase normalizer as template
        'citibank': ChaseNormalizer,      # Using Chase normalizer as template
        'citi': ChaseNormalizer,
    }

    @classmethod
    def get_normalizer(cls, bank_name: str) -> Optional[BankStatementBaseNormalizer]:
        """
        Get appropriate normalizer for the given bank

        Args:
            bank_name: Name of the bank (case-insensitive)

        Returns:
            Appropriate normalizer instance or None if bank not supported

        Examples:
            >>> normalizer = BankStatementNormalizerFactory.get_normalizer('Bank of America')
            >>> normalizer = BankStatementNormalizerFactory.get_normalizer('Chase')
        """
        if not bank_name:
            return None

        # Normalize bank name (lowercase, strip whitespace, remove special chars)
        bank_key = bank_name.lower().strip().replace('-', '').replace('_', '').replace(' ', '')

        # Get normalizer class from registry
        normalizer_class = cls.NORMALIZERS.get(bank_key)

        if normalizer_class:
            return normalizer_class()

        return None

    @classmethod
    def is_supported_bank(cls, bank_name: str) -> bool:
        """
        Check if a bank is supported

        Args:
            bank_name: Name of the bank

        Returns:
            True if bank is supported, False otherwise
        """
        if not bank_name:
            return False

        bank_key = bank_name.lower().strip().replace('-', '').replace('_', '').replace(' ', '')
        return bank_key in cls.NORMALIZERS

    @classmethod
    def get_supported_banks(cls) -> list:
        """
        Get list of all supported banks (canonical names only)

        Returns:
            List of supported bank names
        """
        return ['Bank of America', 'Chase', 'Wells Fargo', 'Citibank']

    @classmethod
    def register_normalizer(cls, bank_name: str, normalizer_class):
        """
        Register a new normalizer for a bank

        Args:
            bank_name: Bank name (will be lowercased)
            normalizer_class: Normalizer class (must inherit from BankStatementBaseNormalizer)
        """
        if not issubclass(normalizer_class, BankStatementBaseNormalizer):
            raise ValueError(f"{normalizer_class} must inherit from BankStatementBaseNormalizer")

        bank_key = bank_name.lower().strip().replace('-', '').replace('_', '').replace(' ', '')
        cls.NORMALIZERS[bank_key] = normalizer_class

    @classmethod
    def normalize_data(cls, bank_name: str, ocr_data: dict):
        """
        Convenience method to normalize bank statement data in one call

        Args:
            bank_name: Bank name
            ocr_data: OCR-extracted data from Mindee

        Returns:
            NormalizedBankStatement instance or None if bank not supported
        """
        normalizer = cls.get_normalizer(bank_name)
        if normalizer:
            return normalizer.normalize(ocr_data)
        return None

