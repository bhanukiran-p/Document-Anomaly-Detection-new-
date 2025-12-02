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

# Fraud Type Taxonomy
PAY_AMOUNT_TAMPERING = "PAY_AMOUNT_TAMPERING"
MISSING_CRITICAL_FIELDS = "MISSING_CRITICAL_FIELDS"
TEMPORAL_INCONSISTENCY = "TEMPORAL_INCONSISTENCY"
TAX_WITHHOLDING_ANOMALY = "TAX_WITHHOLDING_ANOMALY"
YTD_INCONSISTENCY = "YTD_INCONSISTENCY"
BASIC_DATA_QUALITY_ISSUE = "BASIC_DATA_QUALITY_ISSUE"

# Human-readable labels (optional, for UI display)
FRAUD_TYPE_LABELS = {
    PAY_AMOUNT_TAMPERING: "Pay amount tampering / inconsistent pay amounts",
    MISSING_CRITICAL_FIELDS: "Missing critical paystub information",
    TEMPORAL_INCONSISTENCY: "Date or pay period inconsistency",
    TAX_WITHHOLDING_ANOMALY: "Tax withholdings missing or abnormal",
    YTD_INCONSISTENCY: "Year-to-date amounts inconsistent with current period",
    BASIC_DATA_QUALITY_ISSUE: "General data quality or OCR extraction quality issues",
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
            logger.warning(f"Model not found at: {self.model_path} (will use heuristic fallback)")

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
                logger.warning(f"Random Forest model not found at {self.model_path}, using heuristic scoring")
                self.model = None

            # Load scaler
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded feature scaler for paystubs")
            else:
                logger.warning(f"Feature scaler not found at {self.scaler_path}")
                self.scaler = None

            self.models_loaded = (self.model is not None)

        except ImportError:
            logger.warning("joblib not available, using heuristic scoring")
            self.model = None
            self.scaler = None
            self.models_loaded = False
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.model = None
            self.scaler = None
            self.models_loaded = False

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

        # If models are loaded, use them
        if self.models_loaded:
            return self._predict_with_model(features, feature_names, paystub_data)
        else:
            # Use heuristic scoring as fallback
            return self._predict_heuristic(features, feature_names, paystub_data)

    def _predict_with_model(self, features: List[float], feature_names: List[str], paystub_data: Dict) -> Dict:
        """Predict using trained model"""
        try:
            # Convert to numpy array
            X = np.array([features])

            # Scale features if scaler available
            if self.scaler:
                X = self.scaler.transform(X)

            # Get prediction from model
            if self.model:
                # Model predicts risk score (0-100), convert to 0-1
                risk_score_raw = self.model.predict(X)[0]
                fraud_risk_score = min(1.0, max(0.0, risk_score_raw / 100.0))  # Convert 0-100 to 0-1
                
                # Get feature importance if available
                feature_importance = []
                if hasattr(self.model, 'feature_importances_'):
                    importances = self.model.feature_importances_
                    # Get top 3 most important features
                    top_indices = np.argsort(importances)[-3:][::-1]
                    for idx in top_indices:
                        if importances[idx] > 0:
                            feature_importance.append(f"{feature_names[idx]}: {importances[idx]:.3f}")
            else:
                fraud_risk_score = 0.5
                feature_importance = []

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
            # Fallback to heuristic
            return self._predict_heuristic(features, feature_names, paystub_data)

    def _predict_heuristic(self, features: List[float], feature_names: List[str], paystub_data: Dict) -> Dict:
        """Fallback heuristic prediction when model not available"""
        risk_score = 0.0
        indicators = []
        
        # Unpack features
        has_company = features[0]
        has_employee = features[1]
        has_gross = features[2]
        has_net = features[3]
        has_date = features[4]
        gross_pay = features[5]
        net_pay = features[6]
        tax_error = features[7]
        text_quality = features[8]
        missing_fields = features[9]

        # Rule 1: Tax error (net >= gross) - CRITICAL
        if tax_error == 1.0:
            risk_score += 0.5
            indicators.append("CRITICAL: Net Pay is greater than or equal to Gross Pay")

        # Rule 2: Missing critical fields
        if missing_fields > 0:
            risk_score += (missing_fields * 0.1)
            indicators.append(f"Missing {int(missing_fields)} critical fields")
            
        # Rule 3: Low text quality
        if text_quality < 0.7:
            risk_score += 0.2
            indicators.append("Low text quality - incomplete extraction")

        # Rule 4: Missing company or employee
        if has_company == 0.0:
            risk_score += 0.15
            indicators.append("Company name missing")
        if has_employee == 0.0:
            risk_score += 0.15
            indicators.append("Employee name missing")
            
        # Cap score
        risk_score = min(1.0, risk_score)
        
        # Determine level
        if risk_score < 0.3:
            risk_level = 'LOW'
        elif risk_score < 0.7:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
            
        # Classify fraud types and generate machine reasons
        fraud_classification = self._classify_fraud_types(features, feature_names, paystub_data, indicators)

        return {
            'fraud_risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'model_confidence': 0.75,  # Lower confidence for heuristic
            'model_scores': {
                'heuristic': round(risk_score, 2)
            },
            'feature_importance': indicators,
            'anomalies': indicators,
            'fraud_types': fraud_classification['fraud_types'],
            'fraud_reasons': fraud_classification['fraud_reasons']
        }

    def _generate_indicators(self, features: List[float], feature_names: List[str], paystub_data: Dict) -> List[str]:
        """Generate fraud indicators based on features"""
        indicators = []

        # Check tax error
        if features[7] == 1.0:  # tax_error
            indicators.append("CRITICAL: Net Pay >= Gross Pay (impossible)")

        # Check missing fields
        missing_count = int(features[9])  # missing_fields_count
        if missing_count > 0:
            indicators.append(f"Missing {missing_count} critical fields")

        # Check text quality
        text_quality = features[8]
        if text_quality < 0.7:
            indicators.append("Low extraction quality")

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
        
        Args:
            features: List of 10 feature values
            feature_names: List of feature names
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
        
        # Extract feature values with safe defaults
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

        # Extract additional data from normalized_data
        pay_period_start = normalized_data.get('pay_period_start')
        pay_period_end = normalized_data.get('pay_period_end')
        pay_date = normalized_data.get('pay_date')
        ytd_gross = normalized_data.get('ytd_gross', 0)
        ytd_net = normalized_data.get('ytd_net', 0)
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
        ytd_gross_val = get_numeric(ytd_gross) if ytd_gross else 0.0
        ytd_net_val = get_numeric(ytd_net) if ytd_net else 0.0

        # 1. PAY_AMOUNT_TAMPERING
        if tax_error or (gross_pay_val > 0 and net_pay_val >= gross_pay_val):
            if PAY_AMOUNT_TAMPERING not in fraud_types:
                fraud_types.append(PAY_AMOUNT_TAMPERING)
                fraud_reasons.append(
                    "Net pay is greater than or equal to gross pay, which is not possible on a valid paystub."
                )
        
        # Check for unusually high net-to-gross ratio (suspicious)
        if gross_pay_val > 0 and net_pay_val > 0:
            net_to_gross_ratio = net_pay_val / gross_pay_val
            if net_to_gross_ratio > 0.95 and not tax_error:
                if PAY_AMOUNT_TAMPERING not in fraud_types:
                    fraud_types.append(PAY_AMOUNT_TAMPERING)
                    fraud_reasons.append(
                        f"Net pay (${net_pay_val:,.2f}) is unusually close to gross pay (${gross_pay_val:,.2f}), "
                        f"suggesting taxes or deductions may have been removed or tampered with."
                    )

        # 2. TAX_WITHHOLDING_ANOMALY
        # Check if no taxes detected but should have them
        has_any_tax = (federal_tax and get_numeric(federal_tax) > 0) or \
                     (state_tax and get_numeric(state_tax) > 0) or \
                     (social_security and get_numeric(social_security) > 0) or \
                     (medicare and get_numeric(medicare) > 0)
        
        # Check anomalies for tax-related issues
        tax_anomaly_detected = any(
            'tax' in str(anom).lower() or 'withholding' in str(anom).lower() or 'no tax' in str(anom).lower()
            for anom in anomalies
        )
        
        if (gross_pay_val > 1000 and not has_any_tax) or tax_anomaly_detected:
            if TAX_WITHHOLDING_ANOMALY not in fraud_types:
                fraud_types.append(TAX_WITHHOLDING_ANOMALY)
                fraud_reasons.append(
                    "No tax withholdings were detected even though a normal salary paystub is expected to include taxes."
                )

        # 3. MISSING_CRITICAL_FIELDS
        missing_fields_list = []
        if not has_company:
            missing_fields_list.append("employer name")
        if not has_employee:
            missing_fields_list.append("employee name")
        if not has_gross:
            missing_fields_list.append("gross pay")
        if not has_net:
            missing_fields_list.append("net pay")
        if not has_date:
            missing_fields_list.append("pay period dates")
        
        if missing_fields_count > 0 or missing_fields_list:
            if MISSING_CRITICAL_FIELDS not in fraud_types:
                fraud_types.append(MISSING_CRITICAL_FIELDS)
                if missing_fields_list:
                    fraud_reasons.append(
                        f"Missing critical fields: {', '.join(missing_fields_list)}."
                    )
                else:
                    fraud_reasons.append(
                        f"Missing {missing_fields_count} critical field(s) required for paystub verification."
                    )

        # 4. TEMPORAL_INCONSISTENCY
        # Check for future dates
        pay_date_in_future = False
        pay_period_in_future = False
        date_order_invalid = False
        
        try:
            today = datetime.now().date()
            
            # Check pay_date
            if pay_date:
                try:
                    if isinstance(pay_date, str):
                        # Try common date formats
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                            try:
                                pay_date_obj = datetime.strptime(pay_date, fmt).date()
                                if pay_date_obj > today:
                                    pay_date_in_future = True
                                break
                            except:
                                continue
                    elif hasattr(pay_date, 'date'):
                        if pay_date.date() > today:
                            pay_date_in_future = True
                except:
                    pass
            
            # Check pay_period_end
            if pay_period_end:
                try:
                    if isinstance(pay_period_end, str):
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                            try:
                                period_end_obj = datetime.strptime(pay_period_end, fmt).date()
                                if period_end_obj > today:
                                    pay_period_in_future = True
                                break
                            except:
                                continue
                    elif hasattr(pay_period_end, 'date'):
                        if pay_period_end.date() > today:
                            pay_period_in_future = True
                except:
                    pass
            
            # Check date order (start should be before end)
            if pay_period_start and pay_period_end:
                try:
                    start_str = str(pay_period_start)
                    end_str = str(pay_period_end)
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                        try:
                            start_obj = datetime.strptime(start_str, fmt).date()
                            end_obj = datetime.strptime(end_str, fmt).date()
                            if start_obj > end_obj:
                                date_order_invalid = True
                            break
                        except:
                            continue
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error checking temporal consistency: {e}")

        if pay_date_in_future or pay_period_in_future:
            if TEMPORAL_INCONSISTENCY not in fraud_types:
                fraud_types.append(TEMPORAL_INCONSISTENCY)
                fraud_reasons.append(
                    "Pay date or pay period appears to be in the future relative to the analysis date."
                )
        
        if date_order_invalid:
            if TEMPORAL_INCONSISTENCY not in fraud_types:
                fraud_types.append(TEMPORAL_INCONSISTENCY)
                fraud_reasons.append(
                    "Pay period start and end dates are inconsistent or out of order."
                )

        # 5. YTD_INCONSISTENCY
        # Check if YTD is lower than current period (should be cumulative)
        if gross_pay_val > 0 and ytd_gross_val > 0:
            if ytd_gross_val < gross_pay_val:
                if YTD_INCONSISTENCY not in fraud_types:
                    fraud_types.append(YTD_INCONSISTENCY)
                    fraud_reasons.append(
                        f"Year-to-date gross pay (${ytd_gross_val:,.2f}) is lower than current period gross pay "
                        f"(${gross_pay_val:,.2f}), which is inconsistent as YTD should be cumulative."
                    )
        
        if net_pay_val > 0 and ytd_net_val > 0:
            if ytd_net_val < net_pay_val:
                if YTD_INCONSISTENCY not in fraud_types:
                    fraud_types.append(YTD_INCONSISTENCY)
                    fraud_reasons.append(
                        f"Year-to-date net pay (${ytd_net_val:,.2f}) is lower than current period net pay "
                        f"(${net_pay_val:,.2f}), which is inconsistent as YTD should be cumulative."
                    )

        # 6. BASIC_DATA_QUALITY_ISSUE
        if text_quality < 0.7:
            if BASIC_DATA_QUALITY_ISSUE not in fraud_types:
                fraud_types.append(BASIC_DATA_QUALITY_ISSUE)
                fraud_reasons.append(
                    "Overall text extraction quality is low, which makes the paystub hard to verify reliably."
                )
        
        # Check anomalies for OCR/extraction issues
        ocr_anomaly_detected = any(
            'ocr' in str(anom).lower() or 'extraction' in str(anom).lower() or 'quality' in str(anom).lower()
            for anom in anomalies
        )
        
        if ocr_anomaly_detected and BASIC_DATA_QUALITY_ISSUE not in fraud_types:
            fraud_types.append(BASIC_DATA_QUALITY_ISSUE)
            fraud_reasons.append(
                "The paystub has OCR or extraction issues reported by the system."
            )

        # Deduplicate fraud_types and fraud_reasons
        fraud_types = list(dict.fromkeys(fraud_types))  # Preserve order, remove duplicates
        fraud_reasons = list(dict.fromkeys(fraud_reasons))  # Preserve order, remove duplicates

        logger.info(f"Classified fraud types: {fraud_types}")
        logger.debug(f"Generated fraud reasons: {fraud_reasons}")

        return {
            "fraud_types": fraud_types,
            "fraud_reasons": fraud_reasons
        }
