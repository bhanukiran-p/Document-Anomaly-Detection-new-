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
        Get existing customer_id or generate new UUID (does NOT create database record)
        The actual database record will be created by update_customer_fraud_status()
        
        This prevents duplicate records - only update_customer_fraud_status() creates records

        Args:
            account_holder_name: Name of the account holder

        Returns:
            customer_id (UUID) or None if account_holder_name is empty
        """
        if not account_holder_name:
            return None

        try:
            # Search for existing customer by name - get latest record (like paystubs do)
            response = self.supabase.table('bank_statement_customers').select('customer_id').eq('name', account_holder_name).order('created_at', desc=True).limit(1).execute()

            if response.data and len(response.data) > 0:
                # Customer exists, return their ID from latest record
                customer = response.data[0]
                customer_id = customer.get('customer_id')
                logger.info(f"Found existing bank statement customer_id: {customer_id} (no record created)")
                return customer_id
            else:
                # Generate new UUID but DO NOT create database record
                # The record will be created by update_customer_fraud_status()
                from uuid import uuid4
                customer_id = str(uuid4())
                logger.info(f"Generated new customer_id: {customer_id} (record will be created by update_customer_fraud_status)")
                return customer_id

        except Exception as e:
            logger.error(f"Error in get_or_create_customer: {e}", exc_info=True)
            return None

    def get_customer_history(self, account_holder_name: str) -> Dict:
        """
        Get customer history by account holder name
        Returns the FIRST record for the customer (original upload) to avoid duplicate record issues
        Uses MAX() aggregation to get the actual counts across all records

        Args:
            account_holder_name: Name of the account holder

        Returns:
            Customer history dict with fraud_count, escalate_count, etc.
        """
        if not self.supabase or not account_holder_name:
            return {}

        try:
            # Query bank_statement_customers table - get ALL records for this customer
            # Note: Supabase order() doesn't accept asc=True, use .order('column') for ascending
            response = self.supabase.table('bank_statement_customers').select('*').eq('name', account_holder_name).order('created_at').execute()

            if response.data and len(response.data) > 0:
                # Get the FIRST record (original) for customer_id and name
                first_record = response.data[0]
                customer_id = first_record.get('customer_id')
                
                # Calculate MAX counts across ALL records (to handle duplicates correctly)
                # This ensures we get the true counts even if there are duplicate records
                max_fraud_count = max((r.get('fraud_count', 0) or 0) for r in response.data)
                max_escalate_count = max((r.get('escalate_count', 0) or 0) for r in response.data)
                max_total_statements = max((r.get('total_statements', 0) or 0) for r in response.data)
                
                # Get latest recommendation and analysis date from the MOST RECENT record
                latest_record = max(response.data, key=lambda r: r.get('created_at', ''))
                
                return {
                    'customer_id': customer_id,
                    'name': first_record.get('name'),
                    'has_fraud_history': max_fraud_count > 0,
                    'fraud_count': max_fraud_count,
                    'escalate_count': max_escalate_count,
                    'last_recommendation': latest_record.get('last_recommendation'),
                    'last_analysis_date': latest_record.get('last_analysis_date'),
                    'total_statements': max_total_statements
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
        Insert new customer record based on recommendation (always INSERT, never UPDATE)
        Matches paystub_customers logic: each upload creates a new row with same customer_id
        
        Logic:
        - If customer exists: reuse their customer_id, create new row with preserved counts
        - If customer is new: create new customer_id
        - Always INSERT (never UPDATE existing rows)
        - Counts are calculated and inserted, then updated after analysis if needed

        Args:
            account_holder_name: Account holder name
            recommendation: AI recommendation (APPROVE, REJECT, ESCALATE)
            statement_id: Statement ID if available

        Returns:
            True if insert successful, False otherwise
        """
        if not self.supabase or not account_holder_name:
            return False

        try:
            from datetime import datetime
            from uuid import uuid4
            now = datetime.utcnow().isoformat()

            # Step 1: Check if customer already exists to reuse customer_id
            try:
                existing_response = self.supabase.table('bank_statement_customers').select('customer_id, escalate_count, fraud_count, has_fraud_history, total_statements').eq('name', account_holder_name).order('created_at', desc=True).limit(1).execute()
                
                if existing_response.data and len(existing_response.data) > 0:
                    # Customer exists - reuse their customer_id
                    existing_record = existing_response.data[0]
                    customer_id = existing_record.get('customer_id')
                    previous_escalate_count = existing_record.get('escalate_count', 0) or 0
                    previous_fraud_count = existing_record.get('fraud_count', 0) or 0
                    previous_has_fraud_history = existing_record.get('has_fraud_history', False) or False
                    previous_total_statements = existing_record.get('total_statements', 0) or 0
                    
                    logger.info(f"[CUSTOMER_INSERT] Found existing customer: {account_holder_name} with customer_id={customer_id}, escalate_count={previous_escalate_count}, fraud_count={previous_fraud_count}")
                    
                    # Calculate new counts based on recommendation
                    new_fraud_count = previous_fraud_count
                    new_escalate_count = previous_escalate_count
                    has_fraud_history = previous_has_fraud_history
                    
                    if recommendation == 'REJECT':
                        new_fraud_count = previous_fraud_count + 1
                        has_fraud_history = True
                        logger.info(f"[CUSTOMER_INSERT] REJECT: fraud_count = {previous_fraud_count} + 1 = {new_fraud_count}")
                    elif recommendation == 'ESCALATE':
                        new_escalate_count = previous_escalate_count + 1
                        logger.info(f"[CUSTOMER_INSERT] ESCALATE: escalate_count = {previous_escalate_count} + 1 = {new_escalate_count}")
                    
                    # Create new row with same customer_id and updated counts
                    new_customer = {
                        'customer_id': customer_id,  # Reuse same customer_id
                        'name': account_holder_name,
                        'has_fraud_history': has_fraud_history,
                        'fraud_count': new_fraud_count,
                        'escalate_count': new_escalate_count,
                        'last_recommendation': recommendation,
                        'last_analysis_date': now,
                        'total_statements': previous_total_statements + 1,
                        'created_at': now,
                        'updated_at': now
                    }

                    self.supabase.table('bank_statement_customers').insert([new_customer]).execute()
                    logger.info(f"[CUSTOMER_INSERT] Created new row for existing customer: {account_holder_name} (customer_id={customer_id}, id will be auto-generated)")
                    return True
            except Exception as e:
                logger.warning(f"Error querying existing customer: {e}")

            # Step 2: Customer doesn't exist - create new customer_id
            customer_id = str(uuid4())
            logger.info(f"[CUSTOMER_INSERT] Creating new customer: {account_holder_name} with customer_id={customer_id}")
            
            # Initialize counts based on recommendation
            fraud_count = 1 if recommendation == 'REJECT' else 0
            escalate_count = 1 if recommendation == 'ESCALATE' else 0
            has_fraud_history = recommendation == 'REJECT'
            
            new_customer = {
                'customer_id': customer_id,
                'name': account_holder_name,
                'has_fraud_history': has_fraud_history,
                'fraud_count': fraud_count,
                'escalate_count': escalate_count,
                'last_recommendation': recommendation,
                'last_analysis_date': now,
                'total_statements': 1,
                'created_at': now,
                'updated_at': now
            }
            
            self.supabase.table('bank_statement_customers').insert([new_customer]).execute()
            logger.info(f"[CUSTOMER_INSERT] Created new customer record: {account_holder_name} (customer_id={customer_id}, id will be auto-generated)")

            return True
        except Exception as e:
            logger.error(f"Error inserting customer fraud status: {e}", exc_info=True)
            return False

