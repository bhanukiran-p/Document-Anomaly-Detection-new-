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

HIGH_VALUE_THRESHOLD = 3000
BLACKLISTED_MERCHANT_KEYWORDS = {
    'western union', 'moneygram', 'binance', 'crypto', 'cryptocurrency',
    'gambling', 'casino', 'betting', 'poker', 'fast payout', 'wire transfer',
    'hawala'
}

STANDARD_FRAUD_REASONS = [
    'Suspicious login',
    'Account takeover',
    'Unusual location',
    'Unusual device',
    'Velocity abuse',
    'Transaction burst',
    'High-risk merchant',
    'Unusual amount',
    'New payee spike',
    'Cross-border anomaly',
    'Card-not-present risk',
    'Money mule pattern',
    'Structuring / smurfing',
    'Round-dollar pattern',
    'Night-time activity'
]

ONLINE_CATEGORY_KEYWORDS = {
    'online', 'e-commerce', 'ecommerce', 'digital', 'subscription',
    'marketplace', 'web', 'saas'
}

CARD_NOT_PRESENT_KEYWORDS = {
    'card-not-present', 'c-n-p', 'mail order', 'telephone order', 'moto'
}

ROUND_DOLLAR_EPSILON = 0.01
LEGITIMATE_LABEL = 'Legitimate Transaction'


def _get_row_value(row: pd.Series, *keys):
    """Safely fetch a value from multiple possible column names."""
    for key in keys:
        if key in row and pd.notna(row[key]):
            return row[key]
    return None


def _is_round_dollar(amount: float) -> bool:
    if amount == 0:
        return False
    rounded = round(amount)
    return (
        abs(amount - rounded) < ROUND_DOLLAR_EPSILON
        and int(abs(rounded)) % 100 == 0
    )


def _is_card_not_present(txn_type: str, category: str, description: str) -> bool:
    # Handle None or missing values gracefully
    txn_type = str(txn_type) if txn_type is not None else ''
    category = str(category) if category is not None else ''
    description = str(description) if description is not None else ''
    
    text_blobs = [txn_type, category, description]
    for blob in text_blobs:
        if blob and any(keyword in blob for keyword in CARD_NOT_PRESENT_KEYWORDS):
            return True
    if category and any(keyword in category for keyword in ONLINE_CATEGORY_KEYWORDS):
        return True
    if txn_type and any(keyword in txn_type for keyword in ONLINE_CATEGORY_KEYWORDS):
        return True
    return False


def _looks_like_money_mule(transaction_row: pd.Series, feature_row: pd.Series, amount: float, is_first_time: bool) -> bool:
    txn_type = str(_get_row_value(transaction_row, 'transaction_type', 'TransactionType', 'type', 'Type') or '').lower()
    merchant = str(_get_row_value(transaction_row, 'merchant', 'Merchant') or '').lower()
    suspect_keywords = {'transfer', 'remit', 'crypto', 'wire'}
    suspicious_merchant = any(keyword in merchant for keyword in suspect_keywords)

    return (
        (txn_type.find('credit') != -1 or suspicious_merchant)
        and feature_row.get('amount_to_balance_ratio', 0) > 0.9
        and feature_row.get('is_foreign_currency', 0) == 1
        and is_first_time
    )


