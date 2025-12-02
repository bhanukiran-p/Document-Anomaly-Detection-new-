"""
Paystub Base Normalizer
Abstract base class for paystub normalizers
Completely independent from money order normalizers
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional
from .paystub_schema import NormalizedPaystub


class PaystubBaseNormalizer(ABC):
    """
    Abstract base class for paystub normalizers
    All paystub normalizers must inherit from this class
    """

    def __init__(self, company_name: str = "Generic"):
        """
        Initialize normalizer with company name

        Args:
            company_name: Name of the company (e.g., 'Generic', 'ADP', 'Paychex')
        """
        self.company_name = company_name

    @abstractmethod
    def get_field_mappings(self) -> Dict[str, str]:
        """
        Map OCR fields to standardized schema fields
        Must be implemented by subclasses
        """
        pass

    def normalize(self, ocr_data: Dict) -> NormalizedPaystub:
        """
        Normalize paystub data to standardized schema

        Args:
            ocr_data: Raw OCR-extracted data

        Returns:
            NormalizedPaystub instance
        """
        field_mappings = self.get_field_mappings()
        
        # Initialize normalized data
        normalized_data = {
            'company_name': self.company_name,
            'document_type': 'PAYSTUB'
        }
        
        # Map fields
        for ocr_field, std_field in field_mappings.items():
            # Skip None mappings (fields processed separately)
            if std_field is None:
                continue
                
            if ocr_field in ocr_data and ocr_data[ocr_field]:
                raw_value = ocr_data[ocr_field]
                
                # Skip if already normalized (avoid overwriting)
                if std_field in normalized_data and normalized_data[std_field]:
                    continue
                
                # Apply normalization based on field type
                if 'amount' in std_field or 'tax' in std_field or 'pay' in std_field or 'gross' in std_field or 'net' in std_field:
                    normalized_value = self._normalize_amount(raw_value)
                    if normalized_value is not None:
                        normalized_data[std_field] = normalized_value
                elif 'date' in std_field or 'period' in std_field:
                    normalized_value = self._normalize_date(raw_value)
                    if normalized_value is not None:
                        normalized_data[std_field] = normalized_value
                elif 'hours' in std_field or 'rate' in std_field:
                    normalized_value = self._normalize_numeric(raw_value)
                    if normalized_value is not None:
                        normalized_data[std_field] = normalized_value
                else:
                    normalized_value = self._clean_string(raw_value)
                    if normalized_value is not None:
                        normalized_data[std_field] = normalized_value
        
        return NormalizedPaystub(**normalized_data)

    def _normalize_amount(self, value) -> Optional[float]:
        """Normalize amount to float"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols, commas, spaces
            clean_value = re.sub(r'[^\d.-]', '', str(value))
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return None

    def _normalize_date(self, value) -> Optional[str]:
        """Normalize date to ISO format string"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value.isoformat()
        
        if isinstance(value, str):
            # Try to parse common date formats
            date_formats = [
                '%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y',
                '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y',
                '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y'
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(value.strip(), fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # Return as-is if can't parse
            return value.strip()
        
        return None

    def _normalize_numeric(self, value) -> Optional[float]:
        """Normalize numeric value to float"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            clean_value = re.sub(r'[^\d.-]', '', str(value))
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return None

    def _clean_string(self, value) -> Optional[str]:
        """Clean and normalize string value"""
        if value is None:
            return None
        
        if isinstance(value, str):
            # Remove extra whitespace
            cleaned = ' '.join(value.split())
            return cleaned if cleaned else None
        
        return str(value) if value else None

