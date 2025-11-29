"""
Base Normalizer Class for Checks
Abstract base class for all bank-specific check normalizers
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional
from .check_schema import NormalizedCheck


class CheckBaseNormalizer(ABC):
    """
    Abstract base class for check normalizers
    All bank-specific normalizers must inherit from this class
    """

    def __init__(self, bank_name: str):
        """
        Initialize normalizer with bank name

        Args:
            bank_name: Name of the bank (e.g., 'Bank of America', 'Chase')
        """
        self.bank_name = bank_name

    @abstractmethod
    def get_field_mappings(self) -> Dict[str, str]:
        """
        Return mapping from OCR/Mindee field names to standardized field names
        Must be implemented by each bank-specific normalizer

        Returns:
            Dict mapping OCR field names to standardized schema field names
        """
        pass

    def normalize(self, ocr_data: Dict) -> NormalizedCheck:
        """
        Normalize OCR-extracted check data to standardized schema

        Args:
            ocr_data: Dictionary containing OCR-extracted fields from Mindee

        Returns:
            NormalizedCheck instance with standardized data
        """
        # Get bank-specific field mappings
        field_mappings = self.get_field_mappings()

        # Initialize normalized data dictionary
        normalized_data = {
            'bank_name': self.bank_name
        }

        # Map and normalize each field
        for ocr_field, std_field in field_mappings.items():
            if ocr_field in ocr_data and ocr_data[ocr_field] is not None:
                raw_value = ocr_data[ocr_field]

                # Apply field-specific normalization
                if std_field == 'amount_numeric':
                    normalized_data[std_field] = self._normalize_amount(raw_value)
                elif std_field == 'check_date':
                    normalized_data[std_field] = self._normalize_date(raw_value)
                elif std_field == 'signature_detected':
                    normalized_data[std_field] = self._normalize_boolean(raw_value)
                else:
                    # For other fields, clean the string
                    normalized_data[std_field] = self._clean_string(raw_value)

        # Create and return NormalizedCheck instance
        return NormalizedCheck.from_dict(normalized_data)

    def _normalize_amount(self, amount_value) -> Optional[Dict]:
        """
        Normalize amount to {'value': float, 'currency': str} format

        Args:
            amount_value: Amount from OCR (could be float, str, or dict)

        Returns:
            Dictionary with 'value' and 'currency' keys
        """
        if amount_value is None:
            return None

        # If already a dict with value, return it
        if isinstance(amount_value, dict) and 'value' in amount_value:
            return {
                'value': float(amount_value['value']),
                'currency': amount_value.get('currency', 'USD')
            }

        # If it's a number, convert directly
        if isinstance(amount_value, (int, float)):
            return {
                'value': float(amount_value),
                'currency': 'USD'
            }

        # If it's a string, parse it
        if isinstance(amount_value, str):
            amount_str = amount_value.strip()

            # Extract numeric value
            numeric_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', amount_str)
            if not numeric_match:
                return None

            value_str = numeric_match.group(1).replace(',', '')
            try:
                value = float(value_str)
            except ValueError:
                return None

            # Extract currency (default to USD)
            currency = 'USD'
            if 'EUR' in amount_str.upper():
                currency = 'EUR'
            elif 'GBP' in amount_str.upper():
                currency = 'GBP'
            elif 'CAD' in amount_str.upper():
                currency = 'CAD'

            return {
                'value': value,
                'currency': currency
            }

        return None

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date to MM-DD-YYYY format

        Args:
            date_str: Date string from OCR (various formats)

        Returns:
            Date string in MM-DD-YYYY format or None if parsing fails
        """
        if not date_str:
            return None

        date_str = str(date_str).strip()

        # Common date formats to try
        date_formats = [
            '%m/%d/%Y',      # 11/28/2025
            '%m-%d-%Y',      # 11-28-2025
            '%m/%d/%y',      # 11/28/25
            '%m-%d-%y',      # 11-28-25
            '%d/%m/%Y',      # 28/11/2025 (European)
            '%d-%m-%Y',      # 28-11-2025
            '%Y-%m-%d',      # 2025-11-28 (ISO)
            '%B %d, %Y',     # November 28, 2025
            '%b %d, %Y',     # Nov 28, 2025
            '%d %B %Y',      # 28 November 2025
            '%d %b %Y',      # 28 Nov 2025
        ]

        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                # Return in standardized MM-DD-YYYY format
                return date_obj.strftime('%m-%d-%Y')
            except ValueError:
                continue

        # If no format matched, return original
        return date_str

    def _normalize_boolean(self, value) -> Optional[bool]:
        """
        Normalize boolean values

        Args:
            value: Boolean-like value (True, False, 'yes', 'no', 1, 0, etc.)

        Returns:
            Boolean value or None
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value > 0

        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['true', 'yes', '1', 'present', 'detected']:
                return True
            if value_lower in ['false', 'no', '0', 'absent', 'not detected']:
                return False

        return None

    def _clean_string(self, value) -> Optional[str]:
        """
        Clean and normalize string values

        Args:
            value: Raw string value

        Returns:
            Cleaned string or None
        """
        if value is None:
            return None

        # Convert to string if not already
        value = str(value).strip()

        # Remove extra whitespace
        value = ' '.join(value.split())

        # Return None if empty after cleaning
        return value if value else None

    def _parse_address_components(self, address_str: str) -> Dict[str, Optional[str]]:
        """
        Parse address string into components (street, city, state, zip)

        Args:
            address_str: Full address string

        Returns:
            Dict with 'address', 'city', 'state', 'zip' keys
        """
        if not address_str:
            return {'address': None, 'city': None, 'state': None, 'zip': None}

        # Simple regex patterns for US addresses
        # Format: 123 Main St, Anytown, CA 12345
        zip_pattern = r'\b(\d{5}(?:-\d{4})?)\b'
        state_pattern = r'\b([A-Z]{2})\b'

        zip_match = re.search(zip_pattern, address_str)
        state_match = re.search(state_pattern, address_str)

        zip_code = zip_match.group(1) if zip_match else None
        state = state_match.group(1) if state_match else None

        # Extract city (text between last comma and state)
        city = None
        if state_match:
            parts = address_str[:state_match.start()].split(',')
            if len(parts) > 1:
                city = parts[-1].strip()

        # Extract street address (everything before city)
        street_address = address_str
        if city:
            street_address = address_str.split(city)[0].rstrip(', ')

        return {
            'address': street_address if street_address else None,
            'city': city,
            'state': state,
            'zip': zip_code
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(bank='{self.bank_name}')"
