"""
Model Performance Tracker for Document Fraud Detection
Tracks model performance over time and enables rollback decisions
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelPerformanceTracker:
    """Track and compare model performance across versions"""

    def __init__(self, document_type: str):
        """
        Initialize performance tracker for a document type

        Args:
            document_type: Type of document (paystub, check, money_order, bank_statement)
        """
        self.document_type = document_type
        self.models_dir = os.path.join(f"{document_type}/ml/models")
        os.makedirs(self.models_dir, exist_ok=True)

        self.history_path = os.path.join(self.models_dir, "performance_history.json")
        self.active_version_path = os.path.join(self.models_dir, "ACTIVE_VERSION.txt")

    def load_history(self) -> List[Dict[str, Any]]:
        """Load performance history from JSON file"""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading performance history: {e}")
                return []
        return []

    def save_history(self, history: List[Dict[str, Any]]):
        """Save performance history to JSON file"""
        try:
            with open(self.history_path, 'w') as f:
                json.dump(history, f, indent=2)
            logger.info(f"Saved performance history to {self.history_path}")
        except Exception as e:
            logger.error(f"Error saving performance history: {e}")

    def save_metrics(
        self,
        version_id: str,
        metrics: Dict[str, Any],
        data_source: str,
        training_data_info: Dict[str, Any]
    ) -> bool:
        """
        Save metrics for a model version

        Args:
            version_id: Timestamp-based version ID (e.g., "20250122_143052")
            metrics: Dictionary containing r2_score, mse, training_time_seconds, etc.
            data_source: "synthetic", "hybrid", or "real"
            training_data_info: Info about training data (real_samples, synthetic_samples, fraud_ratio)

        Returns:
            True if saved successfully
        """
        try:
            history = self.load_history()

            entry = {
                "version_id": version_id,
                "timestamp": datetime.now().isoformat(),
                "data_source": data_source,
                "training_data": training_data_info,
                "metrics": metrics,
                "is_active": False  # Will be updated if activated
            }

            history.append(entry)
            self.save_history(history)

            logger.info(f"Saved metrics for version {version_id}: R²={metrics.get('r2_score', 0):.3f}, MSE={metrics.get('mse', 0):.2f}")
            return True

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return False

    def get_previous_metrics(self) -> Optional[Dict[str, Any]]:
        """Get metrics for the most recent active version"""
        history = self.load_history()

        # Find most recent active version
        for entry in reversed(history):
            if entry.get('is_active'):
                return entry

        # If no active version found, return most recent entry
        if history:
            return history[-1]

        return None

    def compare_with_previous(
        self,
        new_metrics: Dict[str, Any],
        threshold_drop: float = 0.15
    ) -> Dict[str, Any]:
        """
        Compare new model metrics with previous version

        Args:
            new_metrics: Metrics dict with r2_score, mse, etc.
            threshold_drop: Maximum allowed R² score drop (default: 0.15 = 15%)

        Returns:
            Dict with:
                - should_activate: bool (whether to activate new model)
                - reason: str (explanation)
                - previous_r2: float (or None)
                - new_r2: float
                - delta: float (new - previous)
        """
        previous = self.get_previous_metrics()
        new_r2 = new_metrics.get('r2_score', 0)

        # If no previous model, activate new one
        if previous is None:
            return {
                'should_activate': True,
                'reason': 'No previous model found - activating first version',
                'previous_r2': None,
                'new_r2': new_r2,
                'delta': None
            }

        previous_r2 = previous.get('metrics', {}).get('r2_score', 0)
        delta = new_r2 - previous_r2

        # Check if performance dropped significantly
        if delta < -threshold_drop:
            return {
                'should_activate': False,
                'reason': f'Performance dropped by {abs(delta):.3f} (threshold: {threshold_drop}) - keeping previous version',
                'previous_r2': previous_r2,
                'new_r2': new_r2,
                'delta': delta
            }

        # Performance is acceptable or improved
        if delta >= 0:
            reason = f'Performance improved by {delta:.3f}'
        else:
            reason = f'Performance dropped by {abs(delta):.3f} but within acceptable threshold'

        return {
            'should_activate': True,
            'reason': reason,
            'previous_r2': previous_r2,
            'new_r2': new_r2,
            'delta': delta
        }

    def activate_version(self, version_id: str) -> bool:
        """
        Mark a version as active and update ACTIVE_VERSION.txt

        Args:
            version_id: Version to activate (e.g., "20250122_143052")

        Returns:
            True if activated successfully
        """
        try:
            # Update history - mark this version as active, others as inactive
            history = self.load_history()
            for entry in history:
                entry['is_active'] = (entry['version_id'] == version_id)
            self.save_history(history)

            # Update ACTIVE_VERSION.txt
            with open(self.active_version_path, 'w') as f:
                f.write(version_id)

            logger.info(f"Activated version {version_id} for {self.document_type}")
            return True

        except Exception as e:
            logger.error(f"Error activating version {version_id}: {e}")
            return False

    def get_active_version(self) -> Optional[str]:
        """Get currently active version ID"""
        if os.path.exists(self.active_version_path):
            try:
                with open(self.active_version_path, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Error reading active version: {e}")
        return None

    def cleanup_old_versions(self, keep_n: int = 5):
        """
        Delete old model files, keeping only the N most recent versions

        Args:
            keep_n: Number of recent versions to keep (default: 5)
        """
        try:
            history = self.load_history()

            # Sort by timestamp (oldest first)
            history.sort(key=lambda x: x['version_id'])

            # Identify versions to delete (all except last N)
            if len(history) > keep_n:
                versions_to_delete = history[:-keep_n]

                for entry in versions_to_delete:
                    version_id = entry['version_id']

                    # Delete model files for this version
                    for model_type in ['random_forest', 'xgboost', 'feature_scaler']:
                        model_filename = f"{self.document_type}_{model_type}_{version_id}.pkl"
                        model_path = os.path.join(self.models_dir, model_filename)

                        if os.path.exists(model_path):
                            os.remove(model_path)
                            logger.info(f"Deleted old model file: {model_filename}")

                # Remove from history
                history = history[-keep_n:]
                self.save_history(history)

                logger.info(f"Cleaned up old versions, kept last {keep_n}")
            else:
                logger.info(f"Only {len(history)} versions exist, no cleanup needed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of model performance over time"""
        history = self.load_history()

        if not history:
            return {
                'total_versions': 0,
                'active_version': None,
                'versions': []
            }

        return {
            'total_versions': len(history),
            'active_version': self.get_active_version(),
            'versions': [
                {
                    'version_id': entry['version_id'],
                    'timestamp': entry.get('timestamp'),
                    'data_source': entry.get('data_source'),
                    'r2_score': entry.get('metrics', {}).get('r2_score'),
                    'mse': entry.get('metrics', {}).get('mse'),
                    'is_active': entry.get('is_active', False),
                    'training_samples': entry.get('training_data', {}).get('total_samples')
                }
                for entry in history
            ]
        }
