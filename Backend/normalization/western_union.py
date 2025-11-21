"""
Western Union Money Order Normalizer
Maps Western Union-specific fields to standardized schema
"""

from typing import Dict
from .base_normalizer import BaseNormalizer


class WesternUnionNormalizer(BaseNormalizer):
    """
    Normalizer for Western Union money orders
    Handles Western Union-specific field names and formats
    """

    def __init__(self):
        super().__init__(issuer_name='Western Union')

    def get_field_mappings(self) -> Dict[str, str]:
        """
        Western Union field mappings to standardized schema

        Western Union field names → Standardized schema fields
        """
        return {
            # Issuer name is set in __init__

            # Identification numbers
            'serial_number': 'serial_primary',      # Main serial number
            'serial': 'serial_primary',             # Alternate name
            'control_number': 'serial_secondary',   # Control/reference number
            'reference_number': 'serial_secondary', # Alternate name
            'tracking_number': 'serial_secondary',  # Alternate name

            # Party information
            'receiver': 'recipient',                # Who receives money
            'payee': 'recipient',                   # Alternate name
            'receiver_name': 'recipient',           # Alternate name
            'remitter': 'sender_name',              # Who sends money
            'sender': 'sender_name',                # Alternate name
            'sender_name': 'sender_name',           # Direct match
            'purchaser': 'sender_name',             # Alternate name
            'remitter_address': 'sender_address',   # Sender address
            'sender_address': 'sender_address',     # Direct match
            'from_address': 'sender_address',       # Alternate name

            # Monetary information
            'principal_amount': 'amount_numeric',   # Numeric amount
            'amount': 'amount_numeric',             # Alternate name
            'face_value': 'amount_numeric',         # Alternate name
            'amount_in_words': 'amount_written',    # Written amount
            'written_amount': 'amount_written',     # Alternate name

            # Temporal information
            'date': 'date',                         # Direct match
            'transaction_date': 'date',             # Alternate name
            'purchase_date': 'date',                # Alternate name
            'issue_date': 'date',                   # Alternate name

            # Authorization
            'signature': 'signature',               # Direct match
            'agent_signature': 'signature',         # Alternate name
            'authorized_signature': 'signature',    # Alternate name
        }

    def normalize(self, ocr_data: Dict):
        """
        Normalize Western Union money order data

        Args:
            ocr_data: Raw OCR-extracted data with Western Union field names

        Returns:
            NormalizedMoneyOrder instance
        """
        # Call parent normalize method which handles the mapping
        normalized = super().normalize(ocr_data)

        # Western Union-specific post-processing can be added here
        # For example, if Western Union has specific format quirks

        return normalized
