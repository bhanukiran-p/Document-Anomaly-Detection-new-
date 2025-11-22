"""
Fraud Detection Service - Model Inference and Integration

This module provides high-level API for fraud detection including:
- Transaction fraud detection
- Statement PDF validation
- Combined risk assessment
"""

import joblib
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from pdf_statement_validator import PDFStatementValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FraudRisk(Enum):
    """Fraud risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TransactionPrediction:
    """Transaction fraud prediction result."""
    transaction_id: str
    is_fraud_probability: float
    prediction: int  # 0 or 1
    risk_level: str
    model_used: str
    confidence: float


@dataclass
class PDFValidationResult:
    """PDF validation result."""
    pdf_path: str
    risk_score: float
    verdict: str
    suspicious_indicators: List[str]
    warnings: List[str]
    is_suspicious: bool


@dataclass
class FraudAssessment:
    """Combined fraud assessment result."""
    transaction_prediction: Optional[TransactionPrediction]
    pdf_validation: Optional[PDFValidationResult]
    combined_risk_score: float
    overall_verdict: str
    recommendation: str


class FraudDetectionService:
    """Service for fraud detection using trained models."""

    # Categorical columns
    CATEGORICAL_COLUMNS = [
        'customer_name',
        'bank_name',
        'merchant_name',
        'category'
    ]

    # Columns to drop
    DROP_COLUMNS = [
        'statement_id',
        'account_number',
        'transaction_id',
        'transaction_description',
        'transaction_date',
        'statement_start_date',
        'statement_end_date'
    ]

    def __init__(self, model_dir=None):
        """
        Initialize fraud detection service.

        Args:
            model_dir: Directory containing trained models
        """
        if model_dir is None:
            # Use absolute path based on current script location
            current_dir = Path(__file__).parent
            model_dir = current_dir / 'trained_models'

        self.model_dir = Path(model_dir)
        self.xgb_model = None
        self.rf_model = None
        self.label_encoders = None
        self.feature_names = None
        self._load_models()

    def _load_models(self):
        """Load trained models from disk."""
        try:
            xgb_path = self.model_dir / 'xgboost_model.pkl'
            rf_path = self.model_dir / 'random_forest_model.pkl'
            encoders_path = self.model_dir / 'label_encoders.pkl'

            if not xgb_path.exists() or not rf_path.exists():
                logger.warning(
                    f"Models not found in {self.model_dir}. "
                    "Please run train_fraud_models.py first."
                )
                return False

            self.xgb_model = joblib.load(xgb_path)
            self.rf_model = joblib.load(rf_path)
            self.label_encoders = joblib.load(encoders_path)

            # Store feature names from trained model
            try:
                self.feature_names = list(self.rf_model.feature_names_in_)
            except AttributeError:
                logger.warning("Could not extract feature names from model")

            logger.info("Models loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    def _preprocess_transaction(self, transaction_data: Dict) -> pd.DataFrame:
        """
        Preprocess transaction data for model inference.

        Args:
            transaction_data: Transaction record as dictionary

        Returns:
            pd.DataFrame: Preprocessed transaction data
        """
        df = pd.DataFrame([transaction_data])

        # Drop unnecessary columns
        df = df.drop(columns=[col for col in self.DROP_COLUMNS if col in df.columns])

        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().any():
                df[col].fillna(df[col].mean(), inplace=True)

        # Encode categorical variables
        for col in self.CATEGORICAL_COLUMNS:
            if col in df.columns and self.label_encoders and col in self.label_encoders:
                try:
                    le = self.label_encoders[col]
                    df[col] = le.transform(df[col].astype(str))
                except ValueError:
                    # Handle unknown categories
                    df[col] = le.transform([le.classes_[0]])[0]

        # Ensure all columns are numeric
        df = df.select_dtypes(include=[np.number])

        # Reorder columns to match the order used during model training
        if self.feature_names:
            # Only include columns that exist in the dataframe
            available_cols = [col for col in self.feature_names if col in df.columns]
            if available_cols:
                df = df[available_cols]

        return df

    def predict_transaction_fraud(
        self,
        transaction_data: Dict,
        model_type='ensemble'
    ) -> TransactionPrediction:
        """
        Predict fraud for a single transaction.

        Args:
            transaction_data: Transaction record
            model_type: 'xgboost', 'random_forest', or 'ensemble'

        Returns:
            TransactionPrediction: Prediction result
        """
        if not self.xgb_model or not self.rf_model:
            raise ValueError("Models not loaded. Please train models first.")

        X = self._preprocess_transaction(transaction_data)

        if model_type == 'xgboost':
            pred = self.xgb_model.predict(X)[0]
            prob = self.xgb_model.predict_proba(X)[0, 1]
            model_used = 'XGBoost'
        elif model_type == 'random_forest':
            pred = self.rf_model.predict(X)[0]
            prob = self.rf_model.predict_proba(X)[0, 1]
            model_used = 'Random Forest'
        else:  # ensemble
            xgb_prob = self.xgb_model.predict_proba(X)[0, 1]
            rf_prob = self.rf_model.predict_proba(X)[0, 1]
            prob = (xgb_prob + rf_prob) / 2
            pred = 1 if prob >= 0.5 else 0
            model_used = 'Ensemble'

        # Determine risk level
        if prob >= 0.8:
            risk_level = FraudRisk.CRITICAL.value
        elif prob >= 0.6:
            risk_level = FraudRisk.HIGH.value
        elif prob >= 0.4:
            risk_level = FraudRisk.MEDIUM.value
        else:
            risk_level = FraudRisk.LOW.value

        return TransactionPrediction(
            transaction_id=transaction_data.get('transaction_id', 'unknown'),
            is_fraud_probability=round(prob, 4),
            prediction=pred,
            risk_level=risk_level,
            model_used=model_used,
            confidence=round(abs(prob - 0.5) * 2, 4)  # 0 to 1, higher = more confident
        )

    def validate_statement_pdf(self, pdf_path: str, use_ml: bool = True) -> PDFValidationResult:
        """
        Validate a bank statement PDF using rule-based + ML models.

        Args:
            pdf_path: Path to PDF file
            use_ml: Whether to integrate ML model predictions (default: True)

        Returns:
            PDFValidationResult: Validation result
        """
        try:
            # First, run rule-based PDF validation
            validator = PDFStatementValidator(pdf_path)
            findings = validator.validate()
            rule_risk_score = findings['risk_score']

            # Try to extract transaction data and run ML models
            ml_risk_score = 0.0
            ml_predictions = None

            if use_ml and (self.xgb_model is not None and self.rf_model is not None):
                try:
                    # Extract transaction data from PDF text
                    extracted_transactions = self._extract_transactions_from_pdf(pdf_path)
                    logger.info(f"Extracted {len(extracted_transactions)} transactions from PDF")

                    if extracted_transactions:
                        # Convert list of transactions to DataFrame for batch prediction
                        transactions_df = pd.DataFrame(extracted_transactions)
                        logger.info(f"Created DataFrame with shape: {transactions_df.shape}")

                        # Run ML predictions on extracted transactions
                        ml_predictions = self.batch_predict(
                            transactions_df,
                            model_type='ensemble'
                        )
                        logger.info(f"ML predictions returned: {type(ml_predictions)}, shape: {ml_predictions.shape if hasattr(ml_predictions, 'shape') else 'N/A'}")

                        # Calculate average fraud probability from ML
                        if ml_predictions is not None and len(ml_predictions) > 0:
                            logger.info(f"ML predictions columns: {ml_predictions.columns.tolist()}")
                            # Extract fraud probabilities from predictions DataFrame
                            if 'is_fraud_probability' in ml_predictions.columns:
                                fraud_probs = ml_predictions['is_fraud_probability'].tolist()
                                logger.info(f"Fraud probabilities: {fraud_probs}")
                                if fraud_probs:
                                    ml_risk_score = sum(fraud_probs) / len(fraud_probs)
                                    ml_risk_score = min(ml_risk_score, 1.0)
                                    logger.info(f"ML risk score calculated: {ml_risk_score}")
                                    findings['suspicious_indicators'].append(
                                        f"[ML Model] Ensemble fraud probability: {ml_risk_score:.1%}"
                                    )
                            else:
                                logger.warning(f"'is_fraud_probability' column not found in predictions. Available columns: {ml_predictions.columns.tolist()}")
                        else:
                            logger.warning(f"ML predictions empty or None")
                    else:
                        logger.warning("No transactions extracted from PDF for ML analysis")
                except Exception as e:
                    logger.warning(f"ML model integration failed (continuing with rule-based only): {e}", exc_info=True)

            # Combine rule-based and ML scores (60% rule-based + 40% ML)
            combined_score = (rule_risk_score * 0.6) + (ml_risk_score * 0.4)

            # Update verdict based on combined score
            if combined_score >= 0.7:
                verdict = 'HIGH RISK - FRAUD DETECTED'
            elif combined_score >= 0.45:
                verdict = 'MEDIUM RISK - SUSPICIOUS ACTIVITY'
            elif combined_score >= 0.25:
                verdict = 'LOW RISK - MINOR CONCERNS'
            else:
                verdict = 'CLEAN'

            is_suspicious = verdict != 'CLEAN'

            return PDFValidationResult(
                pdf_path=pdf_path,
                risk_score=round(combined_score, 3),
                verdict=verdict,
                suspicious_indicators=findings.get('suspicious_indicators', []),
                warnings=findings.get('warnings', []),
                is_suspicious=is_suspicious
            )
        except Exception as e:
            logger.error(f"Error validating PDF: {e}")
            raise

    def _extract_transactions_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract transaction-like data from PDF text.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of transaction dictionaries
        """
        try:
            from pdf_statement_validator import PDFStatementValidator

            validator = PDFStatementValidator(pdf_path)
            validator.load_pdf()
            validator.extract_text()

            all_text = ' '.join(validator.text_content.values())

            # Extract financial information
            import re

            # Extract amounts - look for currency amounts with better pattern
            # Pattern: $ followed by optional comma-separated digits and decimal part
            amounts = re.findall(r'\$\s*(\d{1,3}(?:,\d{3}|\d)*(?:\.\d{2})?)', all_text)

            # Filter out values < 10 and convert to clean numbers
            amounts = []
            for match in re.finditer(r'\$\s*(\d{1,3}(?:,\d{3}|\d)*(?:\.\d{2})?)', all_text):
                try:
                    val = float(match.group(1).replace(',', ''))
                    if val > 10:
                        amounts.append(match.group(1))
                except:
                    pass

            # Try multiple date formats
            dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', all_text)  # MM/DD/YYYY
            if not dates:
                dates = re.findall(r'\d{1,2}/\d{1,2}(?=/|$)', all_text)  # MM/DD (without year)
            if not dates:
                dates = re.findall(r'\d{2}/\d{2}', all_text)  # MM/DD format

            # If we found dates or amounts, we can proceed (don't require both)
            if not amounts and not dates:
                logger.warning("No financial data found in PDF for ML analysis")
                return []

            # Create synthetic transaction records from extracted data
            transactions = []

            # Extract opening/ending balances with better pattern
            opening_balance = 5000.0  # Default
            ending_balance = 5000.0   # Default
            balance_match = re.search(r'(?:opening|beginning).*?\$\s*([\d,]+\.?\d*)', all_text, re.IGNORECASE)
            if balance_match:
                opening_balance = float(balance_match.group(1).replace(',', ''))

            balance_match = re.search(r'(?:ending|final).*?\$\s*([\d,]+\.?\d*)', all_text, re.IGNORECASE)
            if balance_match:
                ending_balance = float(balance_match.group(1).replace(',', ''))

            # Count transaction types
            total_amount = sum(float(a.replace('$', '').replace(',', '')) for a in amounts) if amounts else 0
            total_credits = total_amount * 0.5  # Estimate
            total_debits = total_amount * 0.5   # Estimate

            # Detect suspicious keywords for merchant categorization
            is_risky = any(kw in all_text.lower() for kw in
                          ['wire', 'crypto', 'casino', 'gambling', 'western union', 'offshore'])

            # Create a composite transaction record - only need amounts or dates, not both
            if amounts or dates:
                composite_transaction = {
                    'customer_name': 'Unknown',
                    'bank_name': 'Unknown Bank',
                    'merchant_name': 'Multiple Merchants',
                    'category': 'Risk' if is_risky else 'Retail',
                    'opening_balance': opening_balance,
                    'ending_balance': ending_balance,
                    'total_credits': total_credits,
                    'total_debits': total_debits,
                    'amount': sum(float(a.replace('$', '').replace(',', '')) for a in amounts) / max(len(amounts), 1),
                    'balance_after': ending_balance,
                    'is_credit': 1 if total_credits > total_debits else 0,
                    'is_debit': 1 if total_debits > total_credits else 0,
                    'abs_amount': abs(ending_balance - opening_balance),
                    'is_large_transaction': 1 if abs(ending_balance - opening_balance) > 10000 else 0,
                    'amount_to_balance_ratio': abs(ending_balance - opening_balance) / max(opening_balance, 1),
                    'transactions_past_1_day': len(dates),
                    'transactions_past_7_days': len(dates),
                    'cumulative_monthly_credits': total_credits,
                    'cumulative_monthly_debits': total_debits,
                    'is_new_merchant': 0,
                    'weekday': 2,
                    'day_of_month': 15,
                    'is_weekend': 0,
                    'transaction_id': 'PDF_EXTRACTED'
                }
                transactions.append(composite_transaction)

            return transactions
        except Exception as e:
            logger.warning(f"Failed to extract transactions from PDF: {e}")
            return []

    def assess_fraud_risk(
        self,
        transaction_data: Optional[Dict] = None,
        pdf_path: Optional[str] = None,
        model_type='ensemble'
    ) -> FraudAssessment:
        """
        Perform comprehensive fraud assessment.

        Args:
            transaction_data: Transaction record (optional)
            pdf_path: Path to statement PDF (optional)
            model_type: ML model type to use

        Returns:
            FraudAssessment: Combined assessment result
        """
        if not transaction_data and not pdf_path:
            raise ValueError("Provide either transaction_data or pdf_path")

        transaction_pred = None
        pdf_validation = None

        # Predict transaction fraud
        if transaction_data:
            transaction_pred = self.predict_transaction_fraud(transaction_data, model_type)

        # Validate PDF
        if pdf_path:
            pdf_validation = self.validate_statement_pdf(pdf_path)

        # Calculate combined risk score
        combined_risk = 0.0
        if transaction_pred and pdf_validation:
            # Weighted combination: 60% transaction, 40% PDF
            combined_risk = (
                transaction_pred.is_fraud_probability * 0.6 +
                pdf_validation.risk_score * 0.4
            )
        elif transaction_pred:
            combined_risk = transaction_pred.is_fraud_probability
        elif pdf_validation:
            combined_risk = pdf_validation.risk_score

        # Determine overall verdict
        if combined_risk >= 0.7:
            verdict = "HIGH RISK"
            recommendation = "BLOCK TRANSACTION - MANUAL REVIEW REQUIRED"
        elif combined_risk >= 0.5:
            verdict = "MEDIUM RISK"
            recommendation = "FLAG FOR REVIEW - ADDITIONAL VERIFICATION NEEDED"
        elif combined_risk >= 0.3:
            verdict = "LOW RISK"
            recommendation = "MONITOR - APPLY STANDARD CHECKS"
        else:
            verdict = "CLEAN"
            recommendation = "APPROVE TRANSACTION"

        return FraudAssessment(
            transaction_prediction=transaction_pred,
            pdf_validation=pdf_validation,
            combined_risk_score=round(combined_risk, 4),
            overall_verdict=verdict,
            recommendation=recommendation
        )

    def batch_predict(
        self,
        transactions_df: pd.DataFrame,
        model_type='ensemble'
    ) -> pd.DataFrame:
        """
        Predict fraud for multiple transactions.

        Args:
            transactions_df: DataFrame with transaction records
            model_type: ML model type to use

        Returns:
            pd.DataFrame: Original data with fraud predictions
        """
        predictions = []

        for idx, row in transactions_df.iterrows():
            try:
                pred = self.predict_transaction_fraud(row.to_dict(), model_type)
                pred_dict = asdict(pred)
                pred_dict['transaction_index'] = idx
                predictions.append(pred_dict)
            except Exception as e:
                logger.error(f"Error predicting transaction {idx}: {e}")
                predictions.append({
                    'transaction_index': idx,
                    'error': str(e)
                })

        pred_df = pd.DataFrame(predictions)
        return pd.concat([transactions_df.reset_index(drop=True), pred_df], axis=1)


