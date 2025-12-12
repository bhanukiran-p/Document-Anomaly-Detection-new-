"""
Flask API Server for XFORIA DAD
Handles Real-Time Transaction Analysis
"""

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from pathlib import Path
import re
import uuid
from datetime import datetime
from auth import login_user, register_user
from database.supabase_client import get_supabase, check_connection as check_supabase_connection
from auth.supabase_auth import login_user_supabase, register_user_supabase, verify_token
from database.document_storage import (
    store_check_analysis,
    store_paystub_analysis,
    store_money_order_analysis,
    store_bank_statement_analysis
)

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'api_server.log')

# Configure logging to both console and file
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

# File handler with rotation
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured. Log file: {log_file}")

# Google Vision API and PyMuPDF imports (after logger is initialized)
try:
    from google.cloud import vision
    vision_client = vision.ImageAnnotatorClient()
    logger.info("Google Vision API initialized successfully")
except Exception as e:
    logger.warning(f"Google Vision API not initialized: {e}")
    vision_client = None

try:
    import fitz  # PyMuPDF for PDF processing
    logger.info("PyMuPDF (fitz) loaded successfully")
except ImportError:
    logger.warning("PyMuPDF (fitz) not available - PDF conversion will not work")
    fitz = None

# Load environment variables explicitly
from dotenv import load_dotenv
load_dotenv()

# Check for critical environment variables
if os.getenv('OPENAI_API_KEY'):
    logger.info(" OPENAI_API_KEY found in environment")
else:
    logger.error(" OPENAI_API_KEY NOT found in environment")

# Check for GOOGLE_APPLICATION_CREDENTIALS but validate file exists
google_app_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if google_app_creds:
    if os.path.exists(google_app_creds):
        logger.info(f" Google Credentials path (from env): {google_app_creds}")
    else:
        logger.warning(f" GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {google_app_creds}")
        logger.info(" Will use default location in Backend folder instead")
else:
    logger.info(" GOOGLE_APPLICATION_CREDENTIALS not set, will use default location in Backend folder")

# On-demand document extractors removed - only real-time transaction analysis supported

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Supabase client
try:
    supabase = get_supabase()
    supabase_status = check_supabase_connection()
    logger.info(f"Supabase initialization: {supabase_status['message']}")
except Exception as e:
    logger.warning(f"Failed to initialize Supabase: {e}")
    supabase = None

