"""
Flask API Server for XFORIA DAD
Handles Check, Paystub, Money Order, and Bank Statement Analysis
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
from werkzeug.utils import secure_filename
import importlib.util
import re
import base64
import fitz
from google.cloud import vision
from auth import login_user, register_user, token_required

# Import fraud detection modules
try:
    from fraud_detection_service import get_fraud_detection_service
    from pdf_statement_validator import PDFStatementValidator
    FRAUD_DETECTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Fraud detection modules not available: {e}")
    FRAUD_DETECTION_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional Supabase imports
try:
    from supabase_client import get_supabase, check_connection as check_supabase_connection
    from auth_supabase import login_user_supabase, register_user_supabase, verify_token
    SUPABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Supabase modules not available: {e}")
    SUPABASE_AVAILABLE = False
    get_supabase = None
    check_supabase_connection = None
    login_user_supabase = None
    register_user_supabase = None
    verify_token = None

# Load the production extractor
spec = importlib.util.spec_from_file_location(
    "production_extractor", 
    "production_google_vision-extractor.py"
)
production_extractor = importlib.util.module_from_spec(spec)
sys.modules["production_extractor"] = production_extractor
spec.loader.exec_module(production_extractor)

ProductionCheckExtractor = production_extractor.ProductionCheckExtractor

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set up credentials path - check environment variable first, then default location
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
if not CREDENTIALS_PATH:
    # Default to google-credentials.json in the Backend directory
    CREDENTIALS_PATH = os.path.join(BASE_DIR, 'google-credentials.json')

# Also set GOOGLE_APPLICATION_CREDENTIALS environment variable for Google Cloud libraries
if os.path.exists(CREDENTIALS_PATH):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Vision API client once
try:
    if os.path.exists(CREDENTIALS_PATH):
        vision_client = vision.ImageAnnotatorClient.from_service_account_file(CREDENTIALS_PATH)
        logger.info(f"Successfully loaded Google Cloud Vision credentials from {CREDENTIALS_PATH}")
    else:
        # Try using default credentials from environment
        vision_client = vision.ImageAnnotatorClient()
        logger.info("Using default Google Cloud credentials from environment")
except Exception as e:
    logger.warning(f"Failed to load Vision API credentials: {e}")
    vision_client = None

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

def convert_pdf_to_images(pdf_filepath):
    """
    Convert all pages of a PDF to PNG images for Vision API processing.
    Returns list of converted PNG file paths.
    For single-page documents, returns a list with one item.
    """
    try:
        pdf_document = fitz.open(pdf_filepath)
        num_pages = len(pdf_document)
        logger.info(f"PDF has {num_pages} page(s)")

        png_filepaths = []

        # Convert all pages to images
        for page_num in range(num_pages):
            try:
                page = pdf_document[page_num]
                # Use 2x zoom for better quality
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

                # Save as PNG with page number in filename
                base_filepath = pdf_filepath.replace('.pdf', '')
                if num_pages > 1:
                    png_filepath = f"{base_filepath}_page{page_num + 1}.png"
                else:
                    png_filepath = f"{base_filepath}.png"

                pix.save(png_filepath)
                png_filepaths.append(png_filepath)
                logger.info(f"Converted page {page_num + 1} to: {png_filepath}")

            except Exception as e:
                logger.error(f"Failed to convert page {page_num + 1}: {str(e)}")
                continue

        pdf_document.close()

        if not png_filepaths:
            raise Exception("No pages were successfully converted from PDF")

        logger.info(f"Successfully converted {len(png_filepaths)} page(s) from PDF")
        return png_filepaths

    except Exception as e:
        logger.error(f"PDF conversion failed: {str(e)}")
        raise

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
    """Analyze check image endpoint"""
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
            # Handle PDF conversion if needed
            image_filepaths = [filepath]
            if filename.lower().endswith('.pdf'):
                try:
                    image_filepaths = convert_pdf_to_images(filepath)
                    logger.info(f"PDF converted to {len(image_filepaths)} image(s)")
                except Exception as e:
                    logger.error(f"PDF conversion failed: {str(e)}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    raise

            # Initialize extractor and get text for document type detection
            extractor = ProductionCheckExtractor(CREDENTIALS_PATH)

            # Get raw text for document type detection from all pages
            if vision_client is None:
                raise RuntimeError("Vision API client not initialized. Check credentials.")

            raw_text = ""
            for img_path in image_filepaths:
                try:
                    with open(img_path, 'rb') as file:
                        content = file.read()

                    image = vision.Image(content=content)
                    response = vision_client.text_detection(image=image)
                    logger.info(f"Using text_detection for: {os.path.basename(img_path)}")

                    # Check for Vision API errors
                    if response.error.message:
                        logger.error(f"Vision API Error: {response.error.message}")
                        raise Exception(f"Vision API Error: {response.error.message}")

                    page_text = response.text_annotations[0].description if response.text_annotations else ""
                    raw_text += page_text + "\n"
                    logger.info(f"Extracted {len(page_text)} characters from page")

                except Exception as e:
                    logger.error(f"Vision API request failed: {str(e)}")
                    raise

            logger.info(f"Successfully extracted text from all pages, total length: {len(raw_text)}")
            
            # Validate document type
            detected_type = detect_document_type(raw_text)
            if detected_type != 'check' and detected_type != 'unknown':
                # Clean up
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a check. Please upload a bank check.',
                    'message': 'Document type mismatch'
                }), 400
            
            # Analyze check details
            details = extractor.extract_check_details(filepath)
            
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': True,
                'data': details,
                'message': 'Check analyzed successfully'
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze check'
        }), 500

@app.route('/api/paystub/analyze', methods=['POST'])
def analyze_paystub():
    """Analyze paystub document endpoint"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Import paystub extractor from pages
            from pages.paystub_extractor import PaystubExtractor
            
            # Read file
            with open(filepath, 'rb') as f:
                file_bytes = f.read()
            
            # Determine file type
            file_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'image'
            
            # Extract text for validation
            extractor = PaystubExtractor(CREDENTIALS_PATH)
            text = extractor.extract_text(file_bytes, file_type)
            
            # Validate document type
            detected_type = detect_document_type(text)
            if detected_type != 'paystub' and detected_type != 'unknown':
                # Clean up
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a paystub. Please upload a paystub document.',
                    'message': 'Document type mismatch'
                }), 400
            
            # Extract and analyze
            details = extractor.extract_paystub(text)
            
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': True,
                'data': details,
                'message': 'Paystub analyzed successfully'
            })
            
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
    """Analyze money order document endpoint"""
    try:
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
            # Handle PDF conversion if needed
            image_filepaths = [filepath]
            if filename.lower().endswith('.pdf'):
                try:
                    image_filepaths = convert_pdf_to_images(filepath)
                    logger.info(f"PDF converted to {len(image_filepaths)} image(s)")
                except Exception as e:
                    logger.error(f"PDF conversion failed: {str(e)}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    raise

            # Get raw text for document type detection from all pages
            if vision_client is None:
                raise RuntimeError("Vision API client not initialized. Check credentials.")

            raw_text = ""
            for img_path in image_filepaths:
                try:
                    with open(img_path, 'rb') as file:
                        content = file.read()

                    image = vision.Image(content=content)
                    response = vision_client.text_detection(image=image)
                    logger.info(f"Using text_detection for: {os.path.basename(img_path)}")

                    # Check for Vision API errors
                    if response.error.message:
                        logger.error(f"Vision API Error: {response.error.message}")
                        raise Exception(f"Vision API Error: {response.error.message}")

                    page_text = response.text_annotations[0].description if response.text_annotations else ""
                    raw_text += page_text + "\n"
                    logger.info(f"Extracted {len(page_text)} characters from page")

                except Exception as e:
                    logger.error(f"Vision API request failed: {str(e)}")
                    raise

            logger.info(f"Successfully extracted text from all pages, total length: {len(raw_text)}")

            # Validate document type
            detected_type = detect_document_type(raw_text)
            if detected_type != 'money_order' and detected_type != 'unknown':
                # Clean up
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a money order. Please upload a money order document.',
                    'message': 'Document type mismatch'
                }), 400

            # Try to import and use money order extractor
            try:
                from money_order_extractor import MoneyOrderExtractor
                extractor = MoneyOrderExtractor(CREDENTIALS_PATH)
                result = extractor.extract_money_order(filepath)
                logger.info("Money order extracted successfully")
            except ImportError:
                logger.warning("MoneyOrderExtractor module not found. Returning basic analysis.")
                result = {
                    'raw_text': raw_text[:500],
                    'status': 'partial',
                    'message': 'Money order extractor not available. Using vision API text extraction only.'
                }

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'success': True,
                'data': result,
                'message': 'Money order analyzed successfully'
            })

        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze money order'
        }), 500

