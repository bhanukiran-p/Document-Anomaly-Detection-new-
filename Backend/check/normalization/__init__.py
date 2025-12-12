<<<<<<< Updated upstream
"""Check Normalization Module"""
=======
"""
Check Normalization Module
Contains normalizers and factory for check banks
"""

from .check_normalizer_factory import CheckNormalizerFactory
from .check_base_normalizer import CheckBaseNormalizer
from .check_schema import NormalizedCheck
from .bank_of_america import BankOfAmericaNormalizer
from .chase import ChaseNormalizer

__all__ = [
    'CheckNormalizerFactory',
    'CheckBaseNormalizer',
    'NormalizedCheck',
    'BankOfAmericaNormalizer',
    'ChaseNormalizer'
]

>>>>>>> Stashed changes
