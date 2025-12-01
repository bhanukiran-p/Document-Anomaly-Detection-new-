"""
Paystub Schema
Defines the normalized data structure for paystubs
Completely independent from money order schema
"""

from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class NormalizedPaystub:
    """
    Standardized paystub data structure
    All paystubs normalize to this schema
    """

    # Company Information
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    
    # Employee Information
    employee_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_address: Optional[str] = None
    
    # Pay Period Information
    pay_date: Optional[str] = None
    pay_period_start: Optional[str] = None
    pay_period_end: Optional[str] = None
    
    # Earnings
    gross_pay: Optional[float] = None
    net_pay: Optional[float] = None
    regular_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    
    # Year-to-Date (YTD)
    ytd_gross: Optional[float] = None
    ytd_net: Optional[float] = None
    
    # Deductions
    federal_tax: Optional[float] = None
    state_tax: Optional[float] = None
    social_security: Optional[float] = None
    medicare: Optional[float] = None
    other_deductions: Optional[float] = None
    
    # Additional Information
    document_type: str = "PAYSTUB"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NormalizedPaystub':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