# Singleton instance
_service_instance = None


def get_fraud_detection_service(model_dir=None) -> FraudDetectionService:
    """
    Get or create fraud detection service instance.

    Args:
        model_dir: Directory containing trained models (optional)

    Returns:
        FraudDetectionService: Service instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = FraudDetectionService(model_dir)
    return _service_instance


if __name__ == '__main__':
    import json

    # Example usage
    service = FraudDetectionService()

    # Example transaction (with all required features from training)
    sample_transaction = {
        'customer_name': 'John Doe',
        'bank_name': 'Chase',
        'merchant_name': 'Walmart',
        'category': 'Retail',
        'opening_balance': 5000.00,
        'ending_balance': 4850.00,
        'total_credits': 2000.00,
        'total_debits': 2150.00,
        'amount': 150.00,
        'balance_after': 4850.00,
        'is_credit': 0,
        'is_debit': 1,
        'abs_amount': 150.00,
        'is_large_transaction': 0,
        'amount_to_balance_ratio': 0.03,
        'transactions_past_1_day': 2,
        'transactions_past_7_days': 10,
        'cumulative_monthly_credits': 2000.00,
        'cumulative_monthly_debits': 2150.00,
        'is_new_merchant': 0,
        'weekday': 2,
        'day_of_month': 15,
        'is_weekend': 0,
        'transaction_id': 'TXN001'
    }

    print("=" * 60)
    print("TRANSACTION FRAUD PREDICTION")
    print("=" * 60)
    try:
        pred = service.predict_transaction_fraud(sample_transaction)
        print(json.dumps(asdict(pred), indent=2))
    except Exception as e:
        print(f"Error: {e}")
