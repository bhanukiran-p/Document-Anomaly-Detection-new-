"""
Base check normalization classes.
Provides standardized structure for check data.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import re


class NormalizedCheck:
    """
    Standardized check data structure.
    All normalizers should produce this format.
    """

    def __init__(self):
        # Bank information
        self.bank_name: Optional[str] = None
        self.routing_number: Optional[str] = None
        self.account_number: Optional[str] = None

        # Check details
        self.check_number: Optional[str] = None
        self.check_date: Optional[str] = None
        self.check_type: Optional[str] = None

        # Amount information
        self.amount_numeric: Optional[float] = None
        self.amount_words: Optional[str] = None
        self.currency: Optional[str] = "USD"

        # Parties
        self.payee_name: Optional[str] = None
        self.payer_name: Optional[str] = None
        self.payer_address: Optional[str] = None

        # Additional fields
        self.memo: Optional[str] = None
        self.signature_detected: Optional[bool] = None

        # Validation flags
        self.amount_match: Optional[bool] = None
        self.date_valid: Optional[bool] = None
        self.fields_complete: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "bank_name": self.bank_name,
            "routing_number": self.routing_number,
            "account_number": self.account_number,
            "check_number": self.check_number,
            "check_date": self.check_date,
            "check_type": self.check_type,
            "amount_numeric": self.amount_numeric,
            "amount_words": self.amount_words,
            "currency": self.currency,
            "payee_name": self.payee_name,
            "payer_name": self.payer_name,
            "payer_address": self.payer_address,
            "memo": self.memo,
            "signature_detected": self.signature_detected,
            "amount_match": self.amount_match,
            "date_valid": self.date_valid,
            "fields_complete": self.fields_complete,
        }

    def get_completeness_score(self) -> float:
        """
        Calculate completeness score (0.0 to 1.0).
        Based on how many critical fields are populated.
        """
        critical_fields = [
            self.bank_name,
            self.check_number,
            self.check_date,
            self.amount_numeric,
            self.payee_name,
            self.routing_number,
            self.account_number,
        ]

        filled = sum(1 for field in critical_fields if field is not None)
        return filled / len(critical_fields)

    def get_fraud_indicators(self) -> List[str]:
        """
        Return list of potential fraud indicators based on normalization.
        """
        indicators = []

        # Amount mismatch
        if self.amount_match is False:
            indicators.append("Amount mismatch: numeric and written amounts do not match")

        # Date validation
        if self.date_valid is False:
            indicators.append("Invalid or future date detected")
        elif self.check_date:
            try:
                check_date = datetime.strptime(self.check_date, "%Y-%m-%d")
                days_old = (datetime.now() - check_date).days
                if days_old > 180:
                    indicators.append(f"Check is {days_old} days old (stale check)")
                elif days_old < 0:
                    indicators.append("Check date is in the future")
            except (ValueError, TypeError):
                pass

        # Missing critical fields
        if not self.signature_detected:
            indicators.append("No signature detected")

        if not self.payee_name:
            indicators.append("Missing payee name")

        if not self.amount_numeric:
            indicators.append("Missing check amount")

        if not self.check_number:
            indicators.append("Missing check number")

        # Suspicious amounts
        if self.amount_numeric:
            if self.amount_numeric > 50000:
                indicators.append(f"Unusually high amount: ${self.amount_numeric:,.2f}")
            elif self.amount_numeric < 1:
                indicators.append(f"Suspiciously low amount: ${self.amount_numeric:,.2f}")

        # Routing/account number validation
        if self.routing_number and len(str(self.routing_number)) != 9:
            indicators.append("Invalid routing number format")

        return indicators


class BaseCheckNormalizer:
    """
    Base class for check normalizers.
    Subclasses can implement bank-specific normalization logic.
    """

    def __init__(self, bank_name: Optional[str] = None):
        self.bank_name = bank_name

    def normalize(self, extracted_data: Dict[str, Any]) -> NormalizedCheck:
        """
        Normalize extracted check data into standardized format.

        Args:
            extracted_data: Raw extracted data from Mindee or other OCR

        Returns:
            NormalizedCheck object with standardized data
        """
        normalized = NormalizedCheck()

        # Bank information
        normalized.bank_name = self._normalize_bank_name(extracted_data)
        normalized.routing_number = self._normalize_routing_number(extracted_data)
        normalized.account_number = self._normalize_account_number(extracted_data)

        # Check details
        normalized.check_number = self._normalize_check_number(extracted_data)
        normalized.check_date = self._normalize_date(extracted_data)
        normalized.check_type = extracted_data.get("check_type")

        # Amount
        normalized.amount_numeric = self._normalize_amount_numeric(extracted_data)
        normalized.amount_words = self._normalize_amount_words(extracted_data)
        normalized.currency = extracted_data.get("currency") or "USD"

        # Parties
        normalized.payee_name = self._normalize_payee(extracted_data)
        normalized.payer_name = self._normalize_payer(extracted_data)
        normalized.payer_address = extracted_data.get("payer_address")

        # Additional
        normalized.memo = extracted_data.get("memo")
        normalized.signature_detected = self._normalize_signature(extracted_data)

        # Validation
        normalized.amount_match = self._validate_amount_match(normalized)
        normalized.date_valid = self._validate_date(normalized)
        normalized.fields_complete = normalized.get_completeness_score() >= 0.7

        return normalized

    def _normalize_bank_name(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize bank name."""
        return data.get("bank_name")

    def _normalize_routing_number(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize routing number."""
        routing = data.get("routing_number")
        if routing:
            # Remove any non-digit characters
            routing = re.sub(r'\D', '', str(routing))
        return routing

    def _normalize_account_number(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize account number."""
        account = data.get("account_number")
        if account:
            # Remove any non-digit characters
            account = re.sub(r'\D', '', str(account))
        return account

    def _normalize_check_number(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize check number."""
        return data.get("check_number")

    def _normalize_date(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize date to YYYY-MM-DD format."""
        date_value = data.get("date") or data.get("check_date")
        if not date_value:
            return None

        # If already in ISO format
        if isinstance(date_value, str) and re.match(r'\d{4}-\d{2}-\d{2}', date_value):
            return date_value

        # Try to parse common date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y%m%d",
        ]

        for fmt in date_formats:
            try:
                parsed = datetime.strptime(str(date_value), fmt)
                return parsed.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue

        return str(date_value)

    def _normalize_amount_numeric(self, data: Dict[str, Any]) -> Optional[float]:
        """Extract and normalize numeric amount."""
        amount = data.get("amount_numeric")
        if amount is not None:
            try:
                return float(amount)
            except (ValueError, TypeError):
                pass

        # Try to extract from formatted amount
        amount_str = data.get("amount")
        if amount_str:
            # Remove currency symbols and commas
            clean = re.sub(r'[^\d.]', '', str(amount_str))
            if clean:
                try:
                    return float(clean)
                except ValueError:
                    pass

        return None

    def _normalize_amount_words(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize written amount."""
        return data.get("amount_words") or data.get("amount_in_words")

    def _normalize_payee(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize payee name."""
        return data.get("payee_name") or data.get("payee") or data.get("pay_to")

    def _normalize_payer(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize payer name."""
        return data.get("payer_name") or data.get("purchaser")

    def _normalize_signature(self, data: Dict[str, Any]) -> Optional[bool]:
        """Extract and normalize signature detection."""
        sig = data.get("signature_detected") or data.get("signature")
        if sig is None:
            return None
        return bool(sig)

    def _validate_amount_match(self, normalized: NormalizedCheck) -> Optional[bool]:
        """
        Validate that numeric and written amounts match.
        Returns None if comparison cannot be made.
        """
        if not normalized.amount_numeric or not normalized.amount_words:
            return None

        # Simple word-to-number conversion for validation
        # This is a basic implementation - can be enhanced
        words_lower = normalized.amount_words.lower()
        numeric_val = normalized.amount_numeric

        # Extract whole dollar amount
        whole_dollars = int(numeric_val)

        # Check if the number appears in the written amount
        if str(whole_dollars) in words_lower or self._number_to_words(whole_dollars).lower() in words_lower:
            return True

        # If we can't validate, return None rather than False
        return None

    def _validate_date(self, normalized: NormalizedCheck) -> Optional[bool]:
        """
        Validate that the date is reasonable.
        Returns None if validation cannot be performed.
        """
        if not normalized.check_date:
            return None

        try:
            check_date = datetime.strptime(normalized.check_date, "%Y-%m-%d")
            today = datetime.now()

            # Check is not in the future
            if check_date > today:
                return False

            # Check is not too old (e.g., more than 5 years)
            days_old = (today - check_date).days
            if days_old > 1825:  # 5 years
                return False

            return True
        except (ValueError, TypeError):
            return None

    def _number_to_words(self, n: int) -> str:
        """
        Convert number to words (basic implementation).
        For more accurate validation, use a library like num2words.
        """
        if n == 0:
            return "zero"

        # Basic conversion for common amounts
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]

        if n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
        elif n < 1000:
            return ones[n // 100] + " hundred" + (" " + self._number_to_words(n % 100) if n % 100 != 0 else "")
        elif n < 1000000:
            return self._number_to_words(n // 1000) + " thousand" + (" " + self._number_to_words(n % 1000) if n % 1000 != 0 else "")

        return str(n)
