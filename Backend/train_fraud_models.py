"""
Fraud Detection Model Training Script

This module trains XGBoost and Random Forest classifiers on transaction fraud data.
Models are saved to disk for later inference.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    classification_report
)
import xgboost as xgb
import joblib
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FraudModelTrainer:
    """Handles training and evaluation of fraud detection models."""

    # Categorical columns that need encoding
    CATEGORICAL_COLUMNS = [
        'customer_name',
        'bank_name',
        'merchant_name',
        'category'
    ]

    # Columns to drop (identifiers, not features)
    DROP_COLUMNS = [
        'statement_id',
        'account_number',
        'transaction_id',
        'transaction_description',
        'transaction_date',
        'statement_start_date',
        'statement_end_date'
    ]

    def __init__(self, data_path, model_dir='Backend/trained_models'):
        """
        Initialize the trainer.

        Args:
            data_path: Path to the CSV file
            model_dir: Directory to save trained models
        """
        self.data_path = data_path
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.label_encoders = {}

        self.xgb_model = None
        self.rf_model = None

    def load_data(self):
        """Load CSV data."""
        logger.info(f"Loading data from {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        logger.info(f"Data shape: {self.df.shape}")
        logger.info(f"\nData Info:\n{self.df.info()}")
        logger.info(f"\nMissing values:\n{self.df.isnull().sum()}")
        return self

    def preprocess_data(self):
        """
        Preprocess data:
        - Handle missing values
        - Encode categorical variables
        - Separate features and target
        """
        logger.info("Starting preprocessing...")

        # Separate target variable
        if 'is_fraud' not in self.df.columns:
            raise ValueError("Target column 'is_fraud' not found in data")

        y = self.df['is_fraud'].copy()
        X = self.df.drop('is_fraud', axis=1)

        # Drop unnecessary columns
        X = X.drop(columns=[col for col in self.DROP_COLUMNS if col in X.columns])

        # Handle missing values
        logger.info(f"Missing values before handling:\n{X.isnull().sum()}")

        # Fill numeric columns with mean
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if X[col].isnull().any():
                X[col].fillna(X[col].mean(), inplace=True)

        # Fill categorical columns with mode
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if X[col].isnull().any():
                X[col].fillna(X[col].mode()[0] if not X[col].mode().empty else 'Unknown', inplace=True)

        # Encode categorical variables
        logger.info(f"Encoding categorical columns: {self.CATEGORICAL_COLUMNS}")
        for col in self.CATEGORICAL_COLUMNS:
            if col in X.columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.label_encoders[col] = le
                logger.info(f"  - {col}: {len(le.classes_)} classes")

        # Ensure all columns are numeric
        X = X.select_dtypes(include=[np.number])

        logger.info(f"Final feature matrix shape: {X.shape}")
        logger.info(f"Target distribution:\n{y.value_counts()}")

        return X, y

    def split_data(self, X, y, test_size=0.2, random_state=42):
        """Split data into train and test sets."""
        logger.info(f"Splitting data: test_size={test_size}")
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        logger.info(f"Train set: {self.X_train.shape}")
        logger.info(f"Test set: {self.X_test.shape}")
        return self

    def train_xgboost(self):
        """Train XGBoost classifier."""
        logger.info("Training XGBoost classifier...")
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss',
            n_jobs=-1,
            verbosity=0
        )
        self.xgb_model.fit(self.X_train, self.y_train)
        logger.info("XGBoost training complete")
        return self

    def train_random_forest(self):
        """Train Random Forest classifier."""
        logger.info("Training Random Forest classifier...")
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        self.rf_model.fit(self.X_train, self.y_train)
        logger.info("Random Forest training complete")
        return self

    def evaluate_model(self, model, model_name):
        """
        Evaluate model on test set.

        Args:
            model: Trained model
            model_name: Name of model for logging

        Returns:
            dict: Evaluation metrics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluating {model_name}")
        logger.info(f"{'='*60}")

        y_pred = model.predict(self.X_test)
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]

        metrics = {
            'accuracy': accuracy_score(self.y_test, y_pred),
            'precision': precision_score(self.y_test, y_pred, zero_division=0),
            'recall': recall_score(self.y_test, y_pred, zero_division=0),
            'f1': f1_score(self.y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(self.y_test, y_pred_proba),
        }

        logger.info(f"Accuracy:  {metrics['accuracy']:.4f}")
        logger.info(f"Precision: {metrics['precision']:.4f}")
        logger.info(f"Recall:    {metrics['recall']:.4f}")
        logger.info(f"F1-Score:  {metrics['f1']:.4f}")
        logger.info(f"ROC-AUC:   {metrics['roc_auc']:.4f}")

        logger.info(f"\nConfusion Matrix:\n{confusion_matrix(self.y_test, y_pred)}")
        logger.info(f"\nClassification Report:\n{classification_report(self.y_test, y_pred)}")

        return metrics

    def save_models(self):
        """Save trained models and label encoders to disk."""
        logger.info("\nSaving models to disk...")

        xgb_path = self.model_dir / 'xgboost_model.pkl'
        rf_path = self.model_dir / 'random_forest_model.pkl'
        encoders_path = self.model_dir / 'label_encoders.pkl'

        joblib.dump(self.xgb_model, xgb_path)
        logger.info(f"XGBoost model saved to {xgb_path}")

        joblib.dump(self.rf_model, rf_path)
        logger.info(f"Random Forest model saved to {rf_path}")

        joblib.dump(self.label_encoders, encoders_path)
        logger.info(f"Label encoders saved to {encoders_path}")

    def train(self):
        """
        Execute complete training pipeline.

        Returns:
            tuple: (xgb_metrics, rf_metrics)
        """
        self.load_data()
        X, y = self.preprocess_data()
        self.split_data(X, y)

        self.train_xgboost()
        self.train_random_forest()

        xgb_metrics = self.evaluate_model(self.xgb_model, "XGBoost Classifier")
        rf_metrics = self.evaluate_model(self.rf_model, "Random Forest Classifier")

        self.save_models()

        return xgb_metrics, rf_metrics


def compare_models(xgb_metrics, rf_metrics):
    """Print comparison between models."""
    logger.info(f"\n{'='*60}")
    logger.info("MODEL COMPARISON")
    logger.info(f"{'='*60}\n")

    metrics_names = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']

    print(f"{'Metric':<15} {'XGBoost':<15} {'Random Forest':<15} {'Winner':<15}")
    print("-" * 60)

    for metric in metrics_names:
        xgb_val = xgb_metrics[metric]
        rf_val = rf_metrics[metric]
        winner = "XGBoost" if xgb_val > rf_val else "Random Forest" if rf_val > xgb_val else "Tie"
        print(f"{metric:<15} {xgb_val:<15.4f} {rf_val:<15.4f} {winner:<15}")

    # Overall winner
    xgb_wins = sum(1 for m in metrics_names if xgb_metrics[m] > rf_metrics[m])
    rf_wins = sum(1 for m in metrics_names if rf_metrics[m] > xgb_metrics[m])

    logger.info(f"\nOverall: XGBoost wins {xgb_wins}/{len(metrics_names)}, "
                f"Random Forest wins {rf_wins}/{len(metrics_names)}")

    if xgb_wins > rf_wins:
        logger.info("\n✓ WINNER: XGBoost Classifier")
    elif rf_wins > xgb_wins:
        logger.info("\n✓ WINNER: Random Forest Classifier")
    else:
        logger.info("\n✓ RESULT: Tie - Both models perform equally well")


if __name__ == '__main__':
    # Path to the fraud dataset
    DATA_PATH = 'dataset/staement_fraud_5000.csv'

    # Create trainer and run pipeline
    trainer = FraudModelTrainer(DATA_PATH)
    xgb_metrics, rf_metrics = trainer.train()

    # Compare models
    compare_models(xgb_metrics, rf_metrics)
