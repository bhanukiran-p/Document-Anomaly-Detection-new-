"""
Money Order Fraud Detector using ML Models
Uses Random Forest + XGBoost ensemble for fraud detection
"""

import os
import joblib
import numpy as np
from typing import Dict, Tuple, Optional
from .feature_extractor import FeatureExtractor


class MoneyOrderFraudDetector:
    """
    ML-based fraud detection for money orders
    Uses ensemble of Random Forest + XGBoost models
    """

    def __init__(self, model_path: Optional[str] = None, use_mock: bool = True):
        """
        Initialize fraud detector

        Args:
            model_path: Path to trained model file
            use_mock: If True, use mock predictions for testing
        """
        self.feature_extractor = FeatureExtractor()
        self.use_mock = use_mock
        self.model = None

        if not use_mock and model_path and os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                self.use_mock = False
                print(f"Loaded trained model from {model_path}")
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")
                print("Falling back to mock predictions")
                self.use_mock = True
        else:
            print("Using mock ML predictions (model not trained yet)")
            self.use_mock = True

    def predict_fraud(self, extracted_data: Dict, raw_text: str = "") -> Dict:
        """
        Predict fraud probability for a money order

        Args:
            extracted_data: Dictionary of extracted money order fields
            raw_text: Raw OCR text from the document

        Returns:
            Dictionary containing:
                - fraud_risk_score: 0.0-1.0 probability of fraud
                - risk_level: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'
                - model_confidence: Model confidence in prediction
                - model_scores: Individual model scores (RF, XGBoost)
                - feature_importance: Top fraud indicators
        """
        # Extract features
        features = self.feature_extractor.extract_features(extracted_data, raw_text)
        feature_names = self.feature_extractor.get_feature_names()

        if self.use_mock:
            # Mock predictions based on heuristics
            return self._mock_predict(features, feature_names, extracted_data)
        else:
            # Real model predictions
            return self._model_predict(features, feature_names)

    def _mock_predict(self, features: list, feature_names: list, extracted_data: Dict) -> Dict:
        """
        Generate mock fraud predictions based on simple heuristics
        This simulates ML model behavior for testing
        """
        # Calculate risk score based on features
        risk_score = 0.0

        # Create feature dict for easy access
        feature_dict = dict(zip(feature_names, features))

        # Rule 1: Invalid or missing issuer (high risk)
        if feature_dict.get('issuer_valid', 0) < 1.0:
            risk_score += 0.25

        # Rule 2: Serial number issues
        if feature_dict.get('serial_format_valid', 0) == 0:
            risk_score += 0.20

        # Rule 3: Amount inconsistency
        if feature_dict.get('amount_consistent', 1.0) < 1.0:
            risk_score += 0.15

        # Rule 4: Missing critical fields
        missing_count = feature_dict.get('missing_fields_count', 0)
        if missing_count > 0:
            risk_score += min(0.30, missing_count * 0.10)

        # Rule 5: Future date (major red flag)
        if feature_dict.get('date_is_future', 0) == 1.0:
            risk_score += 0.40

        # Rule 6: Very old date or very high amount
        if feature_dict.get('date_age_days', 0) > 90:
            risk_score += 0.10
        if feature_dict.get('amount_category', 0) >= 3.0:
            risk_score += 0.10

        # Rule 7: Poor text quality (suggests tampering/photocopy)
        if feature_dict.get('text_quality_score', 1.0) < 0.5:
            risk_score += 0.15

        # Rule 8: Missing signature or receipt
        if feature_dict.get('signature_present', 0) == 0:
            risk_score += 0.10

        # Normalize risk score to 0-1
        risk_score = min(1.0, risk_score)

        # Add some randomness to simulate model variance (±5%)
        import random
        noise = random.uniform(-0.05, 0.05)
        risk_score = max(0.0, min(1.0, risk_score + noise))

        # Simulate individual model scores
        rf_score = risk_score + random.uniform(-0.03, 0.03)
        xgb_score = risk_score + random.uniform(-0.03, 0.03)
        rf_score = max(0.0, min(1.0, rf_score))
        xgb_score = max(0.0, min(1.0, xgb_score))

        # Calculate model confidence
        # Higher agreement between models = higher confidence
        model_variance = abs(rf_score - xgb_score)
        confidence = max(0.7, 1.0 - (model_variance * 2))

        # Determine risk level
        risk_level = self._categorize_risk(risk_score)

        # Identify top fraud indicators
        fraud_indicators = self._identify_indicators(feature_dict, extracted_data)

        return {
            'fraud_risk_score': round(risk_score, 3),
            'risk_level': risk_level,
            'model_confidence': round(confidence, 3),
            'model_scores': {
                'random_forest': round(rf_score, 3),
                'xgboost': round(xgb_score, 3),
                'ensemble': round(risk_score, 3)
            },
            'feature_importance': fraud_indicators,
            'prediction_type': 'mock'  # Indicate this is a mock prediction
        }

    def _model_predict(self, features: list, feature_names: list) -> Dict:
        """
        Generate predictions using trained ML model
        """
        # Convert features to numpy array
        X = np.array(features).reshape(1, -1)

        # Get prediction probabilities
        fraud_prob = self.model.predict_proba(X)[0][1]  # Probability of fraud class

        # Get individual model scores if ensemble
        try:
            rf_score = self.model.named_estimators_['random_forest'].predict_proba(X)[0][1]
            xgb_score = self.model.named_estimators_['xgboost'].predict_proba(X)[0][1]
        except (AttributeError, KeyError):
            # If not an ensemble, use the same score
            rf_score = fraud_prob
            xgb_score = fraud_prob

        # Calculate confidence based on model agreement
        model_variance = abs(rf_score - xgb_score)
        confidence = max(0.7, 1.0 - (model_variance * 2))

        # Determine risk level
        risk_level = self._categorize_risk(fraud_prob)

        # Get feature importance
        try:
            importances = self.model.feature_importances_
            top_features = sorted(zip(feature_names, importances),
                                key=lambda x: x[1], reverse=True)[:5]
            fraud_indicators = [f"{name}: {importance:.3f}" for name, importance in top_features]
        except AttributeError:
            fraud_indicators = []

        return {
            'fraud_risk_score': round(fraud_prob, 3),
            'risk_level': risk_level,
            'model_confidence': round(confidence, 3),
            'model_scores': {
                'random_forest': round(rf_score, 3),
                'xgboost': round(xgb_score, 3),
                'ensemble': round(fraud_prob, 3)
            },
            'feature_importance': fraud_indicators,
            'prediction_type': 'model'
        }

    def _categorize_risk(self, score: float) -> str:
        """Categorize fraud risk score into levels"""
        if score < 0.3:
            return 'LOW'
        elif score < 0.6:
            return 'MEDIUM'
        elif score < 0.85:
            return 'HIGH'
        else:
            return 'CRITICAL'

    def _identify_indicators(self, feature_dict: Dict, extracted_data: Dict) -> list:
        """Identify top fraud indicators from features"""
        indicators = []

        # Check for specific fraud patterns
        if feature_dict.get('issuer_valid', 0) < 1.0:
            issuer = extracted_data.get('issuer', 'Unknown')
            indicators.append(f"Issuer validation failed: '{issuer}'")

        if feature_dict.get('serial_format_valid', 0) == 0:
            serial = extracted_data.get('serial_number', 'N/A')
            indicators.append(f"Invalid serial number format: '{serial}'")

        if feature_dict.get('amount_consistent', 1.0) < 1.0:
            indicators.append("Amount mismatch between numeric and written values")

        if feature_dict.get('missing_fields_count', 0) > 0:
            count = int(feature_dict['missing_fields_count'])
            indicators.append(f"Missing {count} critical field(s)")

        if feature_dict.get('date_is_future', 0) == 1.0:
            indicators.append("Date is in the future - major red flag")

        if feature_dict.get('text_quality_score', 1.0) < 0.5:
            indicators.append("Poor OCR text quality (possible tampering or photocopy)")

        if feature_dict.get('signature_present', 0) == 0:
            indicators.append("Missing signature")

        if feature_dict.get('date_age_days', 0) > 90:
            days = int(feature_dict['date_age_days'])
            indicators.append(f"Money order is {days} days old (stale)")

        # Limit to top 5 indicators
        return indicators[:5]

    def get_feature_names(self) -> list:
        """Get feature names for reference"""
        return self.feature_extractor.get_feature_names()
