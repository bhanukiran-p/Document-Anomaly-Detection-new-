"""
Flask Web Application for Check Extraction
User-friendly UI layered on top of the Mindee-powered extractor.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from datetime import datetime

try:
    from mindee_extractor import extract_check
    EXTRACTOR_AVAILABLE = True
    EXTRACTOR_ERROR = None
except Exception as exc:
    EXTRACTOR_AVAILABLE = False
    EXTRACTOR_ERROR = str(exc)
    extract_check = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'check-extractor-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
            'error': f'Mindee extractor not available: {EXTRACTOR_ERROR or "missing API key"}'
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
        
        # Extract check details via Mindee
        result = extract_check(filepath)
        details = result.get('extracted_data', {})
        
        return jsonify({
            'success': True,
            'filename': filename,
            'details': details,
            'raw_fields': result.get('raw_fields', {}),
            'raw_text': result.get('raw_text')
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
        print("[OK] Mindee client initialized successfully")
    else:
        print("[WARNING] Mindee extractor not available")
        if EXTRACTOR_ERROR:
            print(f"         Reason: {EXTRACTOR_ERROR}")
    
    print("\n[INFO] Starting web server...")
    print("[INFO] Open your browser and navigate to:")
    print("       http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

