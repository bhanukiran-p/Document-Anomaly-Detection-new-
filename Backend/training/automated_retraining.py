"""
Automated Model Retraining for Document Fraud Detection
Supports checks, paystubs, money orders, and bank statements with:
- Smart data blending (synthetic → hybrid → real)
- Model versioning and rollback
- Performance tracking
"""

import os
import sys
import json
import joblib
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb

from training.model_performance_tracker import ModelPerformanceTracker

logger = logging.getLogger(__name__)


class DocumentModelRetrainer(ABC):
    """
    Base class for document-specific model retraining
    Handles data blending, training, versioning, and rollback
    """

    def __init__(self, document_type: str, config_path: str = None):
        """
        Initialize retrainer for a specific document type

        Args:
            document_type: Type of document (paystub, check, money_order, bank_statement)
            config_path: Path to retraining_config.json (optional)
        """
        self.document_type = document_type

        # Load configuration
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'retraining_config.json'
            )

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.global_settings = self.config['global_settings']
        self.data_blending_config = self.config['data_blending']
        self.doc_config = self.config['document_types'][document_type]

        # Initialize performance tracker
        self.performance_tracker = ModelPerformanceTracker(document_type)

        # Set up output directory - use absolute path to production location
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.models_dir = os.path.join(backend_dir, f"{document_type}/ml/models")
        os.makedirs(self.models_dir, exist_ok=True)

        logger.info(f"Initialized {document_type} model retrainer")

    @abstractmethod
    def generate_synthetic_data(self, n_samples: int) -> pd.DataFrame:
        """
        Generate synthetic training data

        Args:
            n_samples: Number of samples to generate

        Returns:
            DataFrame with features and risk_score column
        """
        pass

    @abstractmethod
    def fetch_real_data_from_database(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Fetch real data from database

        Returns:
            Tuple of (DataFrame with features and labels, error message)
        """
        pass

    def blend_data(
        self,
        real_df: Optional[pd.DataFrame],
        synthetic_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, str]:
        """
        Blend synthetic and real data based on configuration thresholds

        Args:
            real_df: Real data from database (or None)
            synthetic_df: Synthetic data

        Returns:
            Tuple of (blended DataFrame, data_source string)
        """
        if real_df is None or len(real_df) == 0:
            logger.info(f"No real data available, using 100% synthetic data ({len(synthetic_df)} samples)")
            return synthetic_df, "synthetic"

        real_count = len(real_df)
        min_hybrid = self.data_blending_config['min_real_samples_for_hybrid']
        min_real_only = self.data_blending_config['min_real_samples_for_real_only']

        if real_count < min_hybrid:
            # Not enough real data, use 100% synthetic
            logger.info(f"Only {real_count} real samples (< {min_hybrid}), using 100% synthetic")
            return synthetic_df, "synthetic"

        elif real_count < min_real_only:
            # Hybrid mode: blend synthetic + real
            synthetic_weight = self.data_blending_config['synthetic_weight_hybrid']
            real_weight = self.data_blending_config['real_weight_hybrid']

            # Calculate number of synthetic samples to blend
            # We want final mix to be: synthetic_weight% synthetic + real_weight% real
            synthetic_sample_count = int(real_count * (synthetic_weight / real_weight))

            if synthetic_sample_count > len(synthetic_df):
                synthetic_sample_count = len(synthetic_df)

            synthetic_sample = synthetic_df.sample(n=synthetic_sample_count, random_state=42)
            blended_df = pd.concat([synthetic_sample, real_df], ignore_index=True)

            logger.info(
                f"Hybrid mode: {len(synthetic_sample)} synthetic + {real_count} real = "
                f"{len(blended_df)} total ({synthetic_weight*100:.0f}%/{real_weight*100:.0f}% split)"
            )
            return blended_df, "hybrid"

        else:
            # Enough real data, use 100% real
            logger.info(f"Using 100% real data ({real_count} samples)")
            return real_df, "real"

    def validate_data_quality(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate training data quality

        Args:
            df: DataFrame with features and risk_score column

        Returns:
            Tuple of (is_valid, error_message)
        """
        min_samples = self.global_settings['min_samples_for_training']
        min_per_class = self.global_settings['min_samples_per_class']

        # Check minimum total samples
        if len(df) < min_samples:
            return False, f"Insufficient samples: {len(df)} < {min_samples}"

        # Check for risk_score column
        if 'risk_score' not in df.columns:
            return False, "Missing risk_score column"

        # Check class balance (fraud vs legitimate)
        # Consider <30 as legitimate, >70 as fraud
        legitimate_count = len(df[df['risk_score'] <= 30])
        fraud_count = len(df[df['risk_score'] >= 70])

        if legitimate_count < min_per_class:
            return False, f"Too few legitimate samples: {legitimate_count} < {min_per_class}"

        if fraud_count < min_per_class:
            return False, f"Too few fraud samples: {fraud_count} < {min_per_class}"

        # Check fraud ratio (should be between 5% and 95%)
        fraud_ratio = fraud_count / len(df)
        if fraud_ratio < 0.05 or fraud_ratio > 0.95:
            logger.warning(f"Extreme fraud ratio: {fraud_ratio:.2%}")

        # Check for all-zero features
        feature_cols = [col for col in df.columns if col != 'risk_score']
        for col in feature_cols:
            if df[col].sum() == 0 and df[col].nunique() == 1:
                logger.warning(f"Feature '{col}' is all zeros")

        return True, "Data quality checks passed"

    def train_ensemble_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[Any, Any, Any, Dict[str, float]]:
        """
        Train Random Forest + XGBoost ensemble

        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data

        Returns:
            Tuple of (rf_model, xgb_model, scaler, metrics_dict)
        """
        logger.info("Training ensemble models (Random Forest + XGBoost)...")

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train Random Forest
        logger.info("Training Random Forest...")
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        start_time = datetime.now()
        rf_model.fit(X_train_scaled, y_train)
        rf_train_time = (datetime.now() - start_time).total_seconds()

        rf_pred_test = rf_model.predict(X_test_scaled)
        rf_mse = mean_squared_error(y_test, rf_pred_test)
        rf_r2 = r2_score(y_test, rf_pred_test)
        logger.info(f"Random Forest - MSE: {rf_mse:.4f}, R²: {rf_r2:.4f}")

        # Train XGBoost
        logger.info("Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        start_time = datetime.now()
        xgb_model.fit(X_train_scaled, y_train)
        xgb_train_time = (datetime.now() - start_time).total_seconds()

        xgb_pred_test = xgb_model.predict(X_test_scaled)
        xgb_mse = mean_squared_error(y_test, xgb_pred_test)
        xgb_r2 = r2_score(y_test, xgb_pred_test)
        logger.info(f"XGBoost - MSE: {xgb_mse:.4f}, R²: {xgb_r2:.4f}")

        # Ensemble prediction (40% RF + 60% XGB)
        rf_weight = self.doc_config['ensemble_weights']['random_forest']
        xgb_weight = self.doc_config['ensemble_weights']['xgboost']

        ensemble_pred = rf_weight * rf_pred_test + xgb_weight * xgb_pred_test
        ensemble_mse = mean_squared_error(y_test, ensemble_pred)
        ensemble_r2 = r2_score(y_test, ensemble_pred)

        logger.info(
            f"Ensemble ({rf_weight*100:.0f}% RF + {xgb_weight*100:.0f}% XGB) - "
            f"MSE: {ensemble_mse:.4f}, R²: {ensemble_r2:.4f}"
        )

        metrics = {
            'r2_score': float(ensemble_r2),
            'mse': float(ensemble_mse),
            'rf_r2': float(rf_r2),
            'rf_mse': float(rf_mse),
            'xgb_r2': float(xgb_r2),
            'xgb_mse': float(xgb_mse),
            'training_time_seconds': float(rf_train_time + xgb_train_time)
        }

        return rf_model, xgb_model, scaler, metrics

    def save_versioned_model(
        self,
        rf_model: Any,
        xgb_model: Any,
        scaler: Any,
        version_id: str
    ) -> bool:
        """
        Save models with versioned filenames

        Args:
            rf_model: Trained Random Forest model
            xgb_model: Trained XGBoost model
            scaler: Fitted StandardScaler
            version_id: Version timestamp (e.g., "20250122_143052")

        Returns:
            True if saved successfully
        """
        try:
            # Save each model with versioned filename
            rf_path = os.path.join(
                self.models_dir,
                f"{self.document_type}_random_forest_{version_id}.pkl"
            )
            xgb_path = os.path.join(
                self.models_dir,
                f"{self.document_type}_xgboost_{version_id}.pkl"
            )
            scaler_path = os.path.join(
                self.models_dir,
                f"{self.document_type}_feature_scaler_{version_id}.pkl"
            )

            joblib.dump(rf_model, rf_path)
            logger.info(f"Saved: {os.path.basename(rf_path)}")

            joblib.dump(xgb_model, xgb_path)
            logger.info(f"Saved: {os.path.basename(xgb_path)}")

            joblib.dump(scaler, scaler_path)
            logger.info(f"Saved: {os.path.basename(scaler_path)}")

            return True

        except Exception as e:
            logger.error(f"Error saving versioned models: {e}")
            return False

    def retrain(self) -> Dict[str, Any]:
        """
        Main retraining workflow

        Returns:
            Dictionary with retraining results
        """
        try:
            logger.info(f"="*70)
            logger.info(f"Starting automated retraining for {self.document_type}")
            logger.info(f"="*70)

            # Generate version ID (timestamp)
            version_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info(f"Version ID: {version_id}")

            # Step 1: Fetch real data from database
            logger.info("\nStep 1: Fetching real data from database...")
            real_df, error = self.fetch_real_data_from_database()
            if error:
                logger.warning(f"Database fetch error: {error}")

            # Step 2: Generate synthetic data
            logger.info("\nStep 2: Generating synthetic data...")
            synthetic_count = self.data_blending_config['synthetic_sample_count']
            synthetic_df = self.generate_synthetic_data(n_samples=synthetic_count)
            logger.info(f"Generated {len(synthetic_df)} synthetic samples")

            # Step 3: Blend data
            logger.info("\nStep 3: Blending data...")
            blended_df, data_source = self.blend_data(real_df, synthetic_df)

            # Step 4: Validate data quality
            logger.info("\nStep 4: Validating data quality...")
            is_valid, validation_msg = self.validate_data_quality(blended_df)
            if not is_valid:
                logger.error(f"Data validation failed: {validation_msg}")
                return {
                    'success': False,
                    'error': f"Data validation failed: {validation_msg}"
                }
            logger.info(f"✓ {validation_msg}")

            # Step 5: Prepare training data
            logger.info("\nStep 5: Preparing training data...")
            X = blended_df.drop('risk_score', axis=1).values
            y = blended_df['risk_score'].values

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            logger.info(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")

            # Calculate training data stats
            fraud_count = len(blended_df[blended_df['risk_score'] >= 70])
            fraud_ratio = fraud_count / len(blended_df)

            training_data_info = {
                'total_samples': len(blended_df),
                'real_samples': len(real_df) if real_df is not None else 0,
                'synthetic_samples': len(blended_df) - (len(real_df) if real_df is not None else 0),
                'fraud_count': int(fraud_count),
                'fraud_ratio': float(fraud_ratio)
            }

            # Step 6: Train models
            logger.info("\nStep 6: Training ensemble models...")
            rf_model, xgb_model, scaler, metrics = self.train_ensemble_model(
                X_train, y_train, X_test, y_test
            )

            # Step 7: Save metrics
            logger.info("\nStep 7: Saving performance metrics...")
            self.performance_tracker.save_metrics(
                version_id=version_id,
                metrics=metrics,
                data_source=data_source,
                training_data_info=training_data_info
            )

            # Step 8: Compare with previous version
            logger.info("\nStep 8: Comparing with previous version...")
            threshold_drop = self.global_settings['rollback_threshold_drop']
            comparison = self.performance_tracker.compare_with_previous(
                new_metrics=metrics,
                threshold_drop=threshold_drop
            )

            logger.info(f"Comparison: {comparison['reason']}")
            logger.info(f"Previous R²: {comparison['previous_r2']}, New R²: {comparison['new_r2']}, Delta: {comparison['delta']}")

            if not comparison['should_activate']:
                logger.warning("⚠️  New model not activated due to performance drop")
                return {
                    'success': True,
                    'activated': False,
                    'version_id': version_id,
                    'reason': comparison['reason'],
                    'metrics': metrics,
                    'data_source': data_source,
                    'training_data': training_data_info
                }

            # Step 9: Save versioned models
            logger.info("\nStep 9: Saving versioned models...")
            save_success = self.save_versioned_model(
                rf_model, xgb_model, scaler, version_id
            )

            if not save_success:
                return {
                    'success': False,
                    'error': 'Failed to save models'
                }

            # Step 10: Activate new version
            logger.info("\nStep 10: Activating new version...")
            activate_success = self.performance_tracker.activate_version(version_id)

            if not activate_success:
                return {
                    'success': False,
                    'error': 'Failed to activate new version'
                }

            # Step 11: Cleanup old versions
            logger.info("\nStep 11: Cleaning up old versions...")
            keep_n = self.global_settings['keep_n_versions']
            self.performance_tracker.cleanup_old_versions(keep_n=keep_n)

            logger.info(f"\n{'='*70}")
            logger.info(f"✅ Retraining completed successfully for {self.document_type}")
            logger.info(f"✅ Version {version_id} is now ACTIVE")
            logger.info(f"{'='*70}\n")

            return {
                'success': True,
                'activated': True,
                'version_id': version_id,
                'metrics': metrics,
                'data_source': data_source,
                'training_data': training_data_info,
                'comparison': comparison
            }

        except Exception as e:
            logger.error(f"Retraining failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# Import Supabase client for database access
try:
    from database.supabase_client import get_supabase_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase client not available - database fetch will fail")
