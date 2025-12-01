"""
Base Normalizer Class for Bank Statements
Abstract base class for all bank-specific bank statement normalizers
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional, List
from .bank_statement_schema import NormalizedBankStatement


class BankStatementBaseNormalizer(ABC):
    """
    Abstract base class for bank statement normalizers
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
        Return mapping from Mindee field names to standardized field names
        Must be implemented by each bank-specific normalizer

        Returns:
            Dict mapping Mindee field names to standardized schema field names
        """
        pass

    def normalize(self, ocr_data: Dict) -> NormalizedBankStatement:
        """
        Normalize OCR-extracted bank statement data to standardized schema

        Args:
            ocr_data: Dictionary containing OCR-extracted fields from Mindee

        Returns:
            NormalizedBankStatement instance with standardized data
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
                if std_field == 'beginning_balance' or std_field == 'ending_balance' or std_field == 'total_credits' or std_field == 'total_debits':
                    normalized_data[std_field] = self._normalize_amount(raw_value)
                elif 'date' in std_field:
                    normalized_data[std_field] = self._normalize_date(raw_value)
                elif std_field == 'transactions':
                    normalized_data[std_field] = self._normalize_transactions(raw_value)
                elif std_field == 'bank_address' or std_field == 'account_holder_address':
                    normalized_data[std_field] = self._normalize_address(raw_value)
                elif std_field == 'account_holder_names':
                    normalized_data[std_field] = self._normalize_account_holder_names(raw_value)
                else:
                    # For other fields, clean the string
                    normalized_data[std_field] = self._clean_string(raw_value)

        # Create and return NormalizedBankStatement instance
        return NormalizedBankStatement.from_dict(normalized_data)

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
            # Remove currency symbols and commas
            clean_amount = re.sub(r'[^\d.-]', '', amount_value)
            try:
                return {
                    'value': float(clean_amount),
                    'currency': 'USD'
                }
            except ValueError:
                return None

        return None

    def _normalize_date(self, date_value) -> Optional[str]:
        """
        Normalize date to ISO format (YYYY-MM-DD)

        Args:
            date_value: Date from OCR (could be str, datetime, or dict)

        Returns:
            ISO format date string (YYYY-MM-DD) or None
        """
        if date_value is None:
            return None

        # If already a datetime object
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')

        # If it's a dict with date info
        if isinstance(date_value, dict):
            if 'date' in date_value:
                date_value = date_value['date']
            elif 'value' in date_value:
                date_value = date_value['value']

        # If it's a string, parse it
        if isinstance(date_value, str):
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
                '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
                '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
                '%Y/%m/%d', '%Y-%m-%d'
            ]

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_value.strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue

        return None

    def _normalize_transactions(self, transactions_value) -> Optional[List[Dict]]:
        """
        Normalize transactions list

        Args:
            transactions_value: Transactions from OCR (could be list of dicts or list of objects)

        Returns:
            List of normalized transaction dicts
        """
        if transactions_value is None:
            return None

        if not isinstance(transactions_value, list):
            return None

        normalized_transactions = []
        for transaction in transactions_value:
            if isinstance(transaction, dict):
                normalized_txn = {
                    'date': self._normalize_date(transaction.get('date')),
                    'description': self._clean_string(transaction.get('description')),
                    'amount': self._normalize_amount(transaction.get('amount'))
                }
                normalized_transactions.append(normalized_txn)
            elif hasattr(transaction, 'fields'):
                # Mindee object with fields
                fields = transaction.fields if hasattr(transaction, 'fields') else {}
                normalized_txn = {
                    'date': self._normalize_date(fields.get('date').value if hasattr(fields.get('date'), 'value') else fields.get('date')),
                    'description': self._clean_string(fields.get('description').value if hasattr(fields.get('description'), 'value') else fields.get('description')),
                    'amount': self._normalize_amount(fields.get('amount').value if hasattr(fields.get('amount'), 'value') else fields.get('amount'))
                }
                normalized_transactions.append(normalized_txn)

        return normalized_transactions if normalized_transactions else None

    def _normalize_address(self, address_value) -> Optional[Dict]:
        """
        Normalize address to structured format

        Args:
            address_value: Address from OCR (could be dict, str, or object)

        Returns:
            Dictionary with address components
        """
        if address_value is None:
            return None

        # If already a dict with address components
        if isinstance(address_value, dict):
            return {
                'address': address_value.get('address', ''),
                'street': address_value.get('street', ''),
                'city': address_value.get('city', ''),
                'state': address_value.get('state', ''),
                'postal_code': address_value.get('postal_code', ''),
                'country': address_value.get('country', 'US')
            }

        # If it's a Mindee object with fields
        if hasattr(address_value, 'fields'):
            fields = address_value.fields
            return {
                'address': fields.get('address').value if hasattr(fields.get('address'), 'value') else fields.get('address', ''),
                'street': fields.get('street').value if hasattr(fields.get('street'), 'value') else fields.get('street', ''),
                'city': fields.get('city').value if hasattr(fields.get('city'), 'value') else fields.get('city', ''),
                'state': fields.get('state').value if hasattr(fields.get('state'), 'value') else fields.get('state', ''),
                'postal_code': fields.get('postal_code').value if hasattr(fields.get('postal_code'), 'value') else fields.get('postal_code', ''),
                'country': fields.get('country').value if hasattr(fields.get('country'), 'value') else fields.get('country', 'US')
            }

        # If it's a string, try to parse it
        if isinstance(address_value, str):
            # Simple parsing - could be enhanced
            return {
                'address': address_value,
                'street': '',
                'city': '',
                'state': '',
                'postal_code': '',
                'country': 'US'
            }

        return None

    def _normalize_account_holder_names(self, names_value) -> Optional[List[str]]:
        """
        Normalize account holder names to list

        Args:
            names_value: Names from OCR (could be list, str, or object)

        Returns:
            List of account holder names
        """
        if names_value is None:
            return None

        # If already a list
        if isinstance(names_value, list):
            return [self._clean_string(name) for name in names_value if name]

        # If it's a string, convert to list
        if isinstance(names_value, str):
            # Split by comma or newline
            names = [self._clean_string(name) for name in re.split(r'[,;\n]', names_value) if name.strip()]
            return names if names else None

        # If it's a Mindee object with items
        if hasattr(names_value, 'items'):
            names = []
            for item in names_value.items:
                if hasattr(item, 'value'):
                    names.append(self._clean_string(item.value))
                else:
                    names.append(self._clean_string(str(item)))
            return names if names else None

        return None

    def _clean_string(self, value) -> Optional[str]:
        """
        Clean and normalize string value

        Args:
            value: String value to clean

        Returns:
            Cleaned string or None
        """
        if value is None:
            return None

        if isinstance(value, str):
            # Remove extra whitespace
            cleaned = ' '.join(value.split())
            return cleaned if cleaned else None

        # If it's a Mindee SimpleField object
        if hasattr(value, 'value'):
            return self._clean_string(value.value)

        return str(value) if value else None

    def _parse_address_components(self, full_address: str) -> Dict[str, Optional[str]]:
        """
        Parse full address string into components

        Args:
            full_address: Full address string

        Returns:
            Dict with city, state, zip components
        """
        if not full_address:
            return {'city': None, 'state': None, 'zip': None}

        # Common US address pattern: "City, State ZIP"
        pattern = r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
        match = re.search(pattern, full_address)

        if match:
            return {
                'city': match.group(1).strip(),
                'state': match.group(2).strip(),
                'zip': match.group(3).strip()
            }

        return {'city': None, 'state': None, 'zip': None}

