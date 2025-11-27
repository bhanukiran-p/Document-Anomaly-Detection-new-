"""
Factory for creating bank-specific check normalizers.
Returns appropriate normalizer based on bank name.
"""
from typing import Optional
from .check_normalizer import BaseCheckNormalizer


class WellsFargoNormalizer(BaseCheckNormalizer):
    """Normalizer for Wells Fargo checks."""

    def __init__(self):
        super().__init__(bank_name="Wells Fargo")


class BankOfAmericaNormalizer(BaseCheckNormalizer):
    """Normalizer for Bank of America checks."""

    def __init__(self):
        super().__init__(bank_name="Bank of America")


class ChaseNormalizer(BaseCheckNormalizer):
    """Normalizer for Chase Bank checks."""

    def __init__(self):
        super().__init__(bank_name="Chase")


class CitibankNormalizer(BaseCheckNormalizer):
    """Normalizer for Citibank checks."""

    def __init__(self):
        super().__init__(bank_name="Citibank")


class USBankNormalizer(BaseCheckNormalizer):
    """Normalizer for U.S. Bank checks."""

    def __init__(self):
        super().__init__(bank_name="U.S. Bank")


class CheckNormalizerFactory:
    """
    Factory class to get the appropriate check normalizer.
    Returns bank-specific normalizer if available, otherwise returns base normalizer.
    """

    # Map of bank name patterns to normalizer classes
    NORMALIZER_MAP = {
        "wells fargo": WellsFargoNormalizer,
        "bank of america": BankOfAmericaNormalizer,
        "chase": ChaseNormalizer,
        "citibank": CitibankNormalizer,
        "citi bank": CitibankNormalizer,
        "us bank": USBankNormalizer,
        "u.s. bank": USBankNormalizer,
    }

    @classmethod
    def get_normalizer(cls, bank_name: Optional[str] = None) -> BaseCheckNormalizer:
        """
        Get appropriate normalizer for the given bank.

        Args:
            bank_name: Name of the bank (case-insensitive)

        Returns:
            Bank-specific normalizer or base normalizer if bank is unknown
        """
        if not bank_name:
            return BaseCheckNormalizer()

        # Normalize bank name for matching
        normalized_name = bank_name.lower().strip()

        # Try to find matching normalizer
        for pattern, normalizer_class in cls.NORMALIZER_MAP.items():
            if pattern in normalized_name:
                return normalizer_class()

        # Return base normalizer for unknown banks
        return BaseCheckNormalizer(bank_name=bank_name)
