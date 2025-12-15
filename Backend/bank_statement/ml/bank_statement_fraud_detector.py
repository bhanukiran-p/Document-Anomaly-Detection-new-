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

# Fraud Type Taxonomy - 6 fraud types (5 document-level + 1 history-based)
FABRICATED_DOCUMENT = "FABRICATED_DOCUMENT"
ALTERED_LEGITIMATE_DOCUMENT = "ALTERED_LEGITIMATE_DOCUMENT"
SUSPICIOUS_TRANSACTION_PATTERNS = "SUSPICIOUS_TRANSACTION_PATTERNS"
BALANCE_CONSISTENCY_VIOLATION = "BALANCE_CONSISTENCY_VIOLATION"
UNREALISTIC_FINANCIAL_PROPORTIONS = "UNREALISTIC_FINANCIAL_PROPORTIONS"
REPEAT_OFFENDER = "REPEAT_OFFENDER"

# Human-readable labels (optional, for UI display)
FRAUD_TYPE_LABELS = {
    FABRICATED_DOCUMENT: "Completely fake bank statement with non-existent bank or synthetic account",
    ALTERED_LEGITIMATE_DOCUMENT: "Real bank statement that has been manually edited or tampered with",
    SUSPICIOUS_TRANSACTION_PATTERNS: "Unusual transaction patterns (duplicates, timing anomalies)",
    BALANCE_CONSISTENCY_VIOLATION: "Balance calculations don't match (ending ≠ beginning + credits - debits)",
    UNREALISTIC_FINANCIAL_PROPORTIONS: "Unrealistic credit/debit ratios or extreme balance volatility",
    REPEAT_OFFENDER: "Customer with history of fraudulent submissions and escalations",
}


