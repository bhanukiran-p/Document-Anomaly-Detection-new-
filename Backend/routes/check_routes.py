"""
Check Analysis Routes
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from config import Config
from database.document_storage import store_check_analysis

logger = Config.get_logger(__name__)
check_bp = Blueprint('check', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@check_bp.route('/analyze', methods=['POST'])
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
