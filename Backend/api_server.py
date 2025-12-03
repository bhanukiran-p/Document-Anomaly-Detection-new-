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
            
            # Get AI recommendation first
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN') if ai_analysis else 'UNKNOWN'
            ai_recommendation = ai_recommendation.upper()

            # Only show fraud types if recommendation is REJECT
            # For ESCALATE or APPROVE, show "Escalated" or "No Fraud Found"
            fraud_type = None
            fraud_type_label = None
            fraud_explanations = []
            
            if ai_recommendation == 'REJECT':
                # Only show fraud types for REJECT recommendations
                ai_fraud_types = ai_analysis.get('fraud_types', []) if ai_analysis else []
                ml_fraud_types = ml_analysis.get('fraud_types', [])

                # Extract the primary fraud type (should be a single-element list)
                if ai_fraud_types:
                    fraud_type = ai_fraud_types[0] if isinstance(ai_fraud_types, list) else ai_fraud_types
                elif ml_fraud_types:
                    fraud_type = ml_fraud_types[0] if isinstance(ml_fraud_types, list) else ml_fraud_types

                # Format fraud type for display (remove underscores and title case)
                fraud_type_label = fraud_type.replace('_', ' ').title() if fraud_type else None

                # For fraud explanations, prefer AI but include ML reasons if AI doesn't have structured explanations
                fraud_explanations = ai_analysis.get('fraud_explanations', []) if ai_analysis else []
                # If no AI explanations but we have a fraud type and reasons, build explanations from ML
                if not fraud_explanations and fraud_type:
                    ml_fraud_reasons = ml_analysis.get('fraud_reasons', [])
                    fraud_explanations = [{
                        'type': fraud_type,
                        'reasons': ml_fraud_reasons if ml_fraud_reasons else [f"Detected as {fraud_type_label} by ML analysis."]
                    }]
            elif ai_recommendation == 'ESCALATE':
                # For ESCALATE, show "Escalated" and "No Fraud Found"
                fraud_type = 'ESCALATED'
                fraud_type_label = 'Escalated'
                fraud_explanations = [{
                    'type': 'ESCALATED',
                    'reasons': ['No fraud detected. Document escalated for manual review.']
                }]
            elif ai_recommendation == 'APPROVE':
                # For APPROVE, show "Approved" and "No Fraud Found"
                fraud_type = 'APPROVED'
                fraud_type_label = 'Approved'
                fraud_explanations = [{
                    'type': 'APPROVED',
                    'reasons': ['No fraud detected. Document approved.']
                }]

            # Build structured response
            response_data = {
                'success': True,
                'fraud_risk_score': ml_analysis.get('fraud_risk_score', 0.0),
                'risk_level': ml_analysis.get('risk_level', 'UNKNOWN'),
                'model_confidence': ml_analysis.get('model_confidence', 0.0),
                'fraud_type': fraud_type,  # Single fraud type (machine format)
                'fraud_type_label': fraud_type_label,  # Human-readable format (e.g., "Zero Withholding Suspicious")
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

            # Store to database (customer_id now created during storage)
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
                            statement_id=document_id
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


# Database query endpoints for importing from Supabase tables
@app.route('/api/checks/list', methods=['GET'])
def get_checks_list():
    """Fetch list of checks from database view with optional date filtering"""
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
            response = supabase.table('v_checks_analysis').select('*', count=count_param).order('created_at', desc=True).range(offset, offset + page_size - 1).execute()
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
            'count': len(data),
            'total_records': total_available if not date_filter else None,
            'date_filter': date_filter
        })
    except Exception as e:
        logger.error(f"Failed to fetch checks list: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch checks list'
        }), 500


@app.route('/api/checks/<check_id>', methods=['GET'])
def get_check_details(check_id):
    """Fetch detailed check data from view"""
    try:
        supabase = get_supabase()
        response = supabase.table('v_checks_analysis').select('*').eq('check_id', check_id).execute()
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'Check not found',
                'message': f'No check found with ID: {check_id}'
            }), 404
        return jsonify({
            'success': True,
            'data': response.data[0]
        })
    except Exception as e:
        logger.error(f"Failed to fetch check details: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch check details'
        }), 500


