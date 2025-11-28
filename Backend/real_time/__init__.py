"""
Real-Time Transaction Analysis Module
Handles CSV transaction processing, fraud detection, and insights generation
"""

from .csv_processor import process_transaction_csv
from .fraud_detector import detect_fraud_in_transactions
from .model_trainer import train_fraud_model, auto_train_model
from .insights_generator import generate_insights

__all__ = [
    'process_transaction_csv',
    'detect_fraud_in_transactions',
    'train_fraud_model',
    'auto_train_model',
    'generate_insights'
]
