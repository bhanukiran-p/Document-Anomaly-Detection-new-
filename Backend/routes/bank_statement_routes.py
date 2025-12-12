"""
Bank Statement Analysis Routes
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import fitz
from config import Config
from database.document_storage import store_bank_statement_analysis
from google.cloud import vision

logger = Config.get_logger(__name__)
bank_statement_bp = Blueprint('bank_statement', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
CREDENTIALS_PATH = Config.GOOGLE_APPLICATION_CREDENTIALS or 'google-credentials.json'

# Initialize Vision API client once
try:
    vision_client = vision.ImageAnnotatorClient.from_service_account_file(CREDENTIALS_PATH)
    logger.info(f"Successfully loaded Google Cloud Vision credentials from {CREDENTIALS_PATH}")
except Exception as e:
    logger.warning(f"Failed to load Vision API credentials: {e}")
    vision_client = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_document_type(text):
    """Detect document type based on text content"""
    text_lower = text.lower()
    if ('statement period' in text_lower or 'account summary' in text_lower or
        'beginning balance' in text_lower or 'transaction detail' in text_lower):
        return 'bank_statement'
    if 'money order' in text_lower or 'western union' in text_lower or 'moneygram' in text_lower:
        return 'money_order'
    if ('gross pay' in text_lower or 'net pay' in text_lower or
        ('ytd' in text_lower and 'earnings' in text_lower)):
        return 'paystub'
    if 'routing number' in text_lower or 'micr' in text_lower or 'check number' in text_lower:
        return 'check'
    return 'unknown'


@bank_statement_bp.route('/analyze', methods=['POST'])
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

            # Extract fraud types for response (similar to paystub)
            ml_analysis = result.get('ml_analysis', {})
            ai_analysis = result.get('ai_analysis', {})
            customer_info = result.get('customer_info', {})

            # Get AI recommendation first
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN') if ai_analysis else 'UNKNOWN'
            ai_recommendation = ai_recommendation.upper()

            # Check if this is a new customer
            is_new_customer = not customer_info.get('customer_id')

            # Fraud types logic:
            # - For new customers: Never show fraud types (always empty)
            # - For repeat customers: Show fraud types if recommendation is REJECT or ESCALATE (but not APPROVE)
            fraud_type = None
            fraud_type_label = None
            fraud_explanations = []

            # Only extract fraud types for repeat customers (not new customers)
            # Only use what LLM returns - no fallback to ML
            if not is_new_customer and ai_recommendation in ['REJECT', 'ESCALATE']:
                # Show fraud types for repeat customers with REJECT or ESCALATE recommendations
                # Only use AI/LLM fraud_types - no fallback to ML
                ai_fraud_types = ai_analysis.get('fraud_types', []) if ai_analysis else []

                # Extract the primary fraud type (only from LLM response)
                if ai_fraud_types:
                    fraud_type = ai_fraud_types[0] if isinstance(ai_fraud_types, list) else ai_fraud_types
                    # Format fraud type for display (remove underscores and title case)
                    fraud_type_label = fraud_type.replace('_', ' ').title() if fraud_type else None
                else:
                    # LLM didn't provide fraud_types - leave as None (no fallback)
                    fraud_type = None
                    fraud_type_label = None

                # For fraud explanations, only use AI/LLM explanations - no fallback to ML
                fraud_explanations = ai_analysis.get('fraud_explanations', []) if ai_analysis else []
            # For new customers or APPROVE, fraud_type remains None (no fraud detected)

            # Build structured response
            response_data = {
                'success': True,
                'fraud_risk_score': ml_analysis.get('fraud_risk_score', 0.0),
                'risk_level': ml_analysis.get('risk_level', 'UNKNOWN'),
                'model_confidence': ml_analysis.get('model_confidence', 0.0),
                'fraud_type': fraud_type,  # Single fraud type (machine format)
                'fraud_type_label': fraud_type_label,  # Human-readable format
                'fraud_explanations': fraud_explanations if isinstance(fraud_explanations, list) else [],
                'fraud_types': [fraud_type] if fraud_type else [],  # List format for compatibility
                'ai_recommendation': ai_analysis.get('recommendation', 'UNKNOWN'),
                'ai_confidence': ai_analysis.get('confidence_score', 0.0),
                'summary': ai_analysis.get('summary', ''),
                'key_indicators': ai_analysis.get('key_indicators', []),
                'customer_info': result.get('customer_info', {}),  # Include customer history
                'ml_analysis': ml_analysis,  # Include full ML analysis for frontend access
                'ai_analysis': ai_analysis,  # Include full AI analysis for frontend access
                'document_id': document_id,
                'data': result,  # Include full result for backward compatibility
                'message': 'Bank statement analyzed and stored successfully'
            }

            return jsonify(response_data)

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
