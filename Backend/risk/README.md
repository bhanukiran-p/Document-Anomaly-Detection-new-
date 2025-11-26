# Risk Scoring Module

This folder contains ML-based risk scoring and fraud detection rule engines.

## Files

- `ml_risk_scorer.py` - ML-based risk scoring using trained RandomForest models
- `enhanced_fraud_rules.py` - Enhanced fraud detection rules engine
- `enhanced_fraud_rules_example.py` - Example usage of fraud rules

## ML Risk Scorer

The ML Risk Scorer uses trained machine learning models to assess document risk:
- Loads trained models from `models/` directory
- Supports check and paystub document types
- Falls back to weighted rule-based scoring when ML model not available
- Returns risk scores (0-100) with risk factors and recommendations

## Fraud Rules

The Enhanced Fraud Rules engine provides:
- Rule-based fraud detection
- Configurable risk thresholds
- Multiple fraud indicators
- Severity-based risk factors
