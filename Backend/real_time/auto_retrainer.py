"""
Automatic Model Retraining System
Periodically checks Supabase database for new labeled data and retrains the fraud detection model
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import os

logger = logging.getLogger(__name__)

# Retraining configuration
RETRAIN_CHECK_INTERVAL = 3600  # Check every hour (in seconds)
MIN_NEW_SAMPLES_FOR_RETRAIN = 500  # Minimum new samples needed to trigger retraining
MIN_FRAUD_SAMPLES = 50  # Minimum fraud samples required
MODEL_METADATA_PATH = 'real_time/models/model_metadata.json'


class AutoRetrainer:
    """
    Automatic model retraining system that monitors database for new data
    and triggers retraining when sufficient labeled data accumulates
    """

    def __init__(self,
                 check_interval: int = RETRAIN_CHECK_INTERVAL,
                 min_new_samples: int = MIN_NEW_SAMPLES_FOR_RETRAIN,
                 min_fraud_samples: int = MIN_FRAUD_SAMPLES):
        """
        Initialize auto-retrainer

        Args:
            check_interval: Seconds between database checks
            min_new_samples: Minimum new samples to trigger retraining
            min_fraud_samples: Minimum fraud samples required
        """
        self.check_interval = check_interval
        self.min_new_samples = min_new_samples
        self.min_fraud_samples = min_fraud_samples
        self.is_running = False
        self.thread = None
        self.last_check = None
        self.last_retrain = None
        self.retraining_in_progress = False

    def start(self):
        """Start the automatic retraining scheduler"""
        if self.is_running:
            logger.warning("Auto-retrainer already running")
            return

        logger.info(f"Starting automatic model retraining scheduler (check interval: {self.check_interval}s)")
        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the automatic retraining scheduler"""
        logger.info("Stopping automatic model retraining scheduler")
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                self.last_check = datetime.now()
                logger.info("Checking for new training data in database...")

                # Check if retraining is needed
                should_retrain, stats = self._should_retrain()

                if should_retrain:
                    logger.info(f"Retraining triggered: {stats}")
                    self._perform_retraining()
                else:
                    logger.info(f"No retraining needed: {stats}")

            except Exception as e:
                logger.error(f"Error in auto-retraining scheduler: {e}", exc_info=True)

            # Sleep until next check
            time.sleep(self.check_interval)

    def _should_retrain(self) -> tuple[bool, Dict[str, Any]]:
        """
        Check if model should be retrained

        Returns:
            Tuple of (should_retrain, statistics)
        """
        try:
            # Get last training timestamp from metadata
            last_train_time = self._get_last_training_time()
            last_train_samples = self._get_last_training_samples()

            # Get current database statistics
            from database.supabase_client import get_supabase
            supabase = get_supabase()

            # Count total samples in database
            response = supabase.table('analyzed_real_time_trn').select('*', count='exact').execute()
            total_samples = response.count if hasattr(response, 'count') else len(response.data)

            # Count fraud samples
            fraud_response = supabase.table('analyzed_real_time_trn').select('*', count='exact').eq('is_fraud', 1).execute()
            fraud_samples = fraud_response.count if hasattr(fraud_response, 'count') else len(fraud_response.data)

            # Calculate new samples since last training
            new_samples = total_samples - last_train_samples

            stats = {
                'total_samples': total_samples,
                'fraud_samples': fraud_samples,
                'last_train_samples': last_train_samples,
                'new_samples': new_samples,
                'last_train_time': last_train_time.isoformat() if last_train_time else None,
                'min_new_samples_threshold': self.min_new_samples,
                'min_fraud_threshold': self.min_fraud_samples
            }

            # Decision logic
            should_retrain = (
                new_samples >= self.min_new_samples and
                fraud_samples >= self.min_fraud_samples and
                not self.retraining_in_progress
            )

            return should_retrain, stats

        except Exception as e:
            logger.error(f"Error checking retraining status: {e}", exc_info=True)
            return False, {'error': str(e)}

    def _perform_retraining(self):
        """Execute model retraining using database data"""
        try:
            self.retraining_in_progress = True
            logger.info("=" * 60)
            logger.info("AUTOMATIC MODEL RETRAINING STARTED")
            logger.info("=" * 60)

            # Import training function
            from real_time.model_trainer import auto_train_model

            # Train using database data (use_database=True)
            result = auto_train_model(
                transactions_df=None,  # Will fetch from database
                labels=None,  # Will use labels from database
                use_database=True,
                min_samples=100
            )

            if result.get('success'):
                self.last_retrain = datetime.now()
                logger.info("=" * 60)
                logger.info("AUTOMATIC MODEL RETRAINING COMPLETED SUCCESSFULLY")
                logger.info(f"Training samples: {result.get('training_samples')}")
                logger.info(f"Fraud samples: {result.get('fraud_samples')}")
                logger.info(f"Model AUC: {result.get('metrics', {}).get('auc', 0):.3f}")
                logger.info(f"Model Accuracy: {result.get('metrics', {}).get('accuracy', 0):.3f}")
                logger.info("=" * 60)

                # Save retraining event to metadata
                self._save_retraining_event(result)
            else:
                logger.error(f"Automatic retraining failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error during automatic retraining: {e}", exc_info=True)
        finally:
            self.retraining_in_progress = False

    def _get_last_training_time(self) -> Optional[datetime]:
        """Get timestamp of last training from metadata"""
        try:
            if os.path.exists(MODEL_METADATA_PATH):
                with open(MODEL_METADATA_PATH, 'r') as f:
                    metadata = json.load(f)
                    trained_at = metadata.get('trained_at')
                    if trained_at:
                        return datetime.fromisoformat(trained_at)
        except Exception as e:
            logger.warning(f"Could not read last training time: {e}")
        return None

    def _get_last_training_samples(self) -> int:
        """Get number of samples used in last training"""
        try:
            if os.path.exists(MODEL_METADATA_PATH):
                with open(MODEL_METADATA_PATH, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get('training_samples', 0)
        except Exception as e:
            logger.warning(f"Could not read last training samples: {e}")
        return 0

    def _save_retraining_event(self, result: Dict[str, Any]):
        """Save retraining event to metadata file"""
        try:
            # Load existing metadata
            metadata = {}
            if os.path.exists(MODEL_METADATA_PATH):
                with open(MODEL_METADATA_PATH, 'r') as f:
                    metadata = json.load(f)

            # Add retraining history
            if 'retraining_history' not in metadata:
                metadata['retraining_history'] = []

            metadata['retraining_history'].append({
                'timestamp': self.last_retrain.isoformat(),
                'samples': result.get('training_samples'),
                'fraud_samples': result.get('fraud_samples'),
                'metrics': result.get('metrics'),
                'trigger': 'automatic'
            })

            # Keep only last 10 retraining events
            metadata['retraining_history'] = metadata['retraining_history'][-10:]

            # Update metadata
            metadata.update({
                'trained_at': result.get('trained_at'),
                'training_samples': result.get('training_samples'),
                'metrics': result.get('metrics'),
                'last_auto_retrain': self.last_retrain.isoformat()
            })

            # Save
            with open(MODEL_METADATA_PATH, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info("Retraining event saved to metadata")

        except Exception as e:
            logger.error(f"Error saving retraining event: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of auto-retrainer"""
        return {
            'is_running': self.is_running,
            'retraining_in_progress': self.retraining_in_progress,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_retrain': self.last_retrain.isoformat() if self.last_retrain else None,
            'check_interval_seconds': self.check_interval,
            'min_new_samples': self.min_new_samples,
            'min_fraud_samples': self.min_fraud_samples
        }

    def trigger_manual_check(self) -> Dict[str, Any]:
        """Manually trigger a retraining check (useful for testing)"""
        logger.info("Manual retraining check triggered")
        should_retrain, stats = self._should_retrain()

        if should_retrain and not self.retraining_in_progress:
            # Start retraining in background thread
            thread = threading.Thread(target=self._perform_retraining)
            thread.start()
            return {
                'success': True,
                'message': 'Retraining started',
                'stats': stats
            }
        elif self.retraining_in_progress:
            return {
                'success': False,
                'message': 'Retraining already in progress',
                'stats': stats
            }
        else:
            return {
                'success': False,
                'message': 'Insufficient new data for retraining',
                'stats': stats
            }


# Global auto-retrainer instance
_auto_retrainer = None


def get_auto_retrainer() -> AutoRetrainer:
    """Get or create the global auto-retrainer instance"""
    global _auto_retrainer
    if _auto_retrainer is None:
        _auto_retrainer = AutoRetrainer()
    return _auto_retrainer


def start_auto_retraining():
    """Start the automatic retraining scheduler"""
    retrainer = get_auto_retrainer()
    retrainer.start()
    return retrainer


def stop_auto_retraining():
    """Stop the automatic retraining scheduler"""
    retrainer = get_auto_retrainer()
    retrainer.stop()


def get_retraining_status() -> Dict[str, Any]:
    """Get current status of automatic retraining"""
    retrainer = get_auto_retrainer()
    return retrainer.get_status()


def trigger_manual_retraining_check() -> Dict[str, Any]:
    """Manually trigger a retraining check"""
    retrainer = get_auto_retrainer()
    return retrainer.trigger_manual_check()
