"""
Flask API Server for XFORIA DAD
Handles Check, Paystub, Money Order, and Bank Statement Analysis
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import logging
from werkzeug.utils import secure_filename
import importlib.util
import re
import fitz
from datetime import datetime
try:
    from google.cloud import vision
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    vision = None
from auth import login_user, register_user
try:
    from database.supabase_client import get_supabase, check_connection as check_supabase_connection
except ImportError:
    get_supabase = None
    check_supabase_connection = None

try:
    from auth.supabase_auth import login_user_supabase, register_user_supabase, verify_token
except ImportError:
    login_user_supabase = None
    register_user_supabase = None
    verify_token = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the production extractor (optional - for backward compatibility)
try:
    spec = importlib.util.spec_from_file_location(
        "production_extractor", 
        "production_google_vision-extractor.py"
    )
    if spec and spec.loader:
        production_extractor = importlib.util.module_from_spec(spec)
        sys.modules["production_extractor"] = production_extractor
        spec.loader.exec_module(production_extractor)
        ProductionCheckExtractor = production_extractor.ProductionCheckExtractor
        logger.info("Production extractor loaded successfully")
    else:
        ProductionCheckExtractor = None
        logger.warning("Production extractor file not found, using Mindee extractor instead")
except (FileNotFoundError, ImportError, AttributeError) as e:
    ProductionCheckExtractor = None
    logger.warning(f"Production extractor not available: {e}. Using Mindee extractor instead.")

try:
    from bank_statement.extractor import extract_bank_statement as mindee_extract_bank_statement
    BANK_STATEMENT_MINDEE_AVAILABLE = True
except ImportError as e:
    mindee_extract_bank_statement = None
    BANK_STATEMENT_MINDEE_AVAILABLE = False
    logger.warning(f"Bank statement extractor not available: {e}")

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
    if get_supabase and check_supabase_connection:
        supabase = get_supabase()
        supabase_status = check_supabase_connection()
        logger.info(f"Supabase initialization: {supabase_status['message']}")
    else:
        supabase = None
        logger.warning("Supabase client not available")
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

def _safe_parse_currency(value):
    """Convert currency-like values to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    negative = False
    if '(' in text and ')' in text:
        negative = True
    text = text.replace('(', '').replace(')', '')
    text = text.replace('CR', '').replace('DR', '').replace('cr', '').replace('dr', '')
    text = text.replace('$', '').replace(',', '').strip()
    if not text:
        return None
    try:
        number = float(text)
        if negative:
            number = -abs(number)
        return number
    except ValueError:
        return None

def _format_currency(value):
    """Return a currency string or 'N/A'."""
    if value is None:
        return None
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return None

def _mask_account_number(number):
    if not number:
        return None
    digits = re.sub(r'\D', '', str(number))
    if len(digits) < 4:
        return number
    return f"****{digits[-4:]}"

def _extract_bank_statement_transactions(raw_text):
    transactions = []
    if not raw_text:
        return transactions
    pattern = re.compile(
        r'(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+(?P<desc>.+?)\s+(?P<amount>[-\(\)\$0-9,\.]+)(?:\s+(?P<balance>[-\(\)\$0-9,\.]+))?$'
    )
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            amount_value = _safe_parse_currency(match.group('amount'))
            balance_value = _safe_parse_currency(match.group('balance')) if match.group('balance') else None
            transactions.append({
                'date': match.group('date'),
                'description': match.group('desc').strip(),
                'amount': _format_currency(amount_value) if amount_value is not None else match.group('amount'),
                'amount_value': amount_value if amount_value is not None else 0.0,
                'balance': _format_currency(balance_value) if balance_value is not None else match.group('balance')
            })
    return transactions

