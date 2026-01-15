"""
Base Normalizer Class
Abstract base class for all issuer-specific normalizers
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional
from .schema import NormalizedMoneyOrder


class BaseNormalizer(ABC):
    """
    Abstract base class for money order normalizers
    All issuer-specific normalizers must inherit from this class
    """

    def __init__(self, issuer_name: str):
        """
        Initialize normalizer with issuer name

        Args:
            issuer_name: Name of the money order issuer
        """
        self.issuer_name = issuer_name

    @abstractmethod
    def get_field_mappings(self) -> Dict[str, str]:
        """
        Return mapping from OCR field names to standardized field names
        Must be implemented by each issuer-specific normalizer

        Returns:
            Dict mapping OCR field names to standardized schema field names
            Example:
            {
                'purchaser': 'sender_name',
                'payee': 'recipient',
                'amount': 'amount_numeric'
            }
        """
        pass

    def normalize(self, ocr_data: Dict) -> NormalizedMoneyOrder:
        """
        Normalize OCR-extracted data to standardized schema

        Args:
            ocr_data: Dictionary containing OCR-extracted fields

        Returns:
            NormalizedMoneyOrder instance with standardized data
        """
        # Get issuer-specific field mappings
        field_mappings = self.get_field_mappings()

        # Initialize normalized data dictionary
        normalized_data = {
            'issuer_name': self.issuer_name
        }

        # Map and normalize each field
        for ocr_field, std_field in field_mappings.items():
            if ocr_field in ocr_data and ocr_data[ocr_field]:
                raw_value = ocr_data[ocr_field]

                # Apply field-specific normalization
                if std_field == 'amount_numeric':
                    normalized_data[std_field] = self._normalize_amount(raw_value)
                elif std_field == 'date':
                    normalized_data[std_field] = self._normalize_date(raw_value)
                else:
                    # For other fields, just clean the string
                    normalized_data[std_field] = self._clean_string(raw_value)
            # Note: Don't set to None in else - field may have been set by alternate name mapping

        # Create and return NormalizedMoneyOrder instance
        return NormalizedMoneyOrder.from_dict(normalized_data)

    def _normalize_amount(self, amount_str) -> Dict:
        """
        Normalize amount to {'value': float, 'currency': str} format

        Args:
            amount_str: Amount string from OCR (e.g., '$750.00', '750.00 USD') or float value

        Returns:
            Dictionary with 'value' and 'currency' keys
        """
        if not amount_str and amount_str != 0:
            return None

        # Convert to string if it's a number (Mindee returns floats)
        if isinstance(amount_str, (int, float)):
            amount_str = str(amount_str)
        else:
            # Remove whitespace
            amount_str = amount_str.strip()

        # Extract numeric value
        # Patterns: $750.00, 750.00 USD, USD 750.00, 750,00
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
        currency_patterns = ['USD', 'US$', 'EUR', 'GBP', 'CAD']
        for curr in currency_patterns:
            if curr in amount_str.upper():
                currency = curr.replace('US$', 'USD')
                break

        return {
            'value': value,
            'currency': currency
        }

    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize date to MM-DD-YYYY format

        Args:
            date_str: Date string from OCR (various formats)

        Returns:
            Date string in MM-DD-YYYY format or None if parsing fails
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # Common date formats to try
        date_formats = [
            '%m/%d/%Y',      # 10/15/2024
            '%m-%d-%Y',      # 10-15-2024
            '%m/%d/%y',      # 10/15/24
            '%m-%d-%y',      # 10-15-24
            '%d/%m/%Y',      # 15/10/2024 (European)
            '%d-%m-%Y',      # 15-10-2024
            '%Y-%m-%d',      # 2024-10-15 (ISO)
            '%B %d, %Y',     # October 15, 2024
            '%b %d, %Y',     # Oct 15, 2024
            '%d %B %Y',      # 15 October 2024
            '%d %b %Y',      # 15 Oct 2024
        ]

        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                # Return in standardized MM-DD-YYYY format
                return date_obj.strftime('%m-%d-%Y')
            except ValueError:
                continue

        # If no format matched, return None
        return None

    def _clean_string(self, value: str) -> str:
        """
        Clean and normalize string values

        Args:
            value: Raw string value

        Returns:
            Cleaned string
        """
        if not value:
            return None

        # Convert to string if not already
        value = str(value).strip()

        # Remove extra whitespace
        value = ' '.join(value.split())

        # Return None if empty after cleaning
        return value if value else None

    def _extract_phone_number(self, text: str) -> Optional[str]:
        """
        Extract and normalize phone number from text

        Args:
            text: Text containing phone number

        Returns:
            Normalized phone number or None
        """
        if not text:
            return None

        # Pattern for US phone numbers
        phone_pattern = r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
        match = re.search(phone_pattern, text)

        if match:
            # Format as XXX-XXX-XXXX
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        return None

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(issuer='{self.issuer_name}')"
