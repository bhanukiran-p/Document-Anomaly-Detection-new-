"""
Risk scoring and fraud detection rules module
"""
try:
    from .ml_risk_scorer import MLRiskScorer
    ML_RISK_SCORER_AVAILABLE = True
except ImportError:
    ML_RISK_SCORER_AVAILABLE = False
    MLRiskScorer = None

try:
    from .enhanced_fraud_rules import EnhancedFraudRules
    FRAUD_RULES_AVAILABLE = True
except ImportError:
    FRAUD_RULES_AVAILABLE = False
    EnhancedFraudRules = None

__all__ = [
    'MLRiskScorer',
    'EnhancedFraudRules',
    'ML_RISK_SCORER_AVAILABLE',
    'FRAUD_RULES_AVAILABLE'
]
