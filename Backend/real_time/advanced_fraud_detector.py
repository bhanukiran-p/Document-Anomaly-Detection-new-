"""
Advanced ML-Based Fraud Detection System
Uses XGBoost + Isolation Forest ensemble for intelligent pattern detection
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
import os
import joblib
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available, using fallback")

try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, roc_auc_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.error("Scikit-learn not available - ML models disabled")


class AdvancedFraudDetector:
    """
    Industry-standard fraud detection using:
    1. XGBoost for supervised learning (high accuracy)
    2. Isolation Forest for anomaly detection (unknown patterns)
    3. Ensemble scoring combining both approaches
    """

    def __init__(self, model_dir: str = 'real_time/models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        # Models
        self.xgb_model = None
        self.isolation_forest = None
        self.scaler = StandardScaler()

        # Paths
        self.xgb_path = os.path.join(model_dir, 'xgboost_fraud_model.pkl')
        self.isolation_path = os.path.join(model_dir, 'isolation_forest_model.pkl')
        self.scaler_path = os.path.join(model_dir, 'fraud_scaler.pkl')
        self.metadata_path = os.path.join(model_dir, 'advanced_model_metadata.json')

        # Feature importance tracking
        self.feature_names = []
        self.feature_importance = {}

    def extract_behavioral_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract comprehensive behavioral features for fraud detection

        These features capture:
        - Amount patterns
        - Time patterns
        - Location patterns
        - Velocity patterns
        - Merchant patterns
        - Account behavior
        """
        features = pd.DataFrame(index=df.index)

        # ==================== AMOUNT PATTERNS ====================
        # Basic amount features
        features['amount'] = df['amount']
        features['amount_log'] = np.log1p(df['amount'])
        features['amount_squared'] = df['amount'] ** 2
        features['amount_sqrt'] = np.sqrt(df['amount'])

        # Amount statistics
        features['amount_zscore'] = (df['amount'] - df['amount'].mean()) / (df['amount'].std() + 1e-6)
        features['is_high_amount'] = (df['amount'] > df['amount'].quantile(0.95)).astype(int)
        features['is_low_amount'] = (df['amount'] < df['amount'].quantile(0.05)).astype(int)

        # Round dollar detection (structuring indicator)
        features['is_round_100'] = (df['amount'] % 100 < 1).astype(int)
        features['is_round_1000'] = (df['amount'] % 1000 < 1).astype(int)
        features['is_round_10'] = (df['amount'] % 10 < 1).astype(int)

        # ==================== TIME PATTERNS ====================
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

            # Time features
            features['hour'] = df['timestamp'].dt.hour.fillna(12)
            features['day_of_week'] = df['timestamp'].dt.dayofweek.fillna(0)
            features['day_of_month'] = df['timestamp'].dt.day.fillna(15)
            features['month'] = df['timestamp'].dt.month.fillna(6)

            # Behavioral time patterns
            features['is_night'] = ((features['hour'] >= 23) | (features['hour'] <= 5)).astype(int)
            features['is_early_morning'] = ((features['hour'] >= 6) & (features['hour'] <= 8)).astype(int)
            features['is_business_hours'] = ((features['hour'] >= 9) & (features['hour'] <= 17)).astype(int)
            features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
            features['is_midnight'] = (features['hour'] == 0).astype(int)

            # Time-based risk
            features['late_night_high_amount'] = features['is_night'] * features['is_high_amount']
            features['weekend_high_amount'] = features['is_weekend'] * features['is_high_amount']

        else:
            # Default time features if timestamp missing
            for col in ['hour', 'day_of_week', 'day_of_month', 'month', 'is_night',
                       'is_early_morning', 'is_business_hours', 'is_weekend', 'is_midnight',
                       'late_night_high_amount', 'weekend_high_amount']:
                features[col] = 0

        # ==================== LOCATION PATTERNS ====================
        # Country mismatch (home vs transaction vs login)
        if all(col in df.columns for col in ['home_country', 'transaction_country']):
            features['country_mismatch'] = (df['home_country'] != df['transaction_country']).astype(int)
        else:
            features['country_mismatch'] = 0

        if all(col in df.columns for col in ['login_country', 'transaction_country']):
            features['login_country_mismatch'] = (df['login_country'] != df['transaction_country']).astype(int)
        else:
            features['login_country_mismatch'] = 0

        # City mismatch
        if all(col in df.columns for col in ['home_city', 'transaction_city']):
            features['city_mismatch'] = (df['home_city'] != df['transaction_city']).astype(int)
        else:
            features['city_mismatch'] = 0

        # Foreign currency indicator
        if 'currency' in df.columns and 'home_country' in df.columns:
            # Simplified foreign currency detection
            features['is_foreign_currency'] = (~df['currency'].isin(['USD', 'EUR', 'GBP'])).astype(int)
        else:
            features['is_foreign_currency'] = 0

        # Cross-border risk
        features['cross_border_risk'] = features['country_mismatch'] * features['is_high_amount']

        # ==================== VELOCITY PATTERNS ====================
        if 'customer_id' in df.columns and 'timestamp' in df.columns:
            # Transaction count per customer
            customer_counts = df.groupby('customer_id').size()
            features['customer_txn_count'] = df['customer_id'].map(customer_counts).fillna(1)

            # Velocity indicators
            features['is_high_velocity'] = (features['customer_txn_count'] >= 5).astype(int)
            features['is_very_high_velocity'] = (features['customer_txn_count'] >= 10).astype(int)
            features['is_first_transaction'] = (features['customer_txn_count'] == 1).astype(int)

            # Amount deviation from customer average
            customer_avg_amount = df.groupby('customer_id')['amount'].transform('mean')
            customer_std_amount = df.groupby('customer_id')['amount'].transform('std').fillna(1)
            features['amount_deviation_from_avg'] = np.abs(df['amount'] - customer_avg_amount) / (customer_std_amount + 1)
            features['is_amount_anomaly'] = (features['amount_deviation_from_avg'] > 2).astype(int)

            # Same-day transaction count
            if 'timestamp' in df.columns:
                df['date'] = df['timestamp'].dt.date
                same_day_counts = df.groupby(['customer_id', 'date']).size()
                features['same_day_count'] = df.set_index(['customer_id', 'date']).index.map(same_day_counts).fillna(1)
                features['is_burst'] = (features['same_day_count'] >= 3).astype(int)
        else:
            # Default velocity features
            for col in ['customer_txn_count', 'is_high_velocity', 'is_very_high_velocity',
                       'is_first_transaction', 'amount_deviation_from_avg', 'is_amount_anomaly',
                       'same_day_count', 'is_burst']:
                features[col] = 0

        # ==================== MERCHANT PATTERNS ====================
        # High-risk categories
        high_risk_categories = {'gambling', 'casino', 'betting', 'crypto', 'cryptocurrency',
                              'pawn', 'wire transfer', 'money transfer', 'cash advance', 'atm'}

        if 'category' in df.columns:
            features['is_high_risk_category'] = df['category'].str.lower().apply(
                lambda x: 1 if any(risk in str(x).lower() for risk in high_risk_categories) else 0
            )
            # Category diversity (if merchant changes frequently)
            if 'customer_id' in df.columns:
                category_counts = df.groupby('customer_id')['category'].nunique()
                features['category_diversity'] = df['customer_id'].map(category_counts).fillna(1)
        else:
            features['is_high_risk_category'] = 0
            features['category_diversity'] = 1

        # Merchant patterns
        if 'merchant' in df.columns:
            # Merchant with numbers (suspicious)
            features['merchant_has_numbers'] = df['merchant'].str.contains(r'\d', na=False).astype(int)

            # New merchant for customer
            if 'customer_id' in df.columns:
                customer_merchant_counts = df.groupby(['customer_id', 'merchant']).size()
                features['is_new_merchant'] = (df.set_index(['customer_id', 'merchant']).index.map(customer_merchant_counts) == 1).astype(int)
        else:
            features['merchant_has_numbers'] = 0
            features['is_new_merchant'] = 0

        # ==================== TRANSACTION TYPE PATTERNS ====================
        if 'transaction_type' in df.columns:
            features['is_transfer'] = df['transaction_type'].str.contains('transfer', case=False, na=False).astype(int)
            features['is_withdrawal'] = df['transaction_type'].str.contains('withdraw', case=False, na=False).astype(int)
            features['is_purchase'] = df['transaction_type'].str.contains('purchase', case=False, na=False).astype(int)
        else:
            features['is_transfer'] = 0
            features['is_withdrawal'] = 0
            features['is_purchase'] = 0

        # ==================== ACCOUNT BEHAVIOR PATTERNS ====================
        if 'account_balance' in df.columns:
            # Balance ratio
            features['amount_to_balance_ratio'] = df['amount'] / (df['account_balance'] + 1)
            features['is_balance_drain'] = (features['amount_to_balance_ratio'] > 0.8).astype(int)
            features['is_low_balance'] = (df['account_balance'] < 100).astype(int)

            # Balance after transaction
            if 'balanceafter' in df.columns:
                features['balance_change'] = df['account_balance'] - df['balanceafter']
                features['large_balance_drop'] = (features['balance_change'] > df['account_balance'] * 0.5).astype(int)
        else:
            features['amount_to_balance_ratio'] = 0
            features['is_balance_drain'] = 0
            features['is_low_balance'] = 0

        # ==================== INTERACTION FEATURES ====================
        # These capture complex fraud patterns
        features['night_cross_border'] = features['is_night'] * features['country_mismatch']
        features['high_velocity_high_amount'] = features['is_high_velocity'] * features['is_high_amount']
        features['first_txn_high_amount'] = features['is_first_transaction'] * features['is_high_amount']
        features['foreign_high_risk'] = features['is_foreign_currency'] * features['is_high_risk_category']
        features['burst_high_amount'] = features['is_burst'] * features['is_high_amount']
        features['round_amount_transfer'] = features['is_round_100'] * features['is_transfer']

        # Fill any remaining NaN values
        features = features.fillna(0)

        # Store feature names
        self.feature_names = features.columns.tolist()

        logger.info(f"Extracted {len(self.feature_names)} behavioral features for fraud detection")

        return features

    def train(self, df: pd.DataFrame, target_col: str = 'is_fraud') -> Dict[str, Any]:
        """
        Train the ensemble fraud detection system

        Args:
            df: DataFrame with transactions
            target_col: Column name for fraud labels (1=fraud, 0=legit)

        Returns:
            Training results dictionary
        """
        logger.info(f"Training advanced fraud detection on {len(df)} transactions")

        # Check if we have fraud labels
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in data")

        # Extract features
        X = self.extract_behavioral_features(df)
        y = df[target_col].values

        # Check for sufficient fraud samples
        fraud_count = y.sum()
        legit_count = len(y) - fraud_count
        logger.info(f"Training data: {fraud_count} fraud, {legit_count} legitimate")

        if fraud_count < 10:
            raise ValueError(f"Insufficient fraud samples for training (need at least 10, got {fraud_count})")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        results = {}

        # ==================== TRAIN XGBOOST ====================
        if XGBOOST_AVAILABLE:
            logger.info("Training XGBoost model for supervised fraud detection...")

            # Calculate scale_pos_weight for imbalanced data
            scale_pos_weight = legit_count / fraud_count if fraud_count > 0 else 1

            self.xgb_model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                min_child_weight=1,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=scale_pos_weight,
                objective='binary:logistic',
                random_state=42,
                n_jobs=-1,
                tree_method='hist'
            )

            self.xgb_model.fit(X_train, y_train)

            # Evaluate
            y_pred = self.xgb_model.predict(X_test)
            y_proba = self.xgb_model.predict_proba(X_test)[:, 1]

            xgb_accuracy = (y_pred == y_test).mean()
            try:
                xgb_auc = roc_auc_score(y_test, y_proba)
            except:
                xgb_auc = 0.5

            logger.info(f"XGBoost - Accuracy: {xgb_accuracy:.3f}, AUC: {xgb_auc:.3f}")

            # Feature importance
            if hasattr(self.xgb_model, 'feature_importances_'):
                importance = self.xgb_model.feature_importances_
                self.feature_importance = dict(zip(self.feature_names, importance))

                # Log top features
                top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
                logger.info("Top 10 fraud indicators:")
                for feat, imp in top_features:
                    logger.info(f"  {feat}: {imp:.4f}")

            results['xgb_accuracy'] = xgb_accuracy
            results['xgb_auc'] = xgb_auc

        else:
            logger.warning("XGBoost not available, using RandomForest instead")
            self.xgb_model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
            self.xgb_model.fit(X_train, y_train)
            results['xgb_accuracy'] = self.xgb_model.score(X_test, y_test)

        # ==================== TRAIN ISOLATION FOREST ====================
        logger.info("Training Isolation Forest for anomaly detection...")

        # Train on legitimate transactions only (to learn normal behavior)
        X_legit = X_scaled[y_train == 0]

        self.isolation_forest = IsolationForest(
            n_estimators=150,
            contamination=min(0.1, fraud_count / len(y)),  # Expected fraud rate
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        )

        self.isolation_forest.fit(X_legit)

        # Evaluate on test set
        iso_predictions = self.isolation_forest.predict(X_test)
        iso_predictions = (iso_predictions == -1).astype(int)  # -1 = anomaly = fraud
        iso_accuracy = (iso_predictions == y_test).mean()

        logger.info(f"Isolation Forest - Accuracy: {iso_accuracy:.3f}")
        results['isolation_accuracy'] = iso_accuracy

        # Save models
        self.save_models()

        results['features_count'] = len(self.feature_names)
        results['trained_at'] = datetime.now().isoformat()

        logger.info("Advanced fraud detection training complete!")
        return results

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Predict fraud using ensemble of XGBoost + Isolation Forest

        Returns:
            predictions: Binary predictions (0/1)
            probabilities: Fraud probabilities (0.0-1.0)
            reasons: Detailed fraud reasons
        """
        # Extract features
        X = self.extract_behavioral_features(df)
        X_scaled = self.scaler.transform(X)

        # Get predictions from both models
        if self.xgb_model is not None:
            xgb_proba = self.xgb_model.predict_proba(X_scaled)[:, 1]
        else:
            xgb_proba = np.zeros(len(X))

        if self.isolation_forest is not None:
            iso_scores = self.isolation_forest.decision_function(X_scaled)
            # Convert to probability-like scores (0-1)
            iso_proba = 1 / (1 + np.exp(iso_scores))  # Sigmoid transformation
        else:
            iso_proba = np.zeros(len(X))

        # Ensemble: Weighted average (XGBoost gets more weight)
        ensemble_proba = 0.7 * xgb_proba + 0.3 * iso_proba

        # Make binary predictions (threshold = 0.5)
        predictions = (ensemble_proba >= 0.5).astype(int)

        # Generate detailed reasons based on feature importance
        reasons = self._generate_fraud_reasons(X, predictions, ensemble_proba)

        logger.info(f"Predicted {predictions.sum()}/{len(predictions)} fraudulent transactions")

        return predictions, ensemble_proba, reasons

    def _generate_fraud_reasons(self, X: pd.DataFrame, predictions: np.ndarray,
                                probabilities: np.ndarray) -> List[str]:
        """Generate detailed fraud reasons based on activated features"""
        reasons = []

        for idx in range(len(X)):
            if predictions[idx] == 0:
                reasons.append("Legitimate transaction")
                continue

            # Get top contributing features for this transaction
            activated_features = []
            row = X.iloc[idx]

            # Check behavioral patterns
            if row.get('is_high_amount', 0) == 1:
                activated_features.append("unusually high amount")
            if row.get('is_night', 0) == 1:
                activated_features.append("night-time transaction")
            if row.get('country_mismatch', 0) == 1:
                activated_features.append("location mismatch")
            if row.get('is_high_velocity', 0) == 1:
                activated_features.append("high transaction velocity")
            if row.get('is_burst', 0) == 1:
                activated_features.append("transaction burst detected")
            if row.get('is_high_risk_category', 0) == 1:
                activated_features.append("high-risk merchant")
            if row.get('is_foreign_currency', 0) == 1:
                activated_features.append("foreign currency")
            if row.get('is_round_100', 0) == 1 or row.get('is_round_1000', 0) == 1:
                activated_features.append("round-dollar amount")
            if row.get('is_balance_drain', 0) == 1:
                activated_features.append("account balance drain")
            if row.get('is_first_transaction', 0) == 1 and row.get('is_high_amount', 0) == 1:
                activated_features.append("first transaction with high amount")

            # Construct reason
            if activated_features:
                reason = f"Fraud detected ({int(probabilities[idx]*100)}% confidence): " + ", ".join(activated_features[:3])
            else:
                reason = f"Anomaly detected ({int(probabilities[idx]*100)}% confidence): statistical outlier"

            reasons.append(reason)

        return reasons

    def save_models(self):
        """Save trained models to disk"""
        try:
            if self.xgb_model is not None:
                joblib.dump(self.xgb_model, self.xgb_path)
                logger.info(f"XGBoost model saved to {self.xgb_path}")

            if self.isolation_forest is not None:
                joblib.dump(self.isolation_forest, self.isolation_path)
                logger.info(f"Isolation Forest saved to {self.isolation_path}")

            joblib.dump(self.scaler, self.scaler_path)
            logger.info(f"Scaler saved to {self.scaler_path}")

            # Save metadata
            metadata = {
                'feature_names': self.feature_names,
                'feature_importance': self.feature_importance,
                'saved_at': datetime.now().isoformat()
            }
            import json
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def load_models(self) -> bool:
        """Load trained models from disk"""
        try:
            if os.path.exists(self.xgb_path):
                self.xgb_model = joblib.load(self.xgb_path)
                logger.info("XGBoost model loaded")

            if os.path.exists(self.isolation_path):
                self.isolation_forest = joblib.load(self.isolation_path)
                logger.info("Isolation Forest loaded")

            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Scaler loaded")

            if os.path.exists(self.metadata_path):
                import json
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.feature_names = metadata.get('feature_names', [])
                    self.feature_importance = metadata.get('feature_importance', {})
                logger.info("Model metadata loaded")

            return self.xgb_model is not None and self.scaler is not None

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
