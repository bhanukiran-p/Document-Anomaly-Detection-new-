"""
Generic Check Normalizer
Works for all banks with common field mappings
No bank-specific logic - uses standardized Mindee field names
"""

from typing import Dict
from .check_base_normalizer import CheckBaseNormalizer


class GenericCheckNormalizer(CheckBaseNormalizer):
    """
    Generic normalizer for all bank checks
    Uses common field mappings that work across all banks
    Mindee provides standardized field names, so we can use one normalizer
    """

    def __init__(self, bank_name: str = 'Unknown Bank'):
        super().__init__(bank_name=bank_name)

    def get_field_mappings(self) -> Dict[str, str]:
        """
        Generic field mappings that work for all banks

        Mindee Check API provides standardized field names:
        - We use these standard names directly
        - Works for Chase, Bank of America, Wells Fargo, etc.

        Returns:
            Dict mapping Mindee field names to our standardized schema
        """
        return {
            # Bank identification
            'routing_number': 'routing_number',
            'account_number': 'account_number',
            'routing': 'routing_number',              # Alternate
            'account': 'account_number',              # Alternate
            'aba_routing': 'routing_number',          # Some banks
            'aba': 'routing_number',                  # Abbreviation

            # Check identification
            'check_number': 'check_number',
            'number': 'check_number',                 # Alternate
            'check_id': 'check_number',               # Alternate
            'serial_number': 'check_number',          # Some banks
            'check_serial': 'check_number',           # Alternate
            'date': 'check_date',
            'check_date': 'check_date',               # Direct match
            'issue_date': 'check_date',               # Alternate

            # Payer information (person writing the check)
            'payer_name': 'payer_name',
            'payer': 'payer_name',                    # Alternate
            'drawer': 'payer_name',                   # Banking term
            'account_holder': 'payer_name',           # Common term
            'customer_name': 'payer_name',            # Some banks
            'issuer': 'payer_name',                   # Alternate
            'from': 'payer_name',                     # Alternate
            'payer_address': 'payer_address',
            'address': 'payer_address',               # Alternate
            'payer_city': 'payer_city',
            'payer_state': 'payer_state',
            'payer_zip': 'payer_zip',
            'payer_zip_code': 'payer_zip',
            'zip': 'payer_zip',                       # Alternate
            'zip_code': 'payer_zip',                  # Alternate

            # Payee information (person receiving the check)
            'payee_name': 'payee_name',
            'payee': 'payee_name',                    # Alternate
            'pay_to': 'payee_name',                   # "Pay to the order of"
            'pay_to_the_order_of': 'payee_name',      # Full phrase
            'recipient': 'payee_name',                # Alternate
            'beneficiary': 'payee_name',              # Banking term
            'to': 'payee_name',                       # Alternate
            'payee_address': 'payee_address',
            'payee_city': 'payee_city',
            'payee_state': 'payee_state',
            'payee_zip': 'payee_zip',
            'payee_zip_code': 'payee_zip',

            # Monetary information
            'amount': 'amount_numeric',               # Numeric amount (most common)
            'amount_numeric': 'amount_numeric',       # Direct match
            'number_amount': 'amount_numeric',        # Mindee field
            'check_amount': 'amount_numeric',         # Alternate
            'value': 'amount_numeric',                # Alternate
            'amount_value': 'amount_numeric',         # Alternate
            'amount_words': 'amount_written',         # Written amount
            'amount_in_words': 'amount_written',      # Alternate
            'word_amount': 'amount_written',          # Mindee field
            'written_amount': 'amount_written',       # Alternate
            'amount_text': 'amount_written',          # Alternate

            # Authorization & Validation
            'signature': 'signature_detected',
            'signature_detected': 'signature_detected',  # Direct match
            'has_signature': 'signature_detected',       # Boolean variant
            'signed': 'signature_detected',              # Alternate
            'signature_present': 'signature_detected',   # Alternate
            'memo': 'memo',
            'memo_line': 'memo',                      # Alternate
            'note': 'memo',                           # Alternate
            'for': 'memo',                            # Common on check memo lines

            # Additional fields
            'check_type': 'check_type',               # Personal, Business, etc.
            'type': 'check_type',                     # Alternate
            'country': 'country',
            'currency': 'currency',
            'currency_code': 'currency',              # Alternate
        }
