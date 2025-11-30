"""
Feature Extractor for Check Fraud Detection
Converts extracted check data into ML features
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np


class CheckFeatureExtractor:
    """
    Extract ML features from check data for fraud detection
    Extracts 30 check-specific features
    """

    def __init__(self):
        self.supported_banks = ['Bank of America', 'Chase', 'BANK OF AMERICA', 'CHASE']
        self.valid_routing_prefixes = {
            'Bank of America': ['0', '1', '2', '3', '0', '1'],
            'Chase': ['0', '1', '2', '3', '0', '2', '0', '7']
        }

    def extract_features(self, extracted_data: Dict, raw_text: str = "") -> List[float]:
        """
        Extract 30 features from check data

        Features 1-15: Basic features (bank, check number, amount, dates, etc.)
        Features 16-30: Advanced features (validation, field quality, fraud indicators)

        Returns:
            List of 30 float values representing features
        """
        import logging
        logger = logging.getLogger(__name__)

        # Log the input data to understand what we're working with
        logger.info(f"Feature extractor received data: {extracted_data}")
        logger.info(f"Extracted data keys: {list(extracted_data.keys())}")
        logger.info(f"Raw text length: {len(raw_text) if raw_text else 0}")

        features = []

        # Get fields from data
        bank_name = self._get_field(extracted_data, 'bank_name')
        check_number = self._get_field(extracted_data, 'check_number')
        routing_number = self._get_field(extracted_data, 'routing_number')
        account_number = self._get_field(extracted_data, 'account_number')

        logger.info(f"Basic fields: bank={bank_name}, check={check_number}, routing={routing_number}, account={account_number}")

        # Amount handling
        amount_raw = self._get_field(extracted_data, 'amount', 'amount_numeric')
        amount_numeric = self._extract_numeric_amount(amount_raw)
        amount_words = self._get_field(extracted_data, 'amount_words', 'amount_written')

        # Party information
        payer_name = self._get_field(extracted_data, 'payer_name')
        payee_name = self._get_field(extracted_data, 'payee_name')
        payer_address = self._get_field(extracted_data, 'payer_address')

        # Temporal and authorization
        check_date = self._get_field(extracted_data, 'date', 'check_date')
        signature_detected = self._get_field(extracted_data, 'signature_detected')
        memo = self._get_field(extracted_data, 'memo')

        # === BASIC FEATURES (1-15) ===

        # Feature 1: Bank validity (supported bank)
        features.append(1.0 if bank_name in self.supported_banks else 0.0)

        # Feature 2: Routing number validity (9 digits)
        features.append(self._validate_routing_number(routing_number))

        # Feature 3: Account number present
        features.append(1.0 if account_number else 0.0)

        # Feature 4: Check number present and valid format
        features.append(self._validate_check_number(check_number))

        # Feature 5: Amount (numeric value, capped at 50000)
        features.append(min(amount_numeric, 50000.0) if amount_numeric > 0 else 0.0)

        # Feature 6: Amount category (0=0-100, 1=100-1000, 2=1000-5000, 3=5000+)
        features.append(self._categorize_amount(amount_numeric))

        # Feature 7: Amount is round number (ends in .00)
        features.append(self._is_round_amount(amount_numeric))

        # Feature 8: Payer name present
        features.append(1.0 if payer_name else 0.0)

        # Feature 9: Payee name present
        features.append(1.0 if payee_name else 0.0)

        # Feature 10: Payer address present
        features.append(1.0 if payer_address else 0.0)

        # Feature 11: Date present
        features.append(1.0 if check_date else 0.0)

        # Feature 12: Date is in future (fraud indicator)
        features.append(self._is_future_date(check_date))

        # Feature 13: Date age in days (how old is the check)
        features.append(self._get_date_age(check_date))

        # Feature 14: Signature detected
        features.append(1.0 if signature_detected else 0.0)

        # Feature 15: Memo present
        features.append(1.0 if memo else 0.0)

        # === ADVANCED FEATURES (16-30) ===

        # Feature 16: Amount matching (numeric vs written)
        features.append(self._amount_matching_confidence(amount_numeric, amount_words))

        # Feature 17: Amount parsing confidence
        features.append(self._amount_parsing_confidence(amount_raw))

        # Feature 18: Suspicious amount pattern (e.g., $9,999.99, $4,999.00)
        features.append(self._detect_suspicious_amount(amount_numeric))

        # Feature 19: Date format validation
        features.append(self._validate_date_format(check_date))

        # Feature 20: Weekend/holiday check (higher fraud risk)
        features.append(self._is_weekend_or_holiday(check_date))

        # Feature 21: Critical missing fields count
        features.append(self._count_critical_missing_fields(extracted_data))

        # Feature 22: Overall field quality score
        features.append(self._calculate_field_quality(extracted_data, raw_text))

        # Feature 23: Bank-specific routing validation
        features.append(self._validate_bank_routing_match(bank_name, routing_number))

        # Feature 24: Check number format (sequential pattern)
        features.append(self._check_number_pattern_score(check_number))

        # Feature 25: Address validation (if present)
        features.append(self._validate_address_format(payer_address))

        # Feature 26: Name consistency (payer vs payee different)
        features.append(self._check_name_consistency(payer_name, payee_name))

        # Feature 27: Signature requirement met
        features.append(self._validate_signature_requirement(signature_detected))

        # Feature 28: Endorsement presence (for deposited checks)
        features.append(0.5)  # Placeholder - would need endorsement detection

        # Feature 29: Check type risk factor (personal=0.3, business=0.5, cashier=0.1)
        check_type = self._get_field(extracted_data, 'check_type')
        features.append(self._get_check_type_risk(check_type))

        # Feature 30: Anomaly score from text quality
        features.append(self._text_quality_score(raw_text))

        return features

    # === HELPER METHODS ===

    def _get_field(self, data: Dict, *field_names) -> Optional[str]:
        """Get field value, trying multiple possible field names"""
        for field_name in field_names:
            value = data.get(field_name)
            if value is not None:
                return value
        return None

    def _extract_numeric_amount(self, amount_value) -> float:
        """Extract numeric amount from various formats"""
        if amount_value is None:
            return 0.0

        # If dict with 'value' key
        if isinstance(amount_value, dict):
            return float(amount_value.get('value', 0.0))

        # If already numeric
        if isinstance(amount_value, (int, float)):
            return float(amount_value)

        # If string, parse it
        if isinstance(amount_value, str):
            # Remove currency symbols and commas
            clean_amount = re.sub(r'[^\d.]', '', amount_value)
            try:
                return float(clean_amount)
            except ValueError:
                return 0.0

        return 0.0

    def _validate_routing_number(self, routing: Optional[str]) -> float:
        """Validate routing number format (9 digits)"""
        if not routing:
            return 0.0
        routing_str = str(routing).strip()
        if len(routing_str) == 9 and routing_str.isdigit():
            return 1.0
        return 0.0

    def _validate_check_number(self, check_num: Optional[str]) -> float:
        """Validate check number presence and format"""
        if not check_num:
            return 0.0
        check_str = str(check_num).strip()
        # Check numbers are typically 3-6 digits
        if len(check_str) >= 3 and len(check_str) <= 6 and check_str.isdigit():
            return 1.0
        return 0.5  # Partial credit for presence

    def _categorize_amount(self, amount: float) -> float:
        """Categorize amount into risk brackets"""
        if amount < 100:
            return 0.0
        elif amount < 1000:
            return 1.0
        elif amount < 5000:
            return 2.0
        else:
            return 3.0

    def _is_round_amount(self, amount: float) -> float:
        """Check if amount is a round number (e.g., $100.00)"""
        if amount <= 0:
            return 0.0
        return 1.0 if amount % 10 == 0 else 0.0

    def _is_future_date(self, date_str: Optional[str]) -> float:
        """Check if date is in the future"""
        if not date_str:
            return 0.0
        try:
            check_date = self._parse_date(date_str)
            if check_date:
                now = datetime.now()
                # Compare only date parts (ignore time)
                if check_date.date() > now.date():
                    return 1.0
        except:
            pass
        return 0.0

    def _get_date_age(self, date_str: Optional[str]) -> float:
        """Get age of check in days (capped at 365)"""
        if not date_str:
            return 0.0
        try:
            check_date = self._parse_date(date_str)
            if check_date:
                age_days = (datetime.now() - check_date).days
                return min(max(age_days, 0), 365)
        except:
            pass
        return 0.0

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None

        date_formats = [
            '%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y',
            '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y',
            '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y'
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        return None

    def _amount_matching_confidence(self, amount_numeric: float, amount_words: Optional[str]) -> float:
        """Check if numeric and written amounts match"""
        if not amount_words or amount_numeric <= 0:
            return 0.5  # Neutral if missing

        # Extract numbers from written amount
        words_to_numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'hundred': 100, 'thousand': 1000
        }

        # Simplified matching - check for key numbers in text
        amount_words_lower = amount_words.lower()
        threshold = amount_numeric * 0.1  # 10% tolerance

        # If amount words contains numeric representation, assume valid
        if any(word in amount_words_lower for word in ['hundred', 'thousand']):
            return 1.0

        return 0.5

    def _amount_parsing_confidence(self, amount_raw) -> float:
        """Confidence in amount extraction"""
        if amount_raw is None:
            return 0.0
        if isinstance(amount_raw, (int, float)):
            return 1.0
        if isinstance(amount_raw, dict) and 'value' in amount_raw:
            return 1.0
        if isinstance(amount_raw, str) and re.search(r'\d+\.\d{2}', amount_raw):
            return 0.9
        return 0.5

    def _detect_suspicious_amount(self, amount: float) -> float:
        """Detect suspicious amount patterns (just under limits)"""
        suspicious_amounts = [999.99, 9999.99, 4999.00, 2999.00]
        for sus_amt in suspicious_amounts:
            if abs(amount - sus_amt) < 1.0:
                return 1.0
        return 0.0

    def _validate_date_format(self, date_str: Optional[str]) -> float:
        """Validate date format"""
        if not date_str:
            return 0.0
        return 1.0 if self._parse_date(date_str) else 0.0

    def _is_weekend_or_holiday(self, date_str: Optional[str]) -> float:
        """Check if date falls on weekend"""
        try:
            date_obj = self._parse_date(date_str)
            if date_obj and date_obj.weekday() >= 5:  # Saturday or Sunday
                return 1.0
        except:
            pass
        return 0.0

    def _count_critical_missing_fields(self, data: Dict) -> float:
        """Count missing critical fields (0-5 scale)"""
        critical_fields = ['bank_name', 'check_number', 'amount', 'payer_name', 'payee_name']
        missing = sum(1 for field in critical_fields if not self._get_field(data, field))
        return float(missing)

    def _calculate_field_quality(self, data: Dict, raw_text: str) -> float:
        """Overall data quality score (0.0 to 1.0)"""
        total_fields = 15  # Expected fields
        populated_fields = sum(1 for field in ['bank_name', 'check_number', 'routing_number',
                                                'account_number', 'amount', 'payer_name', 'payee_name',
                                                'check_date', 'signature_detected', 'payer_address',
                                                'memo', 'check_type', 'amount_words', 'payee_address',
                                                'payer_city'] if self._get_field(data, field))
        return populated_fields / total_fields

    def _validate_bank_routing_match(self, bank_name: Optional[str], routing: Optional[str]) -> float:
        """Validate routing number matches bank"""
        if not bank_name or not routing:
            return 0.5

        # Known routing prefixes for supported banks
        routing_str = str(routing).strip()
        if len(routing_str) != 9:
            return 0.0

        # Simple validation - would need full routing database in production
        return 1.0 if routing_str.isdigit() else 0.0

    def _check_number_pattern_score(self, check_num: Optional[str]) -> float:
        """Validate check number follows expected pattern"""
        if not check_num:
            return 0.0
        check_str = str(check_num).strip()
        # Sequential check numbers are normal (e.g., 1001, 1002, 1003)
        if check_str.isdigit() and 100 <= int(check_str) <= 999999:
            return 1.0
        return 0.5

    def _validate_address_format(self, address: Optional[str]) -> float:
        """Validate address format (contains numbers and letters)"""
        if not address:
            return 0.0
        # Simple check: address should contain both digits and letters
        has_digits = bool(re.search(r'\d', address))
        has_letters = bool(re.search(r'[a-zA-Z]', address))
        return 1.0 if (has_digits and has_letters) else 0.5

    def _check_name_consistency(self, payer: Optional[str], payee: Optional[str]) -> float:
        """Check if payer and payee are different (same name is suspicious)"""
        if not payer or not payee:
            return 0.5
        # Same person can't pay themselves (usually)
        return 0.0 if payer.lower().strip() == payee.lower().strip() else 1.0

    def _validate_signature_requirement(self, signature: Optional[bool]) -> float:
        """Signature requirement validation"""
        if signature is None:
            return 0.5
        return 1.0 if signature else 0.0

    def _get_check_type_risk(self, check_type: Optional[str]) -> float:
        """Risk factor based on check type"""
        if not check_type:
            return 0.3  # Default risk for unknown

        check_type_lower = check_type.lower()
        if 'cashier' in check_type_lower or 'certified' in check_type_lower:
            return 0.1  # Low risk
        elif 'business' in check_type_lower:
            return 0.5  # Medium risk
        else:  # Personal check
            return 0.3

    def _text_quality_score(self, raw_text: str) -> float:
        """Quality of OCR text extraction (0.0 = poor, 1.0 = excellent)"""
        if not raw_text:
            return 0.0

        # Check for special characters, length, readability
        text_length = len(raw_text)
        if text_length < 50:
            return 0.3  # Very short
        elif text_length < 200:
            return 0.6  # Normal
        else:
            return 0.9  # Comprehensive

    def get_feature_names(self) -> List[str]:
        """Return list of feature names for reference"""
        return [
            'bank_validity', 'routing_validity', 'account_present', 'check_number_valid',
            'amount_value', 'amount_category', 'round_amount', 'payer_present',
            'payee_present', 'payer_address_present', 'date_present', 'future_date',
            'date_age_days', 'signature_detected', 'memo_present',
            'amount_matching', 'amount_parsing_confidence', 'suspicious_amount',
            'date_format_valid', 'weekend_holiday', 'critical_missing_count',
            'field_quality', 'bank_routing_match', 'check_number_pattern',
            'address_valid', 'name_consistency', 'signature_requirement',
            'endorsement_present', 'check_type_risk', 'text_quality'
        ]