@app.route('/api/bank-statement/analyze', methods=['POST'])
def analyze_bank_statement():
    """Analyze bank statement document endpoint"""
    try:
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
            # Handle PDF conversion if needed
            image_filepaths = [filepath]
            if filename.lower().endswith('.pdf'):
                try:
                    image_filepaths = convert_pdf_to_images(filepath)
                    logger.info(f"PDF converted to {len(image_filepaths)} image(s)")
                except Exception as e:
                    logger.error(f"PDF conversion failed: {str(e)}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    raise

            # Get raw text for document type detection from all pages
            if vision_client is None:
                raise RuntimeError("Vision API client not initialized. Check credentials.")

            raw_text = ""
            for img_path in image_filepaths:
                try:
                    with open(img_path, 'rb') as file:
                        content = file.read()

                    image = vision.Image(content=content)
                    response = vision_client.text_detection(image=image)
                    logger.info(f"Using text_detection for: {os.path.basename(img_path)}")

                    # Check for Vision API errors
                    if response.error.message:
                        logger.error(f"Vision API Error: {response.error.message}")
                        raise Exception(f"Vision API Error: {response.error.message}")

                    page_text = response.text_annotations[0].description if response.text_annotations else ""
                    raw_text += page_text + "\n"
                    logger.info(f"Extracted {len(page_text)} characters from page")

                except Exception as e:
                    logger.error(f"Vision API request failed: {str(e)}")
                    raise

            logger.info(f"Successfully extracted text from all pages, total length: {len(raw_text)}")

            # Validate document type
            detected_type = detect_document_type(raw_text)
            if detected_type != 'bank_statement' and detected_type != 'unknown':
                # Clean up all temp files
                for img_path in image_filepaths:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                if filepath != image_filepaths[0] and os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a bank statement. Please upload a bank statement document.',
                    'message': 'Document type mismatch'
                }), 400

            # Try to import and use bank statement extractor
            try:
                from bank_statement_extractor import BankStatementExtractor
                extractor = BankStatementExtractor(CREDENTIALS_PATH)
                # Use the first converted image for extraction (or original if not PDF)
                extract_path = image_filepaths[0] if image_filepaths else filepath
                result = extractor.extract_statement_details(extract_path)
                logger.info("Bank statement extracted successfully")
            except ImportError:
                logger.warning("BankStatementExtractor module not found. Returning basic analysis.")
                result = {
                    'raw_text': raw_text[:500],
                    'status': 'partial',
                    'message': 'Bank statement extractor not available. Using vision API text extraction only.'
                }

            # Clean up all temp files (both original and converted)
            for img_path in image_filepaths:
                if os.path.exists(img_path):
                    os.remove(img_path)
            if filepath != image_filepaths[0] and os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'success': True,
                'data': result,
                'message': 'Bank statement analyzed successfully'
            })

        except Exception as e:
            # Clean up on error - remove all temp files
            try:
                for img_path in image_filepaths:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                if filepath != image_filepaths[0] and os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
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
            service = get_fraud_detection_service(vision_client=vision_client)
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
            service = get_fraud_detection_service(vision_client=vision_client)
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

