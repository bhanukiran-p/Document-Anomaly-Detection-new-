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
            from real_time.csv_duplicate_detector import get_duplicate_detector

            logger.info(f"Processing real-time transaction CSV: {filename}")

            # GUARDRAIL: Check for duplicate CSV uploads
            duplicate_detector = get_duplicate_detector()

            # Compute file hash BEFORE processing (file still exists)
            file_hash = duplicate_detector.compute_file_hash(filepath)

            is_duplicate, duplicate_type, prev_upload = duplicate_detector.check_duplicate(
                filepath=filepath,
                filename=filename
            )

            if is_duplicate:
                logger.warning(f"Duplicate CSV detected: {duplicate_type} - {filename}")
                logger.info("Previous upload: " + str(prev_upload.get('timestamp')))

                # FAST PATH: Try to get cached analysis result from previous upload
                cached_result = prev_upload.get('analysis_result')

                if cached_result:
                    # Return cached result immediately (FAST!)
                    logger.info("⚡ FAST PATH: Returning cached analysis result")

                    # Clean up temp file
                    if os.path.exists(filepath):
                        os.remove(filepath)

                    # Make a copy of cached result to avoid modifying the cache
                    import copy
                    response_data = copy.deepcopy(cached_result)

                    # Update duplicate detection info
                    response_data['duplicate_detection'] = {
                        'is_duplicate': True,
                        'duplicate_type': duplicate_type,
                        'previous_upload': {
                            'filename': prev_upload.get('filename'),
                            'timestamp': prev_upload.get('timestamp')
                        },
                        'action_taken': 'cached_result_returned',
                        'cache_hit': True
                    }
                    response_data['database_status'] = 'duplicate_cached'
                    response_data['message'] = 'Duplicate CSV - Returning cached analysis (FAST)'

                    return jsonify(response_data)

                # No cached result - process but skip database save
                duplicate_mode = True
                logger.info("Processing in DUPLICATE MODE: No cached result, analyzing again but won't save to DB")
            else:
                duplicate_mode = False
                logger.info("New CSV file detected - full analysis will proceed")

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

            # Step 6: Save analyzed transactions to database (SKIP if duplicate)
            from database.analyzed_transactions_db import save_analyzed_transactions

            batch_id = str(uuid.uuid4())
            analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if duplicate_mode:
                # DUPLICATE MODE: Skip database save, update model instead
                logger.info("DUPLICATE MODE: Skipping database save to prevent duplicate transactions")
                db_save_success = False
                db_error = "Duplicate CSV - transactions not saved"

                # Trigger model update with current CSV data
                try:
                    from real_time.model_trainer import auto_train_model

                    def update_model_in_background():
                        """Update model with duplicate CSV data in background"""
                        try:
                            logger.info("Starting model update with duplicate CSV data...")
                            training_result = auto_train_model(
                                transactions=fraud_result.get('transactions', [])
                            )
                            if training_result.get('success'):
                                logger.info(f"Model updated successfully with duplicate data. AUC: {training_result.get('metrics', {}).get('auc', 0):.3f}")
                            else:
                                logger.warning(f"Model update failed: {training_result.get('error')}")
                        except Exception as e:
                            logger.error(f"Background model update error: {e}", exc_info=True)

                    # Start model update in background thread (non-blocking)
                    update_thread = threading.Thread(target=update_model_in_background, daemon=True)
                    update_thread.start()
                    logger.info("Model update triggered in background for duplicate CSV")
                except Exception as e:
                    logger.warning(f"Failed to trigger model update: {e}")

            else:
                # NORMAL MODE: Save to database
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
                'database_status': 'saved' if db_save_success else ('duplicate_skipped' if duplicate_mode else 'failed'),
                'duplicate_detection': {
                    'is_duplicate': is_duplicate,
                    'duplicate_type': duplicate_type,
                    'previous_upload': {
                        'filename': prev_upload.get('filename') if prev_upload else None,
                        'timestamp': prev_upload.get('timestamp') if prev_upload else None
                    } if is_duplicate else None,
                    'action_taken': 'model_update_only' if duplicate_mode else 'full_analysis',
                    'cache_hit': False
                },
                'message': 'Duplicate CSV detected - Analysis varied, model updated, transactions not saved' if duplicate_mode else 'Real-time transaction analysis completed successfully'
            }

            # Cache analysis result for future duplicate uploads (only for new files)
            if not duplicate_mode and file_hash:
                try:
                    # Find cache entry by file hash and store result
                    for cache_key, cache_entry in duplicate_detector.upload_cache.items():
                        if cache_entry.get('file_hash') == file_hash:
                            cache_entry['analysis_result'] = response_data
                            duplicate_detector._save_cache()
                            logger.info(f"Analysis result cached for future duplicates: {filename}")
                            break
                except Exception as e:
                    logger.warning(f"Failed to cache analysis result: {e}")

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
        limit = data.get('limit', 10000)
        min_samples = data.get('min_samples', 100)
        use_recent = data.get('use_recent', True)

        # Import training function
        from real_time.model_trainer import train_model_from_database

        logger.info(f"Training model from database (limit: {limit}, min_samples: {min_samples})")

        # Train model from database
        training_result = train_model_from_database(
            limit=limit,
            min_samples=min_samples,
            use_recent=use_recent
        )

        if not training_result.get('success'):
            return jsonify({
                'success': False,
                'error': training_result.get('error'),
                'message': training_result.get('message', 'Failed to train model from database')
            }), 500

        logger.info("Model training from database completed successfully")

        return jsonify({
            'success': True,
            'message': 'Model trained successfully from database',
            'training_results': {
                'samples': training_result.get('training_samples'),
                'fraud_samples': training_result.get('fraud_samples'),
                'legitimate_samples': training_result.get('legitimate_samples'),
                'metrics': training_result.get('metrics'),
                'trained_at': training_result.get('trained_at')
            }
        })

    except Exception as e:
        logger.error(f"Model training from database failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to train model from database'
        }), 500
