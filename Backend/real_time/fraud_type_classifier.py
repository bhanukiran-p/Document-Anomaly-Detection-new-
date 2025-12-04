"""
ML-Based Fraud Type Classifier
Replaces rule-based fraud type classification with machine learning
"""
import pandas as pd
import numpy as np
import logging
from typing import List, Tuple
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

logger = logging.getLogger(__name__)

MODEL_DIR = 'real_time/models'
FRAUD_TYPE_MODEL_PATH = os.path.join(MODEL_DIR, 'fraud_type_classifier.pkl')
FRAUD_TYPE_ENCODER_PATH = os.path.join(MODEL_DIR, 'fraud_type_encoder.pkl')
FRAUD_TYPE_FEATURES_PATH = os.path.join(MODEL_DIR, 'fraud_type_features.pkl')

class FraudTypeClassifier:
    """ML-based fraud type classifier"""

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.feature_columns = None

    def _prepare_features(self, df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare feature set for fraud type classification
        Combines transaction data with engineered features
        """
        feature_set = pd.DataFrame()

        # Amount-based features
        feature_set['amount'] = df['amount'] if 'amount' in df else 0
        feature_set['amount_log'] = np.log1p(feature_set['amount'])

        # Get features from features_df if available
        if features_df is not None and len(features_df) > 0:
            # Location/geographic features
            feature_set['country_mismatch'] = features_df.get('country_mismatch', 0)
            feature_set['login_transaction_mismatch'] = features_df.get('login_transaction_mismatch', 0)
            feature_set['is_foreign_currency'] = features_df.get('is_foreign_currency', 0)

            # Transaction pattern features
            feature_set['customer_txn_count'] = features_df.get('customer_txn_count', 0)
            feature_set['is_first_time'] = (features_df.get('customer_txn_count', 0) <= 1).astype(int)
            feature_set['amount_to_balance_ratio'] = features_df.get('amount_to_balance_ratio', 0)
            feature_set['amount_deviation'] = features_df.get('amount_deviation', 0)
            feature_set['amount_zscore'] = features_df.get('amount_zscore', 0)

            # Time-based features
            feature_set['is_night'] = features_df.get('is_night', 0)
            feature_set['is_weekend'] = features_df.get('is_weekend', 0)
            feature_set['hour'] = features_df.get('hour', 0)

            # Risk indicators
            feature_set['is_transfer'] = features_df.get('is_transfer', 0)
            feature_set['high_risk_category'] = features_df.get('high_risk_category', 0)
            feature_set['merchant_has_numbers'] = features_df.get('merchant_has_numbers', 0)
            feature_set['low_balance'] = features_df.get('low_balance', 0)

            # Velocity features
            feature_set['same_day_count'] = features_df.get('same_day_count', 0)
            feature_set['transaction_velocity'] = features_df.get('same_day_count', 0) / 24.0

        else:
            # Default values if features_df not available
            for col in ['country_mismatch', 'login_transaction_mismatch', 'is_foreign_currency',
                       'customer_txn_count', 'is_first_time', 'amount_to_balance_ratio',
                       'amount_deviation', 'amount_zscore', 'is_night', 'is_weekend', 'hour',
                       'is_transfer', 'high_risk_category', 'merchant_has_numbers', 'low_balance',
                       'same_day_count', 'transaction_velocity']:
                feature_set[col] = 0

        # Derived features
        feature_set['is_high_value'] = (feature_set['amount'] >= 3000).astype(int)
        feature_set['is_round_amount'] = ((feature_set['amount'] % 100) < 1).astype(int)
        feature_set['is_structuring_range'] = ((feature_set['amount'] >= 9000) &
                                               (feature_set['amount'] <= 10000)).astype(int)

        # Interaction features
        feature_set['high_value_first_time'] = feature_set['is_high_value'] * feature_set['is_first_time']
        feature_set['foreign_high_value'] = feature_set['is_foreign_currency'] * feature_set['is_high_value']
        feature_set['night_high_value'] = feature_set['is_night'] * feature_set['is_high_value']
        feature_set['location_mismatch_foreign'] = feature_set['country_mismatch'] * feature_set['is_foreign_currency']

        return feature_set

    def train(self, df: pd.DataFrame, features_df: pd.DataFrame) -> Tuple[float, str]:
        """
        Train fraud type classifier on labeled data

        Args:
            df: DataFrame with transactions including 'fraud_reason' column
            features_df: DataFrame with engineered features

        Returns:
            Tuple of (accuracy, report)
        """
        try:
            # Filter only fraudulent transactions that have fraud reasons
            fraud_df = df[df['is_fraud'] == 1].copy()
            fraud_features = features_df[df['is_fraud'] == 1].copy()

            logger.info(f"Training data: {len(fraud_df)} fraud samples, {len(df) - len(fraud_df)} legitimate samples")

            if len(fraud_df) < 5:
                error_msg = f"Not enough fraud samples to train fraud type classifier (need at least 5, got {len(fraud_df)})"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Get fraud reasons (must exist in training data)
            if 'fraud_reason' not in fraud_df.columns and 'fraud_type' not in fraud_df.columns:
                error_msg = "No fraud reason labels found in training data"
                logger.error(error_msg)
                raise ValueError(error_msg)

            y = fraud_df['fraud_reason'] if 'fraud_reason' in fraud_df.columns else fraud_df['fraud_type']

            # Check for unique fraud types
            unique_types = y.unique()
            if len(unique_types) < 2:
                error_msg = f"Need at least 2 distinct fraud types for classification (got {len(unique_types)})"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Prepare features
            X = self._prepare_features(fraud_df, fraud_features)
            self.feature_columns = X.columns.tolist()

            logger.info(f"Prepared {len(self.feature_columns)} features: {self.feature_columns[:10]}...")

            # Encode labels
            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)

            logger.info(f"Training fraud type classifier with {len(X)} samples across {len(self.label_encoder.classes_)} fraud types")
            logger.info(f"Fraud types: {list(self.label_encoder.classes_)}")

            # Split data
            if len(X) >= 30:
                try:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
                    )
                except ValueError:
                    # Stratify failed due to imbalanced classes, train without stratification
                    logger.warning("Stratified split failed, using simple split")
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y_encoded, test_size=0.2, random_state=42
                    )
            else:
                # Use all data for training if sample size is small
                logger.warning(f"Small dataset ({len(X)} samples), using all data for both training and testing")
                X_train, y_train = X, y_encoded
                X_test, y_test = X, y_encoded

            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=max(2, min(5, len(X_train) // 10)),
                min_samples_leaf=max(1, min(2, len(X_train) // 20)),
                random_state=42,
                class_weight='balanced',
                n_jobs=-1
            )

            logger.info("Fitting Random Forest classifier...")
            self.model.fit(X_train, y_train)

            # Evaluate
            train_accuracy = self.model.score(X_train, y_train)
            test_accuracy = self.model.score(X_test, y_test)

            y_pred = self.model.predict(X_test)
            report = classification_report(
                y_test, y_pred,
                target_names=self.label_encoder.classes_,
                zero_division=0
            )

            logger.info(f"Fraud type classifier trained successfully!")
            logger.info(f"Train accuracy: {train_accuracy:.3f}, Test accuracy: {test_accuracy:.3f}")

            # Save model
            self.save_model()
            logger.info("Model saved to disk")

            return test_accuracy, report

        except Exception as e:
            logger.error(f"Failed to train fraud type classifier: {e}", exc_info=True)
            # Reset state on failure
            self.model = None
            self.label_encoder = None
            self.feature_columns = None
            raise

    def predict(self, df: pd.DataFrame, features_df: pd.DataFrame) -> List[str]:
        """
        Predict fraud types for transactions

        Args:
            df: DataFrame with transactions
            features_df: DataFrame with engineered features

        Returns:
            List of predicted fraud types
        """
        try:
            if self.model is None or self.label_encoder is None:
                logger.warning("Fraud type classifier not trained, model or encoder is None")
                return ['Unknown fraud type'] * len(df)

            # Prepare features
            X = self._prepare_features(df, features_df)

            # Check if feature_columns is set
            if self.feature_columns is None:
                logger.error("Feature columns not set in classifier, cannot predict")
                return ['Prediction error'] * len(df)

            # Ensure all required features are present
            for col in self.feature_columns:
                if col not in X.columns:
                    X[col] = 0

            X = X[self.feature_columns]

            # Validate feature count
            if X.shape[1] != self.model.n_features_in_:
                logger.error(f"Feature mismatch: expected {self.model.n_features_in_} features, got {X.shape[1]}")
                return ['Prediction error'] * len(df)

            # Predict
            predictions_encoded = self.model.predict(X)
            predictions = self.label_encoder.inverse_transform(predictions_encoded)

            return predictions.tolist()

        except Exception as e:
            logger.error(f"Failed to predict fraud types: {e}", exc_info=True)
            return ['Prediction error'] * len(df)

    def predict_proba(self, df: pd.DataFrame, features_df: pd.DataFrame) -> np.ndarray:
        """
        Get probability distribution over fraud types

        Args:
            df: DataFrame with transactions
            features_df: DataFrame with engineered features

        Returns:
            Array of probabilities for each fraud type
        """
        try:
            if self.model is None:
                return np.zeros((len(df), 1))

            X = self._prepare_features(df, features_df)

            # Ensure all required features are present
            for col in self.feature_columns:
                if col not in X.columns:
                    X[col] = 0

            X = X[self.feature_columns]

            return self.model.predict_proba(X)

        except Exception as e:
            logger.error(f"Failed to predict fraud type probabilities: {e}")
            return np.zeros((len(df), 1))

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance scores"""
        if self.model is None or self.feature_columns is None:
            return pd.DataFrame()

        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance_df

    def save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(MODEL_DIR, exist_ok=True)
            joblib.dump(self.model, FRAUD_TYPE_MODEL_PATH)
            joblib.dump(self.label_encoder, FRAUD_TYPE_ENCODER_PATH)
            joblib.dump(self.feature_columns, FRAUD_TYPE_FEATURES_PATH)
            logger.info(f"Fraud type classifier saved to {FRAUD_TYPE_MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to save fraud type classifier: {e}")

    def load_model(self) -> bool:
        """Load model from disk"""
        try:
            if os.path.exists(FRAUD_TYPE_MODEL_PATH) and os.path.exists(FRAUD_TYPE_ENCODER_PATH):
                self.model = joblib.load(FRAUD_TYPE_MODEL_PATH)
                self.label_encoder = joblib.load(FRAUD_TYPE_ENCODER_PATH)

                # Load feature columns if available
                if os.path.exists(FRAUD_TYPE_FEATURES_PATH):
                    self.feature_columns = joblib.load(FRAUD_TYPE_FEATURES_PATH)
                    logger.info(f"Fraud type classifier loaded successfully with {len(self.feature_columns)} features")
                    return True
                else:
                    logger.warning("Feature columns file not found, classifier may not work properly")
                    self.feature_columns = None
                    return False
            else:
                logger.info("No saved fraud type classifier found")
                return False
        except Exception as e:
            logger.error(f"Failed to load fraud type classifier: {e}")
            self.model = None
            self.label_encoder = None
            self.feature_columns = None
            return False


# Global classifier instance
_fraud_type_classifier = None

def get_fraud_type_classifier() -> FraudTypeClassifier:
    """Get or create global fraud type classifier instance"""
    global _fraud_type_classifier
    if _fraud_type_classifier is None:
        _fraud_type_classifier = FraudTypeClassifier()
        _fraud_type_classifier.load_model()
    return _fraud_type_classifier
