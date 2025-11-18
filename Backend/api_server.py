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
import fitz
from google.cloud import vision
from auth import login_user, register_user, token_required

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
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'google-credentials.json')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Vision API client once
try:
    vision_client = vision.ImageAnnotatorClient.from_service_account_file(CREDENTIALS_PATH)
    logger.info(f"Successfully loaded Google Cloud Vision credentials from {CREDENTIALS_PATH}")
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

def detect_document_type(text):
    """
    Detect document type based on text content
    Returns: 'check', 'paystub', 'money_order', 'bank_statement', or 'unknown'
    """
    text_lower = text.lower()

    # Priority check: Strong identifiers that definitively indicate document type
    # Check for money order FIRST with strong keywords
    if 'money order' in text_lower or 'western union' in text_lower or 'moneygram' in text_lower:
        return 'money_order'

    # Check for bank statement strong indicators
    if ('statement period' in text_lower or 'account summary' in text_lower or
        'beginning balance' in text_lower or 'transaction detail' in text_lower):
        return 'bank_statement'

    # Check for paystub strong indicators
    if ('gross pay' in text_lower or 'net pay' in text_lower or
        ('ytd' in text_lower and 'earnings' in text_lower)):
        return 'paystub'

    # Check for check strong indicators
    if 'routing number' in text_lower or 'micr' in text_lower or 'check number' in text_lower:
        return 'check'

    # Fallback: Use keyword counting for less obvious cases
    # Check for check-specific keywords
    check_keywords = ['pay to the order of', 'account number', 'memo', 'void', 'dollars']
    check_count = sum(1 for keyword in check_keywords if keyword in text_lower)

    # Check for paystub-specific keywords
    paystub_keywords = ['earnings', 'deductions', 'federal tax', 'state tax', 'social security', 'medicare', 'employee', 'employer', 'pay period', 'paycheck']
    paystub_count = sum(1 for keyword in paystub_keywords if keyword in text_lower)

    # Check for money order keywords
    money_order_keywords = ['purchaser', 'serial number', 'receipt', 'remitter']
    money_order_count = sum(1 for keyword in money_order_keywords if keyword in text_lower)

    # Check for bank statement keywords
    bank_statement_keywords = ['ending balance', 'checking summary', 'deposits', 'withdrawals', 'daily balance']
    bank_statement_count = sum(1 for keyword in bank_statement_keywords if keyword in text_lower)

    # Determine document type based on keyword matches
    max_count = max(check_count, paystub_count, money_order_count, bank_statement_count)

    if max_count == 0:
        return 'unknown'

    if check_count == max_count:
        return 'check'
    elif paystub_count == max_count:
        return 'paystub'
    elif bank_statement_count == max_count:
        return 'bank_statement'
    else:
        return 'money_order'

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
    """Login endpoint - Uses Supabase for user authentication"""
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400

        # Try Supabase auth first, fallback to JSON auth if needed
        if SUPABASE_AVAILABLE and login_user_supabase:
            result, status_code = login_user_supabase(data['email'], data['password'])
            return jsonify(result), status_code
        else:
            # Fallback to local auth
            result, status_code = login_user(data['email'], data['password'])
            return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Login failed'
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register endpoint - Uses Supabase for user registration"""
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400

        # Try Supabase auth first, fallback to local auth
        if SUPABASE_AVAILABLE and register_user_supabase:
            result, status_code = register_user_supabase(data['email'], data['password'])
            return jsonify(result), status_code
        else:
            # Fallback to local auth
            result, status_code = register_user(data['email'], data['password'])
            return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Registration failed'
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
            if filename.lower().endswith('.pdf'):
                try:
                    pdf_document = fitz.open(filepath)
                    page = pdf_document[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    pdf_document.close()

                    # Save as PNG
                    new_filepath = filepath.replace('.pdf', '.png')
                    with open(new_filepath, 'wb') as f:
                        f.write(img_bytes)
                    os.remove(filepath)
                    filepath = new_filepath
                    logger.info(f"Successfully converted PDF to PNG: {new_filepath}")
                except Exception as e:
                    logger.error(f"PDF conversion failed: {e}")
                    raise

            # Initialize extractor and get text for validation
            extractor = ProductionCheckExtractor(CREDENTIALS_PATH)

            # Get raw text for document type detection
            if vision_client is None:
                raise RuntimeError("Vision API client not initialized. Check credentials.")

            with open(filepath, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = vision_client.text_detection(image=image)
            raw_text = response.text_annotations[0].description if response.text_annotations else ""
            logger.info(f"Detected document type: check")
            
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
            if filename.lower().endswith('.pdf'):
                try:
                    pdf_document = fitz.open(filepath)
                    page = pdf_document[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    pdf_document.close()

                    # Save as PNG
                    new_filepath = filepath.replace('.pdf', '.png')
                    with open(new_filepath, 'wb') as f:
                        f.write(img_bytes)
                    os.remove(filepath)
                    filepath = new_filepath
                    logger.info(f"Successfully converted PDF to PNG: {new_filepath}")
                except Exception as e:
                    logger.error(f"PDF conversion failed: {e}")
                    raise

            # Get raw text for document type detection
            if vision_client is None:
                raise RuntimeError("Vision API client not initialized. Check credentials.")

            with open(filepath, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = vision_client.text_detection(image=image)
            raw_text = response.text_annotations[0].description if response.text_annotations else ""

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
            if filename.lower().endswith('.pdf'):
                try:
                    pdf_document = fitz.open(filepath)
                    page = pdf_document[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    pdf_document.close()

                    # Save as PNG
                    new_filepath = filepath.replace('.pdf', '.png')
                    with open(new_filepath, 'wb') as f:
                        f.write(img_bytes)
                    os.remove(filepath)
                    filepath = new_filepath
                    logger.info(f"Successfully converted PDF to PNG: {new_filepath}")
                except Exception as e:
                    logger.error(f"PDF conversion failed: {e}")
                    raise

            # Get raw text for document type detection
            if vision_client is None:
                raise RuntimeError("Vision API client not initialized. Check credentials.")

            with open(filepath, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = vision_client.text_detection(image=image)
            raw_text = response.text_annotations[0].description if response.text_annotations else ""

            # Validate document type
            detected_type = detect_document_type(raw_text)
            if detected_type != 'bank_statement' and detected_type != 'unknown':
                # Clean up
                if os.path.exists(filepath):
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
                result = extractor.extract_statement_details(filepath)
                logger.info("Bank statement extracted successfully")
            except ImportError:
                logger.warning("BankStatementExtractor module not found. Returning basic analysis.")
                result = {
                    'raw_text': raw_text[:500],
                    'status': 'partial',
                    'message': 'Bank statement extractor not available. Using vision API text extraction only.'
                }

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'success': True,
                'data': result,
                'message': 'Bank statement analyzed successfully'
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
            'message': 'Failed to analyze bank statement'
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
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5001)

