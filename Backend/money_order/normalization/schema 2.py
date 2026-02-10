"""
Standardized Money Order Schema
Defines the normalized data structure for money orders across all issuers
"""

from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class NormalizedMoneyOrder:
    """
    Standardized money order data structure
    All issuers (Western Union, MoneyGram, USPS, etc.) normalize to this schema
    """

    # Issuer Information
    issuer_name: Optional[str] = None          # e.g., 'Western Union', 'MoneyGram'

    # Identification Numbers
    serial_primary: Optional[str] = None       # Primary serial/tracking number
    serial_secondary: Optional[str] = None     # Secondary control number (if applicable)

    # Party Information
    recipient: Optional[str] = None            # Payee/recipient name
    sender_name: Optional[str] = None          # Sender/purchaser/remitter name
    sender_address: Optional[str] = None       # Sender's address

    # Monetary Information
    amount_numeric: Optional[Dict] = None      # {'value': 750.00, 'currency': 'USD'}
    amount_written: Optional[str] = None       # 'SEVEN HUNDRED FIFTY AND 00/100 DOLLARS'

    # Temporal Information
    date: Optional[str] = None                 # MM-DD-YYYY format

    # Authorization
    signature: Optional[str] = None            # Signature or authorization stamp

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'NormalizedMoneyOrder':
        """Create instance from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def get_missing_fields(self) -> list:
        """Return list of fields that are None"""
        return [field for field, value in asdict(self).items() if value is None]

    def is_valid(self) -> bool:
        """
        Check if minimum required fields are present
        Required: issuer_name, serial_primary, amount_numeric
        """
        return all([
            self.issuer_name is not None,
            self.serial_primary is not None,
            self.amount_numeric is not None
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
