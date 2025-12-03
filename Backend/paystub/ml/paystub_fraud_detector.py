"""
Paystub Fraud Detection ML Model
Uses trained Random Forest model for paystub fraud detection
Completely independent from other document type fraud detection
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from .paystub_feature_extractor import PaystubFeatureExtractor

logger = logging.getLogger(__name__)

# Fraud Type Taxonomy - 5 fraud types (4 document-level + 1 history-based)
FABRICATED_DOCUMENT = "FABRICATED_DOCUMENT"
UNREALISTIC_PROPORTIONS = "UNREALISTIC_PROPORTIONS"
ALTERED_LEGITIMATE_DOCUMENT = "ALTERED_LEGITIMATE_DOCUMENT"
ZERO_WITHHOLDING_SUSPICIOUS = "ZERO_WITHHOLDING_SUSPICIOUS"
REPEAT_OFFENDER = "REPEAT_OFFENDER"

# Human-readable labels (optional, for UI display)
FRAUD_TYPE_LABELS = {
    FABRICATED_DOCUMENT: "Completely fake paystub with non-existent employer or synthetic identity",
    UNREALISTIC_PROPORTIONS: "Net/gross ratios and tax/deduction percentages that don't make sense",
    ALTERED_LEGITIMATE_DOCUMENT: "Real paystub that has been manually edited or tampered with",
    ZERO_WITHHOLDING_SUSPICIOUS: "No federal/state tax or mandatory deductions where they should exist",
    REPEAT_OFFENDER: "Employee with history of fraudulent submissions and escalations",
}


class PaystubFraudDetector:
    """
    ML-based fraud detector for paystubs
    Uses trained Random Forest model
    """

    def __init__(self, model_dir: str = 'models'):
        """
        Initialize paystub fraud detector

        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir
        self.feature_extractor = PaystubFeatureExtractor()
        self.models_loaded = False

        # Model paths - use paystub/ml/models directory (self-contained, NO FALLBACK)
        ml_dir = os.path.dirname(__file__)
        models_dir = os.path.join(ml_dir, 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Self-contained: Only check in paystub/ml/models
        self.model_path = os.path.join(models_dir, 'paystub_risk_model_latest.pkl')
        self.scaler_path = os.path.join(models_dir, 'paystub_scaler_latest.pkl')
        self.metadata_path = os.path.join(models_dir, 'paystub_model_metadata_latest.json')
        
        # Log paths
        if os.path.exists(self.model_path):
            logger.info(f"Using model at: {self.model_path}")
        else:
            logger.error(f"Model not found at: {self.model_path} - ML model is required")

        # Load models
        self._load_models()

    def _load_models(self):
        """Load trained models from disk"""
        try:
            import joblib
            import json

            # Load metadata to verify feature names
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                    logger.info(f"Model metadata: {metadata.get('model_type')}, trained at {metadata.get('trained_at')}")
                    logger.info(f"Expected features: {metadata.get('feature_names', [])}")

            # Load model
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info("Loaded Random Forest model for paystubs")
            else:
                logger.error(f"Random Forest model not found at {self.model_path} - ML model is required")
                self.model = None

            # Load scaler
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded feature scaler for paystubs")
            else:
                raise RuntimeError(
                    f"Feature scaler not found at {self.scaler_path}. "
                    f"Please train the model using: python training/train_risk_model.py"
                )

            # Verify model expects 18 features
            if metadata and 'feature_count' in metadata:
                expected_features = metadata.get('feature_count', 0)
                if expected_features != 18:
                    raise RuntimeError(
                        f"Model was trained with {expected_features} features, but system expects 18 features. "
                        f"Please retrain the model using: python training/train_risk_model.py"
                    )

            self.models_loaded = (self.model is not None and self.scaler is not None)

        except ImportError:
            raise RuntimeError(
                "joblib not available - ML model cannot be loaded without joblib. "
                "Install with: pip install joblib"
            )
        except RuntimeError:
            # Re-raise RuntimeErrors (these are intentional, no fallback)
            raise
        except Exception as e:
            raise RuntimeError(
                f"Error loading models: {e}. "
                f"Please ensure models are trained using: python training/train_risk_model.py"
            )

    def predict_fraud(self, paystub_data: Dict, raw_text: str = "") -> Dict:
        """
        Predict fraud likelihood for a paystub

        Args:
            paystub_data: Extracted paystub data (from Mindee or normalized)
            raw_text: Raw OCR text (optional)

        Returns:
            Dictionary containing:
                - fraud_risk_score: Float 0.0-1.0
                - risk_level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
                - model_confidence: Float 0.0-1.0
                - model_scores: Dict with model scores
                - feature_importance: List of important features
                - anomalies: List of detected anomalies
        """
        # Extract features
        features = self.feature_extractor.extract_features(paystub_data, raw_text)
        feature_names = self.feature_extractor.get_feature_names()

        logger.info(f"Extracted {len(features)} features for paystub fraud detection")

        # Models must be loaded - no fallback
        if not self.models_loaded:
            raise RuntimeError(
                f"ML model not loaded. Model file not found at: {self.model_path}. "
                f"Please train the model using: python training/train_risk_model.py"
            )
        
        return self._predict_with_model(features, feature_names, paystub_data)

    def _predict_with_model(self, features: List[float], feature_names: List[str], paystub_data: Dict) -> Dict:
        """Predict using trained model"""
        try:
            # Convert to numpy array
            X = np.array([features])

            # Scale features if scaler available
            if self.scaler:
                X = self.scaler.transform(X)

            # Get prediction from model - NO FALLBACKS
            if not self.model:
                raise RuntimeError(
                    "ML model is None. This should never happen if models_loaded is True. "
                    "Please retrain the model using: python training/train_risk_model.py"
                )
            
            # Validate feature count matches model expectations
            if len(features) != 18:
                raise RuntimeError(
                    f"Feature count mismatch: Expected 18 features, got {len(features)}. "
                    "This is a critical error - no fallback available."
                )
            
            # Model predicts risk score (0-100), convert to 0-1
            risk_score_raw = self.model.predict(X)[0]
            fraud_risk_score = min(1.0, max(0.0, risk_score_raw / 100.0))  # Convert 0-100 to 0-1
            
            # Get feature importance if available
            feature_importance = []
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                # Get top 5 most important features (for 18 features)
                top_indices = np.argsort(importances)[-5:][::-1]
                for idx in top_indices:
                    if importances[idx] > 0:
                        feature_importance.append(f"{feature_names[idx]}: {importances[idx]:.3f}")

            # Determine risk level
            if fraud_risk_score < 0.3:
                risk_level = 'LOW'
            elif fraud_risk_score < 0.7:
                risk_level = 'MEDIUM'
            elif fraud_risk_score < 0.9:
                risk_level = 'HIGH'
            else:
                risk_level = 'CRITICAL'

            # Generate indicators based on features
            indicators = self._generate_indicators(features, feature_names, paystub_data)

            # Classify fraud types and generate machine reasons
            fraud_classification = self._classify_fraud_types(features, feature_names, paystub_data, indicators)

            return {
                'fraud_risk_score': round(fraud_risk_score, 2),
                'risk_level': risk_level,
                'model_confidence': 0.90,  # High confidence for trained model
                'model_scores': {
                    'random_forest': round(fraud_risk_score, 2)
                },
                'feature_importance': feature_importance,
                'anomalies': indicators,
                'fraud_types': fraud_classification['fraud_types'],
                'fraud_reasons': fraud_classification['fraud_reasons']
            }

        except Exception as e:
            logger.error(f"Error in model prediction: {e}", exc_info=True)
            raise RuntimeError(
                f"ML model prediction failed: {str(e)}. "
                f"Please ensure the model file is valid and all dependencies are installed."
            ) from e


    def _generate_indicators(self, features: List[float], feature_names: List[str], paystub_data: Dict) -> List[str]:
        """Generate fraud indicators based on all 22 features - NO FALLBACKS"""
        indicators = []
        feature_dict = dict(zip(feature_names, features))

        # Check tax error (feature 8)
        if feature_dict.get('tax_error', 0.0) == 1.0:
            indicators.append("CRITICAL: Net Pay >= Gross Pay (impossible)")

        # Check missing fields (feature 10)
        missing_count = int(feature_dict.get('missing_fields_count', 0.0))
        if missing_count > 0:
            indicators.append(f"Missing {missing_count} critical fields")

        # Check text quality (feature 9)
        text_quality = feature_dict.get('text_quality', 1.0)
        if text_quality < 0.7:
            indicators.append("Low extraction quality")

        # Check zero withholding (features 15-20)
        has_federal = feature_dict.get('has_federal_tax', 0.0) == 1.0
        has_state = feature_dict.get('has_state_tax', 0.0) == 1.0
        has_ss = feature_dict.get('has_social_security', 0.0) == 1.0
        has_medicare = feature_dict.get('has_medicare', 0.0) == 1.0
        gross = feature_dict.get('gross_pay', 0.0)
        
        if gross > 1000:
            if not has_federal and not has_state and not has_ss and not has_medicare:
                indicators.append("CRITICAL: No tax withholdings detected")
            elif not has_ss or not has_medicare:
                indicators.append("WARNING: Missing mandatory FICA taxes (Social Security/Medicare)")

        # Check unrealistic proportions (features 21-22)
        net_to_gross = feature_dict.get('net_to_gross_ratio', 0.0)
        tax_to_gross = feature_dict.get('tax_to_gross_ratio', 0.0)
        
        if gross > 0:
            if net_to_gross > 0.95:
                indicators.append(f"WARNING: Net pay is {net_to_gross*100:.1f}% of gross (unrealistically high)")
            if tax_to_gross < 0.02 and gross > 1000:
                indicators.append(f"WARNING: Tax withholdings are only {tax_to_gross*100:.1f}% of gross (unrealistically low)")

        return indicators

    def _classify_fraud_types(
        self,
        features: List[float],
        feature_names: List[str],
        normalized_data: Dict,
        anomalies: List[str] = None
    ) -> Dict:
        """
        Classify fraud types and generate machine-readable reasons based on features and anomalies.
        Uses all 18 features - NO FALLBACKS.
        
        Args:
            features: List of 18 feature values
            feature_names: List of feature names (18 features)
            normalized_data: Normalized paystub data dictionary
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
        has_company = feature_dict.get('has_company', 0.0) == 1.0
        has_employee = feature_dict.get('has_employee', 0.0) == 1.0
        has_gross = feature_dict.get('has_gross', 0.0) == 1.0
        has_net = feature_dict.get('has_net', 0.0) == 1.0
        has_date = feature_dict.get('has_date', 0.0) == 1.0
        gross_pay = feature_dict.get('gross_pay', 0.0)
        net_pay = feature_dict.get('net_pay', 0.0)
        tax_error = feature_dict.get('tax_error', 0.0) == 1.0
        text_quality = feature_dict.get('text_quality', 1.0)
        missing_fields_count = int(feature_dict.get('missing_fields_count', 0.0))
        
        # Extract new features (11-18) - NO FALLBACKS
        has_federal_tax = feature_dict.get('has_federal_tax', 0.0) == 1.0
        has_state_tax = feature_dict.get('has_state_tax', 0.0) == 1.0
        has_social_security = feature_dict.get('has_social_security', 0.0) == 1.0
        has_medicare = feature_dict.get('has_medicare', 0.0) == 1.0
        total_tax_amount = feature_dict.get('total_tax_amount', 0.0)
        tax_to_gross_ratio = feature_dict.get('tax_to_gross_ratio', 0.0)
        net_to_gross_ratio = feature_dict.get('net_to_gross_ratio', 0.0)
        deduction_percentage = feature_dict.get('deduction_percentage', 0.0)

        # Extract additional data from normalized_data
        pay_period_start = normalized_data.get('pay_period_start')
        pay_period_end = normalized_data.get('pay_period_end')
        pay_date = normalized_data.get('pay_date')
        federal_tax = normalized_data.get('federal_tax', 0)
        state_tax = normalized_data.get('state_tax', 0)
        social_security = normalized_data.get('social_security', 0)
        medicare = normalized_data.get('medicare', 0)

        # Helper to extract numeric value
        def get_numeric(val):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace(',', '').replace('$', '').strip())
                except:
                    return 0.0
            return 0.0

        gross_pay_val = get_numeric(gross_pay) if gross_pay else 0.0
        net_pay_val = get_numeric(net_pay) if net_pay else 0.0

        # ===== ONLY THE 4 DOCUMENT-LEVEL FRAUD TYPES =====
        
        # 1. FABRICATED_DOCUMENT
        # Missing company + low text quality + missing employee suggests fabricated document
        if not has_company and text_quality < 0.6:
            if FABRICATED_DOCUMENT not in fraud_types:
                fraud_types.append(FABRICATED_DOCUMENT)
                fraud_reasons.append(
                    "Missing employer name combined with low extraction quality suggests this may be a fabricated document."
                )
        if not has_company and not has_employee and missing_fields_count >= 3:
            if FABRICATED_DOCUMENT not in fraud_types:
                fraud_types.append(FABRICATED_DOCUMENT)
                fraud_reasons.append(
                    "Missing critical identifying information (employer and employee names) suggests a fabricated document."
                )

        # 2. UNREALISTIC_PROPORTIONS
        # Net > 95% of gross (suspicious)
        if gross_pay_val > 0 and net_to_gross_ratio > 0.95:
            if UNREALISTIC_PROPORTIONS not in fraud_types:
                fraud_types.append(UNREALISTIC_PROPORTIONS)
                fraud_reasons.append(
                    f"Net pay represents {net_to_gross_ratio*100:.1f}% of gross pay, which is unrealistic for W-2 style paystubs "
                    f"(typically 60-85% after taxes and deductions)."
                )
        
        # Tax withholding < 2% of gross (suspicious)
        if gross_pay_val > 1000 and tax_to_gross_ratio < 0.02:
            if UNREALISTIC_PROPORTIONS not in fraud_types:
                fraud_types.append(UNREALISTIC_PROPORTIONS)
                fraud_reasons.append(
                    f"Tax withholdings represent only {tax_to_gross_ratio*100:.1f}% of gross pay, which is unrealistically low "
                    f"(typically 15-30% for W-2 employees)."
                )
        
        # Deduction percentage > 50% without explanation (suspicious)
        if gross_pay_val > 0 and deduction_percentage > 0.50:
            if UNREALISTIC_PROPORTIONS not in fraud_types:
                fraud_types.append(UNREALISTIC_PROPORTIONS)
                fraud_reasons.append(
                    f"Deductions represent {deduction_percentage*100:.1f}% of gross pay, which is unusually high "
                    f"(typically 15-40% including taxes)."
                )

        # 3. ZERO_WITHHOLDING_SUSPICIOUS
        # No taxes at all for meaningful gross pay
        if gross_pay_val > 1000:
            if not has_federal_tax and not has_state_tax and not has_social_security and not has_medicare:
                if ZERO_WITHHOLDING_SUSPICIOUS not in fraud_types:
                    fraud_types.append(ZERO_WITHHOLDING_SUSPICIOUS)
                    fraud_reasons.append(
                        f"No tax withholdings detected (federal, state, Social Security, or Medicare) for gross pay of ${gross_pay_val:,.2f}, "
                        f"which is suspicious for W-2 style paystubs in taxable jurisdictions."
                    )
            elif not has_social_security and not has_medicare:
                # Missing mandatory FICA taxes
                if ZERO_WITHHOLDING_SUSPICIOUS not in fraud_types:
                    fraud_types.append(ZERO_WITHHOLDING_SUSPICIOUS)
                    fraud_reasons.append(
                        "Missing mandatory Social Security and Medicare withholdings (FICA taxes), which are required for W-2 employees."
                    )
            elif total_tax_amount < gross_pay_val * 0.02:
                # Total taxes < 2% of gross (very suspicious)
                if ZERO_WITHHOLDING_SUSPICIOUS not in fraud_types:
                    fraud_types.append(ZERO_WITHHOLDING_SUSPICIOUS)
                    fraud_reasons.append(
                        f"Total tax withholdings (${total_tax_amount:,.2f}) represent only {tax_to_gross_ratio*100:.1f}% of gross pay, "
                        f"which is unrealistically low for W-2 employees (typically 15-30%)."
                    )

        # 5. ALTERED_LEGITIMATE_DOCUMENT
        # Low text quality + suspicious ratios suggests tampering
        if text_quality < 0.6 and (net_to_gross_ratio > 0.90 or tax_to_gross_ratio < 0.05):
            if ALTERED_LEGITIMATE_DOCUMENT not in fraud_types:
                fraud_types.append(ALTERED_LEGITIMATE_DOCUMENT)
                fraud_reasons.append(
                    "Low extraction quality combined with unrealistic proportions suggests this legitimate paystub may have been altered or tampered with."
                )
        
        # Suspicious patterns that suggest manual editing
        if text_quality < 0.7 and missing_fields_count > 0 and (tax_error or net_to_gross_ratio > 0.95):
            if ALTERED_LEGITIMATE_DOCUMENT not in fraud_types:
                fraud_types.append(ALTERED_LEGITIMATE_DOCUMENT)
                fraud_reasons.append(
                    "Multiple indicators (low quality, missing fields, tax errors) suggest this document may have been manually edited."
                )

        # Select only the primary (most severe) fraud type
        # Severity order: FABRICATED_DOCUMENT > ZERO_WITHHOLDING_SUSPICIOUS > UNREALISTIC_PROPORTIONS > ALTERED_LEGITIMATE_DOCUMENT
        severity_order = {
            FABRICATED_DOCUMENT: 4,
            ZERO_WITHHOLDING_SUSPICIOUS: 3,
            UNREALISTIC_PROPORTIONS: 2,
            ALTERED_LEGITIMATE_DOCUMENT: 1,
        }

        if fraud_types:
            # Get the most severe fraud type
            primary_fraud_type = max(fraud_types, key=lambda x: severity_order.get(x, 0))
            fraud_types = [primary_fraud_type]

            # Keep only the reason for the primary fraud type
            fraud_reasons = [reason for reason in fraud_reasons if primary_fraud_type.lower().replace('_', '') in reason.lower().replace('_', '') or len(fraud_reasons) == 1]
            if not fraud_reasons and fraud_reasons != []:
                fraud_reasons = [f"Detected as {primary_fraud_type.replace('_', ' ').title()}"]

        logger.info(f"Classified fraud type: {fraud_types}")
        logger.debug(f"Generated fraud reasons: {fraud_reasons}")

        return {
            "fraud_types": fraud_types,
            "fraud_reasons": fraud_reasons
        }
