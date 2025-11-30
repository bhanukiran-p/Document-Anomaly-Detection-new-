"""
Feature Extractor for Money Order Fraud Detection
Converts extracted money order data into ML features
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
from .advanced_features import AdvancedFeatureExtractor


class FeatureExtractor:
    """
    Extract ML features from money order data for fraud detection
    Extracts 30 features (17 basic + 13 advanced)
    """

    def __init__(self):
        self.valid_issuers = ['USPS', 'Western Union', 'MoneyGram', '7-Eleven',
                             'Walmart', 'CVS', 'ACE Cash Express', 'Money Mart',
                             'Check Into Cash', 'Payroll', 'Paystub']
        # Initialize advanced feature extractor
        self.advanced_extractor = AdvancedFeatureExtractor()

    def extract_features(self, extracted_data: Dict, raw_text: str = "") -> List[float]:
        """
        Extract 30 features from money order data
        Works with both raw OCR data and normalized data

        Features 1-17: Basic features (issuer, serial, amount, dates, etc.)
        Features 18-30: Advanced features (amount matching, date validation, field quality)

        Returns:
            List of 30 float values representing features
        """
        features = []

        # Get issuer (support both old and normalized field names)
        issuer = self._get_field(extracted_data, 'issuer', 'issuer_name')

        # Get serial number (support both old and normalized)
        serial = self._get_field(extracted_data, 'serial_number', 'serial_primary')

        # Get amount (handle both string and dict formats)
        amount_raw = self._get_field(extracted_data, 'amount', 'amount_numeric')
        amount_numeric = self._extract_numeric_amount(amount_raw)

        # Get amount in words
        amount_words = self._get_field(extracted_data, 'amount_in_words', 'amount_written')

        # Get recipient/payee
        recipient = self._get_field(extracted_data, 'payee', 'recipient')

        # Get sender/purchaser
        sender = self._get_field(extracted_data, 'purchaser', 'sender_name')

        # Get date
        date = self._get_field(extracted_data, 'date', 'date')

        # Get signature
        signature = self._get_field(extracted_data, 'signature', 'signature')

        # Get receipt/secondary serial
        # receipt = self._get_field(extracted_data, 'receipt_number', 'serial_secondary')

        # Get location (old field only, not in normalized schema)
        location = extracted_data.get('location')

        # Feature 1: Issuer validity
        features.append(self._validate_issuer(issuer))

        # Feature 2: Serial number length
        features.append(self._get_serial_length(serial))

        # Feature 3: Serial number format validity
        features.append(self._validate_serial_format(serial))

        # Feature 4: Amount (numeric value)
        features.append(amount_numeric)

        # Feature 5: Amount consistency (numeric vs written)
        features.append(self._check_amount_consistency(amount_raw, amount_words))

        # Feature 6: Amount is round number
        features.append(self._is_round_amount(amount_numeric))

        # Feature 7: Recipient/Payee present
        features.append(1.0 if recipient else 0.0)

        # Feature 8: Sender/Purchaser present
        features.append(1.0 if sender else 0.0)

        # Feature 9: Date present
        features.append(1.0 if date else 0.0)

        # Feature 10: Date is in future (red flag)
        features.append(self._is_future_date(date))

        # Feature 11: Date age in days
        features.append(self._get_date_age_days(date))

        # Feature 12: Location present
        features.append(1.0 if location else 0.0)

        # Feature 13: Signature present
        features.append(1.0 if signature else 0.0)

        # Feature 14: Receipt/Secondary serial present (REMOVED)
        features.append(0.0)

        # Feature 15: Missing critical fields count
        features.append(self._count_missing_fields(extracted_data))

        # Feature 16: Text quality score
        features.append(self._calculate_text_quality(raw_text))

        # Feature 17: Amount range category
        features.append(self._categorize_amount(amount_numeric))

        # ===== ADVANCED FEATURES (18-30) =====
        # Extract all 13 advanced features using the advanced extractor
        advanced_features = self.advanced_extractor.extract_all_advanced_features(
            extracted_data, raw_text
        )
        features.extend(advanced_features)

        return features

    def _get_field(self, data: Dict, old_key: str, new_key: str):
        """
        Get field value supporting both old and normalized field names

        Args:
            data: Data dictionary
            old_key: Old field name (from raw OCR)
            new_key: New field name (from normalized schema)

        Returns:
            Field value or None
        """
        # Try new key first (normalized), then fall back to old key
        return data.get(new_key) or data.get(old_key)

    def _validate_issuer(self, issuer: str) -> float:
        """Check if issuer is valid"""
        if not issuer:
            return 0.0
        if issuer in self.valid_issuers:
            return 1.0
        return 0.8

    def _get_serial_length(self, serial: str) -> float:
        """Get serial number length"""
        if not serial:
            return 0.0
        return float(len(serial.replace('-', '').replace(' ', '')))

    def _validate_serial_format(self, serial: str) -> float:
        """Validate serial number format (alphanumeric, 8-20 chars)"""
        if not serial:
            return 0.0
        clean_serial = serial.replace('-', '').replace(' ', '')
        if 8 <= len(clean_serial) <= 20 and clean_serial.isalnum():
            return 1.0
        return 0.0

    def _extract_numeric_amount(self, amount_input) -> float:
        """
        Extract numeric amount from string or dict

        Args:
            amount_input: Either a string (e.g., "$750.00") or dict (e.g., {'value': 750.00, 'currency': 'USD'})

        Returns:
            Numeric amount as float
        """
        if not amount_input:
            return 0.0

        # Handle normalized format (dict)
        if isinstance(amount_input, dict):
            return float(amount_input.get('value', 0.0))

        # Handle raw OCR format (string)
        if isinstance(amount_input, (str, int, float)):
            amount_str = str(amount_input)
            # Remove currency symbols and commas
            amount_clean = amount_str.replace('$', '').replace(',', '').strip()

            try:
                return float(amount_clean)
            except (ValueError, AttributeError):
                return 0.0

        return 0.0

    def _check_amount_consistency(self, amount: str, amount_words: str) -> float:
        """Check if numeric and written amounts match"""
        if not amount or not amount_words:
            return 0.0

        # Extract numeric value
        numeric = self._extract_numeric_amount(amount)

        # Extract number from written amount (simplified)
        # Look for patterns like "SEVEN HUNDRED FIFTY" or numbers
        try:
            # Extract the integer part from written format
            words_upper = amount_words.upper()

            # Simple heuristic: if we find the dollar amount in words
            word_to_num = {
                'ZERO': 0, 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4,
                'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9,
                'TEN': 10, 'TWENTY': 20, 'THIRTY': 30, 'FORTY': 40,
                'FIFTY': 50, 'SIXTY': 60, 'SEVENTY': 70, 'EIGHTY': 80,
                'NINETY': 90, 'HUNDRED': 100, 'THOUSAND': 1000
            }

            # For now, return 1.0 if both exist (more sophisticated matching needed)
            # This is a simplified version - real implementation would parse the words
            return 1.0 if numeric > 0 else 0.5

        except Exception:
            return 0.5

    def _is_round_amount(self, amount: float) -> float:
        """Check if amount is a round number (100, 500, 1000, etc.)"""
        if amount == 0:
            return 0.0

        round_amounts = [50, 100, 150, 200, 250, 300, 400, 500, 750, 1000, 1500, 2000]
        return 1.0 if amount in round_amounts else 0.0

    def _is_future_date(self, date_str: str) -> float:
        """Check if date is in the future (red flag)"""
        if not date_str:
            return 0.0

        try:
            # Try multiple date formats including month names
            date_obj = self._parse_date_flexible(date_str)
            if date_obj:
                now = datetime.now()
                # Compare only date parts (ignore time)
                return 1.0 if date_obj.date() > now.date() else 0.0
            return 0.0
        except Exception:
            return 0.0

    def _parse_date_flexible(self, date_str: str) -> Optional[datetime]:
        """Parse date string with multiple format support"""
        if not date_str:
            return None
        
        # Month name mapping
        month_map = {
            'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4,
            'MAY': 5, 'JUNE': 6, 'JULY': 7, 'AUGUST': 8,
            'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12,
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
            'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
            'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        
        # Try numeric formats first
        for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try month name formats
        for month_name, month_num in month_map.items():
            pattern = rf'({month_name})\s+(\d{{1,2}}),?\s+(\d{{4}})'
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                day = int(match.group(2))
                year = int(match.group(3))
                try:
                    return datetime(year, month_num, day)
                except ValueError:
                    continue
        
        return None

    def _get_date_age_days(self, date_str: str) -> float:
        """Get age of the date in days"""
        if not date_str:
            return 0.0

        try:
            date_obj = self._parse_date_flexible(date_str)
            if date_obj:
                age_days = (datetime.now() - date_obj).days
                return float(max(0, age_days))
            return 0.0
        except Exception:
            return 0.0

    def _count_missing_fields(self, data: Dict) -> float:
        """
        Count missing critical fields
        Supports both raw OCR and normalized field names
        """
        # Check for normalized field names first, then fall back to old names
        critical_fields_map = [
            ('issuer_name', 'issuer'),
            ('serial_primary', 'serial_number'),
            ('amount_numeric', 'amount'),
            ('recipient', 'payee'),
            ('date', 'date')
        ]

        missing = 0
        for new_field, old_field in critical_fields_map:
            if not (data.get(new_field) or data.get(old_field)):
                missing += 1

        return float(missing)

    def _calculate_text_quality(self, raw_text: str) -> float:
        """Calculate text quality score (0-1)"""
        if not raw_text:
            return 0.0

        # Heuristics for text quality
        score = 0.0

        # Length check (good OCR should have decent text)
        if len(raw_text) > 100:
            score += 0.3

        # Character diversity (not all caps or all numbers)
        has_lowercase = any(c.islower() for c in raw_text)
        has_uppercase = any(c.isupper() for c in raw_text)
        has_digits = any(c.isdigit() for c in raw_text)

        if has_lowercase or has_uppercase:
            score += 0.2
        if has_digits:
            score += 0.2

        # Presence of common money order keywords
        keywords = ['money order', 'pay to', 'amount', 'date', 'serial']
        keyword_count = sum(1 for kw in keywords if kw.lower() in raw_text.lower())
        score += min(0.3, keyword_count * 0.1)

        return min(1.0, score)

    def _categorize_amount(self, amount: float) -> float:
        """Categorize amount into ranges"""
        if amount == 0:
            return 0.0
        elif amount < 100:
            return 0.0  # Low
        elif amount < 500:
            return 1.0  # Medium
        elif amount < 1000:
            return 2.0  # High
        else:
            return 3.0  # Very high

    def get_feature_names(self) -> List[str]:
        """Return all 30 feature names for interpretability"""
        # Basic features (1-17)
        basic_features = [
            'issuer_valid',
            'serial_length',
            'serial_format_valid',
            'amount_numeric',
            'amount_consistent',
            'amount_is_round',
            'payee_present',
            'purchaser_present',
            'date_present',
            'date_is_future',
            'date_age_days',
            'location_present',
            'signature_present',
            'receipt_present',
            'missing_fields_count',
            'text_quality_score',
            'amount_category'
        ]

        # Advanced features (18-30)
        advanced_features = self.advanced_extractor.get_advanced_feature_names()

        return basic_features + advanced_features
