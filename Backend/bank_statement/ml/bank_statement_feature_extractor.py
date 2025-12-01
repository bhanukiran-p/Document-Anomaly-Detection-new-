"""
Feature Extractor for Bank Statement Fraud Detection
Converts extracted bank statement data into ML features
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np


class BankStatementFeatureExtractor:
    """
    Extract ML features from bank statement data for fraud detection
    Extracts 35 bank statement-specific features
    """

    def __init__(self):
        self.supported_banks = [
            'Bank of America', 'Chase', 'Wells Fargo', 'Citibank',
            'U.S. Bank', 'PNC Bank', 'TD Bank', 'Capital One',
            'BANK OF AMERICA', 'CHASE', 'WELLS FARGO', 'CITIBANK'
        ]

    def extract_features(self, extracted_data: Dict, raw_text: str = "") -> List[float]:
        """
        Extract 35 features from bank statement data

        Features 1-20: Basic features (bank, account, balances, dates, transactions)
        Features 21-35: Advanced features (validation, patterns, fraud indicators)

        Returns:
            List of 35 float values representing features
        """
        import logging
        logger = logging.getLogger(__name__)

        features = []

        # Get fields from data
        bank_name = self._get_field(extracted_data, 'bank_name')
        account_number = self._get_field(extracted_data, 'account_number')
        account_holder_name = self._get_field(extracted_data, 'account_holder_name')
        account_type = self._get_field(extracted_data, 'account_type')

        # Balance handling
        beginning_balance = self._extract_numeric_amount(extracted_data.get('beginning_balance'))
        ending_balance = self._extract_numeric_amount(extracted_data.get('ending_balance'))
        total_credits = self._extract_numeric_amount(extracted_data.get('total_credits'))
        total_debits = self._extract_numeric_amount(extracted_data.get('total_debits'))

        # Date handling
        statement_period_start = self._get_field(extracted_data, 'statement_period_start_date')
        statement_period_end = self._get_field(extracted_data, 'statement_period_end_date')
        statement_date = self._get_field(extracted_data, 'statement_date')

        # Transactions
        transactions = extracted_data.get('transactions', [])

        # === BASIC FEATURES (1-20) ===

        # Feature 1: Bank validity (supported bank)
        features.append(1.0 if bank_name in self.supported_banks else 0.0)

        # Feature 2: Account number present
        features.append(1.0 if account_number else 0.0)

        # Feature 3: Account holder name present
        features.append(1.0 if account_holder_name else 0.0)

        # Feature 4: Account type present
        features.append(1.0 if account_type else 0.0)

        # Feature 5: Beginning balance (capped at 1,000,000)
        features.append(min(abs(beginning_balance), 1000000.0) if beginning_balance else 0.0)

        # Feature 6: Ending balance (capped at 1,000,000)
        features.append(min(abs(ending_balance), 1000000.0) if ending_balance else 0.0)

        # Feature 7: Total credits (capped at 1,000,000)
        features.append(min(abs(total_credits), 1000000.0) if total_credits else 0.0)

        # Feature 8: Total debits (capped at 1,000,000)
        features.append(min(abs(total_debits), 1000000.0) if total_debits else 0.0)

        # Feature 9: Statement period start date present
        features.append(1.0 if statement_period_start else 0.0)

        # Feature 10: Statement period end date present
        features.append(1.0 if statement_period_end else 0.0)

        # Feature 11: Statement date present
        features.append(1.0 if statement_date else 0.0)

        # Feature 12: Statement period is in future (fraud indicator)
        features.append(self._is_future_period(statement_period_start, statement_period_end))

        # Feature 13: Statement period age in days (how old is the statement)
        features.append(self._get_period_age(statement_period_end))

        # Feature 14: Transaction count
        transaction_count = len(transactions) if transactions else 0
        features.append(min(transaction_count, 1000.0))  # Cap at 1000

        # Feature 15: Average transaction amount
        avg_txn_amount = self._calculate_avg_transaction_amount(transactions)
        features.append(min(abs(avg_txn_amount), 50000.0) if avg_txn_amount else 0.0)

        # Feature 16: Largest transaction amount
        max_txn_amount = self._calculate_max_transaction_amount(transactions)
        features.append(min(abs(max_txn_amount), 100000.0) if max_txn_amount else 0.0)

        # Feature 17: Balance change (ending - beginning)
        balance_change = ending_balance - beginning_balance if (ending_balance and beginning_balance) else 0.0
        features.append(min(abs(balance_change), 1000000.0))

        # Feature 18: Negative ending balance (fraud indicator)
        features.append(1.0 if ending_balance and ending_balance < 0 else 0.0)

        # Feature 19: Balance consistency (credits - debits should match balance change)
        balance_consistency = self._check_balance_consistency(
            beginning_balance, ending_balance, total_credits, total_debits
        )
        features.append(balance_consistency)

        # Feature 20: Currency present
        currency = self._get_field(extracted_data, 'currency')
        features.append(1.0 if currency else 0.0)

        # === ADVANCED FEATURES (21-35) ===

        # Feature 21: Suspicious transaction pattern (many small transactions)
        features.append(self._detect_suspicious_transaction_pattern(transactions))

        # Feature 22: Large transaction count (transactions > $10,000)
        large_txn_count = self._count_large_transactions(transactions, threshold=10000)
        features.append(min(large_txn_count, 50.0))

        # Feature 23: Round number transactions (suspicious pattern)
        round_txn_count = self._count_round_number_transactions(transactions)
        features.append(min(round_txn_count, 100.0))

        # Feature 24: Date format validation
        features.append(self._validate_date_format(statement_period_start))

        # Feature 25: Statement period length (in days)
        period_length = self._calculate_period_length(statement_period_start, statement_period_end)
        features.append(min(period_length, 365.0))

        # Feature 26: Critical missing fields count
        features.append(self._count_critical_missing_fields(extracted_data))

        # Feature 27: Overall field quality score
        features.append(self._calculate_field_quality(extracted_data, raw_text))

        # Feature 28: Transaction date consistency (all within statement period)
        features.append(self._check_transaction_date_consistency(transactions, statement_period_start, statement_period_end))

        # Feature 29: Duplicate transaction detection
        features.append(self._detect_duplicate_transactions(transactions))

        # Feature 30: Unusual transaction timing (weekend/holiday transactions)
        features.append(self._detect_unusual_timing(transactions))

        # Feature 31: Account number format validation
        features.append(self._validate_account_number_format(account_number))

        # Feature 32: Account holder name format validation
        features.append(self._validate_name_format(account_holder_name))

        # Feature 33: Balance volatility (large swings)
        features.append(self._calculate_balance_volatility(transactions, beginning_balance))

        # Feature 34: Credit/Debit ratio
        credit_debit_ratio = total_credits / total_debits if total_debits > 0 else (total_credits if total_credits > 0 else 0.0)
        features.append(min(credit_debit_ratio, 100.0))

        # Feature 35: Text quality score
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
            clean_amount = re.sub(r'[^\d.-]', '', amount_value)
            try:
                return float(clean_amount)
            except ValueError:
                return 0.0

        return 0.0

    def _is_future_period(self, start_date: Optional[str], end_date: Optional[str]) -> float:
        """Check if statement period is in the future"""
        if not end_date:
            return 0.0
        try:
            period_end = self._parse_date(end_date)
            if period_end:
                now = datetime.now()
                if period_end.date() > now.date():
                    return 1.0
        except:
            pass
        return 0.0

    def _get_period_age(self, end_date: Optional[str]) -> float:
        """Get age of statement period end date in days (capped at 365)"""
        if not end_date:
            return 0.0
        try:
            period_end = self._parse_date(end_date)
            if period_end:
                age_days = (datetime.now() - period_end).days
                return min(max(age_days, 0), 365)
        except:
            pass
        return 0.0

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None

        date_formats = [
            '%Y-%m-%d', '%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y',
            '%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y'
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        return None

    def _calculate_avg_transaction_amount(self, transactions: List) -> Optional[float]:
        """Calculate average transaction amount"""
        if not transactions:
            return None

        amounts = []
        for txn in transactions:
            if isinstance(txn, dict):
                amount = self._extract_numeric_amount(txn.get('amount'))
                if amount:
                    amounts.append(abs(amount))

        return sum(amounts) / len(amounts) if amounts else None

    def _calculate_max_transaction_amount(self, transactions: List) -> Optional[float]:
        """Calculate maximum transaction amount"""
        if not transactions:
            return None

        amounts = []
        for txn in transactions:
            if isinstance(txn, dict):
                amount = self._extract_numeric_amount(txn.get('amount'))
                if amount:
                    amounts.append(abs(amount))

        return max(amounts) if amounts else None

    def _check_balance_consistency(
        self,
        beginning: Optional[float],
        ending: Optional[float],
        credits: Optional[float],
        debits: Optional[float]
    ) -> float:
        """Check if balances are consistent (ending = beginning + credits - debits)"""
        if not all([beginning is not None, ending is not None, credits is not None, debits is not None]):
            return 0.5  # Neutral if missing data

        expected_ending = beginning + credits - debits
        difference = abs(ending - expected_ending)
        
        # Allow small rounding differences (up to $1)
        if difference <= 1.0:
            return 1.0
        elif difference <= 10.0:
            return 0.5
        else:
            return 0.0

    def _detect_suspicious_transaction_pattern(self, transactions: List) -> float:
        """Detect suspicious patterns (many small transactions)"""
        if not transactions or len(transactions) < 10:
            return 0.0

        small_txn_count = 0
        for txn in transactions:
            if isinstance(txn, dict):
                amount = abs(self._extract_numeric_amount(txn.get('amount')))
                if 0 < amount < 100:  # Many small transactions
                    small_txn_count += 1

        # If more than 50% are small transactions, flag as suspicious
        if small_txn_count / len(transactions) > 0.5:
            return 1.0
        return 0.0

    def _count_large_transactions(self, transactions: List, threshold: float = 10000) -> int:
        """Count transactions above threshold"""
        if not transactions:
            return 0

        count = 0
        for txn in transactions:
            if isinstance(txn, dict):
                amount = abs(self._extract_numeric_amount(txn.get('amount')))
                if amount >= threshold:
                    count += 1
        return count

    def _count_round_number_transactions(self, transactions: List) -> int:
        """Count transactions with round numbers (e.g., $100.00, $1000.00)"""
        if not transactions:
            return 0

        count = 0
        for txn in transactions:
            if isinstance(txn, dict):
                amount = abs(self._extract_numeric_amount(txn.get('amount')))
                if amount > 0 and amount % 100 == 0:  # Round to nearest $100
                    count += 1
        return count

    def _validate_date_format(self, date_str: Optional[str]) -> float:
        """Validate date format"""
        if not date_str:
            return 0.0
        return 1.0 if self._parse_date(date_str) else 0.0

    def _calculate_period_length(self, start_date: Optional[str], end_date: Optional[str]) -> float:
        """Calculate statement period length in days"""
        if not start_date or not end_date:
            return 0.0

        try:
            start = self._parse_date(start_date)
            end = self._parse_date(end_date)
            if start and end:
                return (end - start).days
        except:
            pass
        return 0.0

    def _count_critical_missing_fields(self, data: Dict) -> float:
        """Count missing critical fields"""
        critical_fields = [
            'bank_name', 'account_number', 'account_holder_name',
            'statement_period_start_date', 'statement_period_end_date',
            'beginning_balance', 'ending_balance'
        ]
        missing = sum(1 for field in critical_fields if not self._get_field(data, field))
        return float(missing)

    def _calculate_field_quality(self, data: Dict, raw_text: str) -> float:
        """Overall data quality score (0.0 to 1.0)"""
        total_fields = 17  # Expected Mindee fields
        populated_fields = sum(1 for field in [
            'bank_name', 'account_number', 'account_holder_name', 'account_type',
            'statement_period_start_date', 'statement_period_end_date', 'statement_date',
            'beginning_balance', 'ending_balance', 'total_credits', 'total_debits',
            'currency', 'transactions', 'bank_address'
        ] if self._get_field(data, field))
        return populated_fields / total_fields

    def _check_transaction_date_consistency(
        self,
        transactions: List,
        period_start: Optional[str],
        period_end: Optional[str]
    ) -> float:
        """Check if all transactions are within statement period"""
        if not transactions or not period_start or not period_end:
            return 0.5

        try:
            start = self._parse_date(period_start)
            end = self._parse_date(period_end)
            if not start or not end:
                return 0.5

            consistent_count = 0
            for txn in transactions:
                if isinstance(txn, dict):
                    txn_date = self._parse_date(txn.get('date'))
                    if txn_date and start <= txn_date <= end:
                        consistent_count += 1

            return consistent_count / len(transactions) if transactions else 0.0
        except:
            return 0.5

    def _detect_duplicate_transactions(self, transactions: List) -> float:
        """Detect duplicate transactions"""
        if not transactions or len(transactions) < 2:
            return 0.0

        seen = set()
        duplicates = 0
        for txn in transactions:
            if isinstance(txn, dict):
                # Create a signature: date + amount + description (first 20 chars)
                date = txn.get('date', '')
                amount = self._extract_numeric_amount(txn.get('amount'))
                desc = (txn.get('description', '') or '')[:20]
                signature = f"{date}|{amount}|{desc}"
                
                if signature in seen:
                    duplicates += 1
                else:
                    seen.add(signature)

        return 1.0 if duplicates > 0 else 0.0

    def _detect_unusual_timing(self, transactions: List) -> float:
        """Detect transactions on weekends/holidays"""
        if not transactions:
            return 0.0

        weekend_count = 0
        for txn in transactions:
            if isinstance(txn, dict):
                txn_date = self._parse_date(txn.get('date'))
                if txn_date and txn_date.weekday() >= 5:  # Saturday or Sunday
                    weekend_count += 1

        return weekend_count / len(transactions) if transactions else 0.0

    def _validate_account_number_format(self, account_number: Optional[str]) -> float:
        """Validate account number format"""
        if not account_number:
            return 0.0
        # Account numbers are typically 8-17 digits
        account_str = str(account_number).strip()
        if account_str.isdigit() and 8 <= len(account_str) <= 17:
            return 1.0
        return 0.5  # Partial credit if present but format unclear

    def _validate_name_format(self, name: Optional[str]) -> float:
        """Validate account holder name format"""
        if not name:
            return 0.0
        # Name should contain letters and possibly spaces
        name_str = str(name).strip()
        if re.search(r'[A-Za-z]', name_str) and len(name_str) >= 3:
            return 1.0
        return 0.5

    def _calculate_balance_volatility(self, transactions: List, beginning_balance: Optional[float]) -> float:
        """Calculate balance volatility (large swings)"""
        if not transactions or beginning_balance is None:
            return 0.0

        current_balance = beginning_balance
        max_swing = 0.0

        for txn in transactions:
            if isinstance(txn, dict):
                amount = self._extract_numeric_amount(txn.get('amount'))
                # Assume positive amounts are credits, negative are debits
                # This is simplified - real implementation would check transaction type
                current_balance += amount
                swing = abs(amount)
                max_swing = max(max_swing, swing)

        # Normalize by beginning balance
        if beginning_balance > 0:
            return min(max_swing / beginning_balance, 10.0)  # Cap at 10x
        return 0.0

    def _text_quality_score(self, raw_text: str) -> float:
        """Quality of OCR text extraction (0.0 = poor, 1.0 = excellent)"""
        if not raw_text:
            return 0.0

        text_length = len(raw_text)
        if text_length < 100:
            return 0.3
        elif text_length < 500:
            return 0.6
        else:
            return 0.9

    def get_feature_names(self) -> List[str]:
        """Return list of feature names for reference"""
        return [
            'bank_validity', 'account_number_present', 'account_holder_present', 'account_type_present',
            'beginning_balance', 'ending_balance', 'total_credits', 'total_debits',
            'period_start_present', 'period_end_present', 'statement_date_present', 'future_period',
            'period_age_days', 'transaction_count', 'avg_transaction_amount', 'max_transaction_amount',
            'balance_change', 'negative_ending_balance', 'balance_consistency', 'currency_present',
            'suspicious_transaction_pattern', 'large_transaction_count', 'round_number_transactions',
            'date_format_valid', 'period_length_days', 'critical_missing_count', 'field_quality',
            'transaction_date_consistency', 'duplicate_transactions', 'unusual_timing',
            'account_number_format_valid', 'name_format_valid', 'balance_volatility',
            'credit_debit_ratio', 'text_quality'
        ]

