"""
================================================================================
FILE: api_server.py
CREATED: 2025-11-21
VERSION: 1.0.0
AUTHOR: XFORIA Team
DESCRIPTION:
    Flask API Server for XFORIA DAD (Document Anomaly Detection)
    Handles analysis of Check, Paystub, Money Order, and Bank Statement documents
    using Mindee Document AI for OCR and text extraction.

KEY FEATURES:
    - Multi-document format support (checks, paystubs, money orders, bank statements)
    - PDF to image conversion for processing
    - Document type validation using keyword detection
    - Fraud detection endpoints for transaction analysis
    - User authentication with Supabase fallback to local JSON
    - RESTful API endpoints for document analysis
    - Error handling and temporary file cleanup

GLOBALS DECLARED:
    - logger: Logger instance for application logging
    - FRAUD_DETECTION_AVAILABLE: Boolean flag for fraud detection module availability
    - SUPABASE_AVAILABLE: Boolean flag for Supabase integration availability
    - app: Flask application instance
    - supabase: Supabase client instance
    - UPLOAD_FOLDER: Directory path for temporary file uploads
    - ALLOWED_EXTENSIONS: Set of allowed file extensions
    - BASE_DIR: Base directory path of the script

================================================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from werkzeug.utils import secure_filename
# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
# Configure logging to INFO level for application tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Logger: Provides logging functionality throughout the application

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables must be set manually.")

# ============================================================================
# DOCUMENT EXTRACTION IMPORTS (Organized by document type)
# ============================================================================
from check import extract_check
from paystub import extract_paystub
from money_order import extract_money_order
from bank_statement import extract_bank_statement

# ============================================================================
# AUTHENTICATION IMPORTS
# ============================================================================
from auth import login_user, register_user

# ============================================================================
# OPTIONAL MODULE IMPORTS WITH GRACEFUL DEGRADATION
# ============================================================================
# FRAUD DETECTION MODULES (Optional - gracefully disabled if unavailable)
# Variables: get_fraud_detection_service
try:
    from utils import get_fraud_detection_service
    FRAUD_DETECTION_AVAILABLE = True  # Flag: Set to True if fraud detection modules are loaded
    logger.info("Fraud detection modules loaded successfully")
except ImportError as e:
    logger.warning(f"Fraud detection modules not available: {e}")
    FRAUD_DETECTION_AVAILABLE = False  # Flag: Set to False if imports fail

# SUPABASE DATABASE MODULES (Optional - gracefully disabled if unavailable)
# Variables: get_supabase, check_supabase_connection, login_user_supabase,
#           register_user_supabase, verify_token
try:
    from database import get_supabase, check_connection as check_supabase_connection
    from auth import login_user_supabase, register_user_supabase, verify_token
    SUPABASE_AVAILABLE = True  # Flag: Set to True if Supabase modules are loaded
    logger.info("Supabase modules loaded successfully")
except ImportError as e:
    logger.warning(f"Supabase modules not available: {e}. Using local authentication only.")
    SUPABASE_AVAILABLE = False  # Flag: Set to False if imports fail
    # Initialize all Supabase functions to None for safe fallback
    get_supabase = None
    check_supabase_connection = None
    login_user_supabase = None
    register_user_supabase = None
    verify_token = None

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize ML Risk Scorer
try:
    from risk import MLRiskScorer
    # Models directory relative to Backend folder
    models_dir = os.path.join(BASE_DIR, 'models')
    risk_scorer = MLRiskScorer(models_dir=models_dir)
    logger.info("ML Risk Scorer initialized successfully")
    if risk_scorer.trained_models:
        logger.info(f"Loaded {len(risk_scorer.trained_models)} trained ML model(s)")
    else:
        logger.info("No trained models found - using weighted scoring fallback")
except Exception as e:
    logger.warning(f"Failed to initialize ML Risk Scorer: {e}")
    risk_scorer = None

# Initialize Supabase client
supabase = None
if SUPABASE_AVAILABLE:
    try:
        supabase = get_supabase()
        supabase_status = check_supabase_connection()
        logger.info(f"Supabase initialization: {supabase_status['message']}")
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase: {e}")
        supabase = None
else:
    logger.info("Supabase not available - using local auth only")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_document_type(text):
    """
    Detect document type based on text content
    Returns: 'check', 'paystub', 'money_order', 'bank_statement', or 'unknown'

    Enhanced logic:
    - Strong indicators take priority (exact phrase matches)
    - Bank statements are checked first with comprehensive keywords
    - Paystubs require multiple indicators to avoid false positives
    - Keyword-based fallback only when strong indicators aren't found
    """
    text_lower = text.lower()

    # ========== TIER 1: STRONG DEFINITIVE INDICATORS ==========

    # Bank statement strong indicators - check FIRST
    # More specific patterns to avoid false positives with checks
    bank_statement_strong = [
        'statement period', 'account summary', 'beginning balance',
        'transaction detail', 'ending balance', 'balance forward',
        'previous balance', 'opening balance', 'closing balance',
        'total deposits', 'total withdrawals', 'wire transfer',
        'ach transfer', 'daily balance', 'checking summary',
        'savings summary', 'account statement', 'transaction history'
    ]

    if any(indicator in text_lower for indicator in bank_statement_strong):
        return 'bank_statement'

    # Paystub strong indicators - require multiple to avoid false positives
    paystub_strong_required = ['gross pay', 'net pay', 'ytd earnings', 'ytd gross']
    paystub_strong_count = sum(1 for indicator in paystub_strong_required if indicator in text_lower)

    if paystub_strong_count >= 1:
        return 'paystub'

    # Check strong indicators
    check_strong = ['routing number', 'micr', 'pay to the order of']
    if any(indicator in text_lower for indicator in check_strong):
        return 'check'

    # Money order strong indicators
    if ('money order' in text_lower and 'purchaser' in text_lower):
        return 'money_order'

    # ========== TIER 2: CONTEXTUAL INDICATORS ==========

    # Check for money order (but exclude bank statements)
    if any(x in text_lower for x in ['purchaser', 'serial number', 'money order']):
        # Make sure it doesn't have bank statement indicators
        if not any(x in text_lower for x in ['transaction', 'balance', 'deposit', 'withdrawal']):
            return 'money_order'

    # ========== TIER 3: KEYWORD-BASED FALLBACK ==========
    # Only use if strong indicators weren't found

    # Check keywords (less ambiguous set)
    check_keywords = ['pay to order', 'routing', 'void', 'memo', 'account number:', 'dollars']
    check_count = sum(1 for keyword in check_keywords if keyword in text_lower)

    # Paystub keywords (removed ambiguous ones like 'earnings', 'deductions')
    paystub_keywords = [
        'gross pay', 'net pay', 'federal withholding', 'state withholding',
        'social security', 'medicare', 'pay period', 'paycheck',
        'employee id', 'employer name', 'ytd', 'fica'
    ]
    paystub_count = sum(1 for keyword in paystub_keywords if keyword in text_lower)

    # Money order keywords
    money_order_keywords = ['purchaser', 'serial number', 'receipt', 'remitter', 'issuer']
    money_order_count = sum(1 for keyword in money_order_keywords if keyword in text_lower)

    # Bank statement keywords (expanded list)
    bank_statement_keywords = [
        'ending balance', 'checking summary', 'deposits', 'withdrawals',
        'daily balance', 'opening', 'closing', 'transaction', 'account',
        'statement', 'balance', 'debit', 'credit', 'posted'
    ]
    bank_statement_count = sum(1 for keyword in bank_statement_keywords if keyword in text_lower)

    # Determine document type based on keyword matches
    max_count = max(check_count, paystub_count, money_order_count, bank_statement_count)

    if max_count == 0:
        return 'unknown'

    # Return based on highest count, with bank_statement as tiebreaker
    if bank_statement_count == max_count and bank_statement_count > 0:
        return 'bank_statement'
    elif paystub_count == max_count:
        return 'paystub'
    elif check_count == max_count:
        return 'check'
    elif money_order_count == max_count:
        return 'money_order'
    else:
        return 'unknown'

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if SUPABASE_AVAILABLE and supabase and check_supabase_connection:
        supabase_status = check_supabase_connection()
    else:
        supabase_status = {'status': 'disconnected', 'message': 'Supabase not available'}

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

        # Try Supabase auth first, fallback to local auth
        if SUPABASE_AVAILABLE and login_user_supabase:
            try:
                result, status_code = login_user_supabase(data['email'], data['password'])
                if status_code == 200:
                    return jsonify(result), status_code
            except Exception as supabase_error:
                logger.warning(f"Supabase login failed: {str(supabase_error)}. Falling back to local auth.")

        # Fallback to local JSON auth
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

        # Try Supabase auth first, fallback to local auth
        if SUPABASE_AVAILABLE and register_user_supabase:
            try:
                result, status_code = register_user_supabase(data['email'], data['password'])
                if status_code == 201:
                    return jsonify(result), status_code
            except Exception as supabase_error:
                logger.warning(f"Supabase registration failed: {str(supabase_error)}. Falling back to local auth.")

        # Fallback to local JSON auth
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
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: JPG, JPEG, PNG, PDF'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            result = extract_check(filepath)
            extracted = result.get('extracted_data', {})
            raw_text = extracted.get('raw_ocr_text') or result.get('raw_ocr_text') or result.get('raw_text') or ''

            detected_type = detect_document_type(raw_text)
            if detected_type not in ('check', 'unknown'):
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a check. Please upload a bank check.',
                    'message': 'Document type mismatch'
                }), 400

            risk_assessment = None
            if risk_scorer:
                try:
                    risk_assessment = risk_scorer.calculate_risk_score(
                        'check',
                        extracted,
                        raw_text
                    )
                except Exception as e:
                    logger.error(f"Risk scoring error: {e}", exc_info=True)

            if os.path.exists(filepath):
                os.remove(filepath)

            response_data = {
                'success': True,
                'data': extracted,
                'message': 'Check analyzed successfully'
            }

            if risk_assessment:
                response_data['risk_assessment'] = risk_assessment

            return jsonify(response_data)

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze check'
        }), 500




        
            
            
            
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'message': 'Failed to analyze paystub'
#         }), 500




@app.route('/api/paystub/analyze', methods=['POST'])
def analyze_paystub():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            result = extract_paystub(filepath)
            extracted = result.get('extracted_data', {})
            raw_text = extracted.get('raw_ocr_text') or result.get('raw_ocr_text') or result.get('raw_text') or ''

            detected_type = detect_document_type(raw_text)
            if detected_type not in ('paystub', 'unknown'):
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a paystub. Please upload a paystub document.',
                    'message': 'Document type mismatch'
                }), 400

            risk_assessment = None
            if risk_scorer:
                try:
                    risk_assessment = risk_scorer.calculate_risk_score(
                        'paystub',
                        extracted,
                        raw_text
                    )
                except Exception as e:
                    logger.error(f"Risk scoring error: {e}", exc_info=True)

            if os.path.exists(filepath):
                os.remove(filepath)

            response_data = {
                'success': True,
                'data': extracted,
                'message': 'Paystub analyzed successfully'
            }

            if risk_assessment:
                response_data['risk_assessment'] = risk_assessment

            return jsonify(response_data)

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze paystub'
        }), 500











            
            




@app.route('/api/money-order/analyze', methods=['POST'])
def analyze_money_order():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: JPG, JPEG, PNG, PDF'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            result = extract_money_order(filepath)
            extracted = result.get('extracted_data', {})
            raw_text = extracted.get('raw_ocr_text') or result.get('raw_ocr_text') or result.get('raw_text') or ''

            detected_type = detect_document_type(raw_text)
            if detected_type not in ('money_order', 'unknown'):
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a money order. Please upload a money order document.',
                    'message': 'Document type mismatch'
                }), 400

            risk_assessment = None
            if risk_scorer:
                try:
                    risk_assessment = risk_scorer.calculate_risk_score(
                        'money_order',
                        extracted,
                        raw_text
                    )
                except Exception as e:
                    logger.error(f"Risk scoring error: {e}", exc_info=True)

            if os.path.exists(filepath):
                os.remove(filepath)

            response_data = {
                'success': True,
                'data': result,
                'message': 'Money order analyzed successfully'
            }

            if risk_assessment:
                response_data['risk_assessment'] = risk_assessment

            return jsonify(response_data)

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            logger.error(f"Error processing money order: {e}", exc_info=True)
            raise e

    except Exception as e:
        logger.error(f"Money order analysis failed: {e}", exc_info=True)
        error_message = str(e)
        # Make error messages more user-friendly
        if "MINDEE_API_KEY" in error_message:
            error_message = "Mindee API key is not configured. Please check your environment variables."
        elif "Failed to process document with Mindee API" in error_message:
            error_message = "Failed to process document with Mindee API. Please check your API key and model ID."
        elif "File not found" in error_message:
            error_message = "Uploaded file not found. Please try uploading again."
        
        return jsonify({
            'success': False,
            'error': error_message,
            'message': 'Failed to analyze money order'
        }), 500












            


@app.route('/api/bank-statement/analyze', methods=['POST'])
def analyze_bank_statement():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: JPG, JPEG, PNG, PDF'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            result = extract_bank_statement(filepath)
            extracted = result.get('extracted_data', {})
            raw_text = extracted.get('raw_ocr_text') or result.get('raw_ocr_text') or result.get('raw_text') or ''

            detected_type = detect_document_type(raw_text)
            if detected_type not in ('bank_statement', 'unknown'):
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a bank statement. Please upload a bank statement document.',
                    'message': 'Document type mismatch'
                }), 400

            risk_assessment = None
            if risk_scorer:
                try:
                    risk_assessment = risk_scorer.calculate_risk_score(
                        'bank_statement',
                        extracted,
                        raw_text
                    )
                except Exception as e:
                    logger.error(f"Risk scoring error: {e}", exc_info=True)

            if os.path.exists(filepath):
                os.remove(filepath)

            # Format response for frontend - flatten extracted_data and add balances structure
            extracted = result.get('extracted_data', {})
            formatted_data = {
                **extracted,  # Include all extracted fields at top level
                'statement_period': f"{extracted.get('statement_period_start', '')} to {extracted.get('statement_period_end', '')}".strip(' to '),
                'balances': {
                    'opening_balance': extracted.get('opening_balance'),
                    'ending_balance': extracted.get('closing_balance'),
                    'available_balance': extracted.get('available_balance'),
                    'current_balance': extracted.get('current_balance'),
                },
                'extracted_data': extracted,  # Keep original structure for compatibility
            }

            response_data = {
                'success': True,
                'data': formatted_data,
                'message': 'Bank statement analyzed successfully'
            }

            if risk_assessment:
                response_data['risk_assessment'] = risk_assessment

            return jsonify(response_data)

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze bank statement'
        }), 500








# ==========================================
# FRAUD DETECTION ENDPOINTS
# ==========================================

@app.route('/api/fraud/transaction-predict', methods=['POST'])
def fraud_transaction_predict():
    """
    Predict fraud for a single transaction.

    Expected JSON:
    {
        'transaction_data': {
            'customer_name': 'John Doe',
            'bank_name': 'Chase',
            'merchant_name': 'Walmart',
            'category': 'Retail',
            'amount': 150.00,
            'balance_after': 5000.00,
            'is_large_transaction': 0,
            'amount_to_balance_ratio': 0.03,
            'transactions_past_1_day': 2,
            'transactions_past_7_days': 10,
            'is_new_merchant': 0,
            'transaction_id': 'TXN001'
        },
        'model_type': 'ensemble'  # optional: 'xgboost', 'random_forest', or 'ensemble'
    }
    """
    try:
        if not FRAUD_DETECTION_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Fraud detection service not available',
                'message': 'Fraud detection models not loaded'
            }), 503

        data = request.get_json()
        if not data or 'transaction_data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing transaction_data in request'
            }), 400

        transaction_data = data['transaction_data']
        model_type = data.get('model_type', 'ensemble')

        service = get_fraud_detection_service()
        prediction = service.predict_transaction_fraud(transaction_data, model_type)

        # Convert to dict for JSON serialization
        from dataclasses import asdict
        result = asdict(prediction)

        return jsonify({
            'success': True,
            'data': result,
            'message': 'Transaction fraud prediction completed'
        })

    except Exception as e:
        logger.error(f"Transaction fraud prediction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to predict transaction fraud'
        }), 500


@app.route('/api/fraud/validate-pdf', methods=['POST'])
def fraud_validate_pdf():
    """
    Validate a bank statement PDF for signs of tampering/forgery.

    Expected: File upload with PDF file
    """
    try:
        if not FRAUD_DETECTION_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Fraud detection service not available'
            }), 503

        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only PDF, PNG, JPG allowed'
            }), 400

        # Save temp file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            service = get_fraud_detection_service()
            pdf_validation = service.validate_statement_pdf(filepath)

            # Convert to dict
            from dataclasses import asdict
            result = asdict(pdf_validation)

            return jsonify({
                'success': True,
                'data': result,
                'message': 'PDF validation completed'
            })

        finally:
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        logger.error(f"PDF validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to validate PDF'
        }), 500


@app.route('/api/fraud/assess', methods=['POST'])
def fraud_assess():
    """
    Comprehensive fraud assessment combining transaction and PDF analysis.

    Expected JSON:
    {
        'transaction_data': {...},  # optional
        'pdf_path': '/path/to/file.pdf',  # optional
        'model_type': 'ensemble'  # optional
    }
    """
    try:
        if not FRAUD_DETECTION_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Fraud detection service not available'
            }), 503

        data = request.get_json()

        transaction_data = data.get('transaction_data')
        pdf_path = data.get('pdf_path')
        model_type = data.get('model_type', 'ensemble')

        if not transaction_data and not pdf_path:
            return jsonify({
                'success': False,
                'error': 'Provide either transaction_data or pdf_path'
            }), 400

        service = get_fraud_detection_service()
        assessment = service.assess_fraud_risk(transaction_data, pdf_path, model_type)

        # Convert to dict
        from dataclasses import asdict

        result = {
            'transaction_prediction': asdict(assessment.transaction_prediction) if assessment.transaction_prediction else None,
            'pdf_validation': asdict(assessment.pdf_validation) if assessment.pdf_validation else None,
            'combined_risk_score': assessment.combined_risk_score,
            'overall_verdict': assessment.overall_verdict,
            'recommendation': assessment.recommendation
        }

        return jsonify({
            'success': True,
            'data': result,
            'message': 'Fraud assessment completed'
        })

    except Exception as e:
        logger.error(f"Fraud assessment error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to assess fraud'
        }), 500


@app.route('/api/fraud/batch-predict', methods=['POST'])
def fraud_batch_predict():
    """
    Predict fraud for multiple transactions from CSV.

    Expected: File upload with CSV file
    """
    try:
        if not FRAUD_DETECTION_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Fraud detection service not available'
            }), 503

        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'Only CSV files allowed'
            }), 400

        # Save temp file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            import pandas as pd

            df = pd.read_csv(filepath)
            service = get_fraud_detection_service()
            predictions_df = service.batch_predict(df)

            # Convert to JSON-serializable format
            result_data = predictions_df.to_dict(orient='records')

            return jsonify({
                'success': True,
                'data': result_data,
                'total_transactions': len(predictions_df),
                'message': 'Batch prediction completed'
            })

        finally:
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to perform batch prediction'
        }), 500


@app.route('/api/fraud/models-status', methods=['GET'])
def fraud_models_status():
    """
    Check if fraud detection models are loaded.
    """
    try:
        service = get_fraud_detection_service()
        models_loaded = (service.xgb_model is not None and service.rf_model is not None)

        return jsonify({
            'success': True,
            'data': {
                'models_loaded': models_loaded,
                'xgboost_available': service.xgb_model is not None,
                'random_forest_available': service.rf_model is not None,
                'fraud_detection_available': FRAUD_DETECTION_AVAILABLE
            },
            'message': 'Models status retrieved'
        })

    except Exception as e:
        logger.error(f"Models status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'fraud_detection_available': FRAUD_DETECTION_AVAILABLE
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("XFORIA DAD API Server")
    print("=" * 60)
    print(f"Server running on: http://localhost:5001")
    print(f"API Endpoints:")
    print(f"  - GET  /api/health")
    print(f"  - POST /api/check/analyze")
    print(f"  - POST /api/paystub/analyze")
    print(f"  - POST /api/money-order/analyze")
    print(f"  - POST /api/bank-statement/analyze")
    print(f"\nFraud Detection Endpoints:")
    print(f"  - GET  /api/fraud/models-status")
    print(f"  - POST /api/fraud/transaction-predict")
    print(f"  - POST /api/fraud/validate-pdf")
    print(f"  - POST /api/fraud/assess")
    print(f"  - POST /api/fraud/batch-predict")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5001)

