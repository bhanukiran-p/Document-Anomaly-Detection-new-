"""
Real-Time Analysis Route Handlers
Extracted from api_server.py for better code organization
"""

import os
import uuid
import logging
import threading
from datetime import datetime
from flask import request, jsonify
from werkzeug.utils import secure_filename
import pandas as pd

logger = logging.getLogger(__name__)


def handle_analyze_real_time_transactions(upload_folder):
    """
    Analyze real-time transaction CSV file endpoint handler

    Args:
        upload_folder: Path to upload folder for temporary file storage

    Returns:
        Flask JSON response
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check if file is CSV
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        try:
            # Import real-time analysis modules
            from real_time import (
                process_transaction_csv,
                detect_fraud_in_transactions,
                generate_insights,
                get_agent_service
            )

            logger.info(f"Processing real-time transaction CSV: {filename}")

            # Step 1: Process CSV file
            csv_result = process_transaction_csv(filepath)
            if not csv_result.get('success'):
                return jsonify({
                    'success': False,
                    'error': csv_result.get('error', 'Failed to process CSV file'),
                    'message': csv_result.get('message', 'CSV processing failed')
                }), 400

            # Step 2: Detect fraud in transactions
            fraud_result = detect_fraud_in_transactions(
                csv_result['transactions'],
                auto_train=True
            )

            # Step 3: Generate insights
            insights_result = generate_insights(fraud_result)

            # Step 4: Combine results for AI analysis
            analysis_result = {
                'csv_info': csv_result,
                'fraud_detection': fraud_result,
                'transactions': fraud_result.get('transactions', []),
                'insights': insights_result
            }

            # Step 5: Generate AI-powered comprehensive analysis
            agent_analysis = None
            try:
                agent_service = get_agent_service()
                agent_analysis = agent_service.generate_comprehensive_analysis(analysis_result)
                logger.info("AI analysis generated successfully")
            except Exception as e:
                logger.warning(f"AI analysis failed, continuing without it: {e}")
                agent_analysis = {
                    'success': False,
                    'error': str(e),
                    'message': 'AI analysis unavailable'
                }

            # Step 6: Save analyzed transactions to database
            from database.analyzed_transactions_db import save_analyzed_transactions

            batch_id = str(uuid.uuid4())
            analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            db_save_success, db_error = save_analyzed_transactions(
                transactions=fraud_result.get('transactions', []),
                batch_id=batch_id,
                analysis_id=analysis_id,
                model_type='transaction_fraud_model'
            )

            if db_save_success:
                logger.info(f"Successfully saved {len(fraud_result.get('transactions', []))} transactions to database (batch: {batch_id})")

                # Trigger automatic model training from database (in background)
                try:
                    from real_time.model_trainer import train_model_from_database

                    def train_in_background():
                        """Train model from database in background thread"""
                        try:
                            logger.info("Starting automatic model training from database...")
                            training_result = train_model_from_database(
                                limit=10000,
                                min_samples=100,
                                use_recent=True
                            )
                            if training_result.get('success'):
                                logger.info(f"Automatic model training completed successfully. AUC: {training_result.get('metrics', {}).get('auc', 0):.3f}")
                            else:
                                logger.warning(f"Automatic model training failed: {training_result.get('error')}")
                        except Exception as e:
                            logger.error(f"Background model training error: {e}", exc_info=True)

                    # Start training in background thread (non-blocking)
                    training_thread = threading.Thread(target=train_in_background, daemon=True)
                    training_thread.start()
                    logger.info("Automatic model training triggered in background")
                except Exception as e:
                    logger.warning(f"Failed to trigger automatic model training: {e}")
            else:
                logger.warning(f"Failed to save transactions to database: {db_error}")

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Build complete response
            response_data = {
                'success': True,
                'csv_info': csv_result,
                'fraud_detection': fraud_result,
                'transactions': fraud_result.get('transactions', []),
                'insights': insights_result,
                'agent_analysis': agent_analysis.get('agent_analysis') if agent_analysis and agent_analysis.get('success') else None,
                'batch_id': batch_id if db_save_success else None,
                'analysis_id': analysis_id if db_save_success else None,
                'database_status': 'saved' if db_save_success else 'failed',
                'message': 'Real-time transaction analysis completed successfully'
            }

            return jsonify(response_data)

        except ImportError as e:
            logger.error(f"Real-time analysis module import failed: {e}")
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'success': False,
                'error': 'Real-time analysis module not available',
                'message': str(e)
            }), 500

        except Exception as e:
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)
            logger.error(f"Real-time analysis failed: {e}", exc_info=True)
            raise e

    except Exception as e:
        logger.error(f"Real-time analysis endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze real-time transactions'
        }), 500


def handle_regenerate_plots():
    """
    Regenerate plots with filter parameters applied
    Expects JSON body with 'transactions' array and 'filters' object

    Returns:
        Flask JSON response
    """
    try:
        data = request.get_json()

        if not data or 'transactions' not in data:
            return jsonify({
                'success': False,
                'error': 'Transactions data required'
            }), 400

        transactions = data['transactions']
        filters = data.get('filters', {})

        logger.info(f"Regenerate plots endpoint called with {len(transactions)} transactions")
        logger.info(f"Filters received: {filters}")

        # Apply filters to transactions
        filtered_transactions = transactions

        # Amount filters
        if 'amount_min' in filters:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('amount', 0) >= filters['amount_min']]
            logger.info(f"Amount min filter ({filters['amount_min']}): {before} → {len(filtered_transactions)}")
        if 'amount_max' in filters:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('amount', 0) <= filters['amount_max']]
            logger.info(f"Amount max filter ({filters['amount_max']}): {before} → {len(filtered_transactions)}")

        # Fraud probability filters
        if 'fraud_probability_min' in filters:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('fraud_probability', 0) >= filters['fraud_probability_min']]
            logger.info(f"Fraud prob min filter ({filters['fraud_probability_min']}): {before} → {len(filtered_transactions)}")
        if 'fraud_probability_max' in filters:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('fraud_probability', 0) <= filters['fraud_probability_max']]
            logger.info(f"Fraud prob max filter ({filters['fraud_probability_max']}): {before} → {len(filtered_transactions)}")

        # Category filter
        if 'category' in filters and filters['category']:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if filters['category'].lower() in str(t.get('category', '')).lower()]
            logger.info(f"Category filter ({filters['category']}): {before} → {len(filtered_transactions)}")

        # Transaction Country filter
        if 'transaction_country' in filters and filters['transaction_country']:
            before = len(filtered_transactions)
            filter_country = str(filters['transaction_country']).strip().lower()
            filtered_transactions = [t for t in filtered_transactions if str(t.get('transaction_country', '')).strip().lower() == filter_country]
            logger.info(f"Transaction country filter ({filters['transaction_country']}): {before} → {len(filtered_transactions)}")

        # Login Country filter
        if 'login_country' in filters and filters['login_country']:
            before = len(filtered_transactions)
            filter_country = str(filters['login_country']).strip().lower()
            filtered_transactions = [t for t in filtered_transactions if str(t.get('login_country', '')).strip().lower() == filter_country]
            logger.info(f"Login country filter ({filters['login_country']}): {before} → {len(filtered_transactions)}")

        # Merchant filter
        if 'merchant' in filters and filters['merchant']:
            before = len(filtered_transactions)
            filter_merchant = str(filters['merchant']).lower()
            filtered_transactions = [t for t in filtered_transactions if filter_merchant in str(t.get('merchant', '')).lower()]
            logger.info(f"Merchant filter ({filters['merchant']}): {before} → {len(filtered_transactions)}")

        # Card Type filter
        if 'card_type' in filters and filters['card_type']:
            before = len(filtered_transactions)
            filter_card_type = str(filters['card_type']).strip().lower()
            filtered_transactions = [t for t in filtered_transactions if str(t.get('card_type', '')).strip().lower() == filter_card_type]
            logger.info(f"Card type filter ({filters['card_type']}): {before} → {len(filtered_transactions)}")

        # Transaction Type filter
        if 'transaction_type' in filters and filters['transaction_type']:
            before = len(filtered_transactions)
            filter_txn_type = str(filters['transaction_type']).strip().lower()
            filtered_transactions = [t for t in filtered_transactions if str(t.get('transaction_type', '')).strip().lower() == filter_txn_type]
            logger.info(f"Transaction type filter ({filters['transaction_type']}): {before} → {len(filtered_transactions)}")

        # Currency filter
        if 'currency' in filters and filters['currency']:
            before = len(filtered_transactions)
            filter_currency = str(filters['currency']).strip().upper()
            filtered_transactions = [t for t in filtered_transactions if str(t.get('currency', '')).strip().upper() == filter_currency]
            logger.info(f"Currency filter ({filters['currency']}): {before} → {len(filtered_transactions)}")

        # Date filters
        if 'date_start' in filters and filters['date_start']:
            try:
                before = len(filtered_transactions)
                start_date = datetime.fromisoformat(filters['date_start'])
                filtered_transactions = [t for t in filtered_transactions if t.get('timestamp') and datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00')) >= start_date]
                logger.info(f"Date start filter ({filters['date_start']}): {before} → {len(filtered_transactions)}")
            except Exception as e:
                logger.error(f"Date start filter error: {e}")

        if 'date_end' in filters and filters['date_end']:
            try:
                before = len(filtered_transactions)
                end_date = datetime.fromisoformat(filters['date_end'])
                filtered_transactions = [t for t in filtered_transactions if t.get('timestamp') and datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00')) <= end_date]
                logger.info(f"Date end filter ({filters['date_end']}): {before} → {len(filtered_transactions)}")
            except Exception as e:
                logger.error(f"Date end filter error: {e}")

        # Fraud/Legitimate only filters
        if filters.get('fraud_only'):
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('is_fraud') == 1]
            logger.info(f"Fraud only filter: {before} → {len(filtered_transactions)}")
        if filters.get('legitimate_only'):
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('is_fraud') == 0]
            logger.info(f"Legitimate only filter: {before} → {len(filtered_transactions)}")

        logger.info(f"FINAL: Filtered transactions from {len(transactions)} to {len(filtered_transactions)}")

        # Create a mock analysis result structure with filtered transactions
        fraud_result = {
            'success': True,
            'transactions': filtered_transactions,
            'fraud_count': sum(1 for t in filtered_transactions if t.get('is_fraud') == 1),
            'legitimate_count': sum(1 for t in filtered_transactions if t.get('is_fraud') == 0),
            'fraud_percentage': 0,
            'legitimate_percentage': 0,
            'total_fraud_amount': sum(t.get('amount', 0) for t in filtered_transactions if t.get('is_fraud') == 1),
            'total_legitimate_amount': sum(t.get('amount', 0) for t in filtered_transactions if t.get('is_fraud') == 0),
            'total_amount': sum(t.get('amount', 0) for t in filtered_transactions),
            'average_fraud_probability': sum(t.get('fraud_probability', 0) for t in filtered_transactions) / len(filtered_transactions) if filtered_transactions else 0,
            'model_type': 'filtered'
        }

        if len(filtered_transactions) > 0:
            fraud_result['fraud_percentage'] = (fraud_result['fraud_count'] / len(filtered_transactions)) * 100
            fraud_result['legitimate_percentage'] = (fraud_result['legitimate_count'] / len(filtered_transactions)) * 100

        # Generate insights with filtered transactions
        from real_time.insights_generator import generate_insights
        logger.info(f"Regenerating plots with {len(filtered_transactions)} filtered transactions (from {len(transactions)} total)")
        insights_result = generate_insights(fraud_result)

        if not insights_result.get('success'):
            logger.error(f"Failed to generate insights: {insights_result.get('error')}")
            return jsonify({
                'success': False,
                'error': insights_result.get('error', 'Failed to generate plots')
            }), 500

        logger.info(f"Successfully generated {len(insights_result.get('plots', []))} plots with filters applied")

        return jsonify({
            'success': True,
            'plots': insights_result.get('plots', []),
            'statistics': insights_result.get('statistics', {}),
            'fraud_patterns': insights_result.get('fraud_patterns', {}),
            'recommendations': insights_result.get('recommendations', [])
        })


    except Exception as e:
        logger.error(f"Error regenerating plots: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to regenerate plots'
        }), 500


def handle_retrain_fraud_model():
    """
    Retrain the fraud detection model on uploaded data
    Useful when the current model's training data doesn't match actual data distribution

    Returns:
        Flask JSON response
    """
    try:
        logger.info("Model retraining requested")

        # Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'message': 'Please upload a CSV file with labeled fraud data'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename',
                'message': 'Please select a file to upload'
            }), 400

        # Read CSV
        from real_time.model_trainer import auto_train_model

        df = pd.read_csv(file)

        # Verify required columns
        if 'amount' not in df.columns:
            return jsonify({
                'success': False,
                'error': 'Missing required column: amount'
            }), 400

        # Check if dataset has fraud labels
        if 'is_fraud' not in df.columns:
            return jsonify({
                'success': False,
                'error': 'Missing fraud labels',
                'message': 'Dataset must have an "is_fraud" column with 0/1 labels'
            }), 400

        logger.info(f"Retraining model on {len(df)} transactions")

        # Calculate current fraud distribution
        fraud_count = df['is_fraud'].sum()
        fraud_percentage = (fraud_count / len(df)) * 100

        logger.info(f"Training data has {fraud_count} fraud cases ({fraud_percentage:.1f}%)")

        # Train model
        training_result = auto_train_model(df)

        if not training_result.get('success'):
            return jsonify({
                'success': False,
                'error': training_result.get('error'),
                'message': 'Failed to retrain model'
            }), 500

        logger.info("Model retraining completed successfully")

        return jsonify({
            'success': True,
            'message': 'Model retrained successfully',
            'training_results': {
                'samples': training_result.get('training_samples'),
                'fraud_samples': training_result.get('fraud_samples'),
                'legitimate_samples': training_result.get('legitimate_samples'),
                'fraud_percentage': round(fraud_percentage, 2),
                'metrics': training_result.get('metrics'),
                'trained_at': training_result.get('trained_at')
            }
        })

    except Exception as e:
        logger.error(f"Model retraining failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrain fraud detection model'
        }), 500


def handle_train_from_database():
    """
    Train the fraud detection model automatically from database data
    No CSV file required - uses all analyzed transactions stored in database

    Returns:
        Flask JSON response
    """
    try:
        logger.info("Model training from database requested")

        # Get optional parameters from request
        data = request.get_json() or {}
        max_samples = data.get('max_samples', 50000)  # Increased default for better training
        batch_size = data.get('batch_size', 5000)     # Batch size for incremental loading
        force_retrain = data.get('force_retrain', False)

        logger.info(f"Training parameters: max_samples={max_samples:,}, batch_size={batch_size:,}, force={force_retrain}")

        # Check if model already exists
        if not force_retrain:
            from real_time.model_trainer import TRANSACTION_MODEL_PATH
            import os

            if os.path.exists(TRANSACTION_MODEL_PATH):
                logger.warning("Model already exists. Use force_retrain=true to overwrite.")
                return jsonify({
                    'success': False,
                    'error': 'Model already exists',
                    'message': 'Set force_retrain=true in request body to retrain existing model'
                }), 400

        # Import training function
        from real_time.model_trainer import train_model_from_database

        # Train model from database using incremental loading
        training_result = train_model_from_database(
            limit=max_samples,
            batch_size=batch_size
        )

        if not training_result.get('success'):
            return jsonify({
                'success': False,
                'error': training_result.get('error'),
                'message': training_result.get('message', 'Failed to train model from database')
            }), 500

        logger.info("Model training from database completed successfully")

        # Get database stats if available
        db_stats = training_result.get('database_stats', {})

        return jsonify({
            'success': True,
            'message': 'Model trained successfully from database using incremental batch loading',
            'training_results': {
                'samples': training_result.get('training_samples'),
                'fraud_samples': training_result.get('fraud_samples'),
                'legitimate_samples': training_result.get('legitimate_samples'),
                'metrics': training_result.get('metrics'),
                'trained_at': training_result.get('trained_at'),
                'database_stats': db_stats,
                'incremental_loading': {
                    'max_samples_used': max_samples,
                    'batch_size': batch_size,
                    'total_in_database': db_stats.get('total_transactions', 0),
                    'batches_loaded': db_stats.get('batches_loaded', 0)
                }
            }
        })

    except Exception as e:
        logger.error(f"Model training from database failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to train model from database'
        }), 500