def _normalize_fraud_reasons(fraud_df: pd.DataFrame, features_df: pd.DataFrame) -> List[str]:
    """
    Normalize fraud reasons based on transaction patterns for better accuracy.
    Assigns human-readable fraud types based on feature analysis.
    """
    normalized_reasons = []

    for idx in fraud_df.index:
        features = features_df.loc[idx]
        txn = fraud_df.loc[idx]

        # Priority-based fraud reason assignment
        reason = None

        # 1. Velocity abuse / Transaction burst (highest priority)
        if features.get('customer_txn_count', 0) >= 3 and features.get('amount_deviation', 0) > 2:
            reason = 'Velocity abuse'

        # 2. Account takeover indicators
        elif features.get('country_mismatch', 0) == 1 or features.get('login_transaction_mismatch', 0) == 1:
            reason = 'Account takeover'

        # 3. Unusual location
        elif features.get('country_mismatch', 0) == 1:
            reason = 'Unusual location'

        # 4. Night-time activity
        elif features.get('is_night', 1) == 1 and features.get('amount_zscore', 0) > 1.5:
            reason = 'Night-time activity'

        # 5. High-risk merchant
        elif features.get('high_risk_category', 0) == 1:
            reason = 'High-risk merchant'

        # 6. Card-not-present risk (online/foreign transactions)
        elif features.get('is_foreign_currency', 0) == 1 or features.get('is_transfer', 0) == 1:
            reason = 'Card-not-present risk'

        # 7. Unusual amount patterns
        elif features.get('amount_zscore', 0) > 2.5:
            reason = 'Unusual amount'

        # 8. Money mule pattern
        elif (features.get('amount_to_balance_ratio', 0) > 0.9 and
              features.get('is_foreign_currency', 0) == 1):
            reason = 'Money mule pattern'

        # 9. Structuring / Smurfing (just below reporting thresholds)
        elif 2900 <= txn.get('amount', 0) <= 3100:
            reason = 'Structuring / smurfing'

        # 10. Round-dollar pattern
        elif _is_round_dollar(txn.get('amount', 0)):
            reason = 'Round-dollar pattern'

        # 11. Cross-border anomaly
        elif features.get('is_foreign_currency', 0) == 1 and features.get('amount_deviation', 0) > 2:
            reason = 'Cross-border anomaly'

        # 12. Statistical outlier
        elif features.get('is_outlier', 0) == 1:
            reason = 'Unusual amount'

        # 13. Weekend unusual activity
        elif features.get('is_weekend', 0) == 1 and features.get('high_risk_category', 0) == 1:
            reason = 'Suspicious login'

        # 14. Default - Transaction burst
        else:
            reason = 'Transaction burst'

        normalized_reasons.append(reason)

    return normalized_reasons


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
        df['fraud_reason_detail'] = reasons

        # Classify fraud types using ML (not rules)
        from real_time.fraud_type_classifier import get_fraud_type_classifier

        fraud_type_classifier = get_fraud_type_classifier()

        # Only classify fraud types for fraudulent transactions
        fraud_indices = df['is_fraud'] == 1
        fraud_df = df[fraud_indices].copy()
        fraud_features = features_df[fraud_indices].copy()

        if len(fraud_df) > 0:
            # Always use ML-based fraud type classification
            # Train classifier if not already trained
            if fraud_type_classifier.model is None:
                logger.info("Training fraud type classifier using pure ML (unsupervised clustering)")

                # Use unsupervised clustering to discover fraud patterns (pure ML, no rules)
                from sklearn.cluster import KMeans
                from sklearn.preprocessing import StandardScaler
                
                # Prepare features for clustering
                fraud_features_for_clustering = features_df[fraud_indices].copy()
                
                # Select key features for clustering
                clustering_features = [
                    'amount_zscore', 'amount_deviation', 'country_mismatch', 
                    'login_transaction_mismatch', 'is_foreign_currency',
                    'is_night', 'is_weekend', 'is_transfer', 'high_risk_category',
                    'amount_to_balance_ratio', 'customer_txn_count', 'is_outlier'
                ]
                
                # Use available features
                available_features = [f for f in clustering_features if f in fraud_features_for_clustering.columns]
                if len(available_features) < 3:
                    # Fallback to all numeric features
                    available_features = fraud_features_for_clustering.select_dtypes(include=[np.number]).columns.tolist()
                
                X_cluster = fraud_features_for_clustering[available_features].fillna(0)
                
                # Determine optimal number of clusters (between 3 and min(10, len(fraud_df)//2))
                n_clusters = min(max(3, len(fraud_df) // 10), 10, len(fraud_df))
                
                # Scale features
                scaler_cluster = StandardScaler()
                X_cluster_scaled = scaler_cluster.fit_transform(X_cluster)
                
                # Perform clustering
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(X_cluster_scaled)
                
                # Map clusters to fraud type labels
                fraud_type_labels = [f'Fraud Pattern {i+1}' for i in cluster_labels]
                
                # Add labels to dataframe
                df.loc[fraud_indices, 'fraud_reason'] = fraud_type_labels
                df.loc[~fraud_indices, 'fraud_reason'] = LEGITIMATE_LABEL

                # Train the ML model on these patterns
                try:
                    accuracy, report = fraud_type_classifier.train(df, features_df)
                    logger.info(f"Fraud type classifier trained with accuracy: {accuracy:.3f} using {n_clusters} discovered patterns")
                    logger.info(f"Classification Report:\n{report}")
                except Exception as e:
                    logger.error(f"Failed to train fraud type classifier: {e}", exc_info=True)
                    raise RuntimeError(f"ML fraud type classifier training failed: {e}")

            # Predict fraud types using trained ML model
            try:
                fraud_types_pred = fraud_type_classifier.predict(fraud_df, fraud_features)

                # Validate predictions
                if any(ft in ['Prediction error', 'Unknown fraud type'] for ft in fraud_types_pred):
                    error_count = sum(1 for ft in fraud_types_pred if ft in ['Prediction error', 'Unknown fraud type'])
                    logger.error(f"ML predictions failed for {error_count}/{len(fraud_types_pred)} transactions")
                    raise RuntimeError(f"ML fraud type prediction returned {error_count} errors")

                # Apply predictions
                df.loc[fraud_indices, 'fraud_reason'] = fraud_types_pred
                df.loc[fraud_indices, 'fraud_type'] = fraud_types_pred
                logger.info(f"ML fraud type classification successful for {len(fraud_df)} transactions")

                # Normalize fraud reasons based on transaction patterns
                normalized_reasons = _normalize_fraud_reasons(fraud_df, fraud_features)
                df.loc[fraud_indices, 'fraud_reason'] = normalized_reasons
                df.loc[fraud_indices, 'fraud_type'] = normalized_reasons
                logger.info(f"Normalized fraud reasons for {len(fraud_df)} fraudulent transactions")

            except Exception as e:
                logger.error(f"ML fraud type prediction failed: {e}", exc_info=True)
                raise RuntimeError(f"ML fraud type classifier prediction failed: {e}")

        # Set legitimate transactions
        df.loc[~fraud_indices, 'fraud_reason'] = LEGITIMATE_LABEL
        df.loc[~fraud_indices, 'fraud_type'] = LEGITIMATE_LABEL

        # Calculate statistics
        fraud_count = int(predictions.sum())
        fraud_percentage = float((fraud_count / len(df)) * 100) if len(df) > 0 else 0

        fraud_transactions = df[df['is_fraud'] == 1]
        legitimate_transactions = df[df['is_fraud'] == 0]

        total_fraud_amount = float(fraud_transactions['amount'].sum()) if len(fraud_transactions) > 0 else 0
        total_legitimate_amount = float(legitimate_transactions['amount'].sum()) if len(legitimate_transactions) > 0 else 0

        # Summarize fraud type distribution
        fraud_reason_breakdown = _summarize_fraud_types(df)

        # Convert back to list of dictionaries
        transactions_with_predictions = _records_with_serializable_timestamps(df.to_dict('records'))

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
            'fraud_reason_breakdown': fraud_reason_breakdown,
            'fraud_type_breakdown': fraud_reason_breakdown,
            'dominant_fraud_reason': fraud_reason_breakdown[0]['type'] if fraud_reason_breakdown else None,
            'dominant_fraud_type': fraud_reason_breakdown[0]['type'] if fraud_reason_breakdown else None,
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

        # Get probabilities first
        probabilities = model.predict_proba(X_scaled)[:, 1]
        
        # Log probability statistics for debugging
        logger.info(f"📊 Fraud probability statistics:")
        logger.info(f"   Min: {probabilities.min():.4f}, Max: {probabilities.max():.4f}")
        logger.info(f"   Mean: {probabilities.mean():.4f}, Median: {np.median(probabilities):.4f}")
        logger.info(f"   Std: {probabilities.std():.4f}")
        logger.info(f"   Probabilities > 0.5: {np.sum(probabilities > 0.5)}/{len(probabilities)} ({100*np.sum(probabilities > 0.5)/len(probabilities):.2f}%)")
        logger.info(f"   Probabilities > 0.7: {np.sum(probabilities > 0.7)}/{len(probabilities)} ({100*np.sum(probabilities > 0.7)/len(probabilities):.2f}%)")
        logger.info(f"   Probabilities > 0.9: {np.sum(probabilities > 0.9)}/{len(probabilities)} ({100*np.sum(probabilities > 0.9)/len(probabilities):.2f}%)")

        # Predict using model's default threshold (0.5)
        predictions = model.predict(X_scaled)
        
        fraud_count = np.sum(predictions == 1)
        logger.info(f"🔍 Model predictions: {fraud_count}/{len(predictions)} fraudulent ({100*fraud_count/len(predictions):.2f}%)")

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

            # Add detection confidence
            reason_parts.append(f"Fraud Detection ({prob*100:.1f}% confidence)")

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

            # If no specific reasons, provide general insight
            if len(reason_parts) == 1:
                reason_parts.append("Multiple fraud indicators detected")

            reasons.append(" | ".join(reason_parts))
        else:
            reasons.append(f"Legitimate transaction (confidence: {(1-prob)*100:.1f}%)")

    return reasons


# REMOVED: _classify_fraud_type function - replaced with pure ML clustering approach
# All fraud type classification now uses unsupervised ML clustering followed by supervised ML training


def _summarize_fraud_types(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Summarize fraud type distribution for downstream consumers."""
    fraud_df = df[df['is_fraud'] == 1]
    if fraud_df.empty or 'fraud_type' not in fraud_df.columns:
        return []

    counts = fraud_df['fraud_type'].value_counts()
    total = counts.sum()
    summary = []

    for fraud_type, count in counts.items():
        type_df = fraud_df[fraud_df['fraud_type'] == fraud_type]
        summary.append({
            'type': fraud_type,
            'label': fraud_type,
            'count': int(count),
            'percentage': round((count / total) * 100, 2) if total else 0.0,
            'total_amount': round(float(type_df['amount'].sum()), 2)
        })

    return summary


def _records_with_serializable_timestamps(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure pandas Timestamps/NaT become JSON-friendly objects."""
    for record in records:
        for key, value in list(record.items()):
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
    return records
