"""
Flask API Server for XFORIA DAD
Handles Check and Paystub Analysis
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from werkzeug.utils import secure_filename
import importlib.util

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
CREDENTIALS_PATH = 'check-ocr-project-469619-d18e1cdc414d.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'XFORIA DAD API',
        'version': '1.0.0'
    })

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
                import fitz
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
            
            # Initialize extractor and analyze
            extractor = ProductionCheckExtractor(CREDENTIALS_PATH)
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
            
            # Extract text and analyze
            extractor = PaystubExtractor(CREDENTIALS_PATH)
            text = extractor.extract_text(file_bytes, file_type)
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

if __name__ == '__main__':
    print("=" * 60)
    print("XFORIA DAD API Server")
    print("=" * 60)
    print(f"Server running on: http://localhost:5000")
    print(f"API Endpoints:")
    print(f"  - GET  /api/health")
    print(f"  - POST /api/check/analyze")
    print(f"  - POST /api/paystub/analyze")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