@app.route('/api/checks/search', methods=['GET'])
def search_checks():
    """Search checks by payer name from view"""
    try:
        supabase = get_supabase()
        query = request.args.get('q', default='', type=str)
        limit = request.args.get('limit', default=20, type=int)
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required',
                'message': 'Please provide a search query'
            }), 400
        response = supabase.table('v_checks_analysis').select('*').ilike('payer_name', f'%{query}%').limit(limit).execute()
        return jsonify({
            'success': True,
            'data': response.data,
            'count': len(response.data)
        })
    except Exception as e:
        logger.error(f"Failed to search checks: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to search checks'
        }), 500


# Database query endpoints for money orders
@app.route('/api/money-orders/list', methods=['GET'])
def get_money_orders_list():
    """Fetch list of money orders from database view with optional date filtering"""
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
            response = supabase.table('v_money_orders_analysis').select('*', count=count_param).order('created_at', desc=True).range(offset, offset + page_size - 1).execute()
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
            'count': len(data),
            'total_records': total_available if not date_filter else None,
            'date_filter': date_filter
        })
    except Exception as e:
        logger.error(f"Failed to fetch money orders list: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch money orders list'
        }), 500


@app.route('/api/money-orders/<money_order_id>', methods=['GET'])
def get_money_order_details(money_order_id):
    """Fetch detailed money order data from view"""
    try:
        supabase = get_supabase()
        response = supabase.table('v_money_orders_analysis').select('*').eq('money_order_id', money_order_id).execute()
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'Money order not found',
                'message': f'No money order found with ID: {money_order_id}'
            }), 404
        return jsonify({
            'success': True,
            'data': response.data[0]
        })
    except Exception as e:
        logger.error(f"Failed to fetch money order details: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch money order details'
        }), 500


@app.route('/api/money-orders/search', methods=['GET'])
def search_money_orders():
    """Search money orders by purchaser name from view"""
    try:
        supabase = get_supabase()
        query = request.args.get('q', default='', type=str)
        limit = request.args.get('limit', default=20, type=int)
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required',
                'message': 'Please provide a search query'
            }), 400
        response = supabase.table('v_money_orders_analysis').select('*').ilike('purchaser_name', f'%{query}%').limit(limit).execute()
        return jsonify({
            'success': True,
            'data': response.data,
            'count': len(response.data)
        })
    except Exception as e:
        logger.error(f"Failed to search money orders: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to search money orders'
        }), 500


@app.route('/api/documents/list', methods=['GET'])
def get_documents_list():
    """Fetch list of all documents from v_documents_with_risk view with optional filtering"""
    try:
        from datetime import datetime
        supabase = get_supabase()

        # Fetch all records using pagination to bypass Supabase default limit of 1000
        all_data = []
        page_size = 1000
        offset = 0
        total_count = None
        
        while True:
            # Get count only on first request
            count_param = 'exact' if offset == 0 else None
            response = supabase.table('v_documents_with_risk').select('*', count=count_param).order('upload_date', desc=True).range(offset, offset + page_size - 1).execute()
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

        # Apply filters
        date_filter = request.args.get('date_filter', default=None)
        document_type_filter = request.args.get('document_type', default=None)
        risk_level_filter = request.args.get('risk_level', default=None)
        status_filter = request.args.get('status', default=None)

        if date_filter:
            now = datetime.utcnow()
            filtered_data = []

            for record in data:
                upload_date_str = record.get('upload_date')
                if not upload_date_str:
                    continue

                # Parse upload_date timestamp
                try:
                    if 'T' in upload_date_str:
                        upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00').split('+')[0])
                    else:
                        upload_date = datetime.fromisoformat(upload_date_str)
                except:
                    continue

                days_old = (now - upload_date).days

                if date_filter == 'last_30' and days_old <= 30:
                    filtered_data.append(record)
                elif date_filter == 'last_60' and days_old <= 60:
                    filtered_data.append(record)
                elif date_filter == 'last_90' and days_old <= 90:
                    filtered_data.append(record)
                elif date_filter == 'older' and days_old > 90:
                    filtered_data.append(record)

            data = filtered_data

        # Apply document_type filter
        if document_type_filter:
            data = [r for r in data if r.get('document_type', '').lower() == document_type_filter.lower()]

        # Apply risk_level filter
        if risk_level_filter:
            data = [r for r in data if r.get('risk_level', '').upper() == risk_level_filter.upper()]

        # Apply status filter
        if status_filter:
            data = [r for r in data if r.get('status', '').lower() == status_filter.lower()]

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'total_records': total_available if not (date_filter or document_type_filter or risk_level_filter or status_filter) else None,
            'date_filter': date_filter,
            'document_type_filter': document_type_filter,
            'risk_level_filter': risk_level_filter,
            'status_filter': status_filter
        })
    except Exception as e:
        logger.error(f"Failed to fetch documents list: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch documents list: {str(e)}'
        }), 500


