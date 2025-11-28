"""
Real-Time Transaction Analysis Module
Handles CSV transaction processing, fraud detection, insights generation, and AI-powered analysis
"""

from .csv_processor import process_transaction_csv
from .fraud_detector import detect_fraud_in_transactions
from .model_trainer import train_fraud_model, auto_train_model
from .insights_generator import generate_insights
from .agent_endpoint import get_agent_service, AgentAnalysisService

__all__ = [
    'process_transaction_csv',
    'detect_fraud_in_transactions',
    'train_fraud_model',
    'auto_train_model',
    'generate_insights',
    'get_agent_service',
    'AgentAnalysisService'
]
