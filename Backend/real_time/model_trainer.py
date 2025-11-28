"""
Automatic ML Model Trainer for Transaction Fraud Detection
Uses ensemble of Random Forest and XGBoost with automatic retraining
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
import os
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_fscore_support

logger = logging.getLogger(__name__)

# Model paths
MODEL_DIR = 'real_time/models'
os.makedirs(MODEL_DIR, exist_ok=True)

TRANSACTION_MODEL_PATH = os.path.join(MODEL_DIR, 'transaction_fraud_model.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'transaction_scaler.pkl')
TRAINING_DATA_PATH = os.path.join(MODEL_DIR, 'training_data.csv')
MODEL_METADATA_PATH = os.path.join(MODEL_DIR, 'model_metadata.json')


# Define EnsembleModel at module level so it can be pickled
class EnsembleModel:
    """Ensemble model combining Random Forest and Gradient Boosting"""
    def __init__(self, rf, gb):
        self.rf = rf
        self.gb = gb

    def predict(self, X):
        rf_pred = self.rf.predict(X)
        gb_pred = self.gb.predict(X)
        # Majority voting
        return ((rf_pred + gb_pred) >= 1).astype(int)

    def predict_proba(self, X):
        rf_proba = self.rf.predict_proba(X)
        gb_proba = self.gb.predict_proba(X)
        # Weighted average (60% RF, 40% GB)
        ensemble_proba = 0.6 * rf_proba + 0.4 * gb_proba
        return ensemble_proba


def auto_train_model(transactions_df: pd.DataFrame, labels: np.ndarray = None) -> Dict[str, Any]:
    """
    Automatically train fraud detection model on new data.
    If labels are not provided, uses intelligent labeling based on anomaly patterns.

    Args:
        transactions_df: DataFrame with transaction data
        labels: Optional fraud labels (1 = fraud, 0 = legitimate)

    Returns:
        Training results dictionary
    """
    try:
        logger.info(f"Starting automatic model training with {len(transactions_df)} transactions")

        # Check if dataset has 'is_fraud' column with actual labels
        if labels is None and 'is_fraud' in transactions_df.columns:
            labels = transactions_df['is_fraud'].values
            logger.info(f"Using existing fraud labels from dataset: {labels.sum()} fraud, {len(labels) - labels.sum()} legitimate")
        # If no labels provided and no is_fraud column, generate labels using unsupervised anomaly detection
        elif labels is None:
            labels = _generate_labels_from_anomalies(transactions_df)
            logger.info(f"Generated labels using anomaly detection: {labels.sum()} fraud, {len(labels) - labels.sum()} legitimate")

        # Extract features
        features_df = _extract_training_features(transactions_df)

        # Check if we have enough data
        if len(features_df) < 10:
            logger.warning("Insufficient data for training (need at least 10 transactions)")
            return {
                'success': False,
                'error': 'Insufficient training data',
                'message': 'Need at least 10 transactions to train model'
            }

        # Check class balance
        fraud_ratio = labels.sum() / len(labels)
        if fraud_ratio < 0.01 or fraud_ratio > 0.99:
            logger.warning(f"Imbalanced dataset: {fraud_ratio*100:.1f}% fraud")

        # Train model
        model, scaler, metrics = train_fraud_model(features_df, labels)

        # Save training data for incremental learning
        _save_training_data(transactions_df, labels)

        # Save metadata
        _save_model_metadata(metrics, len(transactions_df))

        result = {
            'success': True,
            'model_path': TRANSACTION_MODEL_PATH,
            'scaler_path': SCALER_PATH,
            'metrics': metrics,
            'training_samples': len(transactions_df),
            'fraud_samples': int(labels.sum()),
            'legitimate_samples': int(len(labels) - labels.sum()),
            'trained_at': datetime.now().isoformat()
        }

        logger.info(f"Model training complete. AUC: {metrics.get('auc', 0):.3f}")
        return result

    except Exception as e:
        logger.error(f"Model training failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to train fraud detection model'
        }


def train_fraud_model(features_df: pd.DataFrame, labels: np.ndarray) -> Tuple:
    """
    Train ensemble fraud detection model.

    Args:
        features_df: Feature DataFrame
        labels: Fraud labels

    Returns:
        Tuple of (model, scaler, metrics)
    """
    # Split data
    # Use stratify only if we have enough samples per class
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            features_df, labels, test_size=0.2, random_state=42, stratify=labels
        )
    except ValueError:
        # Fall back to non-stratified split for small datasets
        logger.warning("Using non-stratified split due to small dataset")
        X_train, X_test, y_train, y_test = train_test_split(
            features_df, labels, test_size=0.2, random_state=42
        )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Adjust model parameters based on dataset size
    n_samples = len(X_train)

    # For larger datasets, use more estimators and deeper trees
    if n_samples > 5000:
        n_estimators = 200
        max_depth_rf = 15
        max_depth_gb = 8
    elif n_samples > 1000:
        n_estimators = 150
        max_depth_rf = 12
        max_depth_gb = 6
    else:
        n_estimators = 100
        max_depth_rf = 10
        max_depth_gb = 5

    logger.info(f"Training with {n_estimators} estimators for {n_samples} samples")

    # Train Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth_rf,
        min_samples_split=min(10, max(2, n_samples // 100)),
        min_samples_leaf=min(5, max(1, n_samples // 200)),
        random_state=42,
        class_weight='balanced',
        n_jobs=-1,
        max_features='sqrt'
    )
    rf_model.fit(X_train_scaled, y_train)

    # Train Gradient Boosting
    gb_model = GradientBoostingClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth_gb,
        learning_rate=0.1,
        min_samples_split=min(10, max(2, n_samples // 100)),
        min_samples_leaf=min(5, max(1, n_samples // 200)),
        random_state=42,
        subsample=0.8
    )
    gb_model.fit(X_train_scaled, y_train)

    # Create ensemble using module-level class
    ensemble = EnsembleModel(rf_model, gb_model)

    # Evaluate
    y_pred = ensemble.predict(X_test_scaled)
    y_proba = ensemble.predict_proba(X_test_scaled)[:, 1]

    # Calculate metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average='binary', zero_division=0
    )

    try:
        auc = roc_auc_score(y_test, y_proba)
    except:
        auc = 0.5

    metrics = {
        'accuracy': float((y_pred == y_test).mean()),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'auc': float(auc),
        'feature_importance': dict(zip(
            features_df.columns,
            rf_model.feature_importances_.tolist()
        ))
    }

    # Save model and scaler
    joblib.dump(ensemble, TRANSACTION_MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    logger.info(f"Model trained - Accuracy: {metrics['accuracy']:.3f}, AUC: {metrics['auc']:.3f}")

    return ensemble, scaler, metrics


def _extract_training_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract comprehensive features for ML training."""
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
        # Category diversity (one-hot encoding for common categories)
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
        # Calculate per-customer statistics
        customer_stats = df.groupby('customer_id')['amount'].agg(['mean', 'std', 'count'])
        customer_stats.columns = ['customer_avg_amount', 'customer_std_amount', 'customer_txn_count']

        df_temp = df.merge(customer_stats, left_on='customer_id', right_index=True, how='left')
        features['customer_avg_amount'] = df_temp['customer_avg_amount'].fillna(df['amount'].mean())
        features['customer_std_amount'] = df_temp['customer_std_amount'].fillna(0)
        features['customer_txn_count'] = df_temp['customer_txn_count'].fillna(1)

        # Deviation from customer's normal behavior
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

    # Fill any remaining NaN values
    features = features.fillna(0)

    # Replace inf values
    features = features.replace([np.inf, -np.inf], 0)

    return features


