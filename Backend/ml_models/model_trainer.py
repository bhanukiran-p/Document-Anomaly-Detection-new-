"""
Model Training Pipeline for Money Order Fraud Detection
Trains Random Forest and XGBoost models on prepared data
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import warnings
warnings.filterwarnings('ignore')

# Try to import XGBoost (optional dependency)
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    print("Warning: XGBoost not installed. Will train Random Forest only.")
    XGBOOST_AVAILABLE = False

# Import our feature extractor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml_models.feature_extractor import FeatureExtractor


class ModelTrainer:
    """
    Train ML models for fraud detection
    """

    def __init__(self, output_dir: str = 'ml_models'):
        """
        Initialize trainer

        Args:
            output_dir: Directory to save trained models
        """
        self.output_dir = output_dir
        self.feature_extractor = FeatureExtractor()
        self.scaler = StandardScaler()
        self.rf_model = None
        self.xgb_model = None
        self.feature_names = self.feature_extractor.get_feature_names()

        # Training metrics
        self.metrics = {}

    def load_training_data(self, csv_path: str) -> pd.DataFrame:
        """
        Load training data from CSV

        Args:
            csv_path: Path to training data CSV

        Returns:
            pandas DataFrame
        """
        print(f"Loading training data from: {csv_path}")
        df = pd.DataFrame(pd.read_csv(csv_path))

        print(f"Loaded {len(df)} samples")
        print(f"  Fraud: {df['is_fraud'].sum()} ({df['is_fraud'].sum()/len(df)*100:.1f}%)")
        print(f"  Legitimate: {(1-df['is_fraud']).sum()} ({(1-df['is_fraud']).sum()/len(df)*100:.1f}%)")

        return df

    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """
        Extract features from raw data

        Args:
            df: DataFrame with money order data

        Returns:
            Tuple of (X, y) where X is feature matrix and y is labels
        """
        print("\nExtracting features...")

        X = []
        y = []

        for idx, row in df.iterrows():
            # Convert row to dictionary format expected by feature extractor
            data = {
                'issuer_name': row.get('issuer_name'),
                'serial_primary': row.get('serial_primary'),
                'serial_secondary': row.get('serial_secondary'),
                'recipient': row.get('recipient'),
                'sender_name': row.get('sender_name'),
                'sender_address': row.get('sender_address'),
                'amount_numeric': {
                    'value': row.get('amount_value', 0),
                    'currency': row.get('amount_currency', 'USD')
                },
                'amount_written': row.get('amount_written'),
                'date': row.get('date'),
                'signature': row.get('signature')
            }

            # Extract features
            features = self.feature_extractor.extract_features(data, raw_text="")
            X.append(features)
            y.append(row['is_fraud'])

            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(df)} samples")

        X = np.array(X)
        y = np.array(y)

        print(f"\nFeature extraction complete:")
        print(f"  Feature matrix shape: {X.shape}")
        print(f"  Number of features: {len(self.feature_names)}")

        return X, y

    def split_data(self, X: np.ndarray, y: np.ndarray,
                   test_size: float = 0.15, val_size: float = 0.15,
                   random_state: int = 42) -> tuple:
        """
        Split data into train, validation, and test sets

        Args:
            X: Feature matrix
            y: Labels
            test_size: Proportion for test set
            val_size: Proportion for validation set
            random_state: Random seed

        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        # First split: separate test set
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Second split: separate validation from training
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio, random_state=random_state, stratify=y_temp
        )

        print(f"\nData split:")
        print(f"  Training set: {len(X_train)} samples ({len(X_train)/len(X)*100:.1f}%)")
        print(f"  Validation set: {len(X_val)} samples ({len(X_val)/len(X)*100:.1f}%)")
        print(f"  Test set: {len(X_test)} samples ({len(X_test)/len(X)*100:.1f}%)")

        return X_train, X_val, X_test, y_train, y_val, y_test

    def scale_features(self, X_train: np.ndarray, X_val: np.ndarray, X_test: np.ndarray) -> tuple:
        """
        Scale features using StandardScaler

        Args:
            X_train, X_val, X_test: Feature matrices

        Returns:
            Tuple of scaled feature matrices
        """
        print("\nScaling features...")

        # Fit scaler on training data only
        self.scaler.fit(X_train)

        # Transform all sets
        X_train_scaled = self.scaler.transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)

        print("  Features scaled using StandardScaler")

        return X_train_scaled, X_val_scaled, X_test_scaled

    def train_random_forest(self, X_train: np.ndarray, y_train: np.ndarray,
                           X_val: np.ndarray, y_val: np.ndarray,
                           tune_hyperparameters: bool = False) -> RandomForestClassifier:
        """
        Train Random Forest classifier

        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data
            tune_hyperparameters: Whether to perform grid search

        Returns:
            Trained RandomForestClassifier
        """
        print("\n" + "="*60)
        print("Training Random Forest Classifier")
        print("="*60)

        if tune_hyperparameters:
            print("Performing hyperparameter tuning...")
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }

            rf = RandomForestClassifier(random_state=42)
            grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='f1',
                                      n_jobs=-1, verbose=1)
            grid_search.fit(X_train, y_train)

            print(f"Best parameters: {grid_search.best_params_}")
            self.rf_model = grid_search.best_estimator_
        else:
            # Use default good parameters
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

            print("Training with default parameters...")
            self.rf_model.fit(X_train, y_train)

        # Cross-validation on training set
        cv_scores = cross_val_score(self.rf_model, X_train, y_train, cv=5, scoring='f1')
        print(f"\nCross-validation F1 scores: {cv_scores}")
        print(f"Mean CV F1 score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        # Validation set performance
        y_val_pred = self.rf_model.predict(X_val)
        val_accuracy = accuracy_score(y_val, y_val_pred)
        val_precision = precision_score(y_val, y_val_pred)
        val_recall = recall_score(y_val, y_val_pred)
        val_f1 = f1_score(y_val, y_val_pred)

        print(f"\nValidation Set Performance:")
        print(f"  Accuracy: {val_accuracy:.4f}")
        print(f"  Precision: {val_precision:.4f}")
        print(f"  Recall: {val_recall:.4f}")
        print(f"  F1-Score: {val_f1:.4f}")

        # Store metrics
        self.metrics['rf'] = {
            'val_accuracy': val_accuracy,
            'val_precision': val_precision,
            'val_recall': val_recall,
            'val_f1': val_f1,
            'cv_f1_mean': cv_scores.mean(),
            'cv_f1_std': cv_scores.std()
        }

        return self.rf_model

    def train_xgboost(self, X_train: np.ndarray, y_train: np.ndarray,
                     X_val: np.ndarray, y_val: np.ndarray) -> 'XGBClassifier':
        """
        Train XGBoost classifier

        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data

        Returns:
            Trained XGBClassifier or None if XGBoost not available
        """
        if not XGBOOST_AVAILABLE:
            print("\nXGBoost not available, skipping...")
            return None

        print("\n" + "="*60)
        print("Training XGBoost Classifier")
        print("="*60)

        self.xgb_model = XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            min_child_weight=1,
            gamma=0,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )

        print("Training XGBoost model...")
        self.xgb_model.fit(X_train, y_train)

        # Validation set performance
        y_val_pred = self.xgb_model.predict(X_val)
        val_accuracy = accuracy_score(y_val, y_val_pred)
        val_precision = precision_score(y_val, y_val_pred)
        val_recall = recall_score(y_val, y_val_pred)
        val_f1 = f1_score(y_val, y_val_pred)

        print(f"\nValidation Set Performance:")
        print(f"  Accuracy: {val_accuracy:.4f}")
        print(f"  Precision: {val_precision:.4f}")
        print(f"  Recall: {val_recall:.4f}")
        print(f"  F1-Score: {val_f1:.4f}")

        # Store metrics
        self.metrics['xgb'] = {
            'val_accuracy': val_accuracy,
            'val_precision': val_precision,
            'val_recall': val_recall,
            'val_f1': val_f1
        }

        return self.xgb_model

    def evaluate_on_test_set(self, X_test: np.ndarray, y_test: np.ndarray):
        """
        Evaluate models on test set

        Args:
            X_test: Test feature matrix
            y_test: Test labels
        """
        print("\n" + "="*60)
        print("FINAL EVALUATION ON TEST SET")
        print("="*60)

        # Random Forest
        if self.rf_model:
            print("\nRandom Forest:")
            y_pred_rf = self.rf_model.predict(X_test)
            y_proba_rf = self.rf_model.predict_proba(X_test)[:, 1]

            print(f"  Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
            print(f"  Precision: {precision_score(y_test, y_pred_rf):.4f}")
            print(f"  Recall: {recall_score(y_test, y_pred_rf):.4f}")
            print(f"  F1-Score: {f1_score(y_test, y_pred_rf):.4f}")
            print(f"  ROC-AUC: {roc_auc_score(y_test, y_proba_rf):.4f}")

            self.metrics['rf']['test_accuracy'] = accuracy_score(y_test, y_pred_rf)
            self.metrics['rf']['test_precision'] = precision_score(y_test, y_pred_rf)
            self.metrics['rf']['test_recall'] = recall_score(y_test, y_pred_rf)
            self.metrics['rf']['test_f1'] = f1_score(y_test, y_pred_rf)
            self.metrics['rf']['test_roc_auc'] = roc_auc_score(y_test, y_proba_rf)

        # XGBoost
        if self.xgb_model:
            print("\nXGBoost:")
            y_pred_xgb = self.xgb_model.predict(X_test)
            y_proba_xgb = self.xgb_model.predict_proba(X_test)[:, 1]

            print(f"  Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")
            print(f"  Precision: {precision_score(y_test, y_pred_xgb):.4f}")
            print(f"  Recall: {recall_score(y_test, y_pred_xgb):.4f}")
            print(f"  F1-Score: {f1_score(y_test, y_pred_xgb):.4f}")
            print(f"  ROC-AUC: {roc_auc_score(y_test, y_proba_xgb):.4f}")

            self.metrics['xgb']['test_accuracy'] = accuracy_score(y_test, y_pred_xgb)
            self.metrics['xgb']['test_precision'] = precision_score(y_test, y_pred_xgb)
            self.metrics['xgb']['test_recall'] = recall_score(y_test, y_pred_xgb)
            self.metrics['xgb']['test_f1'] = f1_score(y_test, y_pred_xgb)
            self.metrics['xgb']['test_roc_auc'] = roc_auc_score(y_test, y_proba_xgb)

        # Ensemble (if both models available)
        if self.rf_model and self.xgb_model:
            print("\nEnsemble (RF: 40%, XGB: 60%):")
            y_proba_ensemble = 0.4 * y_proba_rf + 0.6 * y_proba_xgb
            y_pred_ensemble = (y_proba_ensemble >= 0.5).astype(int)

            print(f"  Accuracy: {accuracy_score(y_test, y_pred_ensemble):.4f}")
            print(f"  Precision: {precision_score(y_test, y_pred_ensemble):.4f}")
            print(f"  Recall: {recall_score(y_test, y_pred_ensemble):.4f}")
            print(f"  F1-Score: {f1_score(y_test, y_pred_ensemble):.4f}")
            print(f"  ROC-AUC: {roc_auc_score(y_test, y_proba_ensemble):.4f}")

            self.metrics['ensemble'] = {
                'test_accuracy': accuracy_score(y_test, y_pred_ensemble),
                'test_precision': precision_score(y_test, y_pred_ensemble),
                'test_recall': recall_score(y_test, y_pred_ensemble),
                'test_f1': f1_score(y_test, y_pred_ensemble),
                'test_roc_auc': roc_auc_score(y_test, y_proba_ensemble)
            }

    def save_models(self):
        """Save trained models and metadata"""
        print("\n" + "="*60)
        print("Saving Models")
        print("="*60)

        # Save Random Forest
        if self.rf_model:
            rf_path = os.path.join(self.output_dir, 'trained_random_forest.pkl')
            joblib.dump(self.rf_model, rf_path)
            print(f"✅ Random Forest saved to: {rf_path}")

        # Save XGBoost
        if self.xgb_model:
            xgb_path = os.path.join(self.output_dir, 'trained_xgboost.pkl')
            joblib.dump(self.xgb_model, xgb_path)
            print(f"✅ XGBoost saved to: {xgb_path}")

        # Save scaler
        scaler_path = os.path.join(self.output_dir, 'feature_scaler.pkl')
        joblib.dump(self.scaler, scaler_path)
        print(f"✅ Feature scaler saved to: {scaler_path}")

        # Save metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'num_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'metrics': self.metrics,
            'models_trained': []
        }

        if self.rf_model:
            metadata['models_trained'].append('random_forest')
        if self.xgb_model:
            metadata['models_trained'].append('xgboost')

        metadata_path = os.path.join(self.output_dir, 'model_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✅ Metadata saved to: {metadata_path}")

        print("\nAll models saved successfully!")

    def train_pipeline(self, csv_path: str, tune_rf: bool = False):
        """
        Complete training pipeline

        Args:
            csv_path: Path to training data CSV
            tune_rf: Whether to tune Random Forest hyperparameters
        """
        print("\n" + "="*60)
        print("MONEY ORDER FRAUD DETECTION - MODEL TRAINING PIPELINE")
        print("="*60)

        # 1. Load data
        df = self.load_training_data(csv_path)

        # 2. Extract features
        X, y = self.prepare_features(df)

        # 3. Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data(X, y)

        # 4. Scale features
        X_train_scaled, X_val_scaled, X_test_scaled = self.scale_features(
            X_train, X_val, X_test
        )

        # 5. Train Random Forest
        self.train_random_forest(X_train_scaled, y_train, X_val_scaled, y_val, tune_rf)

        # 6. Train XGBoost
        self.train_xgboost(X_train_scaled, y_train, X_val_scaled, y_val)

        # 7. Evaluate on test set
        self.evaluate_on_test_set(X_test_scaled, y_test)

        # 8. Save models
        self.save_models()

        print("\n" + "="*60)
        print("TRAINING COMPLETE!")
        print("="*60)


if __name__ == "__main__":
    # Example usage
    trainer = ModelTrainer(output_dir='ml_models')

    # Train on synthetic data (if it exists) or generate it first
    csv_path = 'ml_models/training_data.csv'

    if not os.path.exists(csv_path):
        print("Training data not found. Generating synthetic data...")
        from data_generator import generate_training_data
        generate_training_data(num_samples=2000, output_path=csv_path)

    # Run training pipeline
    trainer.train_pipeline(csv_path, tune_rf=False)
