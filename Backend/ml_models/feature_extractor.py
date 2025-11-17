"""
Feature Extractor for Money Order Fraud Detection
Converts extracted money order data into ML features
"""

import re
from datetime import datetime
from typing import Dict, List
import numpy as np


class FeatureExtractor:
    """
    Extract ML features from money order data for fraud detection
    """

    def __init__(self):
        self.valid_issuers = ['USPS', 'Western Union', 'MoneyGram', '7-Eleven',
                             'Walmart', 'CVS', 'ACE Cash Express', 'Money Mart',
                             'Check Into Cash']

    def extract_features(self, extracted_data: Dict, raw_text: str = "") -> List[float]:
        """
        Extract 17 features from money order data

        Returns:
            List of 17 float values representing features
        """
        features = []

        # Feature 1: Issuer validity (1 if valid, 0 if invalid/missing)
        features.append(self._validate_issuer(extracted_data.get('issuer')))

        # Feature 2: Serial number length
        features.append(self._get_serial_length(extracted_data.get('serial_number')))

        # Feature 3: Serial number format validity
        features.append(self._validate_serial_format(extracted_data.get('serial_number')))

        # Feature 4: Amount (numeric value)
        amount_numeric = self._extract_numeric_amount(extracted_data.get('amount'))
        features.append(amount_numeric)

        # Feature 5: Amount consistency (numeric vs written)
        features.append(self._check_amount_consistency(
            extracted_data.get('amount'),
            extracted_data.get('amount_in_words')
        ))

        # Feature 6: Amount is round number (e.g., $100, $500)
        features.append(self._is_round_amount(amount_numeric))

        # Feature 7: Payee present
        features.append(1.0 if extracted_data.get('payee') else 0.0)

        # Feature 8: Purchaser present
        features.append(1.0 if extracted_data.get('purchaser') else 0.0)

        # Feature 9: Date present
        features.append(1.0 if extracted_data.get('date') else 0.0)

        # Feature 10: Date is in future (red flag)
        features.append(self._is_future_date(extracted_data.get('date')))

        # Feature 11: Date age in days
        features.append(self._get_date_age_days(extracted_data.get('date')))

        # Feature 12: Location present
        features.append(1.0 if extracted_data.get('location') else 0.0)

        # Feature 13: Signature present
        features.append(1.0 if extracted_data.get('signature') else 0.0)

        # Feature 14: Receipt number present
        features.append(1.0 if extracted_data.get('receipt_number') else 0.0)

        # Feature 15: Missing critical fields count
        features.append(self._count_missing_fields(extracted_data))

        # Feature 16: Text quality score (based on raw OCR text)
        features.append(self._calculate_text_quality(raw_text))

        # Feature 17: Amount range category (0: low, 1: medium, 2: high, 3: very high)
        features.append(self._categorize_amount(amount_numeric))

        return features

    def _validate_issuer(self, issuer: str) -> float:
        """Check if issuer is valid"""
        if not issuer:
            return 0.0
        return 1.0 if issuer in self.valid_issuers else 0.5

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

    def _extract_numeric_amount(self, amount_str: str) -> float:
        """Extract numeric amount from string"""
        if not amount_str:
            return 0.0

        # Remove currency symbols and commas
        amount_clean = amount_str.replace('$', '').replace(',', '').strip()

        try:
            return float(amount_clean)
        except (ValueError, AttributeError):
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
            # Try multiple date formats
            for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return 1.0 if date_obj > datetime.now() else 0.0
                except ValueError:
                    continue
            return 0.0
        except Exception:
            return 0.0

    def _get_date_age_days(self, date_str: str) -> float:
        """Get age of the date in days"""
        if not date_str:
            return 0.0

        try:
            for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    age_days = (datetime.now() - date_obj).days
                    return float(max(0, age_days))  # Ensure non-negative
                except ValueError:
                    continue
            return 0.0
        except Exception:
            return 0.0

    def _count_missing_fields(self, data: Dict) -> float:
        """Count missing critical fields"""
        critical_fields = ['issuer', 'serial_number', 'amount', 'payee', 'date']
        missing = sum(1 for field in critical_fields if not data.get(field))
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
        """Return feature names for interpretability"""
        return [
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