def _parse_bank_statement_text(raw_text):
    data = {
        'bank_name': None,
        'account_holder': None,
        'account_number': None,
        'statement_period': None,
        'balances': {
            'opening_balance': None,
            'ending_balance': None,
            'available_balance': None,
            'current_balance': None
        },
        'summary': {
            'transaction_count': 0,
            'total_credits': 0.0,
            'total_debits': 0.0,
            'net_activity': 0.0,
            'confidence': 40.0
        },
        'transactions': []
    }
    if not raw_text:
        return data
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if lines:
        data['bank_name'] = lines[0][:80]
    holder_match = re.search(r'account holder[:\s]+([A-Z][\w\s,\.-]+)', raw_text, re.IGNORECASE)
    if holder_match:
        data['account_holder'] = holder_match.group(1).strip()
    acct_match = re.search(r'account\s+(?:number|no\.|#)[:\s\-]*([\*\dxX]{4,})', raw_text, re.IGNORECASE)
    if acct_match:
        data['account_number'] = _mask_account_number(acct_match.group(1))
    period_match = re.search(r'statement\s+period[:\s]+([^\n]+)', raw_text, re.IGNORECASE)
    if period_match:
        data['statement_period'] = period_match.group(1).strip()
    opening_match = re.search(r'(?:beginning|opening)\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)
    ending_match = re.search(r'(?:ending|closing)\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)
    available_match = re.search(r'available\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)
    current_match = re.search(r'current\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)
    balances = data['balances']
    balances['opening_balance'] = _format_currency(_safe_parse_currency(opening_match.group(1))) if opening_match else None
    balances['ending_balance'] = _format_currency(_safe_parse_currency(ending_match.group(1))) if ending_match else None
    balances['available_balance'] = _format_currency(_safe_parse_currency(available_match.group(1))) if available_match else None
    balances['current_balance'] = _format_currency(_safe_parse_currency(current_match.group(1))) if current_match else None
    transactions = _extract_bank_statement_transactions(raw_text)
    data['transactions'] = transactions
    if transactions:
        total_credits = sum(t['amount_value'] for t in transactions if t['amount_value'] > 0)
        total_debits = sum(-t['amount_value'] for t in transactions if t['amount_value'] < 0)
        net_activity = sum(t['amount_value'] for t in transactions)
        data['summary'].update({
            'transaction_count': len(transactions),
            'total_credits': total_credits,
            'total_debits': total_debits,
            'net_activity': net_activity,
            'confidence': min(95.0, 55.0 + len(transactions) * 2.0)
        })
    data['raw_text'] = raw_text
    return data

def _merge_bank_statement_data(primary, fallback):
    if not isinstance(primary, dict):
        primary = {}
    merged = {}
    merged['bank_name'] = primary.get('bank_name') or fallback.get('bank_name')
    merged['account_holder'] = primary.get('account_holder') or fallback.get('account_holder')
    merged['account_number'] = primary.get('account_number') or fallback.get('account_number')
    merged['statement_period'] = primary.get('statement_period') or fallback.get('statement_period')
    merged['summary'] = primary.get('summary') or fallback.get('summary')
    balances = fallback.get('balances', {})
    balances_primary = primary.get('balances', {})
    merged['balances'] = {
        'opening_balance': balances_primary.get('opening_balance') or balances.get('opening_balance'),
        'ending_balance': balances_primary.get('ending_balance') or balances.get('ending_balance'),
        'available_balance': balances_primary.get('available_balance') or balances.get('available_balance'),
        'current_balance': balances_primary.get('current_balance') or balances.get('current_balance'),
    }
    merged['transactions'] = primary.get('transactions') or fallback.get('transactions') or []
    merged['raw_text'] = primary.get('raw_text') or fallback.get('raw_text')
    return merged

def _evaluate_bank_statement_risk(data):
    score = 0.25
    indicators = []
    raw_text = (data.get('raw_text') or '').lower()
    summary = data.get('summary') or {}
    balances = data.get('balances') or {}
    if not data.get('bank_name'):
        score += 0.15
        indicators.append("Bank name missing")
    if not data.get('account_number'):
        score += 0.15
        indicators.append("Account number missing")
    if summary.get('transaction_count', 0) < 3:
        score += 0.1
        indicators.append("Very few transactions detected")
    suspicious_keywords = ['nsf', 'overdraft', 'chargeback', 'return item', 'fraud alert']
    if any(keyword in raw_text for keyword in suspicious_keywords):
        score += 0.25
        indicators.append("Suspicious activity keywords found")
    opening = _safe_parse_currency(balances.get('opening_balance'))
    ending = _safe_parse_currency(balances.get('ending_balance'))
    net = summary.get('net_activity')
    if opening is not None and ending is not None and isinstance(net, (int, float)):
        if abs((opening + net) - ending) > max(50, abs(ending) * 0.05):
            score += 0.2
            indicators.append("Balances inconsistent with net activity")
    total_debits = summary.get('total_debits') or 0.0
    total_credits = summary.get('total_credits') or 0.0
    if total_credits > 0 and total_debits > total_credits * 2:
        score += 0.15
        indicators.append("Debits significantly exceed credits")
    score = max(0.0, min(1.0, score))
    if score < 0.35:
        level = 'LOW'
    elif score < 0.6:
        level = 'MEDIUM'
    elif score < 0.85:
        level = 'HIGH'
    else:
        level = 'CRITICAL'
    model_confidence = 0.65
    if summary.get('transaction_count', 0) >= 5:
        model_confidence = 0.75
    if summary.get('transaction_count', 0) >= 10:
        model_confidence = 0.85
    return {
        'fraud_risk_score': round(score, 3),
        'risk_level': level,
        'model_confidence': round(model_confidence, 3),
        'feature_importance': indicators,
        'prediction_type': 'bank_statement_rules'
    }

def _build_bank_statement_ai_analysis(risk):
    score = risk.get('fraud_risk_score', 0.0)
    level = risk.get('risk_level', 'UNKNOWN')
    if level in ['HIGH', 'CRITICAL']:
        recommendation = 'REJECT'
        confidence = 0.9
    elif level == 'MEDIUM':
        recommendation = 'ESCALATE'
        confidence = 0.75
    else:
        recommendation = 'APPROVE'
        confidence = 0.65
    summary = f"{level.title()} fraud risk ({score * 100:.1f}%)."
    reasoning = "Heuristic analysis evaluated transaction patterns, balance changes, and metadata for anomalies."
    return {
        'recommendation': recommendation,
        'confidence': confidence,
        'summary': summary,
        'reasoning': reasoning,
        'key_indicators': risk.get('feature_importance', []),
        'verification_notes': "Manual review recommended when anomalies are detected.",
        'analysis_type': 'rule_based',
        'model_used': 'bank_statement_heuristics'
    }

def _collect_bank_statement_anomalies(risk, ai_analysis):
    anomalies = []
    level = risk.get('risk_level')
    score = risk.get('fraud_risk_score', 0.0) * 100
    if level in ['HIGH', 'CRITICAL']:
        anomalies.append(f"High fraud risk detected: {level} (score: {score:.2f}%)")
    if ai_analysis.get('recommendation'):
        anomalies.append(f"AI recommendation: {ai_analysis['recommendation']}")
    anomalies.extend(risk.get('feature_importance', []))
    return anomalies

def _format_statement_period(start, end):
    if start and end:
        return f"{start} to {end}"
    return start or end

def _normalize_mindee_transactions(transactions):
    normalized = []
    if not transactions:
        return normalized
    for txn in transactions:
        if isinstance(txn, dict):
            date = txn.get('date') or txn.get('transaction_date')
            description = txn.get('description') or txn.get('details') or txn.get('label')
            amount_value = _safe_parse_currency(txn.get('amount') or txn.get('value'))
            balance_value = _safe_parse_currency(txn.get('balance'))
            normalized.append({
                'date': date,
                'description': description or 'Transaction',
                'amount': _format_currency(amount_value) if amount_value is not None else txn.get('amount'),
                'amount_value': amount_value if amount_value is not None else 0.0,
                'balance': _format_currency(balance_value) if balance_value is not None else txn.get('balance')
            })
    return normalized

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

            # Use Mindee-based check extractor
            try:
                from check.extractor import extract_check
                logger.info(f"Starting check extraction for file: {filepath}")
                result = extract_check(filepath)
                logger.info(f"Check extraction completed. Result type: {type(result)}, Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

                # Validate result structure
                if not result or not isinstance(result, dict):
                    error_msg = f"Extractor returned invalid result: result is not a dictionary (type: {type(result)})"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                if 'extracted_data' not in result and 'raw_text' not in result:
                    error_msg = f"Extractor returned invalid result: missing required fields. Available keys: {list(result.keys())}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                logger.info("Check extraction validation passed")

            except ImportError as e:
                logger.error(f"Failed to import check extractor: {e}", exc_info=True)
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': 'Check extractor not available',
                    'message': 'Failed to load check extraction module'
                }), 500
            except Exception as e:
                logger.error(f"Check extraction failed: {e}", exc_info=True)
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': f'Failed to extract check data: {str(e)}'
                }), 500

            # Get raw text for document type validation
            extracted_data = result.get('extracted_data', {}) if result else {}
            if not isinstance(extracted_data, dict):
                extracted_data = {}
            raw_text = extracted_data.get('raw_ocr_text') or result.get('raw_text') or '' if result else ''

            # Validate document type if we have raw text
            if raw_text:
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

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Format response for frontend - flatten ML and AI analysis to top level
            ml_analysis = result.get('ml_analysis', {}) or {}
            if not isinstance(ml_analysis, dict):
                ml_analysis = {}

            ai_analysis = result.get('ai_analysis', {}) or {}
            if not isinstance(ai_analysis, dict):
                ai_analysis = {}

            # Get ML values with defaults
            fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0) if isinstance(ml_analysis, dict) else 0.0
            model_confidence = ml_analysis.get('model_confidence', 0.0) if isinstance(ml_analysis, dict) else 0.0
            risk_level = ml_analysis.get('risk_level', 'UNKNOWN') if isinstance(ml_analysis, dict) else 'UNKNOWN'

            # Get AI values with defaults
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN') if isinstance(ai_analysis, dict) else 'UNKNOWN'
            ai_confidence = ai_analysis.get('confidence', 0.0) if isinstance(ai_analysis, dict) else 0.0

            # Helper function to safely convert NumPy types to Python types
            def safe_float(value):
                """Convert value to Python float, handling NumPy types"""
                if value is None:
                    return 0.0
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return 0.0

            # Flatten response with top-level fields for frontend compatibility
            formatted_data = {
                **(extracted_data if isinstance(extracted_data, dict) else {}),
                # Always include ML analysis fields at top level (convert NumPy types)
                'fraud_risk_score': safe_float(fraud_risk_score),
                'model_confidence': safe_float(model_confidence),
                'risk_level': str(risk_level) if risk_level else 'UNKNOWN',
                # Always include AI analysis fields at top level
                'ai_recommendation': str(ai_recommendation) if ai_recommendation else 'UNKNOWN',
                'ai_confidence': safe_float(ai_confidence),
                # Keep nested structures for detailed analysis
                'ml_analysis': ml_analysis if ml_analysis else {},
                'ai_analysis': ai_analysis if ai_analysis else {},
                'anomalies': result.get('anomalies', []),
                'confidence_score': safe_float(result.get('confidence_score', 0.0)),
                'timestamp': result.get('timestamp'),
            }

            response_data = {
                'success': True,
                'data': formatted_data,
                'message': 'Check analyzed successfully'
            }

            logger.info(f"Check response formatted - fraud_risk_score: {formatted_data.get('fraud_risk_score')}, risk_level: {formatted_data.get('risk_level')}")
            return jsonify(response_data)
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        logger.error(f"Check analysis endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to analyze check: {str(e)}'
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
            # Use Mindee-based paystub extractor
            try:
                from paystub.extractor import extract_paystub
                result = extract_paystub(filepath)
                logger.info("Paystub extracted successfully")
                
                # Validate result structure
                if not result or not isinstance(result, dict):
                    raise ValueError("Extractor returned invalid result: result is not a dictionary")
                if 'extracted_data' not in result and 'raw_text' not in result:
                    raise ValueError("Extractor returned invalid result: missing required fields")
                    
            except ImportError as e:
                logger.error(f"Failed to import paystub extractor: {e}")
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': 'Paystub extractor not available',
                    'message': 'Failed to load paystub extraction module'
                }), 500
            except Exception as e:
                logger.error(f"Paystub extraction failed: {e}", exc_info=True)
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': f'Failed to extract paystub data: {str(e)}'
                }), 500

            # Get raw text for document type validation
            extracted_data = result.get('extracted_data', {}) if result else {}
            if not isinstance(extracted_data, dict):
                extracted_data = {}
            raw_text = extracted_data.get('raw_ocr_text') or result.get('raw_text') or '' if result else ''

            # Validate document type if we have raw text
            if raw_text:
                detected_type = detect_document_type(raw_text)
                if detected_type != 'paystub' and detected_type != 'unknown':
                    # Clean up
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return jsonify({
                        'success': False,
                        'error': f'Wrong document type detected. This appears to be a {detected_type}, not a paystub. Please upload a paystub document.',
                        'message': 'Document type mismatch'
                    }), 400

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Format response to match check/money order structure
            extracted_data = result.get('extracted_data', {})
            if not isinstance(extracted_data, dict):
                extracted_data = {}

            ml_analysis = result.get('ml_analysis', {}) or {}
            if not isinstance(ml_analysis, dict):
                ml_analysis = {}

            ai_analysis = result.get('ai_analysis', {}) or {}
            if not isinstance(ai_analysis, dict):
                ai_analysis = {}

            def safe_float(value):
                """Convert value to Python float, handling NumPy types"""
                if value is None:
                    return 0.0
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return 0.0

            formatted_data = {
                **extracted_data,
                'fraud_risk_score': safe_float(ml_analysis.get('fraud_risk_score', 0.0)),
                'model_confidence': safe_float(ml_analysis.get('model_confidence', 0.0)),
                'risk_level': str(ml_analysis.get('risk_level', 'UNKNOWN')),
                'ai_recommendation': str(ai_analysis.get('recommendation', 'UNKNOWN')),
                'ai_confidence': safe_float(ai_analysis.get('confidence', 0.0)),
                'ml_analysis': ml_analysis if ml_analysis else {},
                'ai_analysis': ai_analysis if ai_analysis else {},
                'anomalies': result.get('anomalies', []),
                'confidence_score': safe_float(result.get('confidence_score', 0.0)),
                'raw_text': result.get('raw_text', ''),
                'timestamp': result.get('timestamp'),
            }

            response_data = {
                'success': True,
                'data': formatted_data,
                'message': 'Paystub analyzed successfully'
            }

            logger.info(
                "Paystub response formatted - fraud_risk_score: %s, risk_level: %s",
                formatted_data.get('fraud_risk_score'),
                formatted_data.get('risk_level')
            )

            return jsonify(response_data)
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        logger.error(f"Paystub analysis endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to analyze paystub: {str(e)}'
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

            # Use Mindee-based money order extractor
            try:
                from money_order.extractor import extract_money_order
                logger.info(f"Starting money order extraction for file: {filepath}")
                result = extract_money_order(filepath)
                logger.info(f"Money order extraction completed. Result type: {type(result)}, Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

                # Validate result structure
                if not result or not isinstance(result, dict):
                    error_msg = f"Extractor returned invalid result: result is not a dictionary (type: {type(result)})"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                if 'extracted_data' not in result and 'raw_text' not in result:
                    error_msg = f"Extractor returned invalid result: missing required fields. Available keys: {list(result.keys())}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                logger.info("Money order extraction validation passed")

            except ImportError as e:
                logger.error(f"Failed to import money order extractor: {e}", exc_info=True)
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': 'Money order extractor not available',
                    'message': 'Failed to load money order extraction module'
                }), 500
            except Exception as e:
                logger.error(f"Money order extraction failed: {e}", exc_info=True)
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': f'Failed to extract money order data: {str(e)}'
                }), 500

            # Get raw text for document type validation
            extracted_data = result.get('extracted_data', {}) if result else {}
            if not isinstance(extracted_data, dict):
                extracted_data = {}
            raw_text = extracted_data.get('raw_ocr_text') or result.get('raw_text') or '' if result else ''

            # Validate document type if we have raw text
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

            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

            # Format response for frontend - flatten ML and AI analysis to top level
            # Extract key fields for simplified frontend display
            extracted_data = result.get('extracted_data', {})
            if not isinstance(extracted_data, dict):
                extracted_data = {}
            
            ml_analysis = result.get('ml_analysis', {}) or {}
            if not isinstance(ml_analysis, dict):
                ml_analysis = {}
            
            ai_analysis = result.get('ai_analysis', {}) or {}
            if not isinstance(ai_analysis, dict):
                ai_analysis = {}
            
            # Get ML values with defaults (safely handle any type)
            fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0) if isinstance(ml_analysis, dict) else 0.0
            model_confidence = ml_analysis.get('model_confidence', 0.0) if isinstance(ml_analysis, dict) else 0.0
            risk_level = ml_analysis.get('risk_level', 'UNKNOWN') if isinstance(ml_analysis, dict) else 'UNKNOWN'
            
            # Get AI values with defaults (safely handle any type)
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN') if isinstance(ai_analysis, dict) else 'UNKNOWN'
            ai_confidence = ai_analysis.get('confidence', 0.0) if isinstance(ai_analysis, dict) else 0.0
            
            # Helper function to safely convert NumPy types to Python types
            def safe_float(value):
                """Convert value to Python float, handling NumPy types"""
                if value is None:
                    return 0.0
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return 0.0
            
            # Flatten response with top-level fields for frontend compatibility
            formatted_data = {
                **(extracted_data if isinstance(extracted_data, dict) else {}),
                # Always include ML analysis fields at top level (convert NumPy types)
                'fraud_risk_score': safe_float(fraud_risk_score),
                'model_confidence': safe_float(model_confidence),
                'risk_level': str(risk_level) if risk_level else 'UNKNOWN',
                # Always include AI analysis fields at top level
                'ai_recommendation': str(ai_recommendation) if ai_recommendation else 'UNKNOWN',
                'ai_confidence': safe_float(ai_confidence),
                # Keep nested structures for detailed analysis (already serialized)
                'ml_analysis': ml_analysis if ml_analysis else {},
                'ai_analysis': ai_analysis if ai_analysis else {},
                'normalized_data': result.get('normalized_data'),
                'anomalies': result.get('anomalies', []),
                'confidence_score': safe_float(result.get('confidence_score', 0.0)),
                'raw_text': result.get('raw_text', ''),
                'timestamp': result.get('timestamp'),
            }
            
            response_data = {
                'success': True,
                'data': formatted_data,
                'message': 'Money order analyzed successfully'
            }

            logger.info(f"Response formatted - fraud_risk_score: {formatted_data.get('fraud_risk_score')}, risk_level: {formatted_data.get('risk_level')}, model_confidence: {formatted_data.get('model_confidence')}")
            logger.info(f"Response data keys: {list(formatted_data.keys())}")
            return jsonify(response_data)

        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    except Exception as e:
        logger.error(f"Money order analysis endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to analyze money order: {str(e)}'
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

            raw_text = ""
            mindee_data = {}

            if BANK_STATEMENT_MINDEE_AVAILABLE:
                try:
                    mindee_result = mindee_extract_bank_statement(filepath)
                    mindee_data = mindee_result.get('extracted_data', {}) or {}
                    raw_text = mindee_data.get('raw_ocr_text') or mindee_result.get('raw_text') or ''
                    logger.info("Bank statement extracted via Mindee")
                except Exception as e:
                    logger.error(f"Mindee bank statement extraction failed: {e}", exc_info=True)
                    mindee_data = {}

            if not raw_text and vision_client:
                with open(filepath, 'rb') as image_file:
                    content = image_file.read()
                image = vision.Image(content=content)
                response = vision_client.text_detection(image=image)
                raw_text = response.text_annotations[0].description if response.text_annotations else ""
            elif not raw_text:
                raw_text = ""

            detected_type = detect_document_type(raw_text)
            if detected_type not in ['bank_statement', 'unknown']:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'success': False,
                    'error': f'Wrong document type detected. This appears to be a {detected_type}, not a bank statement. Please upload a bank statement document.',
                    'message': 'Document type mismatch'
                }), 400

            if os.path.exists(filepath):
                os.remove(filepath)

            fallback_data = _parse_bank_statement_text(raw_text)

            initial_data = {
                'bank_name': mindee_data.get('bank_name'),
                'account_holder': mindee_data.get('account_holder'),
                'account_number': mindee_data.get('account_number'),
                'statement_period': _format_statement_period(
                    mindee_data.get('statement_period_start'),
                    mindee_data.get('statement_period_end')
                ),
                'balances': {
                    'opening_balance': _format_currency(_safe_parse_currency(mindee_data.get('opening_balance'))),
                    'ending_balance': _format_currency(_safe_parse_currency(mindee_data.get('closing_balance'))),
                    'available_balance': None,
                    'current_balance': None
                },
                'summary': None,
                'transactions': _normalize_mindee_transactions(mindee_data.get('transactions')),
                'raw_text': raw_text
            }

            structured_data = _merge_bank_statement_data(initial_data, fallback_data)
            risk_analysis = _evaluate_bank_statement_risk(structured_data)
            ai_analysis = _build_bank_statement_ai_analysis(risk_analysis)
            anomalies = _collect_bank_statement_anomalies(risk_analysis, ai_analysis)
            confidence_score = structured_data.get('summary', {}).get('confidence', 0.0)

            formatted_data = {
                **structured_data,
                'fraud_risk_score': risk_analysis.get('fraud_risk_score', 0.0),
                'model_confidence': risk_analysis.get('model_confidence', 0.0),
                'risk_level': risk_analysis.get('risk_level', 'UNKNOWN'),
                'ai_recommendation': ai_analysis.get('recommendation', 'UNKNOWN'),
                'ai_confidence': ai_analysis.get('confidence', 0.0),
                'ml_analysis': risk_analysis,
                'ai_analysis': ai_analysis,
                'anomalies': anomalies,
                'confidence_score': confidence_score,
                'timestamp': datetime.now().isoformat()
            }

            return jsonify({
                'success': True,
                'data': formatted_data,
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

    # Run without debug mode to avoid constant reloads from ML library imports
    app.run(debug=False, host='0.0.0.0', port=5001)
