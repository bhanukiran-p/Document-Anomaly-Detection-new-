"""
Document Storage Module
Handles persistence of all analyzed documents to Supabase database
Supports: Checks, Paystubs, Bank Statements, Money Orders
"""

import uuid
import logging
import json
from datetime import datetime
from typing import Dict, Optional, Any
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class DocumentStorage:
    """Store and retrieve analyzed documents from Supabase"""

    def __init__(self):
        """Initialize Supabase client"""
        self.supabase = get_supabase()

    # ==================== HELPER METHODS ====================

    def _parse_amount(self, value: Any) -> Optional[float]:
        """Convert amount string or number to float"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas: "$1,567.89" → 1567.89
            cleaned = value.replace('$', '').replace(',', '').strip()
            try:
                return float(cleaned) if cleaned else None
            except ValueError:
                logger.warning(f"Could not parse amount: {value}")
                return None
        return None

    def _parse_date(self, value: Any) -> Optional[str]:
        """Convert empty strings to None for dates"""
        if isinstance(value, str) and value.strip() == '':
            return None
        if value is None:
            return None
        return str(value)

    def _safe_string(self, value: Any) -> Optional[str]:
        """Safely convert value to string, return None if empty"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return str(value) if value else None

    def _get_or_create_institution(self, institution_data: Optional[Dict]) -> Optional[str]:
        """Get or create financial institution, return institution_id"""
        if not institution_data:
            return None

        name = institution_data.get('name')
        if not name:
            return None

        try:
            name = self._safe_string(name)
            if not name:
                return None

            # Convert to UPPERCASE for consistent storage
            name = name.upper()

            # Check if exists
            response = self.supabase.table('financial_institutions').select('institution_id').eq(
                'name', name
            ).execute()

            if response.data:
                logger.info(f"Found existing institution: {name}")
                return response.data[0]['institution_id']

            # Create new institution
            institution_id = str(uuid.uuid4())
            new_institution = {
                'institution_id': institution_id,
                'name': name,
                'routing_number': self._safe_string(institution_data.get('routing_number')),
                'address': self._safe_string(institution_data.get('address')),
                'city': self._safe_string(institution_data.get('city')),
                'state': self._safe_string(institution_data.get('state')),
                'zip_code': self._safe_string(institution_data.get('zip')),
                'country': self._safe_string(institution_data.get('country', 'USA'))
            }

            self.supabase.table('financial_institutions').insert([new_institution]).execute()
            logger.info(f"Created new institution: {name} ({institution_id})")
            return institution_id

        except Exception as e:
            logger.warning(f"Error getting/creating institution: {e}")
            return None

    def _get_or_create_employer(self, employer_data: Optional[Dict]) -> Optional[str]:
        """Get or create employer, return employer_id"""
        if not employer_data:
            return None

        name = employer_data.get('name')
        if not name:
            return None

        try:
            name = self._safe_string(name)
            if not name:
                return None

            # Check if exists
            response = self.supabase.table('employers').select('employer_id').eq(
                'name', name
            ).execute()

            if response.data:
                logger.info(f"Found existing employer: {name}")
                return response.data[0]['employer_id']

            # Create new employer
            employer_id = str(uuid.uuid4())
            new_employer = {
                'employer_id': employer_id,
                'name': name,
                'address': self._safe_string(employer_data.get('address')),
                'city': self._safe_string(employer_data.get('city')),
                'state': self._safe_string(employer_data.get('state')),
                'zip_code': self._safe_string(employer_data.get('zip')),
                'country': self._safe_string(employer_data.get('country', 'USA')),
                'phone': self._safe_string(employer_data.get('phone')),
                'email': self._safe_string(employer_data.get('email'))
            }

            self.supabase.table('employers').insert([new_employer]).execute()
            logger.info(f"Created new employer: {name} ({employer_id})")
            return employer_id

        except Exception as e:
            logger.warning(f"Error getting/creating employer: {e}")
            return None

    def _get_or_create_money_order_customer(self, customer_data: Optional[Dict]) -> Optional[str]:
        """Get or create a money order customer record using payer-based tracking.

        For payer-based fraud tracking (Option 2):
        - If payer (name) already exists: reuse their customer_id, create new row
        - If payer (name) is new: create new customer_id only once
        - Multiple rows can have same customer_id (one row per upload/payee combination)
        - Fraud counts are cumulative across all rows with same customer_id
        """
        if not customer_data:
            return None

        name = customer_data.get('name')
        if not name:
            return None

        try:
            name = self._safe_string(name)
            if not name:
                return None

            address = self._safe_string(customer_data.get('address'))
            payee_name = self._safe_string(customer_data.get('payee_name'))

            # Step 1: Check if this payer (name) already exists
            # Query by name ONLY to find existing customer_id for this payer
            # NOTE: We query by name only (not address) because the same payer might use different addresses
            try:
                response = self.supabase.table('money_order_customers').select('customer_id, escalate_count, fraud_count, has_fraud_history').eq('name', name).order('created_at', desc=True).limit(1).execute()
                if response.data and len(response.data) > 0:
                    # Payer already exists - reuse their customer_id
                    existing_customer_record = response.data[0]
                    existing_customer_id = existing_customer_record.get('customer_id')
                    previous_escalate_count = existing_customer_record.get('escalate_count', 0)
                    previous_fraud_count = existing_customer_record.get('fraud_count', 0)
                    previous_has_fraud_history = existing_customer_record.get('has_fraud_history', False)

                    logger.info(f"Found existing payer: {name} with customer_id={existing_customer_id}, escalate_count={previous_escalate_count}, fraud_count={previous_fraud_count}")

                    # Create a new row for this upload with same customer_id and preserved fraud history
                    new_customer = {
                        'customer_id': existing_customer_id,
                        'name': name,
                        'payee_name': payee_name,
                        'address': address,
                        'city': self._safe_string(customer_data.get('city')),
                        'state': self._safe_string(customer_data.get('state')),
                        'zip_code': self._safe_string(customer_data.get('zip')),
                        'phone': self._safe_string(customer_data.get('phone')),
                        'email': self._safe_string(customer_data.get('email')),
                        # Preserve fraud history from previous uploads
                        'escalate_count': previous_escalate_count,
                        'fraud_count': previous_fraud_count,
                        'has_fraud_history': previous_has_fraud_history
                    }
                    self.supabase.table('money_order_customers').insert([new_customer]).execute()
                    logger.info(f"Created new row for existing payer: {name} to {payee_name} (customer_id={existing_customer_id}) with fraud history: escalate_count={previous_escalate_count}")
                    return existing_customer_id
            except Exception as e:
                logger.warning(f"Error querying existing payer: {e}")

            # Step 2: Payer doesn't exist - create new customer_id only once
            customer_id = str(uuid.uuid4())
            new_customer = {
                'customer_id': customer_id,
                'name': name,
                'payee_name': payee_name,
                'address': address,
                'city': self._safe_string(customer_data.get('city')),
                'state': self._safe_string(customer_data.get('state')),
                'zip_code': self._safe_string(customer_data.get('zip')),
                'phone': self._safe_string(customer_data.get('phone')),
                'email': self._safe_string(customer_data.get('email')),
                # Initialize fraud counts to 0 - will be set by _update_customer_fraud_history_after_analysis
                'escalate_count': 0,
                'fraud_count': 0,
                'has_fraud_history': False
            }

            self.supabase.table('money_order_customers').insert([new_customer]).execute()
            logger.info(f"Created new money order customer record: {name} to {payee_name} ({customer_id})")
            return customer_id

        except Exception as e:
            logger.warning(f"Error creating money order customer: {e}")
            return None

    def _update_customer_fraud_history_after_analysis(self, customer_id: Optional[str], ai_analysis: Optional[Dict]) -> None:
        """
        Update customer fraud history in database after analysis completes.

        Logic (Payer-Based Fraud Tracking):
        - Always creates new customer row per upload (done in _get_or_create_money_order_customer)
        - For ESCALATE: Set escalate_count = previous_escalate_count + 1 (from other records for same payer)
        - For REJECT: Set fraud_count = previous_fraud_count + 1 and has_fraud_history = True
        - For APPROVE: Just update recommendation timestamp

        Args:
            customer_id: The customer ID to update
            ai_analysis: The AI analysis result containing the recommendation
        """
        if not customer_id or not ai_analysis:
            return

        try:
            recommendation = ai_analysis.get('recommendation', 'APPROVE')

            logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Starting fraud history update: customer_id={customer_id}, recommendation={recommendation}")

            # Fetch the current customer record to get the payer name
            current_customer_response = self.supabase.table('money_order_customers').select('name').eq('customer_id', customer_id).execute()

            if not current_customer_response.data:
                logger.warning(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Could not fetch customer record: {customer_id}")
                return

            payer_name = current_customer_response.data[0].get('name')
            logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Fetched payer name: {payer_name}")

            # Fetch PREVIOUS records for same payer to get cumulative counts
            # Order by created_at DESC to get the most recent record first
            previous_records_response = self.supabase.table('money_order_customers').select('escalate_count, fraud_count').eq('name', payer_name).order('created_at', desc=True).execute()

            # The first result should be the current record we just created, skip it
            previous_escalate_count = 0
            previous_fraud_count = 0

            if previous_records_response.data and len(previous_records_response.data) > 1:
                # Get counts from the previous record (index 1, since index 0 is current)
                previous_record = previous_records_response.data[1]
                previous_escalate_count = previous_record.get('escalate_count', 0)
                previous_fraud_count = previous_record.get('fraud_count', 0)
                logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Found previous record - escalate_count={previous_escalate_count}, fraud_count={previous_fraud_count}")
            else:
                logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] No previous records found for payer {payer_name}")

            # Determine what to update based on recommendation
            from datetime import timezone
            update_data = {
                'last_recommendation': recommendation,
                'last_analysis_date': datetime.now(timezone.utc).isoformat()
            }

            if recommendation == 'ESCALATE':
                # Increment escalate_count based on previous record's count
                new_escalate_count = previous_escalate_count + 1
                update_data['escalate_count'] = new_escalate_count
                logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] ESCALATE: escalate_count = {previous_escalate_count} + 1 = {new_escalate_count}")

            elif recommendation == 'REJECT':
                # Increment fraud_count based on previous record's count, mark as fraudster
                new_fraud_count = previous_fraud_count + 1
                update_data['fraud_count'] = new_fraud_count
                update_data['has_fraud_history'] = True
                logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] REJECT: fraud_count = {previous_fraud_count} + 1 = {new_fraud_count}, marked as fraudster")

            else:
                # APPROVE or other - just update recommendation timestamp, no counts
                logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] APPROVE: updating timestamp only")

            # Execute the update on the current customer record ONLY
            # Get the most recently created row (the one we just inserted) by selecting the MAX id
            # Then update only that specific row to avoid updating all rows with same customer_id
            logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Executing UPDATE with data: {update_data}")

            # Get the latest row ID for this customer_id (the one we just created)
            latest_row_response = self.supabase.table('money_order_customers').select('id').eq('customer_id', customer_id).order('created_at', desc=True).limit(1).execute()

            if latest_row_response.data and len(latest_row_response.data) > 0:
                latest_row_id = latest_row_response.data[0].get('id')
                # Update only this specific row by id, not all rows with same customer_id
                self.supabase.table('money_order_customers').update(update_data).eq('id', latest_row_id).execute()
                logger.info(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Successfully updated row id={latest_row_id} for customer {payer_name}")
            else:
                logger.warning(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Could not find latest row for customer_id={customer_id}")

        except Exception as e:
            logger.error(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Error updating customer fraud history: {e}")
            import traceback
            logger.error(f"[FRAUD_UPDATE_AFTER_ANALYSIS] Traceback: {traceback.format_exc()}")

    def _store_document(self, user_id: str, document_type: str, file_name: str) -> str:
        """Store document record in documents table, return document_id"""
        try:
            document_id = str(uuid.uuid4())
            doc_data = {
                'document_id': document_id,
                'user_id': user_id,
                'document_type': document_type,
                'file_name': file_name,
                'upload_date': datetime.utcnow().isoformat(),
                'status': 'processing'
            }

            self.supabase.table('documents').insert([doc_data]).execute()
            logger.info(f"Stored document: {document_id}")
            return document_id

        except Exception as e:
            logger.error(f"Error storing document record: {e}")
            raise

    def _update_document_status(self, document_id: str, status: str, fraud_risk: Optional[float] = None):
        """Update document status and fraud risk score"""
        try:
            update_data = {'status': status}
            if fraud_risk is not None:
                update_data['fraud_risk_score'] = fraud_risk

            self.supabase.table('documents').update(update_data).eq(
                'document_id', document_id
            ).execute()
            logger.info(f"Updated document {document_id} status to {status}")

        except Exception as e:
            logger.warning(f"Error updating document status: {e}")

    # ==================== MONEY ORDERS ====================

    def store_money_order(self, user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
        """Store money order analysis result to database"""
        document_id = None
        try:
            extracted = analysis_data.get('extracted_data', {})
            ml_analysis = analysis_data.get('ml_analysis', {})
            ai_analysis = analysis_data.get('ai_analysis', {})

            # Store document record
            document_id = self._store_document(user_id, 'money_order', file_name)

            # Extract institution
            institution_data = {
                'name': extracted.get('issuer'),
                'routing_number': None
            }
            institution_id = self._get_or_create_institution(institution_data)

            # Extract and create/find purchaser customer with payee information in same row
            purchaser_data = {
                'name': extracted.get('purchaser'),
                'address': extracted.get('sender_address'),
                'payee_name': extracted.get('payee')
            }
            purchaser_customer_id = self._get_or_create_money_order_customer(purchaser_data)

            # Update customer fraud history based on AI analysis recommendation
            self._update_customer_fraud_history_after_analysis(purchaser_customer_id, ai_analysis)

            # Prepare money order data with AI analysis
            money_order_data = {
                'money_order_id': str(uuid.uuid4()),
                'document_id': document_id,
                'money_order_number': self._safe_string(extracted.get('serial_number')),
                'amount': self._parse_amount(extracted.get('amount')),
                'currency': 'USD',
                'issue_date': self._parse_date(extracted.get('date')),
                'issuer_name': self._safe_string(extracted.get('issuer')),
                'issuer_address': self._safe_string(extracted.get('issuer_address')),
                'institution_id': institution_id,
                'purchaser_name': self._safe_string(extracted.get('purchaser')),
                'purchaser_address': self._safe_string(extracted.get('sender_address')),
                'purchaser_customer_id': purchaser_customer_id,
                'payee_name': self._safe_string(extracted.get('payee')),
                'serial_number_primary': self._safe_string(extracted.get('serial_number')),
                'serial_number_secondary': self._safe_string(extracted.get('serial_secondary')),
                # ML Analysis results
                'fraud_risk_score': self._parse_amount(ml_analysis.get('fraud_risk_score')),
                'risk_level': self._safe_string(ml_analysis.get('risk_level')),
                'model_confidence': self._parse_amount(ml_analysis.get('model_confidence')),
                # AI Analysis results
                'ai_recommendation': self._safe_string(ai_analysis.get('recommendation')) if ai_analysis else None,
                'ai_confidence': self._parse_amount(ai_analysis.get('confidence_score')) if ai_analysis else None,
                # Anomaly data
                'anomaly_count': len(analysis_data.get('anomalies', [])),
                'top_anomalies': json.dumps(analysis_data.get('anomalies', [])[:5])
            }

            # Insert money order record
            logger.info(f"Attempting to insert money order with data: {money_order_data}")
            self.supabase.table('money_orders').insert([money_order_data]).execute()
            logger.info(f"Stored money order: {money_order_data['money_order_id']}")

            # Update document status
            self._update_document_status(document_id, 'success')

            return document_id

        except Exception as e:
            import traceback
            logger.error(f"Error storing money order: {e}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            logger.error(f"Attempted to insert data: {money_order_data if 'money_order_data' in locals() else 'N/A'}")
            if document_id:
                self._update_document_status(document_id, 'failed')
            return None

    # ==================== BANK STATEMENTS ====================

    def store_bank_statement(self, user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
        """Store bank statement analysis result to database"""
        document_id = None
        try:
            extracted = analysis_data.get('extracted_data', {})
            ml_analysis = analysis_data.get('ml_analysis', {})
            ai_analysis = analysis_data.get('ai_analysis', {})

            # Store document record
            document_id = self._store_document(user_id, 'bank_statement', file_name)

            # Get or create customer first (required for customer_id)
            # Try multiple sources for account holder name
            account_holder_name = (
                self._safe_string(extracted.get('account_holder_name')) or
                self._safe_string(extracted.get('account_holder')) or
                (extracted.get('account_holder_names', [])[0] if isinstance(extracted.get('account_holder_names'), list) and len(extracted.get('account_holder_names', [])) > 0 else None)
            )
            customer_id = None
            if account_holder_name:
                try:
                    from bank_statement.database.bank_statement_customer_storage import BankStatementCustomerStorage
                    customer_storage = BankStatementCustomerStorage()
                    # Get or create customer - will generate UUID if not exists
                    customer_id = customer_storage.get_or_create_customer(account_holder_name)

                    if customer_id:
                        logger.info(f"Got or created bank statement customer: {customer_id}")
                    else:
                        logger.warning(f"Could not create customer for {account_holder_name}")
                except Exception as e:
                    logger.warning(f"Could not get or create customer: {e}")
                    # Continue without customer_id if lookup/creation fails

            # Extract institution
            institution_data = {
                'name': extracted.get('bank_name'),
                'routing_number': extracted.get('routing_number')
            }
            institution_id = self._get_or_create_institution(institution_data)

            # Parse transactions to JSON array
            transactions = extracted.get('transactions', [])
            if not isinstance(transactions, list):
                transactions = []

            # Get AI recommendation first
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN') if ai_analysis else 'UNKNOWN'
            ai_recommendation = ai_recommendation.upper()

            # Only store fraud types if recommendation is REJECT
            # For ESCALATE or APPROVE, keep fraud_type as None (no fraud detected)
            primary_fraud_type = None
            primary_fraud_type_label = None
            fraud_explanations = []
            
            if ai_recommendation == 'REJECT':
                # Only store fraud types for REJECT recommendations (actual fraud detected)
                fraud_types = ai_analysis.get('fraud_types', []) if ai_analysis else ml_analysis.get('fraud_types', [])
                fraud_explanations = ai_analysis.get('fraud_explanations', []) if ai_analysis else []

                # Ensure fraud_types is a list, then extract first element as primary fraud type
                if not isinstance(fraud_types, list):
                    fraud_types = [fraud_types] if fraud_types else []

                # Store only the primary (first) fraud type as a string
                primary_fraud_type = fraud_types[0] if fraud_types else None

                # Format fraud type label for display (remove underscores and title case)
                primary_fraud_type_label = primary_fraud_type.replace('_', ' ').title() if primary_fraud_type else None
            # For ESCALATE or APPROVE, primary_fraud_type remains None (no fraud detected)

            # Ensure fraud_explanations is a list of dicts
            if not isinstance(fraud_explanations, list):
                fraud_explanations = []

            # Prepare bank statement data
            # Convert bank_name to UPPERCASE for consistent storage
            bank_name_raw = self._safe_string(extracted.get('bank_name'))
            bank_name_upper = bank_name_raw.upper() if bank_name_raw else None

            statement_data = {
                'statement_id': str(uuid.uuid4()),
                'document_id': document_id,
                'user_id': user_id,  # Add user_id (required field)
                'file_name': file_name,  # Add file_name (required field)
                'customer_id': customer_id,  # Add customer_id (can be None if account holder name missing)
                'account_holder_name': self._safe_string(account_holder_name or extracted.get('account_holder_name') or extracted.get('account_holder')),
                'account_holder_address': self._safe_string(extracted.get('account_holder_address') or extracted.get('account_holder_address')),
                'account_holder_city': None,
                'account_holder_state': None,
                'account_holder_zip': None,
                'bank_name': bank_name_upper,
                'institution_id': institution_id,
                'bank_address': self._safe_string(extracted.get('bank_address')),
                'bank_city': None,
                'bank_state': None,
                'bank_zip': None,
                'routing_number': self._safe_string(extracted.get('routing_number')),
                'account_number': self._safe_string(extracted.get('account_number')),
                'account_type': self._safe_string(extracted.get('account_type')),
                'currency': self._safe_string(extracted.get('currency', 'USD')),
                'statement_period': self._safe_string(extracted.get('statement_period_start') or extracted.get('statement_period_start_date') or extracted.get('statement_period')),
                'statement_period_start_date': self._parse_date(extracted.get('statement_period_start_date') or extracted.get('statement_period_start')),
                'statement_period_end_date': self._parse_date(extracted.get('statement_period_end_date') or extracted.get('statement_period_end')),
                'opening_balance': self._parse_amount(extracted.get('opening_balance')),
                'ending_balance': self._parse_amount(extracted.get('closing_balance')),
                'available_balance': self._parse_amount(extracted.get('available_balance')),
                'total_transactions': len(transactions),
                'transaction_count': len(transactions),  # Keep for backward compatibility
                'total_credits': self._parse_amount(extracted.get('total_credits')),
                'total_debits': self._parse_amount(extracted.get('total_debits')),
                'net_activity': self._parse_amount(extracted.get('net_activity')),
                'transactions': json.dumps(transactions),
                'fraud_risk_score': self._parse_amount(ml_analysis.get('fraud_risk_score')),
                'risk_level': self._safe_string(ml_analysis.get('risk_level')),
                'model_confidence': self._parse_amount(ml_analysis.get('model_confidence')),
                'ai_recommendation': self._safe_string(ai_analysis.get('recommendation')) if ai_analysis else None,
                'ai_confidence': self._parse_amount(ai_analysis.get('confidence_score')) if ai_analysis else None,
                'anomaly_count': len(analysis_data.get('anomalies', [])),
                'top_anomalies': json.dumps(analysis_data.get('anomalies', [])[:5]),
                # Fraud types - store as human-readable label (primary fraud type only)
                'fraud_types': self._safe_string(primary_fraud_type_label),
                # Note: fraud_explanations column doesn't exist in bank_statements table
                'timestamp': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()  # Keep for backward compatibility
            }

            # Insert bank statement record
            # Note: If customer_id is None, we'll try to insert without it (table may allow NULL)
            try:
                if customer_id is None:
                    # Remove customer_id from data if it's None
                    statement_data_to_insert = {k: v for k, v in statement_data.items() if k != 'customer_id'}
                    self.supabase.table('bank_statements').insert([statement_data_to_insert]).execute()
                    logger.info(f"Stored bank statement without customer_id: {statement_data['statement_id']}")
                else:
                    self.supabase.table('bank_statements').insert([statement_data]).execute()
                    logger.info(f"Stored bank statement with customer_id {customer_id}: {statement_data['statement_id']}")
            except Exception as insert_error:
                error_str = str(insert_error).lower()
                # If insert fails due to customer_id constraint, try without it
                if 'customer_id' in error_str and ('not null' in error_str or 'null value' in error_str):
                    logger.warning(f"Insert failed due to customer_id NOT NULL constraint, retrying without it: {insert_error}")
                    statement_data_to_insert = {k: v for k, v in statement_data.items() if k != 'customer_id'}
                    try:
                        self.supabase.table('bank_statements').insert([statement_data_to_insert]).execute()
                        logger.info(f"Stored bank statement without customer_id (retry): {statement_data['statement_id']}")
                    except Exception as retry_error:
                        logger.error(f"Retry insert also failed: {retry_error}")
                        raise retry_error
                else:
                    logger.error(f"Insert failed with error: {insert_error}")
                    raise insert_error

            # Update document status
            self._update_document_status(document_id, 'success')

            return document_id

        except Exception as e:
            logger.error(f"Error storing bank statement: {e}", exc_info=True)
            if document_id:
                self._update_document_status(document_id, 'failed')
            return None

    # ==================== PAYSTUBS ====================

    def store_paystub(self, user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
        """Store paystub analysis result to database"""
        document_id = None
        try:
            extracted = analysis_data.get('extracted_data', {})
            ml_analysis = analysis_data.get('ml_analysis', {})
            ai_analysis = analysis_data.get('ai_analysis', {})

            # Store document record
            document_id = self._store_document(user_id, 'paystub', file_name)

            # Extract employer
            employer_data = {
                'name': extracted.get('employer_name'),
                'address': extracted.get('employer_address'),
                'city': extracted.get('employer_city'),
                'state': extracted.get('employer_state'),
                'zip': extracted.get('employer_zip'),
                'phone': extracted.get('employer_phone'),
                'email': extracted.get('employer_email')
            }
            employer_id = self._get_or_create_employer(employer_data)

            # Parse deductions to JSON array
            deductions = extracted.get('deductions', [])
            if not isinstance(deductions, list):
                deductions = []

            # Get AI recommendation first
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN') if ai_analysis else 'UNKNOWN'
            ai_recommendation = ai_recommendation.upper()

            # Only store fraud types if recommendation is REJECT
            # For ESCALATE or APPROVE, keep fraud_type as None (no fraud detected)
            primary_fraud_type = None
            primary_fraud_type_label = None
            fraud_explanations = []
            
            if ai_recommendation == 'REJECT':
                # Only store fraud types for REJECT recommendations (actual fraud detected)
                fraud_types = ai_analysis.get('fraud_types') if ai_analysis else ml_analysis.get('fraud_types', [])
                fraud_explanations = ai_analysis.get('fraud_explanations', []) if ai_analysis else []

                # Ensure fraud_types is a list, then extract first element as primary fraud type
                if not isinstance(fraud_types, list):
                    fraud_types = [fraud_types] if fraud_types else []

                # Store only the primary (first) fraud type as a string
                primary_fraud_type = fraud_types[0] if fraud_types else None

                # Format fraud type label for display (remove underscores and title case)
                primary_fraud_type_label = primary_fraud_type.replace('_', ' ').title() if primary_fraud_type else None
            # For ESCALATE or APPROVE, primary_fraud_type remains None (no fraud detected)

            # Ensure fraud_explanations is a list of dicts (already set above, but double-check)
            if not isinstance(fraud_explanations, list):
                fraud_explanations = []

            # Prepare paystub data
            # Match exact schema: paystubs table has employer_address, employer_country, employer_email
            # But NOT: employer_city, employer_state, employer_zip, employer_phone
            # Also NOT: pay_period_start, pay_period_end, pay_date (these don't exist in schema)
            paystub_data = {
                'paystub_id': str(uuid.uuid4()),
                'document_id': document_id,
                'employee_name': self._safe_string(extracted.get('employee_name')),
                'employee_address': self._safe_string(extracted.get('employee_address')),
                'employee_id_number': self._safe_string(extracted.get('employee_id')),
                'employer_id': employer_id,
                'employer_name': self._safe_string(extracted.get('employer_name')),
                'employer_address': self._safe_string(extracted.get('employer_address')),
                'employer_country': self._safe_string(extracted.get('employer_country', 'USA')),
                'employer_email': self._safe_string(extracted.get('employer_email')),
                'gross_pay': self._parse_amount(extracted.get('gross_pay')),
                'net_pay': self._parse_amount(extracted.get('net_pay')),
                'ytd_gross': self._parse_amount(extracted.get('ytd_gross')),
                'ytd_net': self._parse_amount(extracted.get('ytd_net')),
                'deductions': json.dumps(deductions) if deductions else None,
                # ML Analysis results
                'fraud_risk_score': self._parse_amount(ml_analysis.get('fraud_risk_score')),
                'risk_level': self._safe_string(ml_analysis.get('risk_level')),
                'model_confidence': self._parse_amount(ml_analysis.get('model_confidence')),
                # AI Analysis results
                'ai_recommendation': self._safe_string(ai_analysis.get('recommendation')) if ai_analysis else None,
                # Anomaly data
                'anomaly_count': len(analysis_data.get('anomalies', [])),
                'top_anomalies': json.dumps(analysis_data.get('anomalies', [])[:5]) if analysis_data.get('anomalies') else None,
                # Fraud types - store as human-readable label (primary fraud type only)
                'fraud_types': self._safe_string(primary_fraud_type_label),
                'fraud_explanations': json.dumps(fraud_explanations) if fraud_explanations else '[]'
            }

            # Insert paystub record
            try:
                self.supabase.table('paystubs').insert([paystub_data]).execute()
                logger.info(f"Stored paystub: {paystub_data['paystub_id']}")
            except Exception as insert_error:
                logger.error(f"Error inserting paystub into database: {insert_error}", exc_info=True)
                logger.error(f"Paystub data keys: {list(paystub_data.keys())}")
                raise insert_error

            # Update document status
            self._update_document_status(document_id, 'success')

            return document_id

        except Exception as e:
            logger.error(f"Error storing paystub: {e}", exc_info=True)
            if document_id:
                self._update_document_status(document_id, 'failed')
            return None

    # ==================== CHECKS ====================

    def store_check(self, user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
        """Store check analysis result to database"""
        document_id = None
        try:
            extracted = analysis_data.get('extracted_data', {})
            ml_analysis = analysis_data.get('ml_analysis', {})
            ai_analysis = analysis_data.get('ai_analysis', {})

            # Store document record
            document_id = self._store_document(user_id, 'check', file_name)

            # Extract institution
            institution_data = {
                'name': extracted.get('bank_name'),
                'routing_number': extracted.get('routing_number')
            }
            institution_id = self._get_or_create_institution(institution_data)

            # Prepare check data
            # Convert bank_name to UPPERCASE for consistent storage
            bank_name_raw = self._safe_string(extracted.get('bank_name'))
            bank_name_upper = bank_name_raw.upper() if bank_name_raw else None

            check_data = {
                'check_id': str(uuid.uuid4()),
                'document_id': document_id,
                'check_number': self._safe_string(extracted.get('check_number')),
                'amount': self._parse_amount(extracted.get('amount')),
                'check_date': self._parse_date(extracted.get('check_date')),
                'payer_name': self._safe_string(extracted.get('payer_name')),
                'payer_address': self._safe_string(extracted.get('payer_address')),
                'payee_name': self._safe_string(extracted.get('payee_name')),
                'bank_name': bank_name_upper,
                'institution_id': institution_id,
                'account_number': self._safe_string(extracted.get('account_number')),
                'routing_number': self._safe_string(extracted.get('routing_number')),
                'fraud_risk_score': self._parse_amount(ml_analysis.get('fraud_risk_score')),
                'risk_level': self._safe_string(ml_analysis.get('risk_level')),
                'model_confidence': self._parse_amount(ml_analysis.get('model_confidence')),
                'ai_recommendation': self._safe_string(ai_analysis.get('recommendation')) if ai_analysis else None,
                'signature_detected': extracted.get('signature_detected', False),
                'anomaly_count': len(analysis_data.get('anomalies', [])),
                'top_anomalies': json.dumps(analysis_data.get('anomalies', [])[:5]),
                'timestamp': datetime.utcnow().isoformat()
            }

            # Insert check record
            self.supabase.table('checks').insert([check_data]).execute()
            logger.info(f"Stored check: {check_data['check_id']}")

            # Update document status
            self._update_document_status(document_id, 'success')

            return document_id

        except Exception as e:
            logger.error(f"Error storing check: {e}")
            if document_id:
                self._update_document_status(document_id, 'failed')
            return None


# Convenience functions for use in API
def store_money_order_analysis(user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
    """Store money order analysis to database"""
    storage = DocumentStorage()
    return storage.store_money_order(user_id, file_name, analysis_data)


def store_bank_statement_analysis(user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
    """Store bank statement analysis to database using dedicated bank statement storage"""
    try:
        from bank_statement.database.bank_statement_storage import BankStatementStorage
        storage = BankStatementStorage()
        return storage.store_bank_statement(user_id, file_name, analysis_data)
    except Exception as e:
        logger.error(f"Error using dedicated bank statement storage: {e}, falling back to DocumentStorage")
        # Fallback to old method if new storage fails
    storage = DocumentStorage()
    return storage.store_bank_statement(user_id, file_name, analysis_data)


def store_paystub_analysis(user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
    """Store paystub analysis to database"""
    storage = DocumentStorage()
    return storage.store_paystub(user_id, file_name, analysis_data)


def store_check_analysis(user_id: str, file_name: str, analysis_data: Dict) -> Optional[str]:
    """Store check analysis to database"""
    storage = DocumentStorage()
    return storage.store_check(user_id, file_name, analysis_data)
