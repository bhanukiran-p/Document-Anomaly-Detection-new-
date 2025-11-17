"""
Flask Web Application for Check Extraction
User-friendly web interface for the Google Vision API Check Extractor
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import importlib.util
from werkzeug.utils import secure_filename
from datetime import datetime

# Import the module with hyphen in filename
spec = importlib.util.spec_from_file_location("extractor_module", "production_google_vision-extractor.py")
extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor_module)
ProductionCheckExtractor = extractor_module.ProductionCheckExtractor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'check-extractor-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the extractor
CREDENTIALS_PATH = "google-credentials.json"
try:
    extractor = ProductionCheckExtractor(CREDENTIALS_PATH)
    EXTRACTOR_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not initialize extractor: {e}")
    EXTRACTOR_AVAILABLE = False


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', extractor_available=EXTRACTOR_AVAILABLE)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and extraction"""
    if not EXTRACTOR_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Google Vision API not available. Check credentials.'
        }), 500
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Check if file is allowed
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload PNG, JPG, or JPEG files.'
        }), 400
    
    try:
        # Save the file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract check details
        details = extractor.extract_check_details(filepath)
        
        # Return results
        return jsonify({
            'success': True,
            'filename': filename,
            'details': details
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing image: {str(e)}'
        }), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'extractor_available': EXTRACTOR_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Check Extraction Web Application")
    print("=" * 60)
    
    if EXTRACTOR_AVAILABLE:
        print("[OK] Google Vision API initialized successfully")
    else:
        print("[WARNING] Google Vision API not available")
        print("         Please check your credentials file")
    
    print("\n[INFO] Starting web server...")
    print("[INFO] Open your browser and navigate to:")
    print("       http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

