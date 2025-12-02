"""
Advanced Feature Extraction for Money Order Fraud Detection
13 additional features (Features 18-30) for enhanced fraud detection
Completely self-contained - no dependencies on other document type ML modules
"""

import re
from datetime import datetime
from typing import Dict, Optional


class MoneyOrderAdvancedFeatureExtractor:
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

        # Issuer-specific serial patterns
        self.serial_patterns = {
            'Western Union': r'^WU\d{9,12}$',
            'MoneyGram': r'^\d{9,11}$',
            'USPS': r'^\d{10,11}$',
            '7-Eleven': r'^7E\d{8,10}$',
            'Walmart': r'^WM\d{10,12}$',
            'CVS': r'^CVS\d{8,10}$',
            'ACE Cash Express': r'^ACE\d{8,10}$',
            'Money Mart': r'^MM\d{8,10}$',
            'Check Into Cash': r'^CIC\d{8,10}$',
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

    def _parse_amount_from_words(self, amount_words: str) -> Optional[float]:
        """Simple amount parser for written amounts"""
        if not amount_words:
            return None
        
        # Remove common words
        text = amount_words.upper().replace('DOLLARS', '').replace('DOLLAR', '').replace('AND', '').strip()
        
        # Try to extract numbers
        numbers = re.findall(r'\d+', text)
        if numbers:
            try:
                return float(''.join(numbers)) / 100 if len(numbers) > 1 else float(numbers[0])
            except:
                pass
        
        return None

    def feature_18_exact_amount_match(self, amount_numeric: float, amount_written: str) -> float:
        """Feature 18: Exact Amount Match"""
        if not amount_numeric or not amount_written:
            return 0.0
        
        parsed = self._parse_amount_from_words(amount_written)
        if parsed:
            return 1.0 if abs(parsed - amount_numeric) < 0.01 else 0.0
        return 0.0

    def feature_19_amount_parsing_confidence(self, amount_numeric: float, amount_written: str) -> float:
        """Feature 19: Amount Parsing Confidence"""
        if not amount_numeric or not amount_written:
            return 0.0
        
        parsed = self._parse_amount_from_words(amount_written)
        if parsed:
            diff = abs(parsed - amount_numeric)
            if diff < 0.01:
                return 1.0
            elif diff < 10:
                return 0.5
        return 0.0

    def feature_20_suspicious_amount_pattern(self, amount_numeric: float) -> float:
        """Feature 20: Suspicious Amount Pattern"""
        if not amount_numeric or amount_numeric == 0:
            return 0.0
        
        amount_int = int(amount_numeric)
        if amount_int in self.suspicious_amounts:
            return 1.0
        
        for limit in [1000, 3000, 5000, 10000, 15000, 20000, 30000]:
            if limit - 100 <= amount_numeric < limit:
                return 1.0
        
        return 0.0

    def _parse_date_with_month_names(self, date_str: str) -> Optional[datetime]:
        """Parse date supporting month names"""
        if not date_str:
            return None
        
        for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
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
        """Feature 21: Date Format Consistency"""
        if not date_str:
            return 0.0
        
        valid_formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
            '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y',
            '%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y'
        ]
        
        for fmt in valid_formats:
            try:
                datetime.strptime(date_str, fmt)
                return 1.0
            except ValueError:
                continue
        
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
        """Feature 22: Weekend/Holiday Flag"""
        if not date_str:
            return 0.0
        
        date_obj = self._parse_date_with_month_names(date_str)
        if date_obj:
            if date_obj.weekday() in [5, 6]:  # Saturday, Sunday
                return 1.0
        return 0.0

    def feature_23_date_amount_correlation(self, date_str: str, amount_numeric: float) -> float:
        """Feature 23: Date-Amount Correlation"""
        if not date_str or not amount_numeric:
            return 0.0
        
        is_large_amount = amount_numeric > 2000
        is_weekend = self.feature_22_weekend_holiday_flag(date_str) == 1.0
        
        is_very_recent = False
        date_obj = self._parse_date_with_month_names(date_str)
        if date_obj:
            age_days = (datetime.now() - date_obj).days
            if 0 <= age_days <= 3:
                is_very_recent = True
        
        score = 0.0
        if is_large_amount and is_weekend:
            score += 0.6
        if is_large_amount and is_very_recent:
            score += 0.4
        
        return min(1.0, score)

    def feature_24_critical_missing_score(self, data: Dict) -> float:
        """Feature 24: Critical Missing Fields Score"""
        field_groups = [
            {'aliases': ['amount_numeric', 'amount'], 'weight': 0.30},
            {'aliases': ['serial_primary', 'serial_number'], 'weight': 0.25},
            {'aliases': ['recipient', 'payee', 'pay_to'], 'weight': 0.20},
            {'aliases': ['sender_name', 'purchaser', 'from', 'sender'], 'weight': 0.15},
            {'aliases': ['date'], 'weight': 0.10},
            {'aliases': ['signature'], 'weight': 0.05},
            {'aliases': ['issuer_name', 'issuer'], 'weight': 0.05}
        ]

        score = 0.0
        for group in field_groups:
            is_present = any(data.get(alias) for alias in group['aliases'])
            if not is_present:
                score += group['weight']

        return min(5.0, score)

    def feature_25_field_quality_score(self, data: Dict, raw_text: str = "") -> float:
        """Feature 25: Field Quality Score"""
        quality_score = 0.0
        total_checks = 0

        serial = data.get('serial_primary') or data.get('serial_number')
        if serial:
            if 8 <= len(serial.replace('-', '').replace(' ', '')) <= 20:
                quality_score += 1.0
            total_checks += 1

        amount = data.get('amount_numeric') or data.get('amount')
        if amount:
            try:
                if isinstance(amount, dict):
                    amt_val = amount.get('value', 0)
                else:
                    amt_val = float(str(amount).replace('$', '').replace(',', ''))
                if 0 < amt_val <= 10000:
                    quality_score += 1.0
            except:
                pass
            total_checks += 1

        for field in ['recipient', 'sender_name', 'payee', 'purchaser']:
            name = data.get(field)
            if name:
                letters = sum(c.isalpha() or c.isspace() for c in str(name))
                if letters / len(str(name)) > 0.8:
                    quality_score += 1.0
                total_checks += 1

        date = data.get('date')
        if date:
            if self.feature_21_date_format_consistency(date) == 1.0:
                quality_score += 1.0
            total_checks += 1

        return quality_score / total_checks if total_checks > 0 else 0.0

    def feature_26_issuer_specific_validation(self, data: Dict) -> float:
        """Feature 26: Issuer-Specific Field Validation"""
        issuer = data.get('issuer_name') or data.get('issuer')
        if not issuer:
            return 0.0

        required_fields = self.issuer_required_fields.get(issuer, self.issuer_required_fields['default'])
        present_count = sum(1 for field in required_fields if data.get(field))
        total_required = len(required_fields)

        return present_count / total_required if total_required > 0 else 0.0

    def feature_27_serial_pattern_match(self, data: Dict) -> float:
        """Feature 27: Serial Number Pattern Match"""
        issuer = data.get('issuer_name') or data.get('issuer')
        serial = data.get('serial_primary') or data.get('serial_number')

        if not issuer or not serial:
            return 0.0

        pattern = self.serial_patterns.get(issuer)
        if not pattern:
            return 0.5

        clean_serial = serial.replace('-', '').replace(' ', '').upper()
        if re.match(pattern, clean_serial):
            return 1.0
        else:
            return 0.0

    def feature_28_address_validation(self, data: Dict) -> float:
        """Feature 28: Address Validation"""
        address = data.get('sender_address')

        if not address or not isinstance(address, str):
            return 0.0

        has_numbers = bool(re.search(r'\d', address))
        has_letters = bool(re.search(r'[a-zA-Z]', address))
        reasonable_length = 10 <= len(address) <= 100

        if has_numbers and has_letters and reasonable_length:
            return 1.0
        else:
            return 0.0

    def feature_29_name_consistency(self, data: Dict) -> float:
        """Feature 29: Name Consistency"""
        names_to_check = []

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
        if not name or not isinstance(name, str):
            return 0.0

        score = 0.0

        if not re.search(r'\d', name):
            score += 0.4

        words = name.split()
        if len(words) >= 2:
            score += 0.3

        alpha_count = sum(c.isalpha() or c.isspace() for c in name)
        if len(name) > 0 and alpha_count / len(name) > 0.85:
            score += 0.3

        return score

    def feature_30_signature_required_score(self, data: Dict) -> float:
        """Feature 30: Signature Present Score"""
        signature = data.get('signature')
        issuer = data.get('issuer_name') or data.get('issuer')

        signature_required_issuers = ['Western Union', 'MoneyGram', 'USPS']

        if signature:
            if issuer in signature_required_issuers:
                return 1.0
            else:
                return 0.5
        else:
            if issuer in signature_required_issuers:
                return 0.0
            else:
                return 0.5

    def extract_all_advanced_features(self, data: Dict, raw_text: str = "") -> list:
        """Extract all 13 advanced features at once"""
        features = []

        amount_raw = data.get('amount_numeric') or data.get('amount')
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

        features.append(self.feature_18_exact_amount_match(amount_numeric, amount_written))
        features.append(self.feature_19_amount_parsing_confidence(amount_numeric, amount_written))
        features.append(self.feature_20_suspicious_amount_pattern(amount_numeric))
        features.append(self.feature_21_date_format_consistency(date_str))
        features.append(self.feature_22_weekend_holiday_flag(date_str))
        features.append(self.feature_23_date_amount_correlation(date_str, amount_numeric))
        features.append(self.feature_24_critical_missing_score(data))
        features.append(self.feature_25_field_quality_score(data, raw_text))
        features.append(self.feature_26_issuer_specific_validation(data))
        features.append(self.feature_27_serial_pattern_match(data))
        features.append(self.feature_28_address_validation(data))
        features.append(self.feature_29_name_consistency(data))
        features.append(self.feature_30_signature_required_score(data))

        return features

    def get_advanced_feature_names(self) -> list:
        """Return feature names for features 18-30"""
        return [
            'exact_amount_match',
            'amount_parsing_confidence',
            'suspicious_amount_pattern',
            'date_format_consistency',
            'weekend_holiday_flag',
            'date_amount_correlation',
            'critical_missing_score',
            'field_quality_score',
            'issuer_specific_validation',
            'serial_pattern_match',
            'address_validation',
            'name_consistency',
            'signature_required_score'
        ]


