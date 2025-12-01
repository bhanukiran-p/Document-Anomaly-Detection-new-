"""
Bank Statement Fraud Detection ML Model
Ensemble model (Random Forest + XGBoost) for bank statement fraud detection
Completely independent from other document type fraud detection
"""

import os
import logging
from typing import Dict, List, Optional
import numpy as np
from .bank_statement_feature_extractor import BankStatementFeatureExtractor

logger = logging.getLogger(__name__)


class BankStatementFraudDetector:
    """
    ML-based fraud detector for bank statements
    Uses ensemble of Random Forest and XGBoost models
    """

    def __init__(self, model_dir: str = 'ml_models'):
        """
        Initialize bank statement fraud detector

        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir
        self.feature_extractor = BankStatementFeatureExtractor()
        self.models_loaded = False

        # Model paths - use bank_statement/ml/ directory for bank statement-specific models
        ml_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(ml_dir, exist_ok=True)
        self.rf_model_path = os.path.join(ml_dir, 'bank_statement_random_forest.pkl')
        self.xgb_model_path = os.path.join(ml_dir, 'bank_statement_xgboost.pkl')
        self.scaler_path = os.path.join(ml_dir, 'bank_statement_feature_scaler.pkl')
        
        # Fallback to global ml_models directory if bank statement-specific models don't exist
        if not os.path.exists(self.rf_model_path):
            fallback_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml_models')
            self.rf_model_path = os.path.join(fallback_dir, 'bank_statement_random_forest.pkl')
            self.xgb_model_path = os.path.join(fallback_dir, 'bank_statement_xgboost.pkl')
            self.scaler_path = os.path.join(fallback_dir, 'bank_statement_feature_scaler.pkl')

        # Load models
        self._load_models()

    def _load_models(self):
        """Load trained models from disk"""
        try:
            # Try to load pre-trained models
            import joblib

            if os.path.exists(self.rf_model_path):
                self.rf_model = joblib.load(self.rf_model_path)
                logger.info("Loaded Random Forest model for bank statements")
            else:
                logger.warning("Random Forest model not found, using mock scoring")
                self.rf_model = None

            if os.path.exists(self.xgb_model_path):
                self.xgb_model = joblib.load(self.xgb_model_path)
                logger.info("Loaded XGBoost model for bank statements")
            else:
                logger.warning("XGBoost model not found, using mock scoring")
                self.xgb_model = None

            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded feature scaler for bank statements")
            else:
                logger.warning("Feature scaler not found")
                self.scaler = None

            self.models_loaded = (self.rf_model is not None or self.xgb_model is not None)

        except ImportError:
            logger.warning("joblib not available, using mock scoring")
            self.rf_model = None
            self.xgb_model = None
            self.scaler = None
            self.models_loaded = False
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.rf_model = None
            self.xgb_model = None
            self.scaler = None
            self.models_loaded = False

    def predict_fraud(self, bank_statement_data: Dict, raw_text: str = "") -> Dict:
        """
        Predict fraud likelihood for a bank statement

        Args:
            bank_statement_data: Extracted bank statement data (from Mindee or normalized)
            raw_text: Raw OCR text (optional)

        Returns:
            Dictionary containing:
                - fraud_risk_score: Float 0.0-1.0
                - risk_level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
                - model_confidence: Float 0.0-1.0
                - model_scores: Dict with individual model scores
                - feature_importance: List of important features
                - anomalies: List of detected anomalies
        """
        # Extract features
        features = self.feature_extractor.extract_features(bank_statement_data, raw_text)
        feature_names = self.feature_extractor.get_feature_names()

        logger.info(f"Extracted {len(features)} features for bank statement fraud detection")

        # If models are loaded, use them
        if self.models_loaded:
            return self._predict_with_models(features, feature_names, bank_statement_data)
        else:
            # Use mock/heuristic scoring
            return self._predict_mock(features, feature_names, bank_statement_data)

    def _predict_with_models(self, features: List[float], feature_names: List[str], bank_statement_data: Dict) -> Dict:
        """Predict using trained models"""
        try:
            # Convert to numpy array
            X = np.array([features])

            # Scale features if scaler available
            if self.scaler:
                X = self.scaler.transform(X)

            # Get predictions from each model
            rf_score = 0.0
            xgb_score = 0.0

            if self.rf_model:
                rf_proba = self.rf_model.predict_proba(X)[0]
                rf_score = rf_proba[1] if len(rf_proba) > 1 else rf_proba[0]

            if self.xgb_model:
                xgb_proba = self.xgb_model.predict_proba(X)[0]
                xgb_score = xgb_proba[1] if len(xgb_proba) > 1 else xgb_proba[0]

            # Ensemble prediction (40% RF, 60% XGB)
            ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)

            # Apply strict validation rules
            adjusted_score = self._apply_validation_rules(ensemble_score, bank_statement_data, features)

            # Get feature importance
            feature_importance = self._get_feature_importance(features, feature_names)

            # Determine risk level
            risk_level = self._determine_risk_level(adjusted_score)

            # Generate anomalies
            anomalies = self._generate_anomalies(bank_statement_data, features, feature_names, adjusted_score)

            return {
                'fraud_risk_score': round(adjusted_score, 4),
                'risk_level': risk_level,
                'model_confidence': round(max(rf_score, xgb_score), 4),
                'model_scores': {
                    'random_forest': round(rf_score, 4),
                    'xgboost': round(xgb_score, 4),
                    'ensemble': round(ensemble_score, 4),
                    'adjusted': round(adjusted_score, 4)
                },
                'feature_importance': feature_importance,
                'anomalies': anomalies
            }

        except Exception as e:
            logger.error(f"Error in model prediction: {e}")
            return self._predict_mock(features, feature_names, bank_statement_data)

    def _predict_mock(self, features: List[float], feature_names: List[str], bank_statement_data: Dict) -> Dict:
        """Mock/heuristic-based fraud detection when models aren't available"""
        logger.info("Using mock fraud detection for bank statements")

        # Calculate base score from features
        base_score = 0.0
        risk_factors = []

        # Critical checks
        bank_valid = features[0]  # Feature 1: bank_validity
        account_present = features[1]  # Feature 2: account_number_present
        account_holder_present = features[2]  # Feature 3: account_holder_present
        future_period = features[11]  # Feature 12: future_period
        negative_balance = features[17]  # Feature 18: negative_ending_balance
        balance_consistency = features[18]  # Feature 19: balance_consistency
        critical_missing = features[25]  # Feature 26: critical_missing_count
        duplicate_txns = features[28]  # Feature 29: duplicate_transactions

        # Unsupported bank
        if bank_valid == 0.0:
            base_score += 0.50
            risk_factors.append("Unsupported bank detected")

        # Missing account number
        if account_present == 0.0:
            base_score += 0.30
            risk_factors.append("Missing account number")

        # Missing account holder
        if account_holder_present == 0.0:
            base_score += 0.30
            risk_factors.append("Missing account holder name")

        # Future period
        if future_period == 1.0:
            base_score += 0.40
            risk_factors.append("Statement period is in the future")

        # Negative balance
        if negative_balance == 1.0:
            base_score += 0.35
            risk_factors.append("Negative ending balance detected")

        # Balance inconsistency
        if balance_consistency < 0.5:
            base_score += 0.40
            risk_factors.append("Balance inconsistency detected")

        # Critical missing fields
        if critical_missing >= 3:
            base_score += 0.40
            risk_factors.append(f"{int(critical_missing)} critical fields missing")

        # Duplicate transactions
        if duplicate_txns == 1.0:
            base_score += 0.30
            risk_factors.append("Duplicate transactions detected")

        # Balance checks
        ending_balance = features[5]  # Feature 6: ending_balance
        if ending_balance < 0:
            base_score += 0.25
            risk_factors.append(f"Negative balance: ${ending_balance:,.2f}")

        # Transaction count
        txn_count = features[13]  # Feature 14: transaction_count
        if txn_count == 0:
            base_score += 0.30
            risk_factors.append("No transactions found in statement")

        # Cap score at 1.0
        fraud_score = min(base_score, 1.0)

        # Determine risk level
        risk_level = self._determine_risk_level(fraud_score)

        # Feature importance (mock)
        feature_importance = self._get_feature_importance(features, feature_names)

        return {
            'fraud_risk_score': round(fraud_score, 4),
            'risk_level': risk_level,
            'model_confidence': 0.75,  # Mock confidence
            'model_scores': {
                'random_forest': round(fraud_score * 0.9, 4),
                'xgboost': round(fraud_score * 1.1, 4),
                'ensemble': round(fraud_score, 4),
                'adjusted': round(fraud_score, 4)
            },
            'feature_importance': feature_importance[:10],  # Top 10
            'anomalies': risk_factors
        }

    def _apply_validation_rules(self, base_score: float, bank_statement_data: Dict, features: List[float]) -> float:
        """Apply strict validation rules and adjust score"""
        adjusted_score = base_score

        # Extract key data points
        bank_valid = features[0]
        future_period = features[11]
        negative_balance = features[17]
        balance_consistency = features[18]
        critical_missing = features[25]

        # Strict rules
        if bank_valid == 0.0:  # Unsupported bank
            adjusted_score = max(adjusted_score, 0.50)

        if future_period == 1.0:  # Future period
            adjusted_score += 0.40

        if negative_balance == 1.0:  # Negative balance
            adjusted_score += 0.35

        if balance_consistency < 0.5:  # Balance inconsistency
            adjusted_score += 0.40

        if critical_missing >= 4:  # Too many missing fields
            adjusted_score += 0.30

        # Cap at 1.0
        return min(adjusted_score, 1.0)

    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from score"""
        if score < 0.30:
            return 'LOW'
        elif score < 0.60:
            return 'MEDIUM'
        elif score < 0.85:
            return 'HIGH'
        else:
            return 'CRITICAL'

    def _get_feature_importance(self, features: List[float], feature_names: List[str]) -> List[str]:
        """Get top important features contributing to the score"""
        importance = []

        # Map features to descriptions
        for i, (value, name) in enumerate(zip(features, feature_names)):
            if value > 0.5 or (i in [11, 17, 18, 25, 28] and value > 0):  # Highlight important features
                if name == 'bank_validity' and value == 0.0:
                    importance.append("Unsupported bank")
                elif name == 'future_period' and value == 1.0:
                    importance.append("Future statement period")
                elif name == 'negative_ending_balance' and value == 1.0:
                    importance.append("Negative ending balance")
                elif name == 'balance_consistency' and value < 0.5:
                    importance.append("Balance inconsistency")
                elif name == 'critical_missing_count' and value >= 3:
                    importance.append(f"{int(value)} critical fields missing")
                elif name == 'duplicate_transactions' and value == 1.0:
                    importance.append("Duplicate transactions detected")

        return importance if importance else ["No significant risk factors"]

    def _generate_anomalies(self, bank_statement_data: Dict, features: List[float],
                          feature_names: List[str], score: float) -> List[str]:
        """Generate list of anomalies detected"""
        anomalies = []

        # Use feature importance as anomalies
        feature_importance = self._get_feature_importance(features, feature_names)
        anomalies.extend(feature_importance)

        # Additional checks
        ending_balance = features[5]
        if ending_balance < 0:
            anomalies.append(f"Negative ending balance: ${ending_balance:,.2f}")

        if score >= 0.85:
            anomalies.append("CRITICAL fraud risk detected")
        elif score >= 0.60:
            anomalies.append("HIGH fraud risk detected")

        return anomalies if anomalies else []

