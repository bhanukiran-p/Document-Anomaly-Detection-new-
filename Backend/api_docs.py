"""
API Documentation Route - Serves interactive endpoint tester
"""
from flask import send_file, Blueprint
import os

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/api/docs/test')
def api_tester():
    """Serve the interactive API test page"""
    test_file = os.path.join(os.path.dirname(__file__), 'webhooks', 'test_endpoints.html')
    return send_file(test_file)
