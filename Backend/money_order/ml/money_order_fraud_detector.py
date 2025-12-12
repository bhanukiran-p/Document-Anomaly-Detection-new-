"""
Money Order Fraud Detector using ML Models
Uses Random Forest + XGBoost ensemble for fraud detection
Completely self-contained - no dependencies on other document type ML modules
"""

import os
import logging
import joblib
import numpy as np
from typing import Dict, Tuple, Optional
from .money_order_feature_extractor import MoneyOrderFeatureExtractor

logger = logging.getLogger(__name__)


class MoneyOrderFraudDetector:
    """
    ML-based fraud detection for money orders
    Uses ensemble of Random Forest + XGBoost models
    """

    def __init__(self, model_dir: str = 'models'):
        """
        Initialize fraud detector with real trained models

        Args:
            model_dir: Directory containing trained model files (ignored, uses self-contained path)
        """
        self.feature_extractor = MoneyOrderFeatureExtractor()
        self.rf_model = None
        self.xgb_model = None
        self.scaler = None
        self.models_loaded = False

        # Model paths - use money_order/ml/models directory (self-contained, NO FALLBACK)
        ml_dir = os.path.dirname(__file__)
        models_dir = os.path.join(ml_dir, 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Self-contained: Only check in money_order/ml/models
        rf_path = os.path.join(models_dir, 'money_order_random_forest.pkl')
        xgb_path = os.path.join(models_dir, 'money_order_xgboost.pkl')
        scaler_path = os.path.join(models_dir, 'money_order_feature_scaler.pkl')

        try:
            # Load Random Forest
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
                logger.info(f"Random Forest model loaded from {rf_path}")

            # Load XGBoost
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
                logger.info(f"XGBoost model loaded from {xgb_path}")

            # Load scaler
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info(f"Feature scaler loaded from {scaler_path}")

            # Check if we have at least one model
            if self.rf_model or self.xgb_model:
                self.models_loaded = True
                logger.info("ML models loaded successfully - Using real predictions")
            else:
                logger.warning(f"No trained models found at {models_dir} - using mock predictions")
                self.models_loaded = False

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            logger.warning("Falling back to mock predictions")
            self.models_loaded = False

    @staticmethod
    def _build_feature_map(feature_names, features):
        """Return a safe dict mapping feature names to values."""
        return dict(zip(feature_names or [], features or []))

    @staticmethod
    def _has_written_amount(extracted_data: Dict) -> bool:
        """Check if a document includes a written amount."""
        text = (
            extracted_data.get('amount_in_words')
            or extracted_data.get('word_amount')
            or ''
        )
        return bool(str(text).strip())

    @staticmethod
    def _is_paystub(extracted_data: Dict) -> bool:
        """Return True when the extracted document is a paystub."""
        return (extracted_data.get('document_type') or '').lower() == 'paystub'

    def _indicator_context(self, feature_dict: Dict, extracted_data: Dict) -> Dict:
        """Build reusable context required by indicator helpers."""
        return {
            'has_written_amount': self._has_written_amount(extracted_data),
            'is_paystub': self._is_paystub(extracted_data),
            'date_age_days': feature_dict.get('date_age_days', 0),
            'serial_value': extracted_data.get('serial_primary')
            or extracted_data.get('serial_number', 'N/A'),
            'issuer_value': extracted_data.get('issuer_name')
            or extracted_data.get('issuer')
            or 'Unknown',
        }

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
        # Extract features (30 features)
        features = self.feature_extractor.extract_features(extracted_data, raw_text)
        feature_names = self.feature_extractor.get_feature_names()

        if self.models_loaded:
            # Real model predictions with strict validation
            return self._model_predict(features, feature_names, extracted_data)
        else:
            # Mock predictions based on heuristics (fallback)
            return self._mock_predict(features, feature_names, extracted_data)

    def _mock_predict(self, features: list, feature_names: list, extracted_data: Dict) -> Dict:
        """Generate mock fraud predictions based on simple heuristics"""
        feature_dict = self._build_feature_map(feature_names, features)
        risk_score = 0.0

        rules = [
            (feature_dict.get('issuer_valid', 0) < 1.0, 0.25),
            (feature_dict.get('serial_format_valid', 0) == 0, 0.20),
            (feature_dict.get('amount_consistent', 1.0) < 1.0, 0.15),
            (feature_dict.get('date_is_future', 0) == 1.0, 0.40),
            (feature_dict.get('date_age_days', 0) > 90, 0.10),
            (feature_dict.get('amount_category', 0) >= 3.0, 0.10),
            (feature_dict.get('text_quality_score', 1.0) < 0.5, 0.15),
            (feature_dict.get('signature_present', 0) == 0, 0.50),  # CRITICAL: Missing signature now 50% penalty
        ]

        for condition, weight in rules:
            if condition:
                risk_score += weight

        missing_count = feature_dict.get('missing_fields_count', 0)
        if missing_count > 0:
            risk_score += min(0.30, missing_count * 0.10)

        risk_score = min(1.0, risk_score)

        import random
        noise = random.uniform(-0.05, 0.05)
        risk_score = max(0.0, min(1.0, risk_score + noise))

        rf_score = risk_score + random.uniform(-0.03, 0.03)
        xgb_score = risk_score + random.uniform(-0.03, 0.03)
        rf_score = max(0.0, min(1.0, rf_score))
        xgb_score = max(0.0, min(1.0, xgb_score))

        model_variance = abs(rf_score - xgb_score)
        confidence = max(0.7, 1.0 - (model_variance * 2))

        risk_level = self._categorize_risk(risk_score)
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
            'fraud_indicators': fraud_indicators,  # Also store as fraud_indicators for AI agent
            'prediction_type': 'mock'
        }

    def _model_predict(self, features: list, feature_names: list, extracted_data: Dict) -> Dict:
        """Generate predictions using trained ML models with strict validation"""
        X = np.array(features).reshape(1, -1)

        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X

        rf_score = 0.0
        xgb_score = 0.0

        if self.rf_model:
            try:
                # Try predict_proba first (if classifier)
                rf_proba = self.rf_model.predict_proba(X_scaled)[0]
                rf_score = rf_proba[1] if len(rf_proba) > 1 else rf_proba[0]
            except AttributeError:
                # Use predict() for regressors and normalize (0-100 -> 0-1)
                rf_pred = self.rf_model.predict(X_scaled)[0]
                rf_score = max(0.0, min(1.0, rf_pred / 100.0))

        if self.xgb_model:
            try:
                # Try predict_proba first (if classifier)
                xgb_proba = self.xgb_model.predict_proba(X_scaled)[0]
                xgb_score = xgb_proba[1] if len(xgb_proba) > 1 else xgb_proba[0]
            except AttributeError:
                # Use predict() for regressors and normalize (0-100 -> 0-1)
                xgb_pred = self.xgb_model.predict(X_scaled)[0]
                xgb_score = max(0.0, min(1.0, xgb_pred / 100.0))

        if self.rf_model and self.xgb_model:
            base_fraud_score = 0.4 * rf_score + 0.6 * xgb_score
        elif self.rf_model:
            base_fraud_score = rf_score
        elif self.xgb_model:
            base_fraud_score = xgb_score
        else:
            base_fraud_score = 0.5

        final_fraud_score = self._apply_strict_validation(
            base_fraud_score, features, feature_names, extracted_data
        )

        if self.rf_model and self.xgb_model:
            model_variance = abs(rf_score - xgb_score)
            confidence = max(0.7, 1.0 - (model_variance * 2))
        else:
            confidence = 0.85

        risk_level = self._categorize_risk(final_fraud_score)
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
            'fraud_indicators': fraud_indicators,  # Also store as fraud_indicators for AI agent
            'prediction_type': 'model'
        }

    def _apply_strict_validation(self, base_score: float, features: list,
                                 feature_names: list, extracted_data: Dict) -> float:
        """Apply strict validation rules on top of ML prediction"""
        adjusted_score = base_score
        feature_dict = self._build_feature_map(feature_names, features)

        amount_words_present = self._has_written_amount(extracted_data)
        is_paystub = self._is_paystub(extracted_data)

        def apply(condition: bool, delta: float, label: Optional[str] = None):
            nonlocal adjusted_score
            if condition:
                adjusted_score += delta
                if label:
                    logger.debug(label)

        apply(
            amount_words_present and feature_dict.get('exact_amount_match', 1.0) == 0.0,
            0.40,
            "CRITICAL: Amount mismatch detected (+0.40)"
        )
        apply(
            feature_dict.get('date_is_future', 0.0) == 1.0 and not is_paystub,
            0.40,
            "CRITICAL: Future date detected (+0.40)"
        )
        
        # CRITICAL: Validate written amount spelling
        amount_in_words = extracted_data.get('amount_in_words', '')
        if amount_in_words and isinstance(amount_in_words, str):
            # Valid English number words
            valid_number_words = {
                'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
                'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety',
                'hundred', 'thousand', 'million', 'billion',
                'and', 'dollars', 'cents', 'only'
            }
            
            # Extract words from written amount (lowercase, remove punctuation)
            import re
            words = re.findall(r'\b[a-zA-Z]+\b', amount_in_words.lower())
            
            # Check for invalid/misspelled number words
            invalid_words = [w for w in words if w not in valid_number_words and len(w) > 2]
            
            if invalid_words:
                apply(
                    True,
                    0.50,
                    f"CRITICAL: Invalid/misspelled words in written amount: {invalid_words} (+0.50)"
                )

        critical_missing_score = feature_dict.get('critical_missing_score', 0.0)
        apply(critical_missing_score >= 0.30, 0.30, "HIGH: Critical field missing - amount (+0.30)")
        apply(0.25 <= critical_missing_score < 0.30, 0.25, "HIGH: Critical field missing - serial (+0.25)")
        apply(0.20 <= critical_missing_score < 0.25, 0.20, "HIGH: Critical field missing - recipient (+0.20)")

        # CRITICAL: Mandatory signature validation - strict enforcement
        apply(
            feature_dict.get('signature_present', 0) == 0,
            0.60,
            "CRITICAL: Missing signature - mandatory field, document will be rejected (+0.60)"
        )

        date_age_days = feature_dict.get('date_age_days', 0)
        apply(date_age_days > 180 and not is_paystub, 0.20, f"HIGH: Very old date ({int(date_age_days)} days) (+0.20)")

        apply(feature_dict.get('date_format_consistency', 1.0) == 0.0, 0.15, "MEDIUM: Invalid date format (+0.15)")
        apply(feature_dict.get('suspicious_amount_pattern', 0.0) == 1.0 and not is_paystub, 0.10, "MEDIUM: Suspicious amount pattern (+0.10)")
        apply(
            feature_dict.get('weekend_holiday_flag', 0.0) == 1.0
            and feature_dict.get('amount_numeric', 0) > 2000
            and not is_paystub,
            0.15,
            "MEDIUM: Large amount issued on weekend (+0.15)"
        )
        apply(feature_dict.get('serial_format_valid', 1.0) == 0.0, 0.15, "MEDIUM: Invalid serial format (+0.15)")
        apply(feature_dict.get('field_quality_score', 1.0) < 0.5, 0.10, "LOW: Poor field quality (+0.10)")

        final_score = min(1.0, adjusted_score)
        if final_score != base_score:
            logger.debug(f"Score adjusted: {base_score:.3f} -> {final_score:.3f}")

        return final_score

    def _identify_indicators_from_features(self, features: list, feature_names: list,
                                          extracted_data: Dict) -> list:
        """Identify fraud indicators from all 30 features"""
        indicators = []
        feature_dict = self._build_feature_map(feature_names, features)
        ctx = self._indicator_context(feature_dict, extracted_data)

        def add(message: str):
            if message and message not in indicators:
                indicators.append(message)

        if ctx['has_written_amount'] and feature_dict.get('exact_amount_match', 1.0) == 0.0:
            add("CRITICAL: Amount mismatch - numeric vs written")

        if feature_dict.get('amount_parsing_confidence', 1.0) < 0.5:
            add("Amount parsing confidence low")

        if feature_dict.get('suspicious_amount_pattern', 0.0) == 1.0:
            add("Suspicious amount pattern detected")

        if feature_dict.get('date_is_future', 0.0) == 1.0:
            add("CRITICAL: Date is in the future")

        if feature_dict.get('date_format_consistency', 1.0) == 0.0:
            add("Invalid date format")

        if feature_dict.get('weekend_holiday_flag', 0.0) == 1.0 and not ctx['is_paystub']:
            add("Issued on weekend/holiday")

        if feature_dict.get('date_amount_correlation', 0.0) > 0.6:
            add("Suspicious date-amount correlation")

        critical_missing = feature_dict.get('critical_missing_score', 0.0)
        if critical_missing > 0:
            add(f"Missing critical fields (score: {critical_missing:.2f})")

        field_quality = feature_dict.get('field_quality_score', 1.0)
        if field_quality < 0.6:
            add(f"Poor field quality (score: {field_quality:.2f})")

        if feature_dict.get('issuer_specific_validation', 1.0) < 0.8:
            add("Issuer-specific validation failed")

        if feature_dict.get('serial_pattern_match', 1.0) < 0.5:
            add("Serial number doesn't match issuer pattern")

        if feature_dict.get('address_validation', 1.0) == 0.0:
            add("Invalid address format")

        name_consistency = feature_dict.get('name_consistency', 1.0)
        if name_consistency < 0.5:
            add(f"Name format inconsistent (score: {name_consistency:.2f})")

        if feature_dict.get('signature_present', 0) == 0:
            add("CRITICAL: Missing signature - document rejected per mandatory validation policy")

        if feature_dict.get('serial_format_valid', 1.0) == 0.0:
            add(f"Invalid serial format: '{ctx['serial_value']}'")

        if feature_dict.get('issuer_valid', 1.0) < 1.0:
            add(f"Invalid issuer: '{ctx['issuer_value']}'")

        if ctx['date_age_days'] > 180 and not ctx['is_paystub']:
            add(f"Very old ({int(ctx['date_age_days'])} days)")

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
        ctx = self._indicator_context(feature_dict, extracted_data)

        def add(message: str):
            if message and message not in indicators:
                indicators.append(message)

        if feature_dict.get('issuer_valid', 0) < 1.0:
            add(f"Issuer validation failed: '{extracted_data.get('issuer', 'Unknown')}'")

        if feature_dict.get('serial_format_valid', 0) == 0:
            add(f"Invalid serial number format: '{extracted_data.get('serial_number', 'N/A')}'")

        if ctx['has_written_amount'] and feature_dict.get('amount_consistent', 1.0) < 1.0:
            add("Amount mismatch between numeric and written values")

        missing_fields = int(feature_dict.get('missing_fields_count', 0))
        if missing_fields > 0:
            add(f"Missing {missing_fields} critical field(s)")

        if feature_dict.get('date_is_future', 0) == 1.0:
            add("Date is in the future - major red flag")

        if feature_dict.get('text_quality_score', 1.0) < 0.5:
            add("Poor OCR text quality (possible tampering or photocopy)")

        if feature_dict.get('signature_present', 0) == 0:
            add("Missing signature")

        if feature_dict.get('date_age_days', 0) > 90:
            add(f"Money order is {int(feature_dict['date_age_days'])} days old (stale)")

        return indicators[:5]

    def get_feature_names(self) -> list:
        """Get feature names for reference"""
        return self.feature_extractor.get_feature_names()


