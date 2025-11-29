"""
Chase Bank Check Normalizer
Maps Chase-specific fields to standardized check schema
"""

from typing import Dict
from .check_base_normalizer import CheckBaseNormalizer


class ChaseNormalizer(CheckBaseNormalizer):
    """
    Normalizer for Chase bank checks
    Handles Chase-specific field names and formats
    """

    def __init__(self):
        super().__init__(bank_name='Chase')

    def get_field_mappings(self) -> Dict[str, str]:
        """
        Chase field mappings to standardized schema

        Mindee field names → Standardized check schema fields
        """
        return {
            # Bank is set in __init__

            # Bank identification
            'routing_number': 'routing_number',
            'account_number': 'account_number',
            'routing': 'routing_number',              # Alternate name
            'account': 'account_number',              # Alternate name
            'aba_routing': 'routing_number',          # Chase specific

            # Check identification
            'check_number': 'check_number',
            'number': 'check_number',                 # Alternate name
            'check_id': 'check_number',               # Alternate name
            'serial_number': 'check_number',          # Chase may use this
            'date': 'check_date',
            'check_date': 'check_date',               # Direct match

            # Payer information (person writing the check)
            'payer_name': 'payer_name',
            'payer': 'payer_name',                    # Alternate name
            'drawer': 'payer_name',                   # Banking term
            'account_holder': 'payer_name',           # Alternate name
            'customer_name': 'payer_name',            # Chase specific
            'payer_address': 'payer_address',
            'payer_city': 'payer_city',
            'payer_state': 'payer_state',
            'payer_zip': 'payer_zip',
            'payer_zip_code': 'payer_zip',

            # Payee information (person receiving the check)
            'payee_name': 'payee_name',
            'payee': 'payee_name',                    # Alternate name
            'pay_to': 'payee_name',                   # "Pay to the order of"
            'pay_to_the_order_of': 'payee_name',      # Full phrase
            'recipient': 'payee_name',                # Alternate name
            'beneficiary': 'payee_name',              # Chase may use this
            'payee_address': 'payee_address',
            'payee_city': 'payee_city',
            'payee_state': 'payee_state',
            'payee_zip': 'payee_zip',
            'payee_zip_code': 'payee_zip',

            # Monetary information
            'amount': 'amount_numeric',               # Numeric amount
            'amount_numeric': 'amount_numeric',       # Direct match
            'number_amount': 'amount_numeric',        # Mindee field name
            'check_amount': 'amount_numeric',         # Chase specific
            'amount_words': 'amount_written',         # Written amount
            'amount_in_words': 'amount_written',      # Alternate name
            'word_amount': 'amount_written',          # Mindee field name
            'written_amount': 'amount_written',       # Alternate name

            # Authorization & Validation
            'signature': 'signature_detected',
            'signature_detected': 'signature_detected',  # Direct match
            'signed': 'signature_detected',           # Alternate name
            'authorized': 'signature_detected',       # Alternate name
            'memo': 'memo',                           # Direct match
            'memo_line': 'memo',                      # Alternate name
            'note': 'memo',                           # Alternate name
            'for': 'memo',                            # Chase memo field label

            # Additional fields
            'check_type': 'check_type',               # Personal, Business, etc.
            'type': 'check_type',                     # Alternate name
            'country': 'country',                     # Usually 'US'
            'currency': 'currency',                   # Usually 'USD'
        }

    def normalize(self, ocr_data: Dict):
        """
        Normalize Chase check data

        Args:
            ocr_data: Raw OCR-extracted data with Mindee field names

        Returns:
            NormalizedCheck instance
        """
        # Call parent normalize method which handles the mapping
        normalized = super().normalize(ocr_data)

        # Chase-specific post-processing

        # Chase routing numbers typically start with specific prefixes (for JPMorgan Chase)
        # Common Chase routing numbers: 021000021, 022300173, 071000013, etc.
        if normalized.routing_number:
            # Validate Chase routing number format (9 digits)
            if len(normalized.routing_number) != 9:
                # Could be invalid, but we'll keep it
                pass

        # Set default currency if not present
        if normalized.amount_numeric and not normalized.amount_numeric.get('currency'):
            normalized.amount_numeric['currency'] = 'USD'

        # Set default country
        if not normalized.country:
            normalized.country = 'US'

        # Parse payer address components if full address is provided but components are missing
        if normalized.payer_address and not normalized.payer_city:
            components = self._parse_address_components(normalized.payer_address)
            if components['city']:
                normalized.payer_city = components['city']
            if components['state']:
                normalized.payer_state = components['state']
            if components['zip']:
                normalized.payer_zip = components['zip']

        # Parse payee address components if available
        if normalized.payee_address and not normalized.payee_city:
            components = self._parse_address_components(normalized.payee_address)
            if components['city']:
                normalized.payee_city = components['city']
            if components['state']:
                normalized.payee_state = components['state']
            if components['zip']:
                normalized.payee_zip = components['zip']

        return normalized
