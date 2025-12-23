"""
Mock Bank Webhook
Simulates bank API endpoints that return account and transaction data
"""

from flask import request, jsonify, Blueprint
import logging
from datetime import datetime
from typing import Dict, Any, List

# Import Supabase client
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Create Blueprint for webhook routes
webhook_bp = Blueprint('mock_bank_webhook', __name__, url_prefix='/webhook/bank')


@webhook_bp.route('/accounts', methods=['GET'])
def get_mock_bank_accounts():
    """
    Mock bank API - Get ALL accounts (bank-wide analysis)
    Uses pagination to fetch ALL records - future-proof for any data size
    """
    try:
        logger.info("Fetching ALL bank accounts for comprehensive analysis")
        
        supabase = get_supabase()
        
        # Fetch ALL accounts using pagination
        all_accounts = []
        page_size = 1000
        offset = 0
        
        while True:
            result = supabase.table('synthetic_accounts')\
                .select('*')\
                .order('customer_id, account_id')\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            batch = result.data
            if not batch:
                break
            
            all_accounts.extend(batch)
            
            if len(batch) < page_size:
                break
            
            offset += page_size
        
        if not all_accounts:
            logger.warning("No accounts found in database")
            return jsonify({
                'success': False,
                'error': 'No accounts found'
            }), 404
        
        logger.info(f"Found {len(all_accounts)} total accounts across all customers")
        
        return jsonify({
            'success': True,
            'accounts': all_accounts,
            'count': len(all_accounts)
        })
        
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@webhook_bp.route('/transactions', methods=['GET'])
def get_mock_bank_transactions():
    """
    Mock bank API - Get ALL transactions (bank-wide comprehensive analysis)
    Uses pagination to fetch ALL records - future-proof for any data size
    
    Response: {
        "success": True,
        "transactions": [...ALL transactions...],
        "count": <total>
    }
    """
    try:
        logger.info("Fetching ALL transactions for comprehensive bank-wide fraud analysis")
        
        supabase = get_supabase()
        
        # Fetch ALL transactions using pagination to bypass limits
        all_transactions = []
        page_size = 1000
        offset = 0
        
        while True:
            result = supabase.table('synthetic_transactions')\
                .select('*')\
                .order('timestamp', desc=True)\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            batch = result.data
            if not batch:
                break
            
            all_transactions.extend(batch)
            
            # If we got less than page_size, we're done
            if len(batch) < page_size:
                break
            
            offset += page_size
        
        logger.info(f"Found {len(all_transactions)} total transactions across all accounts")
        
        # Return clean transaction data (NO fraud labels - like real banks!)
        return jsonify({
            'success': True,
            'transactions': all_transactions,
            'count': len(all_transactions)
        })
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@webhook_bp.route('/customers', methods=['GET'])
def list_customers():
    """
    List ALL available customers (uses pagination for future-proofing)
    """
    try:
        supabase = get_supabase()
        
        # Fetch ALL customers using pagination
        all_customers = []
        page_size = 1000
        offset = 0
        
        while True:
            result = supabase.table('synthetic_customers')\
                .select('customer_id, first_name, last_name, email, home_city, home_country')\
                .order('customer_id')\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            batch = result.data
            if not batch:
                break
            
            all_customers.extend(batch)
            
            if len(batch) < page_size:
                break
            
            offset += page_size
        
        logger.info(f"Found {len(all_customers)} customers")
        
        return jsonify({
            'success': True,
            'customers': all_customers,
            'count': len(all_customers)
        })
        
    except Exception as e:
        logger.error(f"Error listing customers: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Export blueprint
__all__ = ['webhook_bp']