def _generate_labels_from_anomalies(df: pd.DataFrame) -> np.ndarray:
    """
    Generate fraud labels using unsupervised anomaly detection.
    Uses Isolation Forest for anomaly detection with adaptive contamination rate.
    """
    from sklearn.ensemble import IsolationForest

    # Extract features
    features_df = _extract_training_features(df)

    # Adaptive contamination rate based on dataset analysis
    # Analyze the data to estimate fraud rate
    n_samples = len(features_df)

    # Use statistical analysis to estimate contamination
    # Look for outliers in amount and other key features
    amount_zscore = np.abs((features_df['amount'] - features_df['amount'].mean()) / (features_df['amount'].std() + 1))
    potential_outliers = (amount_zscore > 2.5).sum()
    estimated_contamination = min(0.3, max(0.05, potential_outliers / n_samples))

    logger.info(f"Using adaptive contamination rate: {estimated_contamination:.3f} for {n_samples} transactions")

    # Adjust n_estimators based on dataset size
    if n_samples > 5000:
        n_estimators_iso = 200
    elif n_samples > 1000:
        n_estimators_iso = 150
    else:
        n_estimators_iso = 100

    # Train Isolation Forest
    iso_forest = IsolationForest(
        contamination=estimated_contamination,
        n_estimators=n_estimators_iso,
        max_samples=min(256, n_samples),
        random_state=42,
        n_jobs=-1
    )

    # Predict anomalies (-1 = anomaly, 1 = normal)
    anomaly_predictions = iso_forest.fit_predict(features_df)

    # Convert to fraud labels (1 = fraud, 0 = normal)
    fraud_labels = (anomaly_predictions == -1).astype(int)

    fraud_count = fraud_labels.sum()
    fraud_percentage = (fraud_count / len(fraud_labels)) * 100

    logger.info(f"Anomaly detection found {fraud_count} potential fraud cases ({fraud_percentage:.1f}%)")

    return fraud_labels


def _save_training_data(df: pd.DataFrame, labels: np.ndarray):
    """Save training data for incremental learning."""
    df_copy = df.copy()
    df_copy['is_fraud'] = labels
    df_copy['added_at'] = datetime.now().isoformat()

    # Append to existing data
    if os.path.exists(TRAINING_DATA_PATH):
        existing_df = pd.read_csv(TRAINING_DATA_PATH)
        combined_df = pd.concat([existing_df, df_copy], ignore_index=True)
        # Keep only last 10000 records
        combined_df = combined_df.tail(10000)
        combined_df.to_csv(TRAINING_DATA_PATH, index=False)
    else:
        df_copy.to_csv(TRAINING_DATA_PATH, index=False)

    logger.info(f"Saved {len(df_copy)} training samples")


def _save_model_metadata(metrics: Dict, sample_count: int):
    """Save model training metadata."""
    import json

    metadata = {
        'trained_at': datetime.now().isoformat(),
        'training_samples': sample_count,
        'metrics': metrics,
        'model_version': '1.0'
    }

    with open(MODEL_METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
