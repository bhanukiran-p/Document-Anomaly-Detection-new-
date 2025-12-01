"""
Chase Bank Statement Normalizer
Maps Chase-specific fields to standardized bank statement schema
"""

from typing import Dict
from .bank_statement_base_normalizer import BankStatementBaseNormalizer


class ChaseNormalizer(BankStatementBaseNormalizer):
    """
    Normalizer for Chase bank statements
    Handles Chase-specific field names and formats
    """

    def __init__(self):
        super().__init__(bank_name='Chase')

    def get_field_mappings(self) -> Dict[str, str]:
        """
        Chase field mappings to standardized schema

        Mindee field names → Standardized bank statement schema fields
        """
        return {
            # Bank Information
            'bank_name': 'bank_name',
            'bank_address': 'bank_address',

            # Account Information
            'account_holder_names': 'account_holder_names',
            'account_holder_name': 'account_holder_name',
            'account_holder': 'account_holder_name',
            'account_number': 'account_number',
            'account_type': 'account_type',
            'currency': 'currency',

            # Statement Period
            'statement_period_start_date': 'statement_period_start_date',
            'statement_period_start': 'statement_period_start_date',
            'statement_period_end_date': 'statement_period_end_date',
            'statement_period_end': 'statement_period_end_date',
            'statement_date': 'statement_date',

            # Balance Information
            'beginning_balance': 'beginning_balance',
            'opening_balance': 'beginning_balance',
            'ending_balance': 'ending_balance',
            'closing_balance': 'ending_balance',
            'total_credits': 'total_credits',
            'total_debits': 'total_debits',

            # Transactions
            'list_of_transactions': 'transactions',
            'transactions': 'transactions',

            # Additional
            'account_holder_address': 'account_holder_address',
        }

    def normalize(self, ocr_data: Dict):
        """
        Normalize Chase bank statement data

        Args:
            ocr_data: Raw OCR-extracted data with Mindee field names

        Returns:
            NormalizedBankStatement instance
        """
        # Call parent normalize method which handles the mapping
        normalized = super().normalize(ocr_data)

        # Chase-specific post-processing

        # Set primary account holder name from list if available
        if normalized.account_holder_names and not normalized.account_holder_name:
            normalized.account_holder_name = normalized.account_holder_names[0]

        # Set default currency if not present
        if normalized.beginning_balance and not normalized.beginning_balance.get('currency'):
            normalized.beginning_balance['currency'] = normalized.currency or 'USD'
        if normalized.ending_balance and not normalized.ending_balance.get('currency'):
            normalized.ending_balance['currency'] = normalized.currency or 'USD'
        if normalized.total_credits and not normalized.total_credits.get('currency'):
            normalized.total_credits['currency'] = normalized.currency or 'USD'
        if normalized.total_debits and not normalized.total_debits.get('currency'):
            normalized.total_debits['currency'] = normalized.currency or 'USD'

        # Set default country for addresses
        if normalized.bank_address and not normalized.bank_address.get('country'):
            normalized.bank_address['country'] = 'US'
        if normalized.account_holder_address and not normalized.account_holder_address.get('country'):
            normalized.account_holder_address['country'] = 'US'

        return normalized

