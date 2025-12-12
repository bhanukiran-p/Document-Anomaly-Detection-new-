"""
Paystub Analysis Routes
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from config import Config
from database.document_storage import store_paystub_analysis

logger = Config.get_logger(__name__)
paystub_bp = Blueprint('paystub', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@paystub_bp.route('/analyze', methods=['POST'])
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
            # For ESCALATE or APPROVE, keep fraud_type as None (no fraud detected)
            fraud_type = None
            fraud_type_label = None
            fraud_explanations = []

            if ai_recommendation == 'REJECT':
                # Only show fraud types for REJECT recommendations (actual fraud detected)
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
            # For ESCALATE or APPROVE, fraud_type remains None (no fraud detected)

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
                    'details': 'The ML fraud detection model is not available. Please train the model using: python training/train_paystub_models.py'
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
