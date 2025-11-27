"""
Paystub Normalizer
Normalizes extracted paystub data to standardized schema
"""

from typing import Dict
from .base_normalizer import BaseNormalizer

class PaystubNormalizer(BaseNormalizer):
    """
    Normalizer for Paystub documents
    """

    def __init__(self):
        super().__init__("Paystub")

    def get_field_mappings(self) -> Dict[str, str]:
        """
        Map OCR fields to standardized schema fields
        """
        return {
            'company_name': 'company',
            'employee_name': 'employee',
            'employee_id': 'employee_id',
            'pay_date': 'date',
            'pay_period_start': 'period_start',
            'pay_period_end': 'period_end',
            'gross_pay': 'amount_gross',
            'net_pay': 'amount_net',
            'ytd_gross': 'ytd_gross',
            'ytd_net': 'ytd_net',
            'federal_tax': 'tax_federal',
            'state_tax': 'tax_state',
            'social_security': 'tax_social_security',
            'medicare': 'tax_medicare'
        }

    def normalize(self, ocr_data: Dict) -> Dict:
        """
        Override normalize to handle specific paystub fields
        """
        # Get base normalization
        normalized = super().normalize(ocr_data)
        
        # Convert NormalizedMoneyOrder object back to dict for extension
        # (Since BaseNormalizer returns a specific object, we might need to extend it or just return a dict)
        # For now, let's return a dictionary as the rest of the system expects it
        
        data = {
            'issuer_name': self.issuer_name,
            'document_type': 'PAYSTUB'
        }
        
        field_mappings = self.get_field_mappings()
        
        for ocr_field, std_field in field_mappings.items():
            if ocr_field in ocr_data and ocr_data[ocr_field]:
                raw_value = ocr_data[ocr_field]
                
                # Apply specific normalization
                if 'amount' in std_field or 'tax' in std_field or 'ytd' in std_field:
                    data[std_field] = self._normalize_amount(raw_value)
                elif 'date' in std_field or 'period' in std_field:
                    data[std_field] = self._normalize_date(raw_value)
                else:
                    data[std_field] = self._clean_string(raw_value)
                    
        return data
