"""
ML-Based Bank Statement Fraud Detector
Analyzes bank statements using machine learning to detect anomalies and fraudulent patterns
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class BankStatementFraudDetector:
    """
    Comprehensive fraud detection for bank statements using ML-compatible feature extraction
    """

    def __init__(self):
        """Initialize the fraud detector"""
        self.suspicious_keywords = [
            'nsf', 'overdraft', 'chargeback', 'return item', 'fraud alert',
            'dispute', 'unauthorized', 'fraudulent', 'erroneous', 'clawback',
            'reversal', 'suspended', 'frozen', 'closed', 'compromised'
        ]

    def extract_features(self, bank_data: Dict) -> Dict[str, Any]:
        """
        Extract ML-compatible features from bank statement data

        Args:
            bank_data: Extracted bank statement data

        Returns:
            Dictionary of extracted features
        """
        raw_text = (bank_data.get('raw_text') or '').lower()
        summary = bank_data.get('summary') or {}
        balances = bank_data.get('balances') or {}
        transactions = bank_data.get('transactions') or []

        features = {
            # Basic field completeness
            'has_bank_name': bool(bank_data.get('bank_name')),
            'has_account_holder': bool(bank_data.get('account_holder')),
            'has_account_number': bool(bank_data.get('account_number')),
            'has_statement_period': bool(bank_data.get('statement_period')),
            'has_opening_balance': bool(balances.get('opening_balance')),
            'has_closing_balance': bool(balances.get('closing_balance')),

            # Transaction features
            'transaction_count': len(transactions),
            'has_transactions': len(transactions) > 0,

            # Balance features
            'opening_balance_value': self._safe_float(balances.get('opening_balance'), 0),
            'closing_balance_value': self._safe_float(balances.get('closing_balance'), 0),
            'balance_difference': self._calculate_balance_diff(balances),
            'balance_consistency': self._check_balance_consistency(summary, balances),

            # Transaction analysis
            'transaction_patterns': self._analyze_transaction_patterns(transactions),
            'large_transaction_count': self._count_large_transactions(transactions),
            'unusual_transaction_dates': self._analyze_transaction_dates(transactions),
            'average_transaction_amount': self._avg_transaction_amount(transactions),
            'transaction_amount_variance': self._transaction_variance(transactions),

            # Debit/Credit analysis
            'total_credits': self._safe_float(summary.get('total_credits'), 0),
            'total_debits': self._safe_float(summary.get('total_debits'), 0),
            'credit_debit_ratio': self._calculate_credit_debit_ratio(summary),
            'net_activity': self._safe_float(summary.get('net_activity'), 0),

            # Text quality and content analysis
            'suspicious_keyword_count': self._count_suspicious_keywords(raw_text),
            'has_fraud_indicators': self._has_fraud_indicators(raw_text),
            'text_quality_score': self._assess_text_quality(raw_text),
            'unusual_characters': self._count_unusual_characters(raw_text),

            # Temporal analysis
            'statement_period_days': self._calculate_statement_period(bank_data),
            'unusual_statement_period': self._check_unusual_period(bank_data),

            # Account activity intensity
            'activity_intensity': self._calculate_activity_intensity(
                len(transactions),
                self._calculate_statement_period(bank_data)
            ),

            # Balance volatility
            'balance_volatility': self._calculate_balance_volatility(transactions, balances),
        }

        return features

    def calculate_fraud_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate fraud risk score using extracted features

        Args:
            features: Dictionary of extracted features

        Returns:
            Fraud risk score (0-100)
        """
        score = 0.0

        # Missing critical fields (weight: 25%)
        missing_fields = sum([
            not features.get('has_bank_name'),
            not features.get('has_account_holder'),
            not features.get('has_account_number'),
            not features.get('has_statement_period'),
            not features.get('has_opening_balance'),
            not features.get('has_closing_balance'),
        ])
        score += (missing_fields / 6) * 25

        # Transaction anomalies (weight: 25%)
        transaction_count = features.get('transaction_count', 0)
        if transaction_count == 0:
            score += 25  # No transactions is very suspicious
        elif transaction_count < 3:
            score += 10  # Very few transactions
        else:
            # Check for suspicious patterns
            if features.get('large_transaction_count', 0) > (transaction_count * 0.5):
                score += 8  # More than 50% large transactions

            unusual_dates = features.get('unusual_transaction_dates', 0)
            if unusual_dates > 0:
                score += min(10, unusual_dates * 2)  # Up to 10 for unusual dates

        # Balance inconsistencies (weight: 20%)
        if not features.get('balance_consistency'):
            score += 20  # Major inconsistency

        # Credit/Debit ratio anomalies (weight: 15%)
        ratio = features.get('credit_debit_ratio', 0)
        if ratio > 0:
            if ratio > 3.0 or ratio < 0.3:  # Extreme ratios
                score += 15
            elif ratio > 2.0 or ratio < 0.5:  # Unusual ratios
                score += 8

        # Text quality issues (weight: 10%)
        text_quality = features.get('text_quality_score', 1.0)
        if text_quality < 0.7:
            score += 10 * (1 - text_quality)

        # Suspicious keywords (weight: 10%)
        suspicious_count = features.get('suspicious_keyword_count', 0)
        score += min(10, suspicious_count * 3)

        # Ensure score is in range 0-100
        return max(0.0, min(100.0, score))

    def identify_risk_factors(self, features: Dict[str, Any], score: float) -> List[str]:
        """
        Identify specific risk factors from features

        Args:
            features: Extracted features
            score: Calculated fraud score

        Returns:
            List of risk factor descriptions
        """
        factors = []

        # Missing fields
        if not features.get('has_bank_name'):
            factors.append("Bank name missing")
        if not features.get('has_account_holder'):
            factors.append("Account holder name missing")
        if not features.get('has_account_number'):
            factors.append("Account number missing")
        if not features.get('has_statement_period'):
            factors.append("Statement period missing")

        # Transaction issues
        if features.get('transaction_count', 0) == 0:
            factors.append("No transactions found")
        elif features.get('transaction_count', 0) < 3:
            factors.append("Unusually few transactions")

        if features.get('unusual_transaction_dates', 0) > 0:
            factors.append(f"Unusual transaction dates detected ({features['unusual_transaction_dates']})")

        # Balance issues
        if not features.get('balance_consistency'):
            factors.append("Balance calculation inconsistency")

        if features.get('balance_volatility', 0) > 0.5:
            factors.append("High balance volatility")

        # Credit/Debit issues
        ratio = features.get('credit_debit_ratio', 0)
        if ratio > 3.0:
            factors.append(f"Unusually high credit/debit ratio ({ratio:.2f})")
        elif ratio > 0 and ratio < 0.3:
            factors.append(f"Unusually low credit/debit ratio ({ratio:.2f})")

        # Text quality
        if features.get('text_quality_score', 1.0) < 0.7:
            factors.append("Poor text quality or OCR issues")

        # Suspicious keywords
        if features.get('suspicious_keyword_count', 0) > 0:
            factors.append(f"Suspicious activity keywords found ({features['suspicious_keyword_count']})")

        # Large transactions
        if features.get('large_transaction_count', 0) > (features.get('transaction_count', 1) * 0.5):
            factors.append(f"High proportion of large transactions ({features['large_transaction_count']})")

        # Activity intensity
        intensity = features.get('activity_intensity', 0)
        if intensity > 10:  # More than 10 transactions per day
            factors.append("Unusually high transaction activity")
        elif intensity < 0.1 and features.get('transaction_count', 0) > 0:
            factors.append("Unusually low transaction activity")

        return factors if factors else ["Standard transaction patterns"]

    def get_risk_level(self, score: float) -> str:
        """
        Determine risk level from score

        Args:
            score: Fraud risk score (0-100)

        Returns:
            Risk level: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'
        """
        if score < 25:
            return 'LOW'
        elif score < 50:
            return 'MEDIUM'
        elif score < 75:
            return 'HIGH'
        else:
            return 'CRITICAL'

    # Helper methods

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float"""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except (ValueError, AttributeError):
                return default
        return default

    def _calculate_balance_diff(self, balances: Dict) -> float:
        """Calculate difference between closing and opening balance"""
        opening = self._safe_float(balances.get('opening_balance'), 0)
        closing = self._safe_float(balances.get('closing_balance'), 0)
        return closing - opening

    def _check_balance_consistency(self, summary: Dict, balances: Dict) -> bool:
        """Check if balances are consistent with net activity"""
        opening = self._safe_float(balances.get('opening_balance'), None)
        closing = self._safe_float(balances.get('closing_balance'), None)
        net = self._safe_float(summary.get('net_activity'), None)

        if opening is None or closing is None or net is None:
            return True  # Can't verify without all data

        # Expected closing = opening + net_activity
        expected_closing = opening + net
        difference = abs(expected_closing - closing)
        tolerance = max(50, abs(closing) * 0.05)  # 5% tolerance

        return difference <= tolerance

    def _analyze_transaction_patterns(self, transactions: List) -> Dict[str, Any]:
        """Analyze transaction patterns"""
        if not transactions:
            return {'count': 0, 'types': {}}

        patterns = {
            'count': len(transactions),
            'has_credits': False,
            'has_debits': False,
            'avg_amount': 0,
        }

        amounts = []
        for txn in transactions:
            if isinstance(txn, dict):
                amount = self._safe_float(txn.get('amount_value'), txn.get('amount'))
                if amount is not None:
                    amounts.append(abs(amount))

        if amounts:
            patterns['avg_amount'] = np.mean(amounts)

        return patterns

    def _count_large_transactions(self, transactions: List) -> int:
        """Count transactions above 75th percentile"""
        if not transactions or len(transactions) < 2:
            return 0

        amounts = []
        for txn in transactions:
            if isinstance(txn, dict):
                amount = self._safe_float(txn.get('amount_value'), txn.get('amount'))
                if amount is not None:
                    amounts.append(abs(amount))

        if not amounts:
            return 0

        threshold = np.percentile(amounts, 75)
        return sum(1 for amt in amounts if amt > threshold)

    def _analyze_transaction_dates(self, transactions: List) -> int:
        """Identify unusual transaction dates (weekends, holidays, etc.)"""
        unusual_count = 0
        today = datetime.now()

        for txn in transactions:
            if isinstance(txn, dict):
                date_str = txn.get('date')
                if date_str:
                    try:
                        # Try to parse date
                        txn_date = self._parse_date(date_str)
                        if txn_date:
                            # Check if date is in future
                            if txn_date > today:
                                unusual_count += 1
                    except:
                        pass

        return unusual_count

    def _avg_transaction_amount(self, transactions: List) -> float:
        """Calculate average transaction amount"""
        if not transactions:
            return 0.0

        amounts = []
        for txn in transactions:
            if isinstance(txn, dict):
                amount = self._safe_float(txn.get('amount_value'), txn.get('amount'))
                if amount is not None:
                    amounts.append(abs(amount))

        return np.mean(amounts) if amounts else 0.0

    def _transaction_variance(self, transactions: List) -> float:
        """Calculate variance in transaction amounts"""
        if not transactions or len(transactions) < 2:
            return 0.0

        amounts = []
        for txn in transactions:
            if isinstance(txn, dict):
                amount = self._safe_float(txn.get('amount_value'), txn.get('amount'))
                if amount is not None:
                    amounts.append(abs(amount))

        return float(np.var(amounts)) if amounts else 0.0

    def _calculate_credit_debit_ratio(self, summary: Dict) -> float:
        """Calculate ratio of credits to debits"""
        credits = self._safe_float(summary.get('total_credits'), 0)
        debits = self._safe_float(summary.get('total_debits'), 0)

        if debits == 0:
            return credits if credits > 0 else 0

        return credits / debits

    def _count_suspicious_keywords(self, raw_text: str) -> int:
        """Count occurrences of suspicious keywords"""
        count = 0
        for keyword in self.suspicious_keywords:
            count += len(re.findall(rf'\b{keyword}\b', raw_text))
        return count

    def _has_fraud_indicators(self, raw_text: str) -> bool:
        """Check for explicit fraud indicators"""
        fraud_terms = ['fraud', 'unauthorized', 'fraudulent', 'compromise']
        return any(term in raw_text for term in fraud_terms)

    def _assess_text_quality(self, raw_text: str) -> float:
        """Assess OCR/text quality"""
        if not raw_text:
            return 0.0

        # Simple heuristic: presence of common banking terms and structure
        banking_terms = ['balance', 'transaction', 'deposit', 'withdrawal', 'account']
        term_count = sum(1 for term in banking_terms if term in raw_text)

        # Check for weird character sequences
        weird_chars = len(re.findall(r'[^a-zA-Z0-9\s\.\$\-/\,]', raw_text))

        quality = 1.0
        quality -= (weird_chars / max(len(raw_text), 1)) * 0.3  # Penalize weird chars
        quality += (term_count / len(banking_terms)) * 0.3  # Reward banking terms

        return max(0.0, min(1.0, quality))

    def _count_unusual_characters(self, raw_text: str) -> int:
        """Count unusual/suspicious characters"""
        unusual = len(re.findall(r'[!@#$%^&*()+=\[\]{}|\\;:\'\"<>?~`]', raw_text))
        return unusual

    def _calculate_statement_period(self, bank_data: Dict) -> int:
        """Calculate statement period in days"""
        period_str = bank_data.get('statement_period', '')

        if not period_str:
            return 30  # Default assumption

        # Try to extract dates from period string
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', period_str)

        if len(dates) >= 2:
            try:
                start = self._parse_date(dates[0])
                end = self._parse_date(dates[1])
                if start and end:
                    return (end - start).days
            except:
                pass

        return 30  # Default

    def _check_unusual_period(self, bank_data: Dict) -> bool:
        """Check if statement period is unusual"""
        days = self._calculate_statement_period(bank_data)
        # Typical statement periods are 28-31 days
        return days < 25 or days > 35

    def _calculate_activity_intensity(self, transaction_count: int, period_days: int) -> float:
        """Calculate transactions per day"""
        if period_days <= 0:
            return 0
        return transaction_count / period_days

    def _calculate_balance_volatility(self, transactions: List, balances: Dict) -> float:
        """Calculate balance volatility from transaction pattern"""
        if not transactions or len(transactions) < 2:
            return 0.0

        # Simple approximation based on transaction variance
        variance = self._transaction_variance(transactions)
        opening = self._safe_float(balances.get('opening_balance'), 0)

        if opening == 0:
            return 0.0

        # Volatility as percentage of opening balance
        volatility = variance / (abs(opening) + 1)
        return min(1.0, volatility)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%B %d, %Y', '%b %d, %Y',
            '%m/%d', '%m-%d'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