@app.route('/api/documents/enriched', methods=['GET'])
def get_enriched_documents():
    """Fetch documents with enriched data from individual tables (payer, payee, amount, etc.)"""
    try:
        from datetime import datetime
        supabase = get_supabase()
        
        # Get base documents from view
        date_filter = request.args.get('date_filter', default=None)
        document_type_filter = request.args.get('document_type', default=None)
        risk_level_filter = request.args.get('risk_level', default=None)
        status_filter = request.args.get('status', default=None)
        
        # Build query for base documents
        query = supabase.table('v_documents_with_risk').select('*')
        
        if date_filter:
            # Apply date filter logic (similar to list endpoint)
            # For now, fetch all and filter in Python
            pass
        
        response = query.order('upload_date', desc=True).limit(5000).execute()
        base_docs = response.data or []
        
        # Apply filters
        if date_filter:
            now = datetime.utcnow()
            filtered = []
            for doc in base_docs:
                upload_date_str = doc.get('upload_date')
                if not upload_date_str:
                    continue
                try:
                    if 'T' in upload_date_str:
                        upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00').split('+')[0])
                    else:
                        upload_date = datetime.fromisoformat(upload_date_str)
                    days_old = (now - upload_date).days
                    if date_filter == 'last_30' and days_old <= 30:
                        filtered.append(doc)
                    elif date_filter == 'last_60' and days_old <= 60:
                        filtered.append(doc)
                    elif date_filter == 'last_90' and days_old <= 90:
                        filtered.append(doc)
                    elif date_filter == 'older' and days_old > 90:
                        filtered.append(doc)
                except:
                    continue
            base_docs = filtered
        
        if document_type_filter:
            base_docs = [d for d in base_docs if d.get('document_type', '').lower() == document_type_filter.lower()]
        if risk_level_filter:
            base_docs = [d for d in base_docs if (d.get('risk_level') or '').upper().replace(' ', '') == risk_level_filter.upper()]
        if status_filter:
            base_docs = [d for d in base_docs if (d.get('status') or '').lower() == status_filter.lower()]
        
        # Enrich with data from individual tables
        enriched_docs = []
        for doc in base_docs:
            doc_type = doc.get('document_type', '').lower()
            doc_id = doc.get('document_id')
            
            enriched = {**doc}
            
            # Fetch additional fields based on document type
            try:
                if doc_type == 'check':
                    check_resp = supabase.table('checks').select('payer_name,payee_name,amount,check_number,ai_recommendation,model_confidence').eq('document_id', doc_id).limit(1).execute()
                    if check_resp.data:
                        check_data = check_resp.data[0]
                        enriched['payer_name'] = check_data.get('payer_name')
                        enriched['payee_name'] = check_data.get('payee_name')
                        enriched['amount'] = check_data.get('amount')
                        enriched['check_number'] = check_data.get('check_number')
                        enriched['ai_recommendation'] = enriched.get('ai_recommendation') or check_data.get('ai_recommendation')
                        enriched['model_confidence'] = enriched.get('confidence') or enriched.get('model_confidence') or check_data.get('model_confidence')
                elif doc_type == 'money_order' or doc_type == 'money order':
                    mo_resp = supabase.table('money_orders').select('purchaser_name,payee_name,amount,money_order_number,ai_recommendation,model_confidence').eq('document_id', doc_id).limit(1).execute()
                    if mo_resp.data:
                        mo_data = mo_resp.data[0]
                        enriched['purchaser_name'] = mo_data.get('purchaser_name')
                        enriched['payee_name'] = mo_data.get('payee_name')
                        enriched['amount'] = mo_data.get('amount')
                        enriched['money_order_number'] = mo_data.get('money_order_number')
                        enriched['ai_recommendation'] = enriched.get('ai_recommendation') or mo_data.get('ai_recommendation')
                        enriched['model_confidence'] = enriched.get('confidence') or enriched.get('model_confidence') or mo_data.get('model_confidence')
                elif doc_type == 'paystub':
                    ps_resp = supabase.table('paystubs').select('employee_name,employer_name,gross_pay,ai_recommendation,model_confidence').eq('document_id', doc_id).limit(1).execute()
                    if ps_resp.data:
                        ps_data = ps_resp.data[0]
                        enriched['employee_name'] = ps_data.get('employee_name')
                        enriched['amount'] = ps_data.get('gross_pay')
                        enriched['ai_recommendation'] = enriched.get('ai_recommendation') or ps_data.get('ai_recommendation')
                        enriched['model_confidence'] = enriched.get('confidence') or enriched.get('model_confidence') or ps_data.get('model_confidence')
                elif doc_type == 'bank_statement' or doc_type == 'bank statement':
                    bs_resp = supabase.table('bank_statements').select('account_holder,ai_recommendation,model_confidence').eq('document_id', doc_id).limit(1).execute()
                    if bs_resp.data:
                        bs_data = bs_resp.data[0]
                        enriched['account_holder'] = bs_data.get('account_holder')
                        enriched['ai_recommendation'] = enriched.get('ai_recommendation') or bs_data.get('ai_recommendation')
                        enriched['model_confidence'] = enriched.get('confidence') or enriched.get('model_confidence') or bs_data.get('model_confidence')
            except Exception as e:
                logger.warning(f"Could not enrich document {doc_id}: {e}")
            
            enriched_docs.append(enriched)
        
        return jsonify({
            'success': True,
            'data': enriched_docs,
            'count': len(enriched_docs)
        })
    except Exception as e:
        logger.error(f"Failed to fetch enriched documents: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch enriched documents'
        }), 500


