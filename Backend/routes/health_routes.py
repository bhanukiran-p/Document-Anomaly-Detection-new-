"""
Health Check Routes
"""

from flask import Blueprint, jsonify
from database.supabase_client import get_supabase, check_connection as check_supabase_connection

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    supabase = get_supabase()
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