# Helper functions for file validation and document type detection
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_document_type(text):
    """
    Detect document type from OCR text.
    Returns: 'check', 'money_order', 'bank_statement', 'paystub', or 'unknown'
    """
    text_lower = text.lower()

    # Check for check-specific keywords
    check_keywords = ['pay to the order of', 'check number', 'routing number', 'account number', 'memo']
    check_score = sum(1 for keyword in check_keywords if keyword in text_lower)

    # Check for money order keywords
    mo_keywords = ['money order', 'purchaser', 'sender', 'receiver', 'serial number']
    mo_score = sum(1 for keyword in mo_keywords if keyword in text_lower)

    # Check for bank statement keywords
    bs_keywords = ['bank statement', 'statement period', 'beginning balance', 'ending balance', 'account summary']
    bs_score = sum(1 for keyword in bs_keywords if keyword in text_lower)

    # Check for paystub keywords
    ps_keywords = ['pay stub', 'paystub', 'earnings', 'deductions', 'gross pay', 'net pay', 'year to date']
    ps_score = sum(1 for keyword in ps_keywords if keyword in text_lower)

    # Determine document type based on highest score
    scores = {
        'check': check_score,
        'money_order': mo_score,
        'bank_statement': bs_score,
        'paystub': ps_score
    }

    max_score = max(scores.values())
    if max_score == 0:
        return 'unknown'

    # Return the document type with the highest score
    for doc_type, score in scores.items():
        if score == max_score:
            return doc_type

    return 'unknown'

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    supabase_status = check_supabase_connection() if supabase else {'status': 'disconnected', 'message': 'Supabase not initialized'}

    return jsonify({
        'status': 'healthy',
        'service': 'XFORIA DAD API',
        'version': '1.0.0',
        'database': {
            'supabase': supabase_status['status'],
            'message': supabase_status['message']
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login endpoint - Uses Supabase for user authentication with fallback to local JSON"""
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400

        # Try Supabase auth first
        try:
            result, status_code = login_user_supabase(data['email'], data['password'])
            if status_code == 200:
                return jsonify(result), status_code
        except Exception as supabase_error:
            logger.warning(f"Supabase login failed: {str(supabase_error)}. Falling back to local auth.")

        # Fallback to local JSON auth if Supabase fails
        result, status_code = login_user(data['email'], data['password'])
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': 'Invalid email or password',
            'message': 'Login failed'
        }), 401

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register endpoint - Uses Supabase for user registration with fallback to local JSON"""
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400

        # Try Supabase auth first
        try:
            result, status_code = register_user_supabase(data['email'], data['password'])
            if status_code == 201:
                return jsonify(result), status_code
        except Exception as supabase_error:
            logger.warning(f"Supabase registration failed: {str(supabase_error)}. Falling back to local auth.")

        # Fallback to local JSON auth if Supabase fails
        result, status_code = register_user(data['email'], data['password'])
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return jsonify({
            'error': 'Registration failed',
            'message': str(e)
        }), 500

@app.route('/api/check/analyze', methods=['POST'])
def analyze_check():
    """Analyze check image endpoint using new isolated check pipeline"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: JPG, JPEG, PNG, PDF'}), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            # Use new CheckExtractor (Mindee-only, with normalization, ML, AI)
            from check.check_extractor import CheckExtractor

            logger.info(f"Analyzing check using new CheckExtractor: {filename}")
            extractor = CheckExtractor()
            analysis_results = extractor.extract_and_analyze(filepath)

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Store to database
            user_id = request.form.get('user_id', 'public')
            document_id = store_check_analysis(user_id, filename, analysis_results)
            logger.info(f"Check analysis stored to database: {document_id}")

            # Update customer fraud status if AI analysis available
            ai_analysis = analysis_results.get('ai_analysis')
            if ai_analysis:
                recommendation = ai_analysis.get('recommendation')
                normalized_data = analysis_results.get('normalized_data', {})
                payer_name = normalized_data.get('payer_name')

                if payer_name and recommendation:
                    try:
                        from check.database.check_customer_storage import CheckCustomerStorage
                        customer_storage = CheckCustomerStorage()

                        # Get or create customer
                        customer_id = customer_storage.get_or_create_customer(
                            payer_name=payer_name,
                            payee_name=normalized_data.get('payee_name'),
                            address=normalized_data.get('payer_address')
                        )

                        # Update fraud status
                        if customer_id:
                            customer_storage.update_customer_fraud_status(customer_id, recommendation)
                            logger.info(f"Updated customer {customer_id} fraud status: {recommendation}")
                    except Exception as e:
                        logger.error(f"Failed to update customer fraud status: {e}")

            return jsonify({
                'success': True,
                'data': analysis_results,
                'document_id': document_id,
                'message': 'Check analyzed successfully'
            })

        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    except Exception as e:
        logger.error(f"Check analysis failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze check'
        }), 500

@app.route('/api/real-time/analyze', methods=['POST'])
def analyze_real_time_transactions():
    """Analyze real-time transaction CSV file endpoint"""
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
        filepath = os.path.join(UPLOAD_FOLDER, filename)
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
                'transactions': fraud_result.get('transactions', []),  # Add transactions for CSV download
                'insights': insights_result,
                'agent_analysis': agent_analysis.get('agent_analysis') if agent_analysis and agent_analysis.get('success') else None,
                'batch_id': batch_id if db_save_success else None,
                'analysis_id': analysis_id if db_save_success else None,
                'database_status': 'saved' if db_save_success else 'failed',  # Add database status
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


@app.route('/api/paystubs/insights', methods=['GET'])
def get_paystubs_insights():
    """Fetch paystub insights data from v_paystub_insights_clean view"""
    try:
        from datetime import datetime, timedelta
        supabase = get_supabase()

        # Fetch all records using pagination to bypass Supabase default limit of 1000
        all_data = []
        page_size = 1000
        offset = 0
        total_count = None

        while True:
            # Get count only on first request
            count_param = 'exact' if offset == 0 else None
            response = supabase.table('v_paystub_insights_clean').select('*', count=count_param).order('created_at', desc=True).range(offset, offset + page_size - 1).execute()
            page_data = response.data or []
            if not page_data:
                break

            # Get total count from first response
            if total_count is None:
                total_count = response.count if hasattr(response, 'count') else None

            all_data.extend(page_data)

            # Check if we got all records
            if total_count and len(all_data) >= total_count:
                break
            if len(page_data) < page_size:
                break
            offset += page_size

        data = all_data
        total_available = total_count if total_count is not None else len(data)

        # Optional date filtering
        date_filter = request.args.get('date_filter', default=None)  # 'last_30', 'last_60', 'last_90', 'older'

        if date_filter:
            now = datetime.utcnow()
            filtered_data = []

            for record in data:
                created_at_str = record.get('created_at')
                if not created_at_str:
                    continue

                # Parse created_at timestamp
                try:
                    # Handle ISO format timestamps with or without microseconds
                    if 'T' in created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00').split('+')[0])
                    else:
                        created_at = datetime.fromisoformat(created_at_str)
                except:
                    continue

                days_old = (now - created_at).days

                if date_filter == 'last_30' and days_old <= 30:
                    filtered_data.append(record)
                elif date_filter == 'last_60' and days_old <= 60:
                    filtered_data.append(record)
                elif date_filter == 'last_90' and days_old <= 90:
                    filtered_data.append(record)
                elif date_filter == 'older' and days_old > 90:
                    filtered_data.append(record)

            data = filtered_data

        return jsonify({
            'success': True,
            'data': data,
            'total': len(data),
            'total_available': total_available
        })

    except Exception as e:
        logger.error(f"Error fetching paystub insights: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch paystub insights'
        }), 500


@app.route('/api/real-time/regenerate-plots', methods=['POST'])
def regenerate_plots_with_filters():
    """
    Regenerate plots with filter parameters applied.
    Expects JSON body with 'transactions' array and 'filters' object.
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
            filtered_transactions = [t for t in filtered_transactions if t.get('category') == filters['category']]
            logger.info(f"Category filter ({filters['category']}): {before} → {len(filtered_transactions)}")

        # Merchant filter
        if 'merchant' in filters and filters['merchant']:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('merchant') == filters['merchant']]
            logger.info(f"Merchant filter ({filters['merchant']}): {before} → {len(filtered_transactions)}")

        # City filter
        if 'city' in filters and filters['city']:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if (
                t.get('transaction_city') == filters['city'] or
                t.get('transaction_location_city') == filters['city'] or
                t.get('transactionlocationcity') == filters['city']
            )]
            logger.info(f"City filter ({filters['city']}): {before} → {len(filtered_transactions)}")

        # Country filter
        if 'country' in filters and filters['country']:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if (
                t.get('transaction_country') == filters['country'] or
                t.get('transaction_location_country') == filters['country'] or
                t.get('transactionlocationcountry') == filters['country']
            )]
            logger.info(f"Country filter ({filters['country']}): {before} → {len(filtered_transactions)}")

        # Fraud reason filter
        if 'fraud_reason' in filters and filters['fraud_reason']:
            before = len(filtered_transactions)
            filtered_transactions = [t for t in filtered_transactions if t.get('fraud_reason') == filters['fraud_reason']]
            logger.info(f"Fraud reason filter ({filters['fraud_reason']}): {before} → {len(filtered_transactions)}")

        # Date filters
        from datetime import datetime
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


