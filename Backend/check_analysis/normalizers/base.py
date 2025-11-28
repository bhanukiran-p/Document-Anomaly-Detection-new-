"""
Base Check Normalizer
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseCheckNormalizer(ABC):
    """
    Abstract base class for check normalizers
    """

    def __init__(self, issuer: str):
        self.issuer = issuer

    @abstractmethod
    def normalize(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize extracted data into standard schema
        """
        pass

    def _standardize_amount(self, amount_str: Any) -> float:
        if not amount_str:
            return 0.0
        if isinstance(amount_str, (int, float)):
            return float(amount_str)
        try:
            return float(str(amount_str).replace(',', '').replace('$', ''))
        except:
            return 0.0
