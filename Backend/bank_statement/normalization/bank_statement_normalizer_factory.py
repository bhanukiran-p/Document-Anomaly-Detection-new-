"""
Bank Statement Normalizer Factory
Creates appropriate normalizer based on bank type
"""

from .bank_statement_base_normalizer import BankStatementBaseNormalizer

class BankStatementNormalizerFactory:
    """Factory to create bank statement normalizers"""

    @staticmethod
    def get_normalizer(bank_name: str = None):
        """
        Get appropriate normalizer for the bank

        Args:
            bank_name: Name of the bank (optional)

        Returns:
            BankStatementBaseNormalizer instance
        """
        # For now, return base normalizer for all banks
        # Can be extended to return specific normalizers per bank
        return BankStatementBaseNormalizer()