class BankStatementFraudDetector:
    """
    ML-based fraud detector for bank statements
    Uses ensemble of Random Forest and XGBoost models
    """

    def __init__(self, model_dir: str = 'models'):
        """
        Initialize bank statement fraud detector

        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir
        self.feature_extractor = BankStatementFeatureExtractor()
        self.models_loaded = False

        # Model paths - use bank_statement/ml/models directory (self-contained, NO FALLBACK)
        ml_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(ml_dir, exist_ok=True)
        self.rf_model_path = os.path.join(ml_dir, 'bank_statement_random_forest.pkl')
        self.xgb_model_path = os.path.join(ml_dir, 'bank_statement_xgboost.pkl')
        self.scaler_path = os.path.join(ml_dir, 'bank_statement_feature_scaler.pkl')

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
                logger.error(f"Random Forest model not found at {self.rf_model_path}")
                self.rf_model = None

            if os.path.exists(self.xgb_model_path):
                self.xgb_model = joblib.load(self.xgb_model_path)
                logger.info("Loaded XGBoost model for bank statements")
            else:
                logger.error(f"XGBoost model not found at {self.xgb_model_path}")
                self.xgb_model = None

            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded feature scaler for bank statements")
            else:
                logger.error(f"Feature scaler not found at {self.scaler_path}")
                self.scaler = None

            # Both models are REQUIRED - no fallback
            if self.rf_model is None or self.xgb_model is None:
                missing_models = []
                if self.rf_model is None:
                    missing_models.append("Random Forest")
                if self.xgb_model is None:
                    missing_models.append("XGBoost")
                logger.error(f"Required ML models are missing: {', '.join(missing_models)}")
                self.models_loaded = False
            else:
                self.models_loaded = True

        except ImportError:
            logger.error("joblib is required for ML models but not available. Install with: pip install joblib")
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

        # Models are REQUIRED - no fallback
        if not self.models_loaded:
            raise RuntimeError(
                "ML models are not loaded. Bank statement fraud detection requires trained models. "
                f"Expected models at: {self.rf_model_path} and {self.xgb_model_path}. "
                "Please ensure models are trained and available."
            )
        
        # Use models - no fallback
        return self._predict_with_models(features, feature_names, bank_statement_data)

    def _predict_with_models(self, features: List[float], feature_names: List[str], bank_statement_data: Dict) -> Dict:
        """Predict using trained models"""
        try:
            # Convert to numpy array
            X = np.array([features])

            # Scale features if scaler available
            if self.scaler:
                X = self.scaler.transform(X)

            # Get predictions from each model (regressors return risk scores 0-100, normalize to 0-1)
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

            # Ensemble prediction (40% RF, 60% XGB)
            ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)

            # Use ensemble score directly (no validation rules applied)
            final_score = ensemble_score

            # Get feature importance
            feature_importance = self._get_feature_importance(features, feature_names)
            
            # Log top contributing features for debugging high fraud scores
            if final_score > 0.30:
                logger.info(f"High fraud risk score ({final_score:.1%}) detected. Analyzing contributing features...")
                feature_values = list(zip(feature_names, features))
                # Sort by feature value (highest first) to see what's contributing
                sorted_features = sorted(feature_values, key=lambda x: abs(x[1]), reverse=True)
                top_features = sorted_features[:10]  # Top 10 features
                logger.info(f"Top contributing features to fraud score:")
                for feat_name, feat_value in top_features:
                    logger.info(f"  - {feat_name}: {feat_value:.4f}")

            # Determine risk level
            risk_level = self._determine_risk_level(final_score)

            # Generate anomalies
            anomalies = self._generate_anomalies(bank_statement_data, features, feature_names, final_score)

            # Classify fraud types
            fraud_classification = self._classify_fraud_types(
                features, feature_names, bank_statement_data, anomalies
            )

            return {
                'fraud_risk_score': round(final_score, 4),
                'risk_level': risk_level,
                'model_confidence': round(max(rf_score, xgb_score), 4),
                'model_scores': {
                    'random_forest': round(rf_score, 4),
                    'xgboost': round(xgb_score, 4),
                    'ensemble': round(ensemble_score, 4),
                    'adjusted': round(final_score, 4)
                },
                'feature_importance': feature_importance,
                'anomalies': anomalies,
                'fraud_types': fraud_classification.get('fraud_types', []),
                'fraud_reasons': fraud_classification.get('fraud_reasons', [])
            }

        except Exception as e:
            logger.error(f"Error in model prediction: {e}", exc_info=True)
            raise RuntimeError(
                f"ML model prediction failed. Models are required for bank statement fraud detection. "
                f"Error: {str(e)}"
            ) from e

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

    def _classify_fraud_types(
        self,
        features: List[float],
        feature_names: List[str],
        normalized_data: Dict,
        anomalies: List[str] = None
    ) -> Dict:
        """
        Classify fraud types and generate machine-readable reasons based on features and anomalies.
        Uses all 35 features - NO FALLBACKS.
        
        Args:
            features: List of 35 feature values
            feature_names: List of feature names (35 features)
            normalized_data: Normalized bank statement data dictionary
            anomalies: List of anomaly strings from ML analysis
            
        Returns:
            Dictionary with 'fraud_types' (list[str]) and 'fraud_reasons' (list[str])
        """
        fraud_types = []
        fraud_reasons = []
        anomalies = anomalies or []

        # Build feature dictionary for easier access
        feature_dict = dict(zip(feature_names, features))
        
        # Extract feature values - NO FALLBACKS, use 0.0 if missing
        bank_valid = feature_dict.get('bank_validity', 0.0) == 1.0
        account_present = feature_dict.get('account_number_present', 0.0) == 1.0
        account_holder_present = feature_dict.get('account_holder_present', 0.0) == 1.0
        account_type_present = feature_dict.get('account_type_present', 0.0) == 1.0
        future_period = feature_dict.get('future_period', 0.0) == 1.0
        negative_ending_balance = feature_dict.get('negative_ending_balance', 0.0) == 1.0
        balance_consistency = feature_dict.get('balance_consistency', 1.0)
        suspicious_transaction_pattern = feature_dict.get('suspicious_transaction_pattern', 0.0) == 1.0
        duplicate_transactions = feature_dict.get('duplicate_transactions', 0.0) >= 0.5  # Now can be 0.5 (single) or 1.0 (multiple)
        unusual_timing = feature_dict.get('unusual_timing', 0.0)
        critical_missing_count = int(feature_dict.get('critical_missing_count', 0.0))
        field_quality = feature_dict.get('field_quality', 1.0)
        text_quality = feature_dict.get('text_quality', 1.0)
        credit_debit_ratio = feature_dict.get('credit_debit_ratio', 0.0)
        balance_volatility = feature_dict.get('balance_volatility', 0.0)
        large_transaction_count = int(feature_dict.get('large_transaction_count', 0.0))
        
        # Extract additional data from normalized_data
        bank_name = normalized_data.get('bank_name', '')
        account_number = normalized_data.get('account_number', '')
        account_holder_name = normalized_data.get('account_holder_name', '')
        beginning_balance = normalized_data.get('beginning_balance', {})
        ending_balance = normalized_data.get('ending_balance', {})
        total_credits = normalized_data.get('total_credits', {})
        total_debits = normalized_data.get('total_debits', {})

        # Helper to extract numeric value
        def get_numeric(val):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, dict):
                return float(val.get('value', 0.0))
            if isinstance(val, str):
                try:
                    return float(val.replace(',', '').replace('$', '').strip())
                except:
                    return 0.0
            return 0.0

        beginning_balance_val = get_numeric(beginning_balance)
        ending_balance_val = get_numeric(ending_balance)
        total_credits_val = get_numeric(total_credits)
        total_debits_val = get_numeric(total_debits)

        # ===== ONLY THE 5 DOCUMENT-LEVEL FRAUD TYPES =====
        # (REPEAT_OFFENDER is added by AI agent, not ML)
        
        # 1. FABRICATED_DOCUMENT
        # Missing bank name + missing account holder + low text quality + 3+ critical fields missing
        if not bank_valid and not account_holder_present and text_quality < 0.6:
            if FABRICATED_DOCUMENT not in fraud_types:
                fraud_types.append(FABRICATED_DOCUMENT)
                fraud_reasons.append(
                    "Missing bank name combined with missing account holder and low extraction quality suggests this may be a fabricated document."
                )
        if not bank_valid and not account_holder_present and critical_missing_count >= 3:
            if FABRICATED_DOCUMENT not in fraud_types:
                fraud_types.append(FABRICATED_DOCUMENT)
                fraud_reasons.append(
                    "Missing critical identifying information (bank name and account holder) suggests a fabricated document."
                )

        # 2. ALTERED_LEGITIMATE_DOCUMENT
        # Low text quality + suspicious ratios suggests tampering
        if text_quality < 0.6 and (balance_consistency < 0.5 or field_quality < 0.7):
            if ALTERED_LEGITIMATE_DOCUMENT not in fraud_types:
                fraud_types.append(ALTERED_LEGITIMATE_DOCUMENT)
                fraud_reasons.append(
                    "Low extraction quality combined with balance inconsistencies suggests this legitimate bank statement may have been altered or tampered with."
                )
        
        # Suspicious patterns that suggest manual editing
        if text_quality < 0.7 and critical_missing_count > 0 and balance_consistency < 0.5:
            if ALTERED_LEGITIMATE_DOCUMENT not in fraud_types:
                fraud_types.append(ALTERED_LEGITIMATE_DOCUMENT)
                fraud_reasons.append(
                    "Multiple indicators (low quality, missing fields, balance inconsistencies) suggest this document may have been manually edited."
                )

        # 3. SUSPICIOUS_TRANSACTION_PATTERNS
        # CRITICAL: Only flag if any transaction exceeds $20,000 (policy: only large transfers are suspicious)
        # The feature extractor now only returns 1.0 if a transaction > $20,000 is detected
        if suspicious_transaction_pattern:
            if SUSPICIOUS_TRANSACTION_PATTERNS not in fraud_types:
                fraud_types.append(SUSPICIOUS_TRANSACTION_PATTERNS)
                fraud_reasons.append(
                    "Large transaction detected: A transaction exceeding $20,000 was found, which exceeds the threshold for suspicious transaction patterns."
                )
        # Do NOT flag duplicates or unusual timing as suspicious transaction patterns
        # These are normal patterns and should not trigger fraud detection

        # 4. BALANCE_CONSISTENCY_VIOLATION
        # Ending balance ≠ (beginning + credits - debits) OR negative balance
        if balance_consistency < 0.5:
            if BALANCE_CONSISTENCY_VIOLATION not in fraud_types:
                fraud_types.append(BALANCE_CONSISTENCY_VIOLATION)
                expected_ending = beginning_balance_val + total_credits_val - total_debits_val
                difference = abs(ending_balance_val - expected_ending)
                fraud_reasons.append(
                    f"Balance inconsistency detected: ending balance (${ending_balance_val:,.2f}) does not match expected balance "
                    f"(${expected_ending:,.2f}) based on beginning balance and transactions (difference: ${difference:,.2f})."
                )
        if negative_ending_balance:
            if BALANCE_CONSISTENCY_VIOLATION not in fraud_types:
                fraud_types.append(BALANCE_CONSISTENCY_VIOLATION)
                fraud_reasons.append(
                    f"Negative ending balance detected (${ending_balance_val:,.2f}), which is unusual for legitimate bank statements."
                )

        # 5. UNREALISTIC_FINANCIAL_PROPORTIONS
        # Unrealistic credit/debit ratios, extreme balance swings, or too many large transactions
        if credit_debit_ratio > 100 or (credit_debit_ratio < 0.01 and total_credits_val > 0):
            if UNREALISTIC_FINANCIAL_PROPORTIONS not in fraud_types:
                fraud_types.append(UNREALISTIC_FINANCIAL_PROPORTIONS)
                fraud_reasons.append(
                    f"Unrealistic credit/debit ratio ({credit_debit_ratio:.2f}), which is unusual for legitimate bank statements."
                )
        if balance_volatility > 5.0 and beginning_balance_val > 0:
            if UNREALISTIC_FINANCIAL_PROPORTIONS not in fraud_types:
                fraud_types.append(UNREALISTIC_FINANCIAL_PROPORTIONS)
                fraud_reasons.append(
                    f"Extreme balance volatility detected ({balance_volatility:.2f}x beginning balance), indicating unrealistic financial activity."
                )
        if large_transaction_count > 10:
            if UNREALISTIC_FINANCIAL_PROPORTIONS not in fraud_types:
                fraud_types.append(UNREALISTIC_FINANCIAL_PROPORTIONS)
                fraud_reasons.append(
                    f"Unusually high number of large transactions ({large_transaction_count} transactions > $10,000), which may indicate fabricated activity."
                )

        # Select only the primary (most severe) fraud type
        # Severity order: FABRICATED_DOCUMENT > BALANCE_CONSISTENCY_VIOLATION > SUSPICIOUS_TRANSACTION_PATTERNS > UNREALISTIC_FINANCIAL_PROPORTIONS > ALTERED_LEGITIMATE_DOCUMENT
        severity_order = {
            FABRICATED_DOCUMENT: 5,
            BALANCE_CONSISTENCY_VIOLATION: 4,
            SUSPICIOUS_TRANSACTION_PATTERNS: 3,
            UNREALISTIC_FINANCIAL_PROPORTIONS: 2,
            ALTERED_LEGITIMATE_DOCUMENT: 1,
        }

        if fraud_types:
            # Get the most severe fraud type
            primary_fraud_type = max(fraud_types, key=lambda x: severity_order.get(x, 0))
            fraud_types = [primary_fraud_type]

            # Keep only the reason for the primary fraud type
            fraud_reasons = [reason for reason in fraud_reasons if primary_fraud_type.lower().replace('_', '') in reason.lower().replace('_', '') or len(fraud_reasons) == 1]
            if not fraud_reasons:
                fraud_reasons = [f"Detected as {primary_fraud_type.replace('_', ' ').title()}"]

        logger.info(f"Classified fraud type: {fraud_types}")
        logger.debug(f"Generated fraud reasons: {fraud_reasons}")

        return {
            "fraud_types": fraud_types,
            "fraud_reasons": fraud_reasons
        }

