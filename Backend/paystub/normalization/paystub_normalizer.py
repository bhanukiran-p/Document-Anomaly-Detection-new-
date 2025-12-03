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
        Map Mindee fields to standardized schema fields
        ONLY Mindee field names - no legacy OCR field names
        """
        return {
            # Company/Employer fields (Mindee field names)
            'employer_name': 'company_name',
            'employer_address': 'company_address',
            
            # Employee fields (Mindee field names)
            'employee_name': 'employee_name',  # Already combined from first_name + last_name in extractor
            'employee_id': 'employee_id',
            'employee_address': 'employee_address',
            'social_security_number': 'social_security_number',  # For reference, not in schema
            
            # Pay period fields (Mindee field names)
            'pay_date': 'pay_date',
            'pay_period_start_date': 'pay_period_start',  # Mindee uses pay_period_start_date
            'pay_period_end_date': 'pay_period_end',  # Mindee uses pay_period_end_date
            
            # Pay amounts (Mindee field names)
            'gross_pay': 'gross_pay',
            'net_pay': 'net_pay',
            'ytd_gross': 'ytd_gross',
            'ytd_net': 'ytd_net',
            
            # Tax fields (extracted from deductions/taxes arrays in extractor)
            'federal_tax': 'federal_tax',
            'state_tax': 'state_tax',
            'social_security': 'social_security',
            'medicare': 'medicare',
            
            # Deductions and taxes arrays (handled in extractor, not mapped here)
            'deductions': None,  # Processed separately
            'taxes': None  # Processed separately
        }

