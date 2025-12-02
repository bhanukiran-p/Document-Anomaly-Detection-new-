"""
Flask API Server for XFORIA DAD
Handles Check, Paystub, Money Order, and Bank Statement Analysis
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
import importlib.util
import re
import fitz
from google.cloud import vision
from auth import login_user, register_user
from database.supabase_client import get_supabase, check_connection as check_supabase_connection
from auth.supabase_auth import login_user_supabase, register_user_supabase, verify_token
from database.document_storage import store_money_order_analysis, store_bank_statement_analysis, store_paystub_analysis, store_check_analysis

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

# Load environment variables explicitly
from dotenv import load_dotenv
load_dotenv()

# Check for critical environment variables
if os.getenv('OPENAI_API_KEY'):
    logger.info("✅ OPENAI_API_KEY found in environment")
else:
    logger.error("❌ OPENAI_API_KEY NOT found in environment")

if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    logger.info(f"✅ Google Credentials path: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
else:
    logger.warning("⚠️ GOOGLE_APPLICATION_CREDENTIALS not set")

# Load the production extractor
try:
    spec = importlib.util.spec_from_file_location(
        "production_extractor",
        "production_google_vision-extractor.py"
    )
    production_extractor = importlib.util.module_from_spec(spec)
    sys.modules["production_extractor"] = production_extractor
    spec.loader.exec_module(production_extractor)
    ProductionCheckExtractor = production_extractor.ProductionCheckExtractor
    PRODUCTION_EXTRACTOR_AVAILABLE = True
except Exception as e:
    logger.warning(f"Production extractor not available: {e}. Using Mindee extractor instead.")
    ProductionCheckExtractor = None
    PRODUCTION_EXTRACTOR_AVAILABLE = False

# Legacy import removed - using check.CheckExtractor instead
# from check_analysis.orchestrator import CheckAnalysisOrchestrator

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
try:
    supabase = get_supabase()
    supabase_status = check_supabase_connection()
    logger.info(f"Supabase initialization: {supabase_status['message']}")
except Exception as e:
    logger.warning(f"Failed to initialize Supabase: {e}")
    supabase = None

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
            from check import CheckExtractor

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
            # Import paystub extractor (Mindee-based)
            from paystub.paystub_extractor import PaystubExtractor
            
            # Initialize extractor (no credentials needed for Mindee)
            extractor = PaystubExtractor()
            
            # Extract and analyze (complete pipeline)
            details = extractor.extract_and_analyze(filepath)

            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)

            # Store to database
            user_id = request.form.get('user_id', 'public')
            document_id = store_paystub_analysis(user_id, filename, details)
            logger.info(f"Paystub stored to database: {document_id}")

            # Update employee fraud status after analysis
            try:
                from paystub.database.paystub_customer_storage import PaystubCustomerStorage
                employee_name = details.get('normalized_data', {}).get('employee_name') or details.get('extracted_data', {}).get('employee_name')
                ai_recommendation = details.get('ai_analysis', {}).get('recommendation') or details.get('ai_recommendation', 'UNKNOWN')
                
                if employee_name and ai_recommendation in ['APPROVE', 'REJECT', 'ESCALATE']:
                    storage = PaystubCustomerStorage()
                    storage.update_employee_fraud_status(employee_name, ai_recommendation, document_id)
                    logger.info(f"Updated employee {employee_name} fraud status: {ai_recommendation}")
            except Exception as e:
                logger.warning(f"Failed to update employee fraud status: {e}")

            # Extract fraud types and explanations for API response
            ml_analysis = details.get('ml_analysis', {})
            ai_analysis = details.get('ai_analysis', {})
            employee_info = details.get('employee_info', {})

            # Prefer AI fraud types/explanations, fallback to ML
            # Always include ML fraud types even if AI doesn't have them (e.g., repeat offenders)
            ai_fraud_types = ai_analysis.get('fraud_types', []) if ai_analysis else []
            ml_fraud_types = ml_analysis.get('fraud_types', [])
            fraud_types = ai_fraud_types if ai_fraud_types else ml_fraud_types

            # For fraud explanations, prefer AI but include ML reasons if AI doesn't have structured explanations
            fraud_explanations = ai_analysis.get('fraud_explanations', []) if ai_analysis else []
            # If no AI explanations but we have ML fraud types and reasons, build explanations from ML
            if not fraud_explanations and ml_fraud_types:
                ml_fraud_reasons = ml_analysis.get('fraud_reasons', [])
                fraud_explanations = [{
                    'type': fraud_type,
                    'reasons': ml_fraud_reasons if ml_fraud_reasons else [f"Detected as {fraud_type.replace('_', ' ').title()} by ML analysis."]
                } for fraud_type in ml_fraud_types[:1]]  # Use first fraud type for primary card

            # Build structured response
            response_data = {
                'success': True,
                'fraud_risk_score': ml_analysis.get('fraud_risk_score', 0.0),
                'risk_level': ml_analysis.get('risk_level', 'UNKNOWN'),
                'model_confidence': ml_analysis.get('model_confidence', 0.0),
                'fraud_types': fraud_types if isinstance(fraud_types, list) else [],
                'fraud_explanations': fraud_explanations if isinstance(fraud_explanations, list) else [],
                'ai_recommendation': ai_analysis.get('recommendation', 'UNKNOWN'),
                'ai_confidence': ai_analysis.get('confidence_score', 0.0),
                'summary': ai_analysis.get('summary', ''),
                'key_indicators': ai_analysis.get('key_indicators', []),
                'employee_info': employee_info,  # Include employee history
                'document_id': document_id,
                'data': details,  # Keep full details for backward compatibility
                'message': 'Paystub analyzed and stored successfully'
            }
            
            return jsonify(response_data)
        except RuntimeError as e:
            # Clean up file on error
            if os.path.exists(filepath):
                os.remove(filepath)
            
            error_msg = str(e)
            logger.error(f"Paystub analysis failed: {error_msg}")
            
            # Check if it's ML or AI error
            if "ML model" in error_msg or "model" in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': 'ML_MODEL_ERROR',
                    'message': f'ML model error: {error_msg}',
                    'details': 'The ML fraud detection model is not available. Please train the model using: python training/train_risk_model.py'
                }), 500
            elif "AI" in error_msg or "OpenAI" in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'AI_ANALYSIS_ERROR',
                    'message': f'AI analysis error: {error_msg}',
                    'details': 'The AI fraud analysis service is not available. Please check OpenAI API key and network connectivity.'
                }), 500
            else:
                return jsonify({
                    'success': False,
                    'error': 'ANALYSIS_ERROR',
                    'message': error_msg
                }), 500
            
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
            raw_text = ""
            if vision_client is not None:
                try:
                    with open(filepath, 'rb') as image_file:
                        content = image_file.read()
                    image = vision.Image(content=content)
                    response = vision_client.text_detection(image=image)
                    raw_text = response.text_annotations[0].description if response.text_annotations else ""
                    logger.info("Successfully extracted text using Vision API")
                except Exception as e:
                    logger.warning(f"Vision API text extraction failed: {e}. Proceeding without OCR text.")
                    raw_text = ""
            else:
                logger.warning("Vision API client not initialized. Proceeding without OCR text.")

            # Validate document type only if we have text
            if raw_text:
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
                from money_order.extractor import MoneyOrderExtractor
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

            def convert_numpy_types(obj):
                import numpy as np
                if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                                  np.int16, np.int32, np.int64, np.uint8,
                                  np.uint16, np.uint32, np.uint64)):
                    return int(obj)
                elif isinstance(obj, (np.float16, np.float32, np.float64)):
                    return float(obj)
                elif isinstance(obj, (np.ndarray,)):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(i) for i in obj]
                return obj

            # Return full response
            analysis_id = result.get('analysis_id')

            # Ensure we return the complete result with converted types
            response_data = convert_numpy_types(result)

            # Store to database
            user_id = request.form.get('user_id', 'public')
            document_id = store_money_order_analysis(user_id, filename, result)
            logger.info(f"Money order stored to database: {document_id}")

            return jsonify({
                'success': True,
                'data': response_data,
                'analysis_id': analysis_id,  # For download
                'document_id': document_id,  # Database record ID
                'message': 'Money order analyzed and stored successfully'
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


@app.route('/api/analysis/download/<analysis_id>', methods=['GET'])
def download_analysis(analysis_id):
    """Download complete JSON analysis by ID"""
    try:
        # Build file path
        filepath = os.path.join('analysis_results', f"{analysis_id}.json")

        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Analysis not found',
                'message': f'No analysis found with ID: {analysis_id}'
            }), 404

        # Send file as download
        return send_file(
            filepath,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'{analysis_id}.json'
        )

    except Exception as e:
        logger.error(f"Error downloading analysis {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to download analysis'
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

            # Use new bank statement extractor module
            try:
                from bank_statement.bank_statement_extractor import BankStatementExtractor
                extractor = BankStatementExtractor()
                result = extractor.extract_and_analyze(filepath)
                logger.info("Bank statement extracted and analyzed successfully")
            except ImportError as e:
                logger.warning(f"Bank statement extractor module not found: {e}. Returning basic analysis.")
                result = {
                    'raw_text': raw_text[:500],
                    'status': 'partial',
                    'message': 'Bank statement extractor not available. Using vision API text extraction only.'
                }
            except Exception as e:
                logger.error(f"Bank statement extraction failed: {e}", exc_info=True)
                # Clean up temp file
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to analyze bank statement'
                }), 500

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Store to database
            user_id = request.form.get('user_id', 'public')
            document_id = store_bank_statement_analysis(user_id, filename, result)
            logger.info(f"Bank statement stored to database: {document_id}")

            # Update customer fraud status after analysis
            ai_analysis = result.get('ai_analysis')
            if ai_analysis:
                recommendation = ai_analysis.get('recommendation')
                # Try multiple sources for account holder name
                extracted_data = result.get('extracted_data', {})
                normalized_data = result.get('normalized_data', {})
                account_holder_name = (
                    normalized_data.get('account_holder_name') or 
                    extracted_data.get('account_holder_name') or 
                    extracted_data.get('account_holder') or
                    (extracted_data.get('account_holder_names', [])[0] if isinstance(extracted_data.get('account_holder_names'), list) and len(extracted_data.get('account_holder_names', [])) > 0 else None)
                )

                if account_holder_name and recommendation:
                    try:
                        from bank_statement.database.bank_statement_customer_storage import BankStatementCustomerStorage
                        customer_storage = BankStatementCustomerStorage()
                        customer_storage.update_customer_fraud_status(
                            account_holder_name=account_holder_name,
                            recommendation=recommendation,
                            statement_id=result.get('statement_id')
                        )
                        logger.info(f"Updated customer {account_holder_name} fraud status: {recommendation}")
                    except Exception as e:
                        logger.error(f"Failed to update customer fraud status: {e}", exc_info=True)
                else:
                    if not account_holder_name:
                        logger.warning("Cannot update customer fraud status - account holder name missing")
                    if not recommendation:
                        logger.warning("Cannot update customer fraud status - AI recommendation missing")

            return jsonify({
                'success': True,
                'data': result,
                'document_id': document_id,
                'message': 'Bank statement analyzed and stored successfully'
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

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Build complete response
            response_data = {
                'success': True,
                'csv_info': csv_result,
                'fraud_detection': fraud_result,
                'insights': insights_result,
                'agent_analysis': agent_analysis.get('agent_analysis') if agent_analysis and agent_analysis.get('success') else None,
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
    print(f"  - POST /api/real-time/analyze")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5001)

