"""
Mock Bank API Module
Provides mock bank functionality for testing without external dependencies
"""

from .synthetic_data_generator import (
    generate_synthetic_customers,
    generate_synthetic_accounts,
    generate_synthetic_transactions,
    generate_all_synthetic_data
)
from .bank_client import BankAPIClient

__all__ = [
    'generate_synthetic_customers',
    'generate_synthetic_accounts',
    'generate_synthetic_transactions',
    'generate_all_synthetic_data',
    'BankAPIClient'
]