@app.route('/api/documents/search', methods=['GET'])
def search_documents():
    """Search documents by file_name or document_id"""
    try:
        supabase = get_supabase()
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))

        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required',
                'message': 'Please provide a search query'
            }), 400

        # Search in file_name and document_id - try both and combine results
        try:
            # Try searching both fields using or_ filter
            response = supabase.table('v_documents_with_risk').select('*').or_(f'file_name.ilike.%{query}%,document_id.ilike.%{query}%').order('upload_date', desc=True).limit(limit).execute()
        except:
            # Fallback: search file_name only if or_ doesn't work
            response = supabase.table('v_documents_with_risk').select('*').ilike('file_name', f'%{query}%').order('upload_date', desc=True).limit(limit).execute()

        return jsonify({
            'success': True,
            'data': response.data or [],
            'count': len(response.data or []),
            'query': query
        })
    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to search documents'
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
    print(f"  - GET  /api/checks/list")
    print(f"  - GET  /api/checks/search")
    print(f"  - GET  /api/checks/<check_id>")
    print(f"  - GET  /api/money-orders/list")
    print(f"  - GET  /api/money-orders/search")
    print(f"  - GET  /api/money-orders/<money_order_id>")
    print(f"  - GET  /api/documents/list")
    print(f"  - GET  /api/documents/search")
    print(f"  - GET  /api/paystubs/insights")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5001)

