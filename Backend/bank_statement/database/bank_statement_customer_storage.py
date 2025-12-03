"""
Bank Statement Customer Storage
Handles customer history tracking for bank statements
Completely independent from other document type customer storage
"""

import logging
from typing import Dict, Optional, List
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class BankStatementCustomerStorage:
    """
    Manages bank statement customer history in Supabase
    Tracks fraud counts, escalation counts, and customer information
    """

    def __init__(self):
        """Initialize with Supabase client"""
        try:
            self.supabase = get_supabase()
            logger.info("Initialized BankStatementCustomerStorage with Supabase connection")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None

    def get_or_create_customer(self, account_holder_name: str) -> Optional[str]:
        """
        Get existing customer or create new one with UUID

        Args:
            account_holder_name: Name of the account holder

        Returns:
            customer_id (UUID) or None if account_holder_name is empty
        """
        if not account_holder_name:
            return None

        try:
            # Search for existing customer by name
            response = self.supabase.table('bank_statement_customers').select('*').eq('name', account_holder_name).execute()

            if response.data and len(response.data) > 0:
                # Customer exists, return their ID
                customer = response.data[0]
                customer_id = customer.get('customer_id')
                logger.info(f"Found existing bank statement customer: {customer_id}")
                return customer_id
            else:
                # Create new customer with generated UUID
                from uuid import uuid4
                from datetime import datetime

                new_customer = {
                    'customer_id': str(uuid4()),
                    'name': account_holder_name,
                    'has_fraud_history': False,
                    'fraud_count': 0,
                    'escalate_count': 0,
                    'total_statements': 0,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }

                self.supabase.table('bank_statement_customers').insert([new_customer]).execute()
                logger.info(f"Created new bank statement customer: {new_customer['customer_id']}")
                return new_customer['customer_id']

        except Exception as e:
            logger.error(f"Error in get_or_create_customer: {e}", exc_info=True)
            return None

    def get_customer_history(self, account_holder_name: str) -> Dict:
        """
        Get customer history by account holder name

        Args:
            account_holder_name: Name of the account holder

        Returns:
            Customer history dict with fraud_count, escalate_count, etc.
        """
        if not self.supabase or not account_holder_name:
            return {}

        try:
            # Query bank_statement_customers table
            response = self.supabase.table('bank_statement_customers').select('*').eq('name', account_holder_name).execute()

            if response.data and len(response.data) > 0:
                customer = response.data[0]
                return {
                    'customer_id': customer.get('customer_id'),
                    'name': customer.get('name'),
                    'has_fraud_history': customer.get('has_fraud_history', False),
                    'fraud_count': customer.get('fraud_count', 0),
                    'escalate_count': customer.get('escalate_count', 0),
                    'last_recommendation': customer.get('last_recommendation'),
                    'last_analysis_date': customer.get('last_analysis_date'),
                    'total_statements': customer.get('total_statements', 0)
                }
            else:
                # New customer
                return {
                    'customer_id': None,
                    'name': account_holder_name,
                    'has_fraud_history': False,
                    'fraud_count': 0,
                    'escalate_count': 0,
                    'last_recommendation': None,
                    'last_analysis_date': None,
                    'total_statements': 0
                }
        except Exception as e:
            logger.error(f"Error getting customer history: {e}")
            return {}

    def check_duplicate_statement(self, account_number: str, statement_period_start: str, account_holder_name: str) -> bool:
        """
        Check if this bank statement has been submitted before

        Args:
            account_number: Account number
            statement_period_start: Statement period start date
            account_holder_name: Account holder name

        Returns:
            True if duplicate found, False otherwise
        """
        if not self.supabase:
            return False

        try:
            # Query bank_statements table for duplicate
            # Check by account_number + statement_period_start_date
            response = self.supabase.table('bank_statements').select('statement_id').eq('account_number', account_number).eq('statement_period_start_date', statement_period_start).execute()

            if response.data and len(response.data) > 0:
                # Found existing statement with same account and period
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False

    def update_customer_fraud_status(
        self,
        account_holder_name: str,
        recommendation: str,
        statement_id: Optional[str] = None
    ) -> bool:
        """
        Update customer fraud status based on recommendation

        Args:
            account_holder_name: Account holder name
            recommendation: AI recommendation (APPROVE, REJECT, ESCALATE)
            statement_id: Statement ID if available

        Returns:
            True if update successful, False otherwise
        """
        if not self.supabase or not account_holder_name:
            return False

        try:
            # Get existing customer or create new
            customer_history = self.get_customer_history(account_holder_name)
            customer_id = customer_history.get('customer_id')

            from datetime import datetime
            now = datetime.utcnow().isoformat()

            update_data = {
                'last_recommendation': recommendation,
                'last_analysis_date': now,
                'updated_at': now
            }

            # Update counts based on recommendation
            if recommendation == 'REJECT':
                update_data['fraud_count'] = customer_history.get('fraud_count', 0) + 1
                update_data['has_fraud_history'] = True
            elif recommendation == 'ESCALATE':
                update_data['escalate_count'] = customer_history.get('escalate_count', 0) + 1
            
            # Increment total statements
            update_data['total_statements'] = customer_history.get('total_statements', 0) + 1

            if customer_id:
                # Update existing customer
                self.supabase.table('bank_statement_customers').update(update_data).eq('customer_id', customer_id).execute()
                logger.info(f"Updated customer {account_holder_name} fraud status")
            else:
                # Create new customer
                from uuid import uuid4
                new_customer = {
                    'customer_id': str(uuid4()),
                    'name': account_holder_name,
                    'has_fraud_history': recommendation == 'REJECT',
                    'fraud_count': 1 if recommendation == 'REJECT' else 0,
                    'escalate_count': 1 if recommendation == 'ESCALATE' else 0,
                    'last_recommendation': recommendation,
                    'last_analysis_date': now,
                    'total_statements': 1,
                    'created_at': now,
                    'updated_at': now
                }
                self.supabase.table('bank_statement_customers').insert([new_customer]).execute()
                logger.info(f"Created new customer {account_holder_name}")

            return True
        except Exception as e:
            logger.error(f"Error updating customer fraud status: {e}")
            return False

