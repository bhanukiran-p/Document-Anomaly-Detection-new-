"""
Paystub Normalizer
Normalizes extracted paystub data to standardized schema
Uses PaystubBaseNormalizer (completely independent from money orders)
"""

from typing import Dict
from .paystub_base_normalizer import PaystubBaseNormalizer


class PaystubNormalizer(PaystubBaseNormalizer):
    """
    Normalizer for Paystub documents
    """

    def __init__(self):
        super().__init__(company_name="Generic")

    def get_field_mappings(self) -> Dict[str, str]:
        """
        Map OCR fields to standardized schema fields
        """
        return {
            'company_name': 'company_name',
            'employee_name': 'employee_name',
            'employee_id': 'employee_id',
            'pay_date': 'pay_date',
            'pay_period_start': 'pay_period_start',
            'pay_period_end': 'pay_period_end',
            'gross_pay': 'gross_pay',
            'net_pay': 'net_pay',
            'ytd_gross': 'ytd_gross',
            'ytd_net': 'ytd_net',
            'federal_tax': 'federal_tax',
            'state_tax': 'state_tax',
            'social_security': 'social_security',
            'medicare': 'medicare'
        }

