"""
Bank of America Check Normalizer
"""

from typing import Dict, Any
from .base import BaseCheckNormalizer

class BankOfAmericaNormalizer(BaseCheckNormalizer):
    """
    Normalizer for Bank of America checks
    """
    def __init__(self):
        super().__init__('Bank of America')

    def normalize(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'issuer_name': 'Bank of America',
            'amount_numeric': {'value': self._standardize_amount(extracted_data.get('amount_numeric')), 'currency': 'USD'},
            'amount_written': extracted_data.get('amount_words'),
            'date': extracted_data.get('date'),
            'serial_primary': extracted_data.get('check_number'),
            'recipient': extracted_data.get('payee_name'),
            'sender_name': extracted_data.get('payer_name'),
            'signature': extracted_data.get('signature_detected'),
            'account_number': extracted_data.get('account_number'),
            'routing_number': extracted_data.get('routing_number')
        }
