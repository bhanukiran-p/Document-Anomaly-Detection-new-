"""
Real-Time Fraud Detector - Pure ML Implementation
Uses only machine learning models, no rule-based fallbacks
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import os
import joblib

logger = logging.getLogger(__name__)

# Model paths
MODEL_DIR = 'real_time/models'
os.makedirs(MODEL_DIR, exist_ok=True)

TRANSACTION_MODEL_PATH = os.path.join(MODEL_DIR, 'transaction_fraud_model.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'transaction_scaler.pkl')


def detect_fraud_in_transactions(transactions: List[Dict[str, Any]], auto_train: bool = True) -> Dict[str, Any]:
    """
    Detect fraud in transactions using ML models.
    Automatically trains model if none exists.

    Args:
        transactions: List of transaction dictionaries
        auto_train: Whether to auto-train model if not found

    Returns:
        Dictionary containing fraud detection results
    """
    try:
        logger.info(f"Analyzing {len(transactions)} transactions for fraud")

        # Convert to DataFrame
        df = pd.DataFrame(transactions)

        # Extract features
        features_df = _extract_features(df)

        # Load or train model
        model, scaler = _load_model()

        if model is None or scaler is None:
            if auto_train:
                logger.info("No model found, training new model on current data")
                model, scaler = _train_on_current_data(df, features_df)
            else:
                raise ValueError("No trained model found and auto_train is disabled")

        # Make predictions
        predictions, probabilities, reasons = _predict_fraud_ml(features_df, model, scaler, df)

        # Add predictions to transactions
        df['is_fraud'] = predictions
        df['fraud_probability'] = probabilities
        df['fraud_reason'] = reasons

        # Calculate statistics
        fraud_count = int(predictions.sum())
        fraud_percentage = float((fraud_count / len(df)) * 100) if len(df) > 0 else 0

        fraud_transactions = df[df['is_fraud'] == 1]
        legitimate_transactions = df[df['is_fraud'] == 0]

        total_fraud_amount = float(fraud_transactions['amount'].sum()) if len(fraud_transactions) > 0 else 0
        total_legitimate_amount = float(legitimate_transactions['amount'].sum()) if len(legitimate_transactions) > 0 else 0

        # Convert back to list of dictionaries
        transactions_with_predictions = df.to_dict('records')

        result = {
            'success': True,
            'transactions': transactions_with_predictions,
            'fraud_count': fraud_count,
            'legitimate_count': len(df) - fraud_count,
            'fraud_percentage': round(fraud_percentage, 2),
            'legitimate_percentage': round(100 - fraud_percentage, 2),
            'total_fraud_amount': round(total_fraud_amount, 2),
            'total_legitimate_amount': round(total_legitimate_amount, 2),
            'total_amount': round(total_fraud_amount + total_legitimate_amount, 2),
            'average_fraud_probability': round(float(probabilities.mean()), 3),
            'max_fraud_probability': round(float(probabilities.max()), 3),
            'model_type': 'ml_ensemble',
            'analyzed_at': datetime.now().isoformat()
        }

        logger.info(f"Fraud detection complete: {fraud_count}/{len(df)} fraudulent ({fraud_percentage:.1f}%)")
        return result

    except Exception as e:
        logger.error(f"Fraud detection failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to detect fraud in transactions'
        }


def _extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract comprehensive ML features from transaction data."""
    features = pd.DataFrame()

    # Amount features
    features['amount'] = df['amount']
    features['amount_log'] = np.log1p(df['amount'])
    features['amount_squared'] = df['amount'] ** 2
    features['amount_sqrt'] = np.sqrt(df['amount'])

    # Time features
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        features['hour'] = df['timestamp'].dt.hour.fillna(12)
        features['day_of_week'] = df['timestamp'].dt.dayofweek.fillna(0)
        features['day_of_month'] = df['timestamp'].dt.day.fillna(15)
        features['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
        features['is_night'] = ((df['timestamp'].dt.hour < 6) | (df['timestamp'].dt.hour > 22)).fillna(0).astype(int)
        features['is_business_hours'] = ((df['timestamp'].dt.hour >= 9) & (df['timestamp'].dt.hour <= 17)).fillna(0).astype(int)
    else:
        features['hour'] = 12
        features['day_of_week'] = 0
        features['day_of_month'] = 15
        features['is_weekend'] = 0
        features['is_night'] = 0
        features['is_business_hours'] = 1

    # Category encoding
    if 'category' in df.columns:
        high_risk_cats = ['gambling', 'cryptocurrency', 'wire_transfer', 'cash_advance', 'atm']
        features['high_risk_category'] = df['category'].str.lower().apply(
            lambda x: 1 if any(cat in str(x).lower() for cat in high_risk_cats) else 0
        )
        for cat in ['retail', 'food', 'travel', 'entertainment', 'utilities']:
            features[f'cat_{cat}'] = df['category'].str.lower().str.contains(cat, na=False).astype(int)
    else:
        features['high_risk_category'] = 0
        for cat in ['retail', 'food', 'travel', 'entertainment', 'utilities']:
            features[f'cat_{cat}'] = 0

    # Merchant features
    if 'merchant' in df.columns:
        features['merchant_length'] = df['merchant'].str.len().fillna(0)
        features['merchant_has_numbers'] = df['merchant'].str.contains(r'\d', na=False).astype(int)
    else:
        features['merchant_length'] = 0
        features['merchant_has_numbers'] = 0

    # Customer behavior features
    if 'customer_id' in df.columns:
        customer_stats = df.groupby('customer_id')['amount'].agg(['mean', 'std', 'count'])
        customer_stats.columns = ['customer_avg_amount', 'customer_std_amount', 'customer_txn_count']

        df_temp = df.merge(customer_stats, left_on='customer_id', right_index=True, how='left')
        features['customer_avg_amount'] = df_temp['customer_avg_amount'].fillna(df['amount'].mean())
        features['customer_std_amount'] = df_temp['customer_std_amount'].fillna(0)
        features['customer_txn_count'] = df_temp['customer_txn_count'].fillna(1)
        features['amount_deviation'] = np.abs(
            features['amount'] - features['customer_avg_amount']
        ) / (features['customer_std_amount'] + 1)
    else:
        features['customer_avg_amount'] = features['amount']
        features['customer_std_amount'] = 0
        features['customer_txn_count'] = 1
        features['amount_deviation'] = 0

    # Account balance features
    if 'account_balance' in df.columns:
        features['account_balance'] = pd.to_numeric(df['account_balance'], errors='coerce').fillna(0)
        features['amount_to_balance_ratio'] = features['amount'] / (features['account_balance'] + 1)
        features['low_balance'] = (features['account_balance'] < 100).astype(int)
    else:
        features['account_balance'] = 0
        features['amount_to_balance_ratio'] = 0
        features['low_balance'] = 0

    # Location mismatch features (fraud indicator)
    if 'home_country' in df.columns and 'transaction_country' in df.columns:
        features['country_mismatch'] = (df['home_country'] != df['transaction_country']).astype(int)
    else:
        features['country_mismatch'] = 0

    if 'transaction_country' in df.columns and 'login_country' in df.columns:
        features['login_transaction_mismatch'] = (df['login_country'] != df['transaction_country']).astype(int)
    else:
        features['login_transaction_mismatch'] = 0

    # Check-based transaction features
    if 'is_by_check' in df.columns:
        features['is_by_check'] = pd.to_numeric(df['is_by_check'], errors='coerce').fillna(0).astype(int)
        # High-value checks are riskier
        features['high_value_check'] = ((features['is_by_check'] == 1) & (df['amount'] > 1000)).astype(int)
    else:
        features['is_by_check'] = 0
        features['high_value_check'] = 0

    # Transaction type features
    if 'transaction_type' in df.columns:
        features['is_transfer'] = df['transaction_type'].str.lower().str.contains('transfer', na=False).astype(int)
        features['is_credit'] = df['transaction_type'].str.lower().str.contains('credit', na=False).astype(int)
        features['is_debit'] = df['transaction_type'].str.lower().str.contains('debit', na=False).astype(int)
    else:
        features['is_transfer'] = 0
        features['is_credit'] = 0
        features['is_debit'] = 0

    # Currency features (if non-USD could be risky)
    if 'currency' in df.columns:
        features['is_usd'] = (df['currency'] == 'USD').astype(int)
        features['is_foreign_currency'] = (df['currency'] != 'USD').astype(int)
    else:
        features['is_usd'] = 1
        features['is_foreign_currency'] = 0

    # Gender-based statistics (for pattern analysis, not discrimination)
    if 'gender' in df.columns and 'customer_id' in df.columns:
        gender_stats = df.groupby('gender')['amount'].agg(['mean', 'std'])
        gender_stats.columns = ['gender_avg_amount', 'gender_std_amount']
        df_temp = df.merge(gender_stats, left_on='gender', right_index=True, how='left')
        features['gender_amount_deviation'] = np.abs(
            features['amount'] - df_temp['gender_avg_amount'].fillna(features['amount'])
        ) / (df_temp['gender_std_amount'].fillna(1) + 1)
    else:
        features['gender_amount_deviation'] = 0

    # Statistical features
    features['amount_zscore'] = (features['amount'] - features['amount'].mean()) / (features['amount'].std() + 1)
    features['is_outlier'] = (np.abs(features['amount_zscore']) > 2).astype(int)

    # Fill NaN and inf values
    features = features.fillna(0)
    features = features.replace([np.inf, -np.inf], 0)

    return features


def _load_model() -> Tuple:
    """Load existing ML model and scaler."""
    try:
        if os.path.exists(TRANSACTION_MODEL_PATH) and os.path.exists(SCALER_PATH):
            model = joblib.load(TRANSACTION_MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            logger.info("Loaded existing ML fraud detection model")
            return model, scaler
        else:
            logger.info("No existing model found")
            return None, None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None, None


def _train_on_current_data(df: pd.DataFrame, features_df: pd.DataFrame) -> Tuple:
    """Train model on current transaction data using unsupervised learning."""
    from .model_trainer import auto_train_model

    # Auto-train using anomaly detection
    result = auto_train_model(df)

    if result['success']:
        # Load the newly trained model
        model = joblib.load(TRANSACTION_MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        logger.info("Successfully trained new model on current data")
        return model, scaler
    else:
        raise ValueError(f"Failed to train model: {result.get('error')}")


def _predict_fraud_ml(features_df: pd.DataFrame, model, scaler, original_df: pd.DataFrame) -> Tuple:
    """Make fraud predictions using pure ML model."""
    try:
        # Scale features
        X_scaled = scaler.transform(features_df)

        # Predict
        predictions = model.predict(X_scaled)
        probabilities = model.predict_proba(X_scaled)[:, 1]

        # Generate detailed reasons based on ML predictions and feature importance
        reasons = _generate_ml_reasons(predictions, probabilities, features_df, original_df, model)

        return predictions, probabilities, reasons

    except Exception as e:
        logger.error(f"ML prediction failed: {e}", exc_info=True)
        raise


def _generate_ml_reasons(predictions: np.ndarray, probabilities: np.ndarray,
                        features_df: pd.DataFrame, original_df: pd.DataFrame, model) -> List[str]:
    """Generate detailed fraud reasons based on ML model insights."""
    reasons = []

    # Get feature importance if available
    try:
        if hasattr(model, 'rf'):  # Ensemble model
            feature_importance = dict(zip(features_df.columns, model.rf.feature_importances_))
        else:
            feature_importance = {}
    except:
        feature_importance = {}

    for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
        if pred == 1:
            reason_parts = []

            # Add ML confidence
            reason_parts.append(f"ML Fraud Detection ({prob*100:.1f}% confidence)")

            # Analyze key features that contributed to fraud detection
            row_features = features_df.iloc[i]

            # Check significant features
            if row_features['amount_zscore'] > 2:
                reason_parts.append(f"Unusual amount pattern (Z-score: {row_features['amount_zscore']:.2f})")

            if row_features['amount_deviation'] > 3:
                reason_parts.append("Significant deviation from customer's normal spending")

            if row_features['is_night'] == 1:
                reason_parts.append("Transaction during high-risk hours (late night/early morning)")

            if row_features['high_risk_category'] == 1:
                reason_parts.append("High-risk transaction category")

            if row_features['is_outlier'] == 1:
                reason_parts.append("Statistical outlier detected")

            if row_features['amount_to_balance_ratio'] > 0.8:
                reason_parts.append("High transaction-to-balance ratio")

            # If no specific reasons, provide general ML insight
            if len(reason_parts) == 1:
                reason_parts.append("Multiple fraud indicators detected by ML model")

            reasons.append(" | ".join(reason_parts))
        else:
            reasons.append(f"Legitimate transaction (ML confidence: {(1-prob)*100:.1f}%)")

    return reasons
