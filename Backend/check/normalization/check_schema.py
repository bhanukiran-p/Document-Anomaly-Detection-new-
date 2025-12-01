"""
Standardized Check Schema
Defines the normalized data structure for checks across all banks
"""

from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class NormalizedCheck:
    """
    Standardized check data structure
    All banks (Bank of America, Chase, etc.) normalize to this schema
    """

    # Bank Information
    bank_name: Optional[str] = None              # e.g., 'Bank of America', 'Chase'
    institution_id: Optional[str] = None         # Foreign key to financial_institutes table
    routing_number: Optional[str] = None         # 9-digit routing number
    account_number: Optional[str] = None         # Account number

    # Check Identification
    check_number: Optional[str] = None           # Check number
    check_date: Optional[str] = None             # Check date (MM-DD-YYYY format)

    # Payer Information (Person writing the check)
    payer_name: Optional[str] = None             # Payer name
    payer_address: Optional[str] = None          # Payer street address
    payer_city: Optional[str] = None             # Payer city
    payer_state: Optional[str] = None            # Payer state
    payer_zip: Optional[str] = None              # Payer ZIP code

    # Payee Information (Person receiving the check)
    payee_name: Optional[str] = None             # Payee/recipient name
    payee_address: Optional[str] = None          # Payee street address
    payee_city: Optional[str] = None             # Payee city
    payee_state: Optional[str] = None            # Payee state
    payee_zip: Optional[str] = None              # Payee ZIP code

    # Monetary Information
    amount_numeric: Optional[Dict] = None        # {'value': 1500.00, 'currency': 'USD'}
    amount_written: Optional[str] = None         # 'One thousand five hundred and 00/100'

    # Authorization & Validation
    signature_detected: Optional[bool] = None    # True if signature present
    memo: Optional[str] = None                   # Memo field content

    # Additional Fields
    check_type: Optional[str] = None             # Personal, Business, Cashier's, etc.
    country: Optional[str] = None                # Country (usually 'US')
    currency: Optional[str] = None               # Currency code (usually 'USD')

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'NormalizedCheck':
        """Create instance from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def get_missing_fields(self) -> list:
        """Return list of fields that are None"""
        return [field for field, value in asdict(self).items() if value is None]

    def is_valid(self) -> bool:
        """
        Check if minimum required fields are present
        Required: bank_name, check_number, amount_numeric, payer_name, payee_name
        """
        return all([
            self.bank_name is not None,
            self.check_number is not None,
            self.amount_numeric is not None,
            self.payer_name is not None,
            self.payee_name is not None
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
        Critical fields: bank_name, check_number, amount_numeric, payer_name, payee_name, signature_detected
        """
        critical_fields = [
            'bank_name',
            'check_number',
            'amount_numeric',
            'payer_name',
            'payee_name',
            'check_date',
            'signature_detected'
        ]
        data = asdict(self)
        return [field for field in critical_fields if data.get(field) is None]

    def is_supported_bank(self) -> bool:
        """
        Check if bank is supported (Bank of America or Chase)
        """
        supported_banks = ['Bank of America', 'Chase', 'BANK OF AMERICA', 'CHASE']
        return self.bank_name in supported_banks if self.bank_name else False
