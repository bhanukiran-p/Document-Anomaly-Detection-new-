"""
API endpoint for triggering model training from database
"""
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)


def handle_train_from_database():
    """
    Train the fraud detection model from database transactions.
    Endpoint: POST /api/real-time/train-from-database

    Request body (optional):
        {
            "max_samples": 50000,      # Maximum samples to use
            "batch_size": 5000,        # Batch size for loading
            "force_retrain": false     # Force retrain even if model exists
        }

    Returns:
        JSON response with training results
    """
    try:
        data = request.get_json() or {}

        max_samples = data.get('max_samples', 50000)
        batch_size = data.get('batch_size', 5000)
        force_retrain = data.get('force_retrain', False)

        logger.info(f"Training request received:")
        logger.info(f"  - Max samples: {max_samples:,}")
        logger.info(f"  - Batch size: {batch_size:,}")
        logger.info(f"  - Force retrain: {force_retrain}")

        # Check if model exists
        if not force_retrain:
            import os
            from real_time.model_trainer import TRANSACTION_MODEL_PATH

            if os.path.exists(TRANSACTION_MODEL_PATH):
                return jsonify({
                    'success': False,
                    'error': 'Model already exists. Set force_retrain=true to retrain.',
                    'message': 'Use force_retrain parameter to overwrite existing model'
                }), 400

        # Train from database
        from real_time.model_trainer import train_model_from_database

        result = train_model_from_database(
            limit=max_samples,
            batch_size=batch_size
        )

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Model trained successfully from database',
                'metrics': result.get('metrics', {}),
                'database_stats': result.get('database_stats', {}),
                'training_samples': result.get('training_samples'),
                'trained_at': result.get('trained_at')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'message': result.get('message', 'Training failed')
            }), 500

    except Exception as e:
        logger.error(f"Training endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to train model from database'
        }), 500


def handle_get_training_status():
    """
    Get current training status.
    Endpoint: GET /api/real-time/training-status

    Returns:
        JSON response with training status
    """
    try:
        from real_time.incremental_trainer import get_training_status

        status = get_training_status()

        return jsonify({
            'success': True,
            **status
        }), 200

    except Exception as e:
        logger.error(f"Training status error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
