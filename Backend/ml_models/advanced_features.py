"""
Advanced Feature Extraction for Money Order Fraud Detection
13 additional features (Features 18-30) for enhanced fraud detection
"""

import re
from datetime import datetime
from typing import Dict, Optional
from .amount_parser import amount_parser


class AdvancedFeatureExtractor:
    """
    Extract advanced fraud detection features
    Features 18-30 for enhanced ML model accuracy
    """

    def __init__(self):
        # Suspicious amount patterns (common fraud amounts)
        self.suspicious_amounts = [
            999, 1499, 1999, 2499, 2999, 3999, 4999,
            9999, 14999, 19999, 29999
        ]

        # Issuer-specific serial patterns (updated to match real formats)
        self.serial_patterns = {
            'Western Union': r'^WU\d{9,12}$',  # Western Union uses WU prefix
            'MoneyGram': r'^\d{9,11}$',        # MoneyGram: Just numbers, no prefix (e.g., 9021056789)
            'USPS': r'^\d{10,11}$',            # USPS: 10-11 digits
            '7-Eleven': r'^7E\d{8,10}$',       # 7-Eleven uses 7E prefix
            'Walmart': r'^WM\d{10,12}$',       # Walmart uses WM prefix
            'CVS': r'^CVS\d{8,10}$',          # CVS uses CVS prefix
            'ACE Cash Express': r'^ACE\d{8,10}$',  # ACE uses ACE prefix
            'Money Mart': r'^MM\d{8,10}$',    # Money Mart uses MM prefix
            'Check Into Cash': r'^CIC\d{8,10}$',  # Check Into Cash uses CIC prefix
            'Payroll': r'^PAYROLL[A-Z0-9]{3,}$'
        }

        # Issuer-specific required fields
        self.issuer_required_fields = {
            'Western Union': ['serial_primary', 'recipient', 'amount_numeric', 'sender_name', 'date'],
            'MoneyGram': ['serial_primary', 'recipient', 'amount_numeric', 'sender_name'],
            'USPS': ['serial_primary', 'recipient', 'amount_numeric', 'date'],
            'Payroll': ['serial_primary', 'recipient', 'amount_numeric', 'date'],
            'default': ['serial_primary', 'recipient', 'amount_numeric']
        }

    # ============================================================================
    # AMOUNT VALIDATION FEATURES (18-20)
    # ============================================================================

    def feature_18_exact_amount_match(self, amount_numeric: float, amount_written: str) -> float:
        """
        Feature 18: Exact Amount Match
        Check if numeric amount exactly matches parsed written amount

        Args:
            amount_numeric: Numeric amount value
            amount_written: Written amount text

        Returns:
            1.0 if exact match, 0.0 if mismatch or cannot parse
        """
        return amount_parser.exact_amount_match(amount_numeric, amount_written)

    def feature_19_amount_parsing_confidence(self, amount_numeric: float, amount_written: str) -> float:
        """
        Feature 19: Amount Parsing Confidence
        Confidence score of amount match (0.0-1.0)

        Args:
            amount_numeric: Numeric amount value
            amount_written: Written amount text

        Returns:
            Confidence score (1.0 = exact match, 0.5 = close, 0.0 = mismatch)
        """
        confidence, _ = amount_parser.get_amount_confidence(amount_numeric, amount_written)
        return confidence

    def feature_20_suspicious_amount_pattern(self, amount_numeric: float) -> float:
        """
        Feature 20: Suspicious Amount Pattern
        Detect fraud-prone amounts (e.g., $1499, $2999, just under limits)

        Args:
            amount_numeric: Numeric amount value

        Returns:
            1.0 if suspicious amount, 0.0 if normal
        """
        if not amount_numeric or amount_numeric == 0:
            return 0.0

        # Check if amount matches known suspicious patterns
        amount_int = int(amount_numeric)
        if amount_int in self.suspicious_amounts:
            return 1.0

        # Check if amount is just under common limits
        # (e.g., $999 under $1000 limit, $2999 under $3000 limit)
        for limit in [1000, 3000, 5000, 10000, 15000, 20000, 30000]:
            if limit - 100 <= amount_numeric < limit:
                return 1.0

        return 0.0

    # ============================================================================
    # DATE VALIDATION FEATURES (21-23)
    # ============================================================================

    def _parse_date_with_month_names(self, date_str: str) -> Optional[datetime]:
        """Parse date supporting month names"""
        if not date_str:
            return None
        
        # Try numeric formats
        for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try month name formats
        month_map = {
            'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4,
            'MAY': 5, 'JUNE': 6, 'JULY': 7, 'AUGUST': 8,
            'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12,
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
            'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
            'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        
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

    def feature_21_date_format_consistency(self, date_str: str) -> float:
        """
        Feature 21: Date Format Consistency
        Check if date is in valid, consistent format

        Args:
            date_str: Date string

        Returns:
            1.0 if valid format, 0.0 if invalid
        """
        if not date_str:
            return 0.0

        # Valid formats including month names
        valid_formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
            '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y',
            '%B %d, %Y', '%b %d, %Y',  # Full and abbreviated month names
            '%B %d %Y', '%b %d %Y'      # Without comma
        ]
        
        # Try standard formats
        for fmt in valid_formats:
            try:
                datetime.strptime(date_str, fmt)
                return 1.0
            except ValueError:
                continue
        
        # Try parsing month names manually
        month_names = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                       'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER',
                       'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                       'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        for month in month_names:
            pattern = rf'({month})\s+\d{{1,2}},?\s+\d{{4}}'
            if re.match(pattern, date_str, re.IGNORECASE):
                return 1.0
        
        return 0.0

    def feature_22_weekend_holiday_flag(self, date_str: str) -> float:
        """
        Feature 22: Weekend/Holiday Flag
        Money orders are rarely issued on weekends (red flag)

        Args:
            date_str: Date string

        Returns:
            1.0 if weekend date, 0.0 if weekday or cannot parse
        """
        if not date_str:
            return 0.0

        date_obj = self._parse_date_with_month_names(date_str)
        if date_obj:
            # 5 = Saturday, 6 = Sunday
            if date_obj.weekday() in [5, 6]:
                return 1.0
        return 0.0

    def feature_23_date_amount_correlation(self, date_str: str, amount_numeric: float) -> float:
        """
        Feature 23: Date-Amount Correlation
        Large amounts on unusual dates (weekends, very recent) are suspicious

        Args:
            date_str: Date string
            amount_numeric: Numeric amount

        Returns:
            Float score indicating suspicion level (0.0-1.0)
        """
        if not date_str or not amount_numeric:
            return 0.0

        # Large amounts (>$2000)
        is_large_amount = amount_numeric > 2000

        # Check if weekend
        is_weekend = self.feature_22_weekend_holiday_flag(date_str) == 1.0

        # Check if very recent (within 3 days)
        is_very_recent = False
        date_obj = self._parse_date_with_month_names(date_str)
        if date_obj:
            age_days = (datetime.now() - date_obj).days
            if 0 <= age_days <= 3:
                is_very_recent = True

        # Scoring logic
        score = 0.0
        if is_large_amount and is_weekend:
            score += 0.6  # High suspicion
        if is_large_amount and is_very_recent:
            score += 0.4  # Medium suspicion

        return min(1.0, score)

    # ============================================================================
    # FIELD COMPLETENESS FEATURES (24-26)
    # ============================================================================

    def feature_24_critical_missing_score(self, data: Dict) -> float:
        """
        Feature 24: Critical Missing Fields Score
        Weighted score based on importance of missing fields

        Args:
            data: Money order data dictionary

        Returns:
            Weighted missing fields score (higher = more missing)
        """
        # Define critical field groups (aliases) and their weights
        # If ANY field in the group is present, the requirement is met
        field_groups = [
            # Amount (Weight: 0.30)
            {'aliases': ['amount_numeric', 'amount'], 'weight': 0.30},
            
            # Serial Number (Weight: 0.25)
            {'aliases': ['serial_primary', 'serial_number'], 'weight': 0.25},
            
            # Recipient (Weight: 0.20)
            {'aliases': ['recipient', 'payee', 'pay_to'], 'weight': 0.20},
            
            # Sender (Weight: 0.15)
            {'aliases': ['sender_name', 'purchaser', 'from', 'sender'], 'weight': 0.15},
            
            # Date (Weight: 0.10)
            {'aliases': ['date'], 'weight': 0.10},
            
            # Signature (Weight: 0.05)
            {'aliases': ['signature'], 'weight': 0.05},
            
            # Issuer (Weight: 0.05)
            {'aliases': ['issuer_name', 'issuer'], 'weight': 0.05}
        ]

        score = 0.0
        for group in field_groups:
            # Check if ANY alias in the group has a value
            is_present = any(data.get(alias) for alias in group['aliases'])
            
            if not is_present:
                score += group['weight']

        return min(5.0, score)  # Cap at 5.0

    def feature_25_field_quality_score(self, data: Dict, raw_text: str = "") -> float:
        """
        Feature 25: Field Quality Score
        Assess OCR quality per field based on patterns and completeness

        Args:
            data: Money order data dictionary
            raw_text: Raw OCR text

        Returns:
            Quality score (0.0-1.0, higher = better quality)
        """
        quality_score = 0.0
        total_checks = 0

        # Check serial number quality
        serial = data.get('serial_primary') or data.get('serial_number')
        if serial:
            # Good serial: alphanumeric, 8-20 chars
            if 8 <= len(serial.replace('-', '').replace(' ', '')) <= 20:
                quality_score += 1.0
            total_checks += 1

        # Check amount quality
        amount = data.get('amount_numeric') or data.get('amount')
        if amount:
            # Good amount: positive number with reasonable value
            try:
                if isinstance(amount, dict):
                    amt_val = amount.get('value', 0)
                else:
                    amt_val = float(str(amount).replace('$', '').replace(',', ''))

                if 0 < amt_val <= 10000:  # Reasonable range
                    quality_score += 1.0
            except:
                pass
            total_checks += 1

        # Check name quality (no excessive special characters)
        for field in ['recipient', 'sender_name', 'payee', 'purchaser']:
            name = data.get(field)
            if name:
                # Good name: mostly letters, minimal special chars
                letters = sum(c.isalpha() or c.isspace() for c in str(name))
                if letters / len(str(name)) > 0.8:
                    quality_score += 1.0
                total_checks += 1

        # Check date quality
        date = data.get('date')
        if date:
            # Good date: valid format
            if self.feature_21_date_format_consistency(date) == 1.0:
                quality_score += 1.0
            total_checks += 1

        # Return average quality
        return quality_score / total_checks if total_checks > 0 else 0.0

    def feature_26_issuer_specific_validation(self, data: Dict) -> float:
        """
        Feature 26: Issuer-Specific Field Validation
        Check if all required fields for specific issuer are present

        Args:
            data: Money order data dictionary

        Returns:
            Completeness score (0.0-1.0)
        """
        issuer = data.get('issuer_name') or data.get('issuer')
        if not issuer:
            return 0.0

        # Get required fields for issuer
        required_fields = self.issuer_required_fields.get(issuer,
                                                          self.issuer_required_fields['default'])

        # Check how many required fields are present
        present_count = sum(1 for field in required_fields if data.get(field))
        total_required = len(required_fields)

        return present_count / total_required if total_required > 0 else 0.0

    # ============================================================================
    # ADVANCED PATTERN FEATURES (27-30)
    # ============================================================================

    def feature_27_serial_pattern_match(self, data: Dict) -> float:
        """
        Feature 27: Serial Number Pattern Match
        Check if serial number matches issuer-specific format

        Args:
            data: Money order data dictionary

        Returns:
            1.0 if matches pattern, 0.0 if doesn't match or unknown issuer
        """
        issuer = data.get('issuer_name') or data.get('issuer')
        serial = data.get('serial_primary') or data.get('serial_number')

        if not issuer or not serial:
            return 0.0

        # Get pattern for issuer
        pattern = self.serial_patterns.get(issuer)
        if not pattern:
            return 0.5  # Unknown issuer, neutral score

        # Check if serial matches pattern
        clean_serial = serial.replace('-', '').replace(' ', '').upper()
        if re.match(pattern, clean_serial):
            return 1.0
        else:
            return 0.0

    def feature_28_address_validation(self, data: Dict) -> float:
        """
        Feature 28: Address Validation
        Check if address format is valid

        Args:
            data: Money order data dictionary

        Returns:
            1.0 if valid address format, 0.0 if invalid or missing
        """
        address = data.get('sender_address')

        # Check if address exists and is a string
        if not address or not isinstance(address, str):
            return 0.0

        # Valid address should have:
        # - Numbers (street number)
        # - Letters (street name)
        # - Reasonable length (10-100 chars)
        has_numbers = bool(re.search(r'\d', address))
        has_letters = bool(re.search(r'[a-zA-Z]', address))
        reasonable_length = 10 <= len(address) <= 100

        if has_numbers and has_letters and reasonable_length:
            return 1.0
        else:
            return 0.0

    def feature_29_name_consistency(self, data: Dict) -> float:
        """
        Feature 29: Name Consistency
        Check if names follow typical patterns (first + last, no numbers, etc.)

        Args:
            data: Money order data dictionary

        Returns:
            Average consistency score across all names (0.0-1.0)
        """
        names_to_check = []

        # Gather names from data
        recipient = data.get('recipient') or data.get('payee')
        sender = data.get('sender_name') or data.get('purchaser')

        if recipient:
            names_to_check.append(recipient)
        if sender:
            names_to_check.append(sender)

        if not names_to_check:
            return 0.0

        scores = []
        for name in names_to_check:
            score = self._validate_name_pattern(name)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _validate_name_pattern(self, name: str) -> float:
        """Validate single name pattern"""
        # Check if name exists and is a string
        if not name or not isinstance(name, str):
            return 0.0

        score = 0.0

        # Good: No numbers in name
        if not re.search(r'\d', name):
            score += 0.4

        # Good: Has at least 2 words (first + last)
        words = name.split()
        if len(words) >= 2:
            score += 0.3

        # Good: Mostly alphabetic characters
        alpha_count = sum(c.isalpha() or c.isspace() for c in name)
        if len(name) > 0 and alpha_count / len(name) > 0.85:
            score += 0.3

        return score

    def feature_30_signature_required_score(self, data: Dict) -> float:
        """
        Feature 30: Signature Present Score
        Weighted by issuer requirements

        Args:
            data: Money order data dictionary

        Returns:
            1.0 if signature present and required, 0.5 if present but not required,
            0.0 if missing when required
        """
        signature = data.get('signature')
        issuer = data.get('issuer_name') or data.get('issuer')

        # Issuers that require signatures
        signature_required_issuers = ['Western Union', 'MoneyGram', 'USPS']

        if signature:
            # Signature present
            if issuer in signature_required_issuers:
                return 1.0  # Required and present
            else:
                return 0.5  # Not required but present
        else:
            # Signature missing
            if issuer in signature_required_issuers:
                return 0.0  # Required but missing (red flag)
            else:
                return 0.5  # Not required and not present (neutral)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def extract_all_advanced_features(self, data: Dict, raw_text: str = "") -> list:
        """
        Extract all 13 advanced features at once

        Args:
            data: Money order data dictionary
            raw_text: Raw OCR text

        Returns:
            List of 13 float values (features 18-30)
        """
        features = []

        # Get values from data (support both old and new field names)
        amount_raw = data.get('amount_numeric') or data.get('amount')

        # Handle amount (string or dict)
        if isinstance(amount_raw, dict):
            amount_numeric = amount_raw.get('value', 0.0)
        elif amount_raw:
            try:
                amount_numeric = float(str(amount_raw).replace('$', '').replace(',', ''))
            except:
                amount_numeric = 0.0
        else:
            amount_numeric = 0.0

        amount_written = data.get('amount_written') or data.get('amount_in_words')
        date_str = data.get('date')

        # Features 18-20: Amount Validation
        features.append(self.feature_18_exact_amount_match(amount_numeric, amount_written))
        features.append(self.feature_19_amount_parsing_confidence(amount_numeric, amount_written))
        features.append(self.feature_20_suspicious_amount_pattern(amount_numeric))

        # Features 21-23: Date Validation
        features.append(self.feature_21_date_format_consistency(date_str))
        features.append(self.feature_22_weekend_holiday_flag(date_str))
        features.append(self.feature_23_date_amount_correlation(date_str, amount_numeric))

        # Features 24-26: Field Completeness
        features.append(self.feature_24_critical_missing_score(data))
        features.append(self.feature_25_field_quality_score(data, raw_text))
        features.append(self.feature_26_issuer_specific_validation(data))

        # Features 27-30: Advanced Patterns
        features.append(self.feature_27_serial_pattern_match(data))
        features.append(self.feature_28_address_validation(data))
        features.append(self.feature_29_name_consistency(data))
        features.append(self.feature_30_signature_required_score(data))

        return features

    def get_advanced_feature_names(self) -> list:
        """Return feature names for features 18-30"""
        return [
            'exact_amount_match',              # 18
            'amount_parsing_confidence',       # 19
            'suspicious_amount_pattern',       # 20
            'date_format_consistency',         # 21
            'weekend_holiday_flag',            # 22
            'date_amount_correlation',         # 23
            'critical_missing_score',          # 24
            'field_quality_score',             # 25
            'issuer_specific_validation',      # 26
            'serial_pattern_match',            # 27
            'address_validation',              # 28
            'name_consistency',                # 29
            'signature_required_score'         # 30
        ]
