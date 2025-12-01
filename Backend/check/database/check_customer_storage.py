"""
Check Customer Storage
Handles check customer tracking, fraud history, and duplicate detection
"""

"""
Check Customer Storage
Handles check customer tracking, fraud history, and duplicate detection
Completely independent from money order customer tracking
"""

import logging
import uuid
from typing import Dict, Optional
from datetime import datetime
import sys
import os

# Add parent directories to path to access database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class CheckCustomerStorage:
    """
    Manage check customer records and fraud tracking
    Similar to money order customer tracking but for checks
    """

    def __init__(self):
        """Initialize Supabase client"""
        self.supabase = get_supabase()

    def get_or_create_customer(self, payer_name: str, payee_name: Optional[str] = None,
                               address: Optional[str] = None) -> Optional[str]:
        """
        Get existing customer or create new one

        Args:
            payer_name: Payer/customer name
            payee_name: Payee name (optional)
            address: Payer address (optional)

        Returns:
            customer_id (UUID) or None
        """
        if not payer_name:
            return None

        try:
            # Search for existing customer by name
            result = self.supabase.table('check_customers').select('*').eq('name', payer_name).execute()

            if result.data and len(result.data) > 0:
                # Customer exists
                customer = result.data[0]
                customer_id = customer['customer_id']
                logger.info(f"Found existing check customer: {customer_id}")
                return customer_id
            else:
                # Create new customer
                customer_data = {
                    'customer_id': str(uuid.uuid4()),
                    'name': payer_name,
                    'payee_name': payee_name,
                    'address': address,
                    'has_fraud_history': False,
                    'fraud_count': 0,
                    'escalate_count': 0,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }

                self.supabase.table('check_customers').insert([customer_data]).execute()
                logger.info(f"Created new check customer: {customer_data['customer_id']}")
                return customer_data['customer_id']

        except Exception as e:
            logger.error(f"Error in get_or_create_customer: {e}", exc_info=True)
            return None

    def get_customer_history(self, payer_name: str) -> Dict:
        """
        Get customer fraud history

        Args:
            payer_name: Payer name

        Returns:
            Customer history dict
        """
        if not payer_name:
            return {}

        try:
            result = self.supabase.table('check_customers').select('*').eq('name', payer_name).execute()

            if result.data and len(result.data) > 0:
                customer = result.data[0]
                return {
                    'customer_id': customer['customer_id'],
                    'has_fraud_history': customer.get('has_fraud_history', False),
                    'fraud_count': customer.get('fraud_count', 0),
                    'escalate_count': customer.get('escalate_count', 0),
                    'last_recommendation': customer.get('last_recommendation'),
                    'last_analysis_date': customer.get('last_analysis_date')
                }
            else:
                return {}

        except Exception as e:
            logger.error(f"Error getting customer history: {e}")
            return {}

    def update_customer_fraud_status(self, customer_id: str, recommendation: str):
        """
        Update customer fraud counters based on AI recommendation

        Args:
            customer_id: Customer UUID
            recommendation: AI recommendation (APPROVE, REJECT, ESCALATE)
        """
        if not customer_id or not recommendation:
            return

        try:
            # Get current customer data
            result = self.supabase.table('check_customers').select('*').eq('customer_id', customer_id).execute()

            if not result.data:
                logger.warning(f"Customer {customer_id} not found")
                return

            customer = result.data[0]
            fraud_count = customer.get('fraud_count', 0)
            escalate_count = customer.get('escalate_count', 0)

            # Update counters based on recommendation
            if recommendation == 'REJECT':
                fraud_count += 1
                has_fraud_history = True
            elif recommendation == 'ESCALATE':
                escalate_count += 1
                has_fraud_history = customer.get('has_fraud_history', False)
            else:  # APPROVE
                has_fraud_history = customer.get('has_fraud_history', False)

            # Update customer record
            update_data = {
                'fraud_count': fraud_count,
                'escalate_count': escalate_count,
                'has_fraud_history': has_fraud_history,
                'last_recommendation': recommendation,
                'last_analysis_date': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            self.supabase.table('check_customers').update(update_data).eq('customer_id', customer_id).execute()

            logger.info(f"Updated customer {customer_id}: fraud_count={fraud_count}, escalate_count={escalate_count}")

        except Exception as e:
            logger.error(f"Error updating customer fraud status: {e}", exc_info=True)

    def check_duplicate_check(self, check_number: str, payer_name: str) -> bool:
        """
        Check if this check has been submitted before

        Args:
            check_number: Check number
            payer_name: Payer name

        Returns:
            True if duplicate found, False otherwise
        """
        if not check_number or not payer_name:
            return False

        try:
            result = self.supabase.table('checks').select('check_id')\
                .eq('check_number', check_number)\
                .eq('payer_name', payer_name)\
                .execute()

            is_duplicate = result.data and len(result.data) > 0

            if is_duplicate:
                logger.warning(f"Duplicate check detected: {check_number} from {payer_name}")

            return is_duplicate

        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False

    def link_check_to_customer(self, check_id: str, customer_id: str):
        """
        Link a check record to a customer

        Args:
            check_id: Check UUID
            customer_id: Customer UUID
        """
        if not check_id or not customer_id:
            return

        try:
            self.supabase.table('checks').update({
                'payer_customer_id': customer_id
            }).eq('check_id', check_id).execute()

            logger.info(f"Linked check {check_id} to customer {customer_id}")

        except Exception as e:
            logger.error(f"Error linking check to customer: {e}")


# Convenience functions
def get_check_customer_history(payer_name: str) -> Dict:
    """Get customer history by payer name"""
    storage = CheckCustomerStorage()
    return storage.get_customer_history(payer_name)


def update_check_customer_fraud_status(customer_id: str, recommendation: str):
    """Update customer fraud status"""
    storage = CheckCustomerStorage()
    storage.update_customer_fraud_status(customer_id, recommendation)


def check_for_duplicate_check(check_number: str, payer_name: str) -> bool:
    """Check for duplicate check"""
    storage = CheckCustomerStorage()
    return storage.check_duplicate_check(check_number, payer_name)
