"""
Field Normalization Module
Standardizes money order data from different issuers into a unified schema
"""

from .schema import NormalizedMoneyOrder
from .normalizer_factory import NormalizerFactory
from .base_normalizer import BaseNormalizer

__all__ = [
    'NormalizedMoneyOrder',
    'NormalizerFactory',
    'BaseNormalizer'
]
