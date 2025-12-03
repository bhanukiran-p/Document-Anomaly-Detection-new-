"""
Money Order Analysis Module

Complete modular package for money order extraction, normalization, fraud detection,
and analysis. Organizes all money order-related logic including AI agents, prompts,
and tools.

Submodules:
    - extractor: MoneyOrderExtractor for OCR and field extraction
    - ai: AI analysis components (FraudAnalysisAgent, prompts, tools)
    - normalizer: Data normalization for different money order types
"""

from .extractor import MoneyOrderExtractor
from .ai import FraudAnalysisAgent, ResultStorage, DataAccessTools

__all__ = [
    'MoneyOrderExtractor',
    'FraudAnalysisAgent',
    'ResultStorage',
    'DataAccessTools',
]