@app.route('/api/real-time/filter-options', methods=['POST'])
def get_filter_options():
    """
    Extract available filter options from the transaction dataset.
    Returns dropdown options for categories, merchants, cities, etc.
    """
    try:
        data = request.get_json()

        if not data or 'transactions' not in data:
            return jsonify({
                'success': False,
                'error': 'Transactions data required'
            }), 400

        transactions = data['transactions']

        if not transactions:
            return jsonify({
                'success': False,
                'error': 'Empty transactions list'
            }), 400

        logger.info(f"Extracting filter options from {len(transactions)} transactions")

        # Extract unique values for each filterable field
        categories = set()
        merchants = set()
        cities = set()
        countries = set()
        fraud_reasons = set()

        # Amount statistics for bucketing
        amounts = []
        fraud_probabilities = []

        for txn in transactions:
            # Categories
            if txn.get('category'):
                categories.add(str(txn['category']))

            # Merchants
            if txn.get('merchant'):
                merchants.add(str(txn['merchant']))

            # Cities (try multiple field variations)
            city = (txn.get('transaction_city') or
                   txn.get('transaction_location_city') or
                   txn.get('transactionlocationcity'))
            if city:
                cities.add(str(city))

            # Countries
            country = (txn.get('transaction_country') or
                      txn.get('transaction_location_country') or
                      txn.get('transactionlocationcountry'))
            if country:
                countries.add(str(country))

            # Fraud reasons
            if txn.get('fraud_reason') and txn.get('is_fraud') == 1:
                fraud_reasons.add(str(txn['fraud_reason']))

            # Amount
            if txn.get('amount'):
                amounts.append(float(txn['amount']))

            # Fraud probability
            if txn.get('fraud_probability') is not None:
                fraud_probabilities.append(float(txn['fraud_probability']))

        # Calculate amount ranges
        amount_ranges = []
        if amounts:
            min_amount = min(amounts)
            max_amount = max(amounts)

            # Create 5 buckets
            if max_amount > min_amount:
                step = (max_amount - min_amount) / 5
                for i in range(5):
                    range_start = min_amount + (i * step)
                    range_end = min_amount + ((i + 1) * step)
                    amount_ranges.append({
                        'label': f"${range_start:.2f} - ${range_end:.2f}",
                        'min': round(range_start, 2),
                        'max': round(range_end, 2)
                    })

        # Sort and clean up options
        filter_options = {
            'categories': sorted([c for c in categories if c and c != 'N/A']),
            'merchants': sorted([m for m in merchants if m and m != 'Unknown Merchant'])[:50],  # Limit to top 50
            'cities': sorted([c for c in cities if c])[:50],  # Limit to top 50
            'countries': sorted([c for c in countries if c]),
            'fraud_reasons': sorted([fr for fr in fraud_reasons if fr]),
            'amount_ranges': amount_ranges,
            'fraud_probability_ranges': [
                {'label': '0% - 20%', 'min': 0, 'max': 0.2},
                {'label': '20% - 40%', 'min': 0.2, 'max': 0.4},
                {'label': '40% - 60%', 'min': 0.4, 'max': 0.6},
                {'label': '60% - 80%', 'min': 0.6, 'max': 0.8},
                {'label': '80% - 100%', 'min': 0.8, 'max': 1.0}
            ]
        }

        logger.info(f"Extracted filter options: {len(filter_options['categories'])} categories, "
                   f"{len(filter_options['merchants'])} merchants, {len(filter_options['cities'])} cities")

        return jsonify({
            'success': True,
            'filter_options': filter_options
        })

    except Exception as e:
        logger.error(f"Error extracting filter options: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to extract filter options'
        }), 500


