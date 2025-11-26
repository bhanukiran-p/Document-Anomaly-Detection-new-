"""
Train Random Forest model for Bank Statement Fraud Detection
Uses real training data from dataset/staement_fraud_5000.csv
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# ML Libraries
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    mean_squared_error, r2_score, accuracy_score, f1_score, precision_score, recall_score
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BankStatementModelTrainer:
    """Train ML models specifically for bank statement fraud detection"""

    def __init__(self):
        """Initialize trainer"""
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_dir = 'models'
        os.makedirs(self.model_dir, exist_ok=True)

    def load_training_data(self, csv_path):
        """
        Load training data from CSV

        Args:
            csv_path: Path to the staement_fraud_5000.csv file

        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading training data from {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} features")
        logger.info(f"Fraud distribution:\n{df['is_fraud'].value_counts()}")
        return df

    def prepare_features(self, df):
        """
        Prepare features for model training

        Args:
            df: DataFrame with raw data

        Returns:
            Tuple of (X features, y labels)
        """
        logger.info("Preparing features for training...")

        # Features to use (exclude statement_id, customer_name, account_number, transaction_id, etc.)
        feature_cols = [
            'opening_balance', 'ending_balance', 'total_credits', 'total_debits',
            'amount', 'balance_after', 'is_credit', 'is_debit', 'abs_amount',
            'is_large_transaction', 'amount_to_balance_ratio',
            'transactions_past_1_day', 'transactions_past_7_days',
            'cumulative_monthly_credits', 'cumulative_monthly_debits',
            'is_new_merchant', 'weekday', 'day_of_month', 'is_weekend'
        ]

        # Check which features are available in the data
        available_features = [col for col in feature_cols if col in df.columns]
        missing_features = [col for col in feature_cols if col not in df.columns]

        logger.info(f"Using {len(available_features)} features: {available_features}")
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")

        # Create feature matrix
        X = df[available_features].copy()

        # Handle missing values
        X = X.fillna(X.mean())

        # Target variable
        y = df['is_fraud'].copy()

        self.feature_names = available_features

        logger.info(f"Feature matrix shape: {X.shape}")
        logger.info(f"Target distribution:\n{y.value_counts()}")

        return X, y, available_features

    def train_random_forest(self, X, y, test_size=0.2, random_state=42):
        """
        Train Random Forest Classifier for fraud detection

        Args:
            X: Feature matrix
            y: Target labels (0 or 1)
            test_size: Proportion of test set
            random_state: Random seed

        Returns:
            Dictionary with trained model and metrics
        """
        logger.info("Training Random Forest Classifier with class weight balancing...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        logger.info(f"Training set size: {len(X_train)}")
        logger.info(f"Test set size: {len(X_test)}")
        logger.info(f"Training set fraud distribution: {y_train.value_counts().to_dict()}")
        logger.info(f"Test set fraud distribution: {y_test.value_counts().to_dict()}")

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Calculate class weights to handle imbalance (70% fraud, 30% legitimate)
        from sklearn.utils.class_weight import compute_class_weight
        class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
        class_weight_dict = {i: w for i, w in enumerate(class_weights)}
        logger.info(f"Class weights: {class_weight_dict}")

        # Train Random Forest Classifier with balanced class weights
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=random_state,
            n_jobs=-1,
            verbose=1,
            class_weight=class_weight_dict,  # Handle class imbalance
            max_features='sqrt',  # Reduce overfitting
            bootstrap=True,
            criterion='gini'
        )

        self.model.fit(X_train_scaled, y_train)

        # Make predictions
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)

        # Get probability predictions for ROC-AUC
        y_train_pred_proba = self.model.predict_proba(X_train_scaled)[:, 1]
        y_test_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        # Evaluate
        train_accuracy = accuracy_score(y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        train_f1 = f1_score(y_train, y_train_pred)
        test_f1 = f1_score(y_test, y_test_pred)
        train_precision = precision_score(y_train, y_train_pred)
        test_precision = precision_score(y_test, y_test_pred)
        train_recall = recall_score(y_train, y_train_pred)
        test_recall = recall_score(y_test, y_test_pred)
        test_roc_auc = roc_auc_score(y_test, y_test_pred_proba)

        metrics = {
            'model_type': 'RandomForestClassifier',
            'train_accuracy': float(train_accuracy),
            'test_accuracy': float(test_accuracy),
            'train_f1_score': float(train_f1),
            'test_f1_score': float(test_f1),
            'train_precision': float(train_precision),
            'test_precision': float(test_precision),
            'train_recall': float(train_recall),
            'test_recall': float(test_recall),
            'test_roc_auc': float(test_roc_auc),
            'n_features': len(self.feature_names),
            'n_samples_train': len(X_train),
            'n_samples_test': len(X_test),
            'class_weights': class_weight_dict,
        }

        logger.info("=" * 70)
        logger.info("CLASSIFIER MODEL PERFORMANCE METRICS:")
        logger.info("=" * 70)
        logger.info(f"Training Accuracy:  {train_accuracy:.4f}")
        logger.info(f"Test Accuracy:      {test_accuracy:.4f}")
        logger.info(f"Training F1 Score:  {train_f1:.4f}")
        logger.info(f"Test F1 Score:      {test_f1:.4f}")
        logger.info(f"Training Precision: {train_precision:.4f}")
        logger.info(f"Test Precision:     {test_precision:.4f}")
        logger.info(f"Training Recall:    {train_recall:.4f}")
        logger.info(f"Test Recall:        {test_recall:.4f}")
        logger.info(f"Test ROC-AUC:       {test_roc_auc:.4f}")
        logger.info("=" * 70)

        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_test_pred, target_names=['Legitimate', 'Fraud']))

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        logger.info("\nTop 10 Most Important Features:")
        logger.info(feature_importance.head(10).to_string())

        return metrics, feature_importance

    def save_model(self, metrics, feature_importance):
        """
        Save trained model and related artifacts

        Args:
            metrics: Model metrics dictionary
            feature_importance: Feature importance DataFrame
        """
        logger.info("Saving model and artifacts...")

        # Timestamp for versioning
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save model
        model_path = os.path.join(self.model_dir, 'bank_statement_risk_model_latest.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved to {model_path}")

        # Save with timestamp
        model_path_ts = os.path.join(self.model_dir, f'bank_statement_risk_model_{timestamp}.pkl')
        with open(model_path_ts, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Timestamped model saved to {model_path_ts}")

        # Save scaler
        scaler_path = os.path.join(self.model_dir, 'bank_statement_scaler_latest.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        logger.info(f"Scaler saved to {scaler_path}")

        # Save with timestamp
        scaler_path_ts = os.path.join(self.model_dir, f'bank_statement_scaler_{timestamp}.pkl')
        with open(scaler_path_ts, 'wb') as f:
            pickle.dump(self.scaler, f)
        logger.info(f"Timestamped scaler saved to {scaler_path_ts}")

        # Save metadata
        metadata = {
            'model_type': 'RandomForestClassifier',
            'n_estimators': 150,
            'max_depth': 12,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'max_features': 'sqrt',
            'class_weight': 'balanced',
            'feature_names': self.feature_names,
            'metrics': metrics,
            'training_date': datetime.now().isoformat(),
            'training_file': 'dataset/staement_fraud_5000.csv',
            'top_features': feature_importance.head(10).to_dict('records')
        }

        metadata_path = os.path.join(self.model_dir, 'bank_statement_model_metadata_latest.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to {metadata_path}")

        # Save with timestamp
        metadata_path_ts = os.path.join(self.model_dir, f'bank_statement_model_metadata_{timestamp}.json')
        with open(metadata_path_ts, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Timestamped metadata saved to {metadata_path_ts}")

        logger.info("\n✅ Model training complete!")
        logger.info(f"Model files saved in {self.model_dir}/")
        logger.info(f"Files:")
        logger.info(f"  - bank_statement_risk_model_latest.pkl")
        logger.info(f"  - bank_statement_scaler_latest.pkl")
        logger.info(f"  - bank_statement_model_metadata_latest.json")


def main():
    """Main training function"""
    # Path to training data
    data_path = '../dataset/staement_fraud_5000.csv'

    if not os.path.exists(data_path):
        logger.error(f"Training data not found at {data_path}")
        logger.info("Please ensure dataset/staement_fraud_5000.csv exists")
        return

    # Initialize trainer
    trainer = BankStatementModelTrainer()

    # Load and prepare data
    df = trainer.load_training_data(data_path)
    X, y, feature_names = trainer.prepare_features(df)

    # Train model
    metrics, feature_importance = trainer.train_random_forest(X, y)

    # Save model
    trainer.save_model(metrics, feature_importance)

    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info("\nYour Random Forest model is ready for bank statement fraud detection!")
    logger.info("The model will be automatically loaded when the API starts.")


if __name__ == '__main__':
    main()
