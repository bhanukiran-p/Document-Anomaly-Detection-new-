"""
Standardized Bank Statement Schema
Defines the normalized data structure for bank statements across all banks
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class NormalizedBankStatement:
    """
    Standardized bank statement data structure
    All banks normalize to this schema
    """

    # Bank Information
    bank_name: Optional[str] = None              # e.g., 'Bank of America', 'Chase'
    institution_id: Optional[str] = None         # Foreign key to financial_institutes table
    bank_address: Optional[Dict] = None          # {'address': str, 'street': str, 'city': str, 'state': str, 'postal_code': str, 'country': str}

    # Account Information
    account_holder_name: Optional[str] = None     # Primary account holder name
    account_holder_names: Optional[List[str]] = None  # List of all account holders
    account_number: Optional[str] = None          # Account number
    account_type: Optional[str] = None            # Checking, Savings, etc.
    currency: Optional[str] = None                # USD, EUR, etc.

    # Statement Period
    statement_period_start_date: Optional[str] = None  # YYYY-MM-DD format
    statement_period_end_date: Optional[str] = None    # YYYY-MM-DD format
    statement_date: Optional[str] = None               # Date statement was issued (YYYY-MM-DD)

    # Balance Information
    beginning_balance: Optional[Dict] = None      # {'value': float, 'currency': str}
    ending_balance: Optional[Dict] = None        # {'value': float, 'currency': str}
    total_credits: Optional[Dict] = None        # {'value': float, 'currency': str}
    total_debits: Optional[Dict] = None          # {'value': float, 'currency': str}

    # Transactions
    transactions: Optional[List[Dict]] = None    # List of transaction dicts: [{'date': str, 'description': str, 'amount': {'value': float, 'currency': str}}]

    # Additional Fields
    account_holder_address: Optional[Dict] = None  # Account holder address (if available)

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'NormalizedBankStatement':
        """Create instance from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def get_missing_fields(self) -> list:
        """Return list of fields that are None"""
        return [field for field, value in asdict(self).items() if value is None]

    def is_valid(self) -> bool:
        """
        Check if minimum required fields are present
        Required: bank_name, account_number, statement_period_start_date, statement_period_end_date, beginning_balance, ending_balance
        """
        return all([
            self.bank_name is not None,
            self.account_number is not None,
            self.statement_period_start_date is not None,
            self.statement_period_end_date is not None,
            self.beginning_balance is not None,
            self.ending_balance is not None
        ])

    def get_completeness_score(self) -> float:
        """
        Calculate data completeness score (0.0 to 1.0)
        Based on how many fields are populated
        """
        fields = asdict(self)
        total_fields = len(fields)
        populated_fields = sum(1 for v in fields.values() if v is not None)
        return round(populated_fields / total_fields, 2)

    def get_critical_missing_fields(self) -> list:
        """
        Return list of critical fields that are missing
        Critical fields: bank_name, account_number, statement_period dates, balances
        """
        critical_fields = [
            'bank_name',
            'account_number',
            'statement_period_start_date',
            'statement_period_end_date',
            'beginning_balance',
            'ending_balance',
            'account_holder_name'
        ]
        data = asdict(self)
        return [field for field in critical_fields if data.get(field) is None]

    def is_supported_bank(self) -> bool:
        """
        Check if bank is supported (Bank of America, Chase, Wells Fargo, etc.)
        """
        supported_banks = [
            'Bank of America', 'Chase', 'Wells Fargo', 'Citibank',
            'U.S. Bank', 'PNC Bank', 'TD Bank', 'Capital One',
            'BANK OF AMERICA', 'CHASE', 'WELLS FARGO', 'CITIBANK'
        ]
        return self.bank_name in supported_banks if self.bank_name else False

    def get_transaction_count(self) -> int:
        """Get number of transactions"""
        return len(self.transactions) if self.transactions else 0

    def get_total_transaction_amount(self) -> float:
        """Calculate total transaction amount (credits - debits)"""
        if self.total_credits and self.total_debits:
            credits = self.total_credits.get('value', 0) if isinstance(self.total_credits, dict) else 0
            debits = self.total_debits.get('value', 0) if isinstance(self.total_debits, dict) else 0
            return credits - debits
        return 0.0

