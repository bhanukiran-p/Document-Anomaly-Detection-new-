"""
Money Order Analysis Routes
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import fitz
from config import Config
from database.document_storage import store_money_order_analysis
from google.cloud import vision

logger = Config.get_logger(__name__)
money_order_bp = Blueprint('money_order', __name__)

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
    if 'money order' in text_lower or 'western union' in text_lower or 'moneygram' in text_lower:
        return 'money_order'
    if ('statement period' in text_lower or 'account summary' in text_lower or
        'beginning balance' in text_lower or 'transaction detail' in text_lower):
        return 'bank_statement'
    if ('gross pay' in text_lower or 'net pay' in text_lower or
        ('ytd' in text_lower and 'earnings' in text_lower)):
        return 'paystub'
    if 'routing number' in text_lower or 'micr' in text_lower or 'check number' in text_lower:
        return 'check'
    return 'unknown'


@money_order_bp.route('/analyze', methods=['POST'])
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

            # Extract fraud types and explanations for API response (similar to paystub/bank statement)
            ml_analysis = result.get('ml_analysis', {})
            ai_analysis = result.get('ai_analysis', {})

            # Get AI recommendation first
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN') if ai_analysis else 'UNKNOWN'
            ai_recommendation = ai_recommendation.upper()

            # Only show fraud types if recommendation is REJECT or ESCALATE
            # For APPROVE, keep fraud_type as None (no fraud detected)
            fraud_type = None
            fraud_type_label = None
            fraud_explanations = []

            if ai_recommendation in ['REJECT', 'ESCALATE']:
                # Extract fraud types from AI analysis
                ai_fraud_types = ai_analysis.get('fraud_types', []) if ai_analysis else []

                # Extract the primary fraud type (first in list)
                if ai_fraud_types:
                    fraud_type = ai_fraud_types[0] if isinstance(ai_fraud_types, list) else ai_fraud_types
                    # Format fraud type for display (remove underscores and title case)
                    fraud_type_label = fraud_type.replace('_', ' ').title() if fraud_type else None

                # Get fraud explanations from AI analysis
                fraud_explanations = ai_analysis.get('fraud_explanations', []) if ai_analysis else []
            # For APPROVE, fraud_type remains None (no fraud detected)

            return jsonify({
                'success': True,
                'fraud_risk_score': ml_analysis.get('fraud_risk_score', 0.0),
                'risk_level': ml_analysis.get('risk_level', 'UNKNOWN'),
                'model_confidence': ml_analysis.get('model_confidence', 0.0),
                'fraud_type': fraud_type,  # Single fraud type (machine format)
                'fraud_type_label': fraud_type_label,  # Human-readable format (e.g., "Signature Forgery")
                'fraud_explanations': fraud_explanations if isinstance(fraud_explanations, list) else [],
                'fraud_types': [fraud_type] if fraud_type else [],  # List format for compatibility
                'ai_recommendation': ai_analysis.get('recommendation', 'UNKNOWN'),
                'ai_confidence': ai_analysis.get('confidence_score', 0.0),
                'summary': ai_analysis.get('summary', ''),
                'key_indicators': ai_analysis.get('key_indicators', []),
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
