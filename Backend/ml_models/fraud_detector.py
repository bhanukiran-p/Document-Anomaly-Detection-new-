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

    def __init__(self, model_dir: str = 'ml_models'):
        """
        Initialize fraud detector with real trained models

        Args:
            model_dir: Directory containing trained model files
        """
        self.feature_extractor = FeatureExtractor()
        self.rf_model = None
        self.xgb_model = None
        self.scaler = None
        self.models_loaded = False

        # Try to load trained models
        rf_path = os.path.join(model_dir, 'trained_random_forest.pkl')
        xgb_path = os.path.join(model_dir, 'trained_xgboost.pkl')
        scaler_path = os.path.join(model_dir, 'feature_scaler.pkl')

        try:
            # Load Random Forest
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
                print(f"✅ Random Forest model loaded from {rf_path}")

            # Load XGBoost
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
                print(f"✅ XGBoost model loaded from {xgb_path}")

            # Load scaler
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                print(f"✅ Feature scaler loaded from {scaler_path}")

            # Check if we have at least one model
            if self.rf_model or self.xgb_model:
                self.models_loaded = True
                print("✅ ML models loaded successfully - Using real predictions")
            else:
                print("⚠️  No trained models found - Using mock predictions")
                self.models_loaded = False

        except Exception as e:
            print(f"⚠️  Error loading models: {e}")
            print("Falling back to mock predictions")
            self.models_loaded = False

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
        # Extract features (now 30 features)
        features = self.feature_extractor.extract_features(extracted_data, raw_text)
        feature_names = self.feature_extractor.get_feature_names()

        if self.models_loaded:
            # Real model predictions with strict validation
            return self._model_predict(features, feature_names, extracted_data)
        else:
            # Mock predictions based on heuristics (fallback)
            return self._mock_predict(features, feature_names, extracted_data)

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

    def _model_predict(self, features: list, feature_names: list, extracted_data: Dict) -> Dict:
        """
        Generate predictions using trained ML models with strict validation
        Uses ensemble of Random Forest + XGBoost with strict fraud rules
        """
        # Convert features to numpy array
        X = np.array(features).reshape(1, -1)

        # Scale features if scaler is available
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X

        # Get predictions from available models
        rf_score = 0.0
        xgb_score = 0.0

        if self.rf_model:
            rf_proba = self.rf_model.predict_proba(X_scaled)[0][1]
            rf_score = rf_proba

        if self.xgb_model:
            xgb_proba = self.xgb_model.predict_proba(X_scaled)[0][1]
            xgb_score = xgb_proba

        # Calculate ensemble score (RF: 40%, XGB: 60%)
        if self.rf_model and self.xgb_model:
            base_fraud_score = 0.4 * rf_score + 0.6 * xgb_score
        elif self.rf_model:
            base_fraud_score = rf_score
        elif self.xgb_model:
            base_fraud_score = xgb_score
        else:
            base_fraud_score = 0.5  # Fallback

        # Apply strict validation rules to adjust fraud score
        final_fraud_score = self._apply_strict_validation(
            base_fraud_score, features, feature_names, extracted_data
        )

        # Calculate model confidence
        if self.rf_model and self.xgb_model:
            model_variance = abs(rf_score - xgb_score)
            confidence = max(0.7, 1.0 - (model_variance * 2))
        else:
            confidence = 0.85  # Single model confidence

        # Determine risk level
        risk_level = self._categorize_risk(final_fraud_score)

        # Identify fraud indicators
        fraud_indicators = self._identify_indicators_from_features(
            features, feature_names, extracted_data
        )

        return {
            'fraud_risk_score': round(final_fraud_score, 3),
            'risk_level': risk_level,
            'model_confidence': round(confidence, 3),
            'model_scores': {
                'random_forest': round(rf_score, 3),
                'xgboost': round(xgb_score, 3),
                'ensemble': round(base_fraud_score, 3),
                'adjusted': round(final_fraud_score, 3)
            },
            'feature_importance': fraud_indicators,
            'prediction_type': 'model'
        }

    def _apply_strict_validation(self, base_score: float, features: list,
                                 feature_names: list, extracted_data: Dict) -> float:
        """
        Apply strict validation rules on top of ML prediction

        Args:
            base_score: Base ML prediction score
            features: Feature values
            feature_names: Feature names
            extracted_data: Original extracted data

        Returns:
            Adjusted fraud score with strict rules applied
        """
        adjusted_score = base_score
        feature_dict = dict(zip(feature_names, features))

        # CRITICAL RULES (add +0.40 to fraud score)

        # Rule 1: Amount mismatch (feature 18)
        exact_amount_match = feature_dict.get('exact_amount_match', 1.0)
        if exact_amount_match == 0.0:
            adjusted_score += 0.40
            print("⚠️  CRITICAL: Amount mismatch detected (+0.40)")

        # Rule 2: Future date (feature 10)
        date_is_future = feature_dict.get('date_is_future', 0.0)
        if date_is_future == 1.0:
            adjusted_score += 0.40
            print("⚠️  CRITICAL: Future date detected (+0.40)")

        # HIGH PRIORITY RULES (add +0.20-0.30)

        # Rule 3: Missing critical fields (feature 24)
        critical_missing_score = feature_dict.get('critical_missing_score', 0.0)
        if critical_missing_score >= 0.30:  # Missing amount
            adjusted_score += 0.30
            print("⚠️  HIGH: Critical field missing - amount (+0.30)")
        elif critical_missing_score >= 0.25:  # Missing serial
            adjusted_score += 0.25
            print("⚠️  HIGH: Critical field missing - serial (+0.25)")
        elif critical_missing_score >= 0.20:  # Missing recipient
            adjusted_score += 0.20
            print("⚠️  HIGH: Critical field missing - recipient (+0.20)")

        # Rule 4: Very old date (feature 11)
        date_age_days = feature_dict.get('date_age_days', 0)
        if date_age_days > 180:
            adjusted_score += 0.20
            print(f"⚠️  HIGH: Very old date ({int(date_age_days)} days) (+0.20)")

        # MEDIUM PRIORITY RULES (add +0.10-0.15)

        # Rule 5: Invalid date format (feature 21)
        date_format_valid = feature_dict.get('date_format_consistency', 1.0)
        if date_format_valid == 0.0:
            adjusted_score += 0.15
            print("⚠️  MEDIUM: Invalid date format (+0.15)")

        # Rule 6: Suspicious amount pattern (feature 20)
        suspicious_amount = feature_dict.get('suspicious_amount_pattern', 0.0)
        if suspicious_amount == 1.0:
            adjusted_score += 0.10
            print("⚠️  MEDIUM: Suspicious amount pattern (+0.10)")

        # Rule 7: Weekend issue (feature 22)
        weekend_flag = feature_dict.get('weekend_holiday_flag', 0.0)
        amount = feature_dict.get('amount_numeric', 0)
        if weekend_flag == 1.0 and amount > 2000:
            adjusted_score += 0.15
            print("⚠️  MEDIUM: Large amount issued on weekend (+0.15)")

        # Rule 8: Invalid serial format (feature 3)
        serial_valid = feature_dict.get('serial_format_valid', 1.0)
        if serial_valid == 0.0:
            adjusted_score += 0.15
            print("⚠️  MEDIUM: Invalid serial format (+0.15)")

        # LOW PRIORITY RULES (add +0.05-0.10)

        # Rule 9: Poor field quality (feature 25)
        field_quality = feature_dict.get('field_quality_score', 1.0)
        if field_quality < 0.5:
            adjusted_score += 0.10
            print("⚠️  LOW: Poor field quality (+0.10)")

        # Rule 10: Missing signature when required (feature 30)
        signature_score = feature_dict.get('signature_required_score', 0.5)
        if signature_score == 0.0:
            adjusted_score += 0.10
            print("⚠️  LOW: Missing required signature (+0.10)")

        # Cap final score at 1.0
        final_score = min(1.0, adjusted_score)

        if final_score != base_score:
            print(f"📊 Score adjusted: {base_score:.3f} → {final_score:.3f}")

        return final_score

    def _identify_indicators_from_features(self, features: list, feature_names: list,
                                          extracted_data: Dict) -> list:
        """
        Identify fraud indicators from all 30 features

        Args:
            features: Feature values
            feature_names: Feature names
            extracted_data: Original extracted data

        Returns:
            List of fraud indicators
        """
        indicators = []
        feature_dict = dict(zip(feature_names, features))

        # Check all critical indicators

        # Amount validation (features 18-20)
        if feature_dict.get('exact_amount_match', 1.0) == 0.0:
            indicators.append("CRITICAL: Amount mismatch - numeric ≠ written")

        amount_confidence = feature_dict.get('amount_parsing_confidence', 1.0)
        if amount_confidence < 0.5:
            indicators.append("Amount parsing confidence low")

        if feature_dict.get('suspicious_amount_pattern', 0.0) == 1.0:
            indicators.append("Suspicious amount pattern detected")

        # Date validation (features 21-23)
        if feature_dict.get('date_is_future', 0.0) == 1.0:
            indicators.append("CRITICAL: Date is in the future")

        if feature_dict.get('date_format_consistency', 1.0) == 0.0:
            indicators.append("Invalid date format")

        if feature_dict.get('weekend_holiday_flag', 0.0) == 1.0:
            indicators.append("Issued on weekend/holiday")

        date_amount_corr = feature_dict.get('date_amount_correlation', 0.0)
        if date_amount_corr > 0.6:
            indicators.append("Suspicious date-amount correlation")

        # Field completeness (features 24-26)
        critical_missing = feature_dict.get('critical_missing_score', 0.0)
        if critical_missing > 0:
            indicators.append(f"Missing critical fields (score: {critical_missing:.2f})")

        field_quality = feature_dict.get('field_quality_score', 1.0)
        if field_quality < 0.6:
            indicators.append(f"Poor field quality (score: {field_quality:.2f})")

        issuer_validation = feature_dict.get('issuer_specific_validation', 1.0)
        if issuer_validation < 0.8:
            indicators.append("Issuer-specific validation failed")

        # Pattern validation (features 27-30)
        if feature_dict.get('serial_pattern_match', 1.0) < 0.5:
            indicators.append("Serial number doesn't match issuer pattern")

        if feature_dict.get('address_validation', 1.0) == 0.0:
            indicators.append("Invalid address format")

        name_consistency = feature_dict.get('name_consistency', 1.0)
        if name_consistency < 0.5:
            indicators.append(f"Name format inconsistent (score: {name_consistency:.2f})")

        if feature_dict.get('signature_required_score', 0.5) == 0.0:
            indicators.append("Missing required signature")

        # Basic features
        if feature_dict.get('serial_format_valid', 1.0) == 0.0:
            serial = extracted_data.get('serial_primary') or extracted_data.get('serial_number', 'N/A')
            indicators.append(f"Invalid serial format: '{serial}'")

        if feature_dict.get('issuer_valid', 1.0) < 1.0:
            issuer = extracted_data.get('issuer_name') or extracted_data.get('issuer', 'Unknown')
            indicators.append(f"Invalid issuer: '{issuer}'")

        date_age = feature_dict.get('date_age_days', 0)
        if date_age > 180:
            indicators.append(f"Very old ({int(date_age)} days)")

        # Limit to top 10 most critical indicators
        return indicators[:10]

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
