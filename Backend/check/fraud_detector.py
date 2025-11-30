"""
Check Fraud Detection Wrapper
Routes check fraud detection to the correct CheckFraudDetector from ml_models
"""

from ml_models.check_fraud_detector import CheckFraudDetector
from typing import Dict, Any


class CheckFraudDetectorWrapper(CheckFraudDetector):
    """
    Wrapper for CheckFraudDetector that inherits all functionality
    from the ML-based check fraud detector.

    This allows check/extractor.py to import from check.fraud_detector
    instead of ml_models.fraud_detector, ensuring checks use the
    correct detector (check-specific models) rather than the
    money order detector.
    """
    pass
