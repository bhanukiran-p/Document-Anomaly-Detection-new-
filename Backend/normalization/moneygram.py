"""
MoneyGram Money Order Normalizer
Maps MoneyGram-specific fields to standardized schema
"""

from typing import Dict
from .base_normalizer import BaseNormalizer


class MoneyGramNormalizer(BaseNormalizer):
    """
    Normalizer for MoneyGram money orders
    Handles MoneyGram-specific field names and formats
    """

    def __init__(self):
        super().__init__(issuer_name='MoneyGram')

    def get_field_mappings(self) -> Dict[str, str]:
        """
        MoneyGram field mappings to standardized schema

        MoneyGram field names → Standardized schema fields
        """
        return {
            # Issuer name is set in __init__

            # Identification numbers
            'serial_number': 'serial_primary',      # Main serial number
            'serial': 'serial_primary',             # Alternate name
            'money_order_number': 'serial_primary', # MoneyGram specific
            'reference_number': 'serial_secondary', # Reference number
            'control_number': 'serial_secondary',   # Control number
            'receipt_number': 'serial_secondary',   # Receipt number

            # Party information
            'pay_to': 'recipient',                  # Who receives money
            'payee': 'recipient',                   # Alternate name
            'receiver': 'recipient',                # Alternate name
            'receiver_name': 'recipient',           # Alternate name
            'purchaser': 'sender_name',             # Who sends money
            'sender': 'sender_name',                # Alternate name
            'sender_name': 'sender_name',           # Direct match
            'from': 'sender_name',                  # Alternate name
            'purchaser_address': 'sender_address',  # Sender address
            'sender_address': 'sender_address',     # Direct match
            'address': 'sender_address',            # Alternate name

            # Monetary information
            'amount': 'amount_numeric',             # Numeric amount
            'face_amount': 'amount_numeric',        # MoneyGram specific
            'principal': 'amount_numeric',          # Alternate name
            'money_order_amount': 'amount_numeric', # Alternate name
            'amount_in_words': 'amount_written',    # Written amount
            'written_amount': 'amount_written',     # Alternate name

            # Temporal information
            'date': 'date',                         # Direct match
            'purchase_date': 'date',                # Alternate name
            'issue_date': 'date',                   # Alternate name
            'transaction_date': 'date',             # Alternate name

            # Authorization
            'signature': 'signature',               # Direct match
            'purchaser_signature': 'signature',     # Alternate name
            'authorized_signature': 'signature',    # Alternate name
            'agent_stamp': 'signature',             # MoneyGram specific
        }

    def normalize(self, ocr_data: Dict):
        """
        Normalize MoneyGram money order data

        Args:
            ocr_data: Raw OCR-extracted data with MoneyGram field names

        Returns:
            NormalizedMoneyOrder instance
        """
        # Call parent normalize method which handles the mapping
        normalized = super().normalize(ocr_data)

        # MoneyGram-specific post-processing can be added here
        # For example, if MoneyGram has specific format quirks

        return normalized
