"""
Flask API Server for XFORIA DAD
Handles Check, Paystub, Money Order, and Bank Statement Analysis
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import logging
import importlib.util
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Import utilities
from utils.file_handler import save_uploaded_file, handle_pdf_conversion, cleanup_file
from utils.document_detector import validate_document_type
from utils.response_formatter import format_analysis_response, format_bank_statement_response
from bank_statement.parser import (
    safe_parse_currency, format_currency, format_statement_period,
    parse_bank_statement_text, merge_bank_statement_data, normalize_mindee_transactions
)
from bank_statement.risk_analyzer import evaluate_risk, build_ai_analysis, collect_anomalies

# Import real-time transaction analysis
from real_time import process_transaction_csv, detect_fraud_in_transactions, generate_insights

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
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'google-credentials.json')

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

def get_agent_service():
    """
    Return an agent service instance. Tries to import a real implementation if available;
    otherwise returns a lightweight fallback that provides the expected interface.
    The agent service must implement generate_comprehensive_analysis(full_analysis_result)
    and return a dict with at least a 'success' boolean.
    """
    try:
        # Import the actual agent service from real_time module
        from real_time.agent_endpoint import AgentAnalysisService
        logger.info("Successfully loaded AgentAnalysisService")
        return AgentAnalysisService()
    except Exception as e:
        logger.warning(f"Failed to load AgentAnalysisService: {e}")
        # Fallback agent service that returns a non-failing response indicating
        # the agent is not configured. This prevents NameError and keeps endpoints working.
        class FallbackAgentService:
            def generate_comprehensive_analysis(self, full_analysis_result):
                # Minimal, safe response the caller expects
                return {
                    'success': False,
                    'error': f'Agent service not configured: {str(e)}'
                }
        return FallbackAgentService()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    supabase_status = check_supabase_connection() if supabase else {
        'status': 'disconnected',
        'message': 'Supabase not initialized'
    }

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
    filepath = None
    try:
        # Save uploaded file
        file = request.files.get('file')
        filepath = save_uploaded_file(file)

        # Handle PDF conversion if needed
        filepath = handle_pdf_conversion(filepath)

        # Extract check data
        try:
            from check.extractor import extract_check
            logger.info(f"Starting check extraction for file: {filepath}")
            result = extract_check(filepath)
            logger.info(f"Check extraction completed")

            # Validate result structure
            if not result or not isinstance(result, dict):
                raise ValueError("Extractor returned invalid result")
            if 'extracted_data' not in result and 'raw_text' not in result:
                raise ValueError("Extractor returned invalid result: missing required fields")

        except ImportError as e:
            logger.error(f"Failed to import check extractor: {e}", exc_info=True)
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': 'Check extractor not available',
                'message': 'Failed to load check extraction module'
            }), 500
        except Exception as e:
            logger.error(f"Check extraction failed: {e}", exc_info=True)
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': str(e),
                'message': f'Failed to extract check data: {str(e)}'
            }), 500

        # Validate document type
        extracted_data = result.get('extracted_data', {}) or {}
        raw_text = extracted_data.get('raw_ocr_text') or result.get('raw_text') or ''

        is_valid, error_message = validate_document_type(raw_text, 'check')
        if not is_valid:
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': error_message,
                'message': 'Document type mismatch'
            }), 400

        # Clean up temp file
        cleanup_file(filepath)

        # Format and return response
        return jsonify(format_analysis_response(result, 'check'))

    except ValueError as e:
        cleanup_file(filepath)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        cleanup_file(filepath)
        logger.error(f"Check analysis endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to analyze check: {str(e)}'
        }), 500


@app.route('/api/paystub/analyze', methods=['POST'])
def analyze_paystub():
    """Analyze paystub document endpoint"""
    filepath = None
    try:
        # Save uploaded file
        file = request.files.get('file')
        filepath = save_uploaded_file(file)

        # Handle PDF conversion if needed
        filepath = handle_pdf_conversion(filepath)

        # Extract paystub data
        try:
            from paystub.extractor import extract_paystub
            result = extract_paystub(filepath)
            logger.info("Paystub extracted successfully")

            # Validate result structure
            if not result or not isinstance(result, dict):
                raise ValueError("Extractor returned invalid result")
            if 'extracted_data' not in result and 'raw_text' not in result:
                raise ValueError("Extractor returned invalid result: missing required fields")

        except ImportError as e:
            logger.error(f"Failed to import paystub extractor: {e}")
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': 'Paystub extractor not available',
                'message': 'Failed to load paystub extraction module'
            }), 500
        except Exception as e:
            logger.error(f"Paystub extraction failed: {e}", exc_info=True)
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': str(e),
                'message': f'Failed to extract paystub data: {str(e)}'
            }), 500

        # Validate document type
        extracted_data = result.get('extracted_data', {}) or {}
        raw_text = extracted_data.get('raw_ocr_text') or result.get('raw_text') or ''

        is_valid, error_message = validate_document_type(raw_text, 'paystub')
        if not is_valid:
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': error_message,
                'message': 'Document type mismatch'
            }), 400

        # Clean up temp file
        cleanup_file(filepath)

        # Format and return response
        return jsonify(format_analysis_response(result, 'paystub'))

    except ValueError as e:
        cleanup_file(filepath)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        cleanup_file(filepath)
        logger.error(f"Paystub analysis endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to analyze paystub: {str(e)}'
        }), 500


@app.route('/api/money-order/analyze', methods=['POST'])
def analyze_money_order():
    """Analyze money order document endpoint"""
    filepath = None
    try:
        # Save uploaded file
        file = request.files.get('file')
        filepath = save_uploaded_file(file)

        # Handle PDF conversion if needed
        filepath = handle_pdf_conversion(filepath)

        # Extract money order data
        try:
            from money_order.extractor import extract_money_order
            logger.info(f"Starting money order extraction for file: {filepath}")
            result = extract_money_order(filepath)
            logger.info("Money order extraction completed")

            # Validate result structure
            if not result or not isinstance(result, dict):
                raise ValueError("Extractor returned invalid result")
            if 'extracted_data' not in result and 'raw_text' not in result:
                raise ValueError("Extractor returned invalid result: missing required fields")

        except ImportError as e:
            logger.error(f"Failed to import money order extractor: {e}", exc_info=True)
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': 'Money order extractor not available',
                'message': 'Failed to load money order extraction module'
            }), 500
        except Exception as e:
            logger.error(f"Money order extraction failed: {e}", exc_info=True)
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': str(e),
                'message': f'Failed to extract money order data: {str(e)}'
            }), 500

        # Validate document type
        extracted_data = result.get('extracted_data', {}) or {}
        raw_text = extracted_data.get('raw_ocr_text') or result.get('raw_text') or ''

        is_valid, error_message = validate_document_type(raw_text, 'money_order')
        if not is_valid:
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': error_message,
                'message': 'Document type mismatch'
            }), 400

        # Clean up temp file
        cleanup_file(filepath)

        # Format and return response
        return jsonify(format_analysis_response(result, 'money order'))

    except ValueError as e:
        cleanup_file(filepath)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        cleanup_file(filepath)
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
    filepath = None
    try:
        # Save uploaded file
        file = request.files.get('file')
        filepath = save_uploaded_file(file)

        # Handle PDF conversion if needed
        filepath = handle_pdf_conversion(filepath)

        # Extract text using Mindee or Vision API
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

        # Validate document type
        is_valid, error_message = validate_document_type(raw_text, 'bank_statement')
        if not is_valid:
            cleanup_file(filepath)
            return jsonify({
                'success': False,
                'error': error_message,
                'message': 'Document type mismatch'
            }), 400

        # Clean up temp file
        cleanup_file(filepath)

        # Parse bank statement text
        fallback_data = parse_bank_statement_text(raw_text)

        # Prepare initial data from Mindee
        initial_data = {
            'bank_name': mindee_data.get('bank_name'),
            'account_holder': mindee_data.get('account_holder'),
            'account_number': mindee_data.get('account_number'),
            'statement_period': format_statement_period(
                mindee_data.get('statement_period_start'),
                mindee_data.get('statement_period_end')
            ),
            'balances': {
                'opening_balance': format_currency(safe_parse_currency(mindee_data.get('opening_balance'))),
                'ending_balance': format_currency(safe_parse_currency(mindee_data.get('closing_balance'))),
                'available_balance': None,
                'current_balance': None
            },
            'summary': None,
            'transactions': normalize_mindee_transactions(mindee_data.get('transactions')),
            'raw_text': raw_text
        }

        # Merge data
        structured_data = merge_bank_statement_data(initial_data, fallback_data)

        # Analyze risk
        risk_analysis = evaluate_risk(structured_data)
        ai_analysis = build_ai_analysis(risk_analysis)
        anomalies = collect_anomalies(risk_analysis, ai_analysis)
        confidence_score = structured_data.get('summary', {}).get('confidence', 0.0)

        # Add timestamp
        structured_data['timestamp'] = datetime.now().isoformat()

        # Format and return response
        return jsonify(format_bank_statement_response(
            structured_data,
            risk_analysis,
            ai_analysis,
            anomalies,
            confidence_score
        ))

    except ValueError as e:
        cleanup_file(filepath)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        cleanup_file(filepath)
        logger.error(f"Bank statement analysis error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze bank statement'
        }), 500


@app.route('/api/real-time/analyze', methods=['POST'])
def analyze_real_time_transactions():
    """
    Analyze real-time transaction CSV file.
    Uses ML-based fraud detection with automatic model training.
    """
    try:
        logger.info("Received real-time transaction analysis request")






        # Check for CSV file
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if not file or file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate CSV file
        if not file.filename.lower().endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'Only CSV files are supported'
            }), 400

        # Save file
        filepath = save_uploaded_file(file, 'csv')
        logger.info(f"CSV file saved: {filepath}")

        try:
            # Step 1: Process CSV file
            logger.info("Step 1: Processing CSV file")
            csv_result = process_transaction_csv(filepath)

            if not csv_result.get('success'):
                cleanup_file(filepath)
                return jsonify(csv_result), 400

            transactions = csv_result['transactions']
            logger.info(f"Processed {len(transactions)} transactions")

            # Step 2: Detect fraud using ML
            logger.info("Step 2: Running ML fraud detection")
            fraud_result = detect_fraud_in_transactions(transactions, auto_train=True)

            if not fraud_result.get('success'):
                cleanup_file(filepath)
                return jsonify(fraud_result), 500

            logger.info(f"Fraud detection complete: {fraud_result['fraud_count']} fraudulent transactions")

            # Step 3: Generate insights
            logger.info("Step 3: Generating insights and plots")
            insights_result = generate_insights(fraud_result)

            if not insights_result.get('success'):
                logger.warning(f"Insight generation failed: {insights_result.get('error')}")
                insights_result = {
                    'success': True,
                    'statistics': {},
                    'plots': [],
                    'fraud_patterns': {},
                    'recommendations': []
                }

            # Step 4: Generate LLM agent analysis
            logger.info("Step 4: Generating LLM agent analysis")
            agent_analysis = None
            try:
                # Combine all data for agent analysis
                full_analysis_result = {
                    'csv_info': {
                        'total_count': csv_result['total_count'],
                        'date_range': csv_result['date_range'],
                        'summary': csv_result['summary'],
                        'columns': csv_result.get('columns', [])
                    },
                    'fraud_detection': {
                        'fraud_count': fraud_result['fraud_count'],
                        'legitimate_count': fraud_result['legitimate_count'],
                        'fraud_percentage': fraud_result['fraud_percentage'],
                        'legitimate_percentage': fraud_result['legitimate_percentage'],
                        'total_fraud_amount': fraud_result['total_fraud_amount'],
                        'total_legitimate_amount': fraud_result['total_legitimate_amount'],
                        'total_amount': fraud_result['total_amount'],
                        'average_fraud_probability': fraud_result['average_fraud_probability'],
                        'model_type': fraud_result['model_type']
                    },
                    'transactions': fraud_result['transactions'],
                    'insights': insights_result
                }

                # Get agent service and generate analysis
                agent_service = get_agent_service()
                agent_result = agent_service.generate_comprehensive_analysis(full_analysis_result)

                if agent_result.get('success'):
                    agent_analysis = agent_result.get('agent_analysis')
                    logger.info("LLM agent analysis generated successfully")
                else:
                    logger.warning(f"Agent analysis failed: {agent_result.get('error')}")
            except Exception as agent_error:
                logger.warning(f"Could not generate agent analysis: {agent_error}")

            # Cleanup file
            cleanup_file(filepath)

            # Combine results
            response = {
                'success': True,
                'csv_info': {
                    'total_count': csv_result['total_count'],
                    'date_range': csv_result['date_range'],
                    'summary': csv_result['summary']
                },
                'fraud_detection': {
                    'fraud_count': fraud_result['fraud_count'],
                    'legitimate_count': fraud_result['legitimate_count'],
                    'fraud_percentage': fraud_result['fraud_percentage'],
                    'legitimate_percentage': fraud_result['legitimate_percentage'],
                    'total_fraud_amount': fraud_result['total_fraud_amount'],
                    'total_legitimate_amount': fraud_result['total_legitimate_amount'],
                    'total_amount': fraud_result['total_amount'],
                    'average_fraud_probability': fraud_result['average_fraud_probability'],
                    'model_type': fraud_result['model_type'],
                    'fraud_type_breakdown': fraud_result.get('fraud_type_breakdown', []),
                    'dominant_fraud_type': fraud_result.get('dominant_fraud_type')
                },
                'transactions': fraud_result['transactions'],
                'insights': insights_result,
                'agent_analysis': agent_analysis,  # Include LLM agent analysis
                'analyzed_at': datetime.now().isoformat()
            }

            logger.info("Real-time transaction analysis complete")
            return jsonify(response)

        except Exception as e:
            cleanup_file(filepath)
            raise e

    except Exception as e:
        logger.error(f"Real-time analysis error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze transactions'
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
        
        # Create a mock analysis result structure
        fraud_result = {
            'success': True,
            'transactions': transactions,
            'fraud_count': sum(1 for t in transactions if t.get('is_fraud') == 1),
            'legitimate_count': sum(1 for t in transactions if t.get('is_fraud') == 0),
            'fraud_percentage': 0,
            'legitimate_percentage': 0,
            'total_fraud_amount': sum(t.get('amount', 0) for t in transactions if t.get('is_fraud') == 1),
            'total_legitimate_amount': sum(t.get('amount', 0) for t in transactions if t.get('is_fraud') == 0),
            'total_amount': sum(t.get('amount', 0) for t in transactions),
            'average_fraud_probability': sum(t.get('fraud_probability', 0) for t in transactions) / len(transactions) if transactions else 0,
            'model_type': 'filtered'
        }
        
        if len(transactions) > 0:
            fraud_result['fraud_percentage'] = (fraud_result['fraud_count'] / len(transactions)) * 100
            fraud_result['legitimate_percentage'] = (fraud_result['legitimate_count'] / len(transactions)) * 100
        
        # Generate insights with filters
        from real_time.insights_generator import generate_insights
        logger.info(f"Regenerating plots with {len(transactions)} transactions and filters: {filters}")
        insights_result = generate_insights(fraud_result, filters=filters)
        
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
    print(f"  - POST /api/bank-statement/analyze")
    print("=" * 60)

    # Run without debug mode to avoid constant reloads from ML library imports
    app.run(debug=False, host='0.0.0.0', port=5001)
