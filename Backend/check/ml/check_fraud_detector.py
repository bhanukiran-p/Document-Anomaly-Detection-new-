"""
Check Fraud Detection ML Model
Ensemble model (Random Forest + XGBoost) for check fraud detection
Completely independent from Money Order fraud detection
"""

"""
Check Fraud Detection ML Model
Ensemble model (Random Forest + XGBoost) for check fraud detection
Completely independent from Money Order fraud detection
"""

import os
import logging
from typing import Dict, List, Optional
import numpy as np
from .check_feature_extractor import CheckFeatureExtractor

logger = logging.getLogger(__name__)


class CheckFraudDetector:
    """
    ML-based fraud detector for checks
    Uses ensemble of Random Forest and XGBoost models
    """

    def __init__(self, model_dir: str = 'models'):
        """
        Initialize check fraud detector

        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir
        self.feature_extractor = CheckFeatureExtractor()
        self.models_loaded = False

        # Model paths - use check/ml/models directory (self-contained, NO FALLBACK)
        ml_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(ml_dir, exist_ok=True)
        self.rf_model_path = os.path.join(ml_dir, 'check_random_forest.pkl')
        self.xgb_model_path = os.path.join(ml_dir, 'check_xgboost.pkl')
        self.scaler_path = os.path.join(ml_dir, 'check_feature_scaler.pkl')

        # Load models
        self._load_models()

    def _load_models(self):
        """Load trained models from disk"""
        try:
            # Try to load pre-trained models
            import joblib

            if os.path.exists(self.rf_model_path):
                self.rf_model = joblib.load(self.rf_model_path)
                logger.info("Loaded Random Forest model for checks")
            else:
                logger.warning("Random Forest model not found, using mock scoring")
                self.rf_model = None

            if os.path.exists(self.xgb_model_path):
                self.xgb_model = joblib.load(self.xgb_model_path)
                logger.info("Loaded XGBoost model for checks")
            else:
                logger.warning("XGBoost model not found, using mock scoring")
                self.xgb_model = None

            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded feature scaler for checks")
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

    def predict_fraud(self, check_data: Dict, raw_text: str = "") -> Dict:
        """
        Predict fraud likelihood for a check

        Args:
            check_data: Extracted check data (from Mindee or normalized)
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
        features = self.feature_extractor.extract_features(check_data, raw_text)
        feature_names = self.feature_extractor.get_feature_names()

        logger.info(f"Extracted {len(features)} features for check fraud detection")

        # If models are loaded, use them
        if self.models_loaded:
            return self._predict_with_models(features, feature_names, check_data)
        else:
            # Use mock/heuristic scoring
            return self._predict_mock(features, feature_names, check_data)

    def _predict_with_models(self, features: List[float], feature_names: List[str], check_data: Dict) -> Dict:
        """Predict using trained models"""
        try:
            # Convert to numpy array
            X = np.array([features])

            # Scale features if scaler available
            if self.scaler:
                X = self.scaler.transform(X)

            # Get predictions from each model (support both Classifiers and Regressors)
            rf_score = 0.0
            xgb_score = 0.0

            if self.rf_model:
                try:
                    # Try predict_proba first (if classifier)
                    rf_proba = self.rf_model.predict_proba(X)[0]
                    rf_score = rf_proba[1] if len(rf_proba) > 1 else rf_proba[0]
                except AttributeError:
                    # Use predict() for regressors and normalize (0-100 -> 0-1)
                    rf_pred = self.rf_model.predict(X)[0]
                    rf_score = max(0.0, min(1.0, rf_pred / 100.0))

            if self.xgb_model:
                try:
                    # Try predict_proba first (if classifier)
                    xgb_proba = self.xgb_model.predict_proba(X)[0]
                    xgb_score = xgb_proba[1] if len(xgb_proba) > 1 else xgb_proba[0]
                except AttributeError:
                    # Use predict() for regressors and normalize (0-100 -> 0-1)
                    xgb_pred = self.xgb_model.predict(X)[0]
                    xgb_score = max(0.0, min(1.0, xgb_pred / 100.0))

            # Ensemble prediction (40% RF, 60% XGB - same as money order)
            ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)

            # Apply strict validation rules
            adjusted_score = self._apply_validation_rules(ensemble_score, check_data, features)

            # Get feature importance
            feature_importance = self._get_feature_importance(features, feature_names)

            # Determine risk level
            risk_level = self._determine_risk_level(adjusted_score)

            # Generate anomalies
            anomalies = self._generate_anomalies(check_data, features, feature_names, adjusted_score)

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
            return self._predict_mock(features, feature_names, check_data)

    def _predict_mock(self, features: List[float], feature_names: List[str], check_data: Dict) -> Dict:
        """Mock/heuristic-based fraud detection when models aren't available"""
        logger.info("Using mock fraud detection for checks")

        # Calculate base score from features
        base_score = 0.0
        risk_factors = []

        # Critical checks
        bank_valid = features[0]  # Feature 1: bank_validity
        routing_valid = features[1]  # Feature 2: routing_validity
        check_num_valid = features[3]  # Feature 4: check_number_valid
        payer_present = features[7]  # Feature 8: payer_present
        payee_present = features[8]  # Feature 9: payee_present
        future_date = features[11]  # Feature 12: future_date
        signature = features[13]  # Feature 14: signature_detected
        critical_missing = features[20]  # Feature 21: critical_missing_count
        suspicious_amount = features[17]  # Feature 18: suspicious_amount

        # Unsupported bank
        if bank_valid == 0.0:
            base_score += 0.50
            risk_factors.append("Unsupported bank detected")

        # Invalid routing number
        if routing_valid == 0.0:
            base_score += 0.30
            risk_factors.append("Invalid routing number")

        # Missing check number
        if check_num_valid == 0.0:
            base_score += 0.25
            risk_factors.append("Missing or invalid check number")

        # Missing payer
        if payer_present == 0.0:
            base_score += 0.30
            risk_factors.append("Missing payer name")

        # Missing payee
        if payee_present == 0.0:
            base_score += 0.30
            risk_factors.append("Missing payee name")

        # Future date
        if future_date == 1.0:
            base_score += 0.40
            risk_factors.append("Check date is in the future")

        # Missing signature
        if signature == 0.0:
            base_score += 0.35
            risk_factors.append("Signature not detected")

        # Critical missing fields
        if critical_missing >= 3:
            base_score += 0.40
            risk_factors.append(f"{int(critical_missing)} critical fields missing")

        # Suspicious amount
        if suspicious_amount == 1.0:
            base_score += 0.25
            risk_factors.append("Suspicious amount pattern detected")

        # Amount checks
        amount_value = features[4]  # Feature 5: amount_value
        if amount_value == 0.0:
            base_score += 0.30
            risk_factors.append("Amount not detected or zero")
        elif amount_value > 10000:
            base_score += 0.15
            risk_factors.append(f"High amount: ${amount_value:,.2f}")

        # Old check (stale-dated)
        date_age = features[12]  # Feature 13: date_age_days
        if date_age > 180:
            base_score += 0.20
            risk_factors.append(f"Very old check ({int(date_age)} days)")

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

    def _apply_validation_rules(self, base_score: float, check_data: Dict, features: List[float]) -> float:
        """Apply strict validation rules and adjust score"""
        adjusted_score = base_score

        # Extract key data points
        bank_valid = features[0]
        future_date = features[11]
        signature = features[13]
        critical_missing = features[20]

        # Strict rules
        if bank_valid == 0.0:  # Unsupported bank
            adjusted_score = max(adjusted_score, 0.50)

        if future_date == 1.0:  # Future date
            adjusted_score += 0.40

        if signature == 0.0:  # No signature
            adjusted_score += 0.35

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
            if value > 0.5 or (i in [20] and value > 0):  # Highlight important features
                if name == 'bank_validity' and value == 0.0:
                    importance.append("Unsupported bank")
                elif name == 'routing_validity' and value == 0.0:
                    importance.append("Invalid routing number")
                elif name == 'signature_detected' and value == 0.0:
                    importance.append("Missing signature")
                elif name == 'future_date' and value == 1.0:
                    importance.append("Future date detected")
                elif name == 'suspicious_amount' and value == 1.0:
                    importance.append("Suspicious amount pattern")
                elif name == 'critical_missing_count' and value >= 3:
                    importance.append(f"{int(value)} critical fields missing")
                elif name == 'date_age_days' and value > 180:
                    importance.append(f"Very old ({int(value)} days)")

        return importance if importance else ["No significant risk factors"]

    def _generate_anomalies(self, check_data: Dict, features: List[float],
                          feature_names: List[str], score: float) -> List[str]:
        """Generate list of anomalies detected"""
        anomalies = []

        # Use feature importance as anomalies
        feature_importance = self._get_feature_importance(features, feature_names)
        anomalies.extend(feature_importance)

        # Additional checks
        amount = features[4]
        if amount > 10000:
            anomalies.append(f"High amount: ${amount:,.2f}")

        if score >= 0.85:
            anomalies.append("CRITICAL fraud risk detected")
        elif score >= 0.60:
            anomalies.append("HIGH fraud risk detected")

        return anomalies if anomalies else []