@app.route('/api/real-time/retrain-model', methods=['POST'])
def retrain_fraud_model():
    """
    Retrain the fraud detection model.
    Can use data from:
    1. Supabase database (analyzed_real_time_trn table) - Default
    2. Uploaded CSV file (if provided)
    """
    try:
        logger.info("Model retraining requested")

        import pandas as pd
        from real_time.model_trainer import auto_train_model

        df = None
        use_database = True

        # Check if file is uploaded
        if 'file' in request.files and request.files['file'].filename != '':
            logger.info("Training from uploaded CSV file")
            file = request.files['file']
            df = pd.read_csv(file)
            use_database = False

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

            logger.info(f"Retraining model on {len(df)} uploaded transactions")
        else:
            logger.info("No file uploaded, will fetch data from Supabase database")

        # Get minimum samples parameter (default 100)
        min_samples = request.form.get('min_samples', 100, type=int)

        # Train model (will fetch from database if df is None)
        training_result = auto_train_model(
            transactions_df=df,
            use_database=use_database,
            min_samples=min_samples
        )

        if not training_result.get('success'):
            return jsonify({
                'success': False,
                'error': training_result.get('error'),
                'message': training_result.get('message', 'Failed to retrain model')
            }), 500

        # Calculate fraud percentage
        fraud_count = training_result.get('fraud_samples', 0)
        total_samples = training_result.get('training_samples', 1)
        fraud_percentage = (fraud_count / total_samples) * 100 if total_samples > 0 else 0

        logger.info(f"Training data has {fraud_count} fraud cases ({fraud_percentage:.1f}%)")
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


@app.route('/custom.geo.json', methods=['GET'])
def serve_geo_json():
    """Serve the custom geo JSON file for map visualizations"""
    try:
        # Path to the geo.json file in the frontend public folder
        frontend_public = Path(__file__).resolve().parent.parent / 'Frontend' / 'public' / 'custom.geo.json'

        if not frontend_public.exists():
            return jsonify({
                'error': 'Geo JSON file not found'
            }), 404

        response = send_file(
            str(frontend_public),
            mimetype='application/json'
        )
        # Set cache headers
        response.cache_control.max_age = 3600  # Cache for 1 hour
        return response
    except Exception as e:
        logger.error(f"Error serving geo JSON: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to serve geo JSON file'
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("XFORIA DAD API Server")
    print("=" * 60)
    print(f"Server running on: http://localhost:5001")
    print(f"API Endpoints:")
    print(f"  - GET  /api/health")
    print(f"  - POST /api/real-time/analyze")
    print(f"  - POST /api/real-time/regenerate-plots")
    print(f"  - POST /api/real-time/filter-options")
    print(f"  - POST /api/real-time/retrain-model")
    print("=" * 60)

    app.run(debug=False, host='0.0.0.0', port=5001, use_reloader=False)

