"""
Bank Statement Storage
Handles storing bank statement analysis results to database
Completely independent from other document type storage
Matches the paystub storage pattern
"""

import logging
import json
import uuid
from typing import Dict, Optional
from datetime import datetime
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class BankStatementStorage:
    """
    Manages bank statement storage in Supabase
    Stores complete analysis results similar to paystub storage pattern
    """

    def __init__(self):
        """Initialize with Supabase client"""
        try:
            self.supabase = get_supabase()
            logger.info("Initialized BankStatementStorage with Supabase connection")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None

    def _safe_string(self, value) -> Optional[str]:
        """Convert value to string safely"""
        if value is None:
            return None
        return str(value).strip() if str(value).strip() else None

    def _parse_amount(self, value) -> Optional[float]:
        """Parse amount to float safely"""
        if value is None:
            return None
        try:
            if isinstance(value, dict):
                return float(value.get('value', 0))
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value) -> Optional[str]:
        """Parse date to ISO format string"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Try to parse if it's already a date string
                from dateutil import parser
                parsed = parser.parse(value)
                return parsed.date().isoformat()
            return str(value)
        except Exception:
            return None

    def store_bank_statement(
        self,
        user_id: str,
        file_name: str,
        analysis_data: Dict
    ) -> Optional[str]:
        """
        Store bank statement analysis result to database
        Matches paystub storage pattern exactly

        Args:
            user_id: User ID who uploaded the document
            file_name: Original file name
            analysis_data: Complete analysis results dict with:
                - extracted_data: Raw extracted data
                - normalized_data: Normalized data
                - ml_analysis: ML fraud analysis results
                - ai_analysis: AI analysis results
                - anomalies: List of anomalies

        Returns:
            document_id (UUID) or None if storage failed
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return None

        document_id = None
        try:
            # Store document record first (like paystubs do)
            try:
                from database.document_storage import DocumentStorage
                doc_storage = DocumentStorage()
                document_id = doc_storage._store_document(user_id, 'bank_statement', file_name)
                if document_id:
                    logger.info(f"Created document record: {document_id}")
            except Exception as e:
                logger.warning(f"Could not create document record: {e}, continuing without document_id")
            extracted = analysis_data.get('extracted_data', {})
            normalized = analysis_data.get('normalized_data', {})
            ml_analysis = analysis_data.get('ml_analysis', {})
            ai_analysis = analysis_data.get('ai_analysis', {})

            # Get account holder name from multiple sources
            account_holder_name = (
                self._safe_string(normalized.get('account_holder_name')) or
                self._safe_string(extracted.get('account_holder_name')) or
                self._safe_string(extracted.get('account_holder')) or
                (extracted.get('account_holder_names', [])[0] if isinstance(extracted.get('account_holder_names'), list) and len(extracted.get('account_holder_names', [])) > 0 else None)
            )

            # Get or create customer
            customer_id = None
            if account_holder_name:
                try:
                    from .bank_statement_customer_storage import BankStatementCustomerStorage
                    customer_storage = BankStatementCustomerStorage()
                    customer_id = customer_storage.get_or_create_customer(account_holder_name)
                    if customer_id:
                        logger.info(f"Got or created customer: {customer_id}")
                except Exception as e:
                    logger.warning(f"Could not get or create customer: {e}")

            # Get institution_id (if needed)
            institution_id = None
            bank_name = self._safe_string(extracted.get('bank_name') or normalized.get('bank_name'))
            if bank_name:
                try:
                    # Use DocumentStorage helper method to get/create institution
                    from database.document_storage import DocumentStorage
                    doc_storage = DocumentStorage()
                    institution_data = {
                        'name': bank_name,
                        'routing_number': self._safe_string(extracted.get('routing_number'))
                    }
                    # Access the method (it's a public method in DocumentStorage)
                    institution_id = doc_storage._get_or_create_institution(institution_data)
                except Exception as e:
                    logger.warning(f"Could not get or create institution: {e}")
                    # Continue without institution_id if lookup fails

            # Parse transactions
            transactions = extracted.get('transactions', [])
            if not isinstance(transactions, list):
                transactions = []

            # Get balances for JSONB storage
            balances = {
                'beginning_balance': self._parse_amount(extracted.get('beginning_balance') or normalized.get('beginning_balance')),
                'ending_balance': self._parse_amount(extracted.get('ending_balance') or normalized.get('ending_balance')),
                'available_balance': self._parse_amount(extracted.get('available_balance') or normalized.get('available_balance')),
                'total_credits': self._parse_amount(extracted.get('total_credits') or normalized.get('total_credits')),
                'total_debits': self._parse_amount(extracted.get('total_debits') or normalized.get('total_debits'))
            }

            # Get AI recommendation (LLM is required)
            ai_recommendation = ai_analysis.get('recommendation', 'UNKNOWN')
            ai_recommendation = ai_recommendation.upper()

            # Only store fraud types if recommendation is REJECT
            # Only use LLM fraud_types - no fallback to ML
            primary_fraud_type = None
            primary_fraud_type_label = None
            fraud_explanations = []
            
            if ai_recommendation == 'REJECT':
                # Get fraud types from LLM only - no fallback to ML
                fraud_types = ai_analysis.get('fraud_types', [])
                fraud_explanations = ai_analysis.get('fraud_explanations', [])

                # Ensure fraud_types is a list
                if not isinstance(fraud_types, list):
                    fraud_types = [fraud_types] if fraud_types else []

                # Store only the primary (first) fraud type
                primary_fraud_type = fraud_types[0] if fraud_types else None

                # Format fraud type label for display (remove underscores and title case)
                if primary_fraud_type:
                    primary_fraud_type_label = primary_fraud_type.replace('_', ' ').title()

            # Ensure fraud_explanations is a list
            if not isinstance(fraud_explanations, list):
                fraud_explanations = []

            # Get anomalies
            anomalies_list = analysis_data.get('anomalies', [])
            if not isinstance(anomalies_list, list):
                anomalies_list = []

            # Prepare bank statement data matching the table schema
            statement_id = str(uuid.uuid4())
            now = datetime.utcnow()

            statement_data = {
                'statement_id': statement_id,
                'customer_id': customer_id,
                'user_id': user_id,
                'file_name': file_name,
                'document_id': document_id,
                'bank_name': bank_name,
                'account_holder': account_holder_name,  # Legacy field
                'account_holder_name': account_holder_name,
                'account_holder_address': self._safe_string(extracted.get('account_holder_address') or normalized.get('account_holder_address')),
                'account_holder_city': self._safe_string(extracted.get('account_holder_city') or normalized.get('account_holder_city')),
                'account_holder_state': self._safe_string(extracted.get('account_holder_state') or normalized.get('account_holder_state')),
                'account_holder_zip': self._safe_string(extracted.get('account_holder_zip') or normalized.get('account_holder_zip')),
                'institution_id': institution_id,
                'bank_address': self._safe_string(extracted.get('bank_address') or normalized.get('bank_address')),
                'bank_city': self._safe_string(extracted.get('bank_city') or normalized.get('bank_city')),
                'bank_state': self._safe_string(extracted.get('bank_state') or normalized.get('bank_state')),
                'bank_zip': self._safe_string(extracted.get('bank_zip') or normalized.get('bank_zip')),
                'routing_number': self._safe_string(extracted.get('routing_number') or normalized.get('routing_number')),
                'account_number': self._safe_string(extracted.get('account_number') or normalized.get('account_number')),
                'account_type': self._safe_string(extracted.get('account_type') or normalized.get('account_type')),
                'currency': self._safe_string(extracted.get('currency', 'USD') or normalized.get('currency', 'USD')),
                'statement_period': self._safe_string(extracted.get('statement_period') or normalized.get('statement_period')),
                'statement_period_start_date': self._parse_date(extracted.get('statement_period_start_date') or normalized.get('statement_period_start_date') or extracted.get('statement_period_start')),
                'statement_period_end_date': self._parse_date(extracted.get('statement_period_end_date') or normalized.get('statement_period_end_date') or extracted.get('statement_period_end')),
                # Balances as JSONB
                'balances': json.dumps(balances),
                # Balance fields (separate columns)
                'opening_balance': balances.get('beginning_balance'),
                'ending_balance': balances.get('ending_balance'),
                'available_balance': balances.get('available_balance'),
                # Transaction data
                'transaction_count': len(transactions),
                'total_transactions': len(transactions),
                'total_credits': balances.get('total_credits'),
                'total_debits': balances.get('total_debits'),
                'net_activity': balances.get('total_credits', 0) - balances.get('total_debits', 0) if balances.get('total_credits') and balances.get('total_debits') else None,
                'transactions': json.dumps(transactions) if transactions else None,
                # ML Analysis results
                'fraud_risk_score': self._parse_amount(ml_analysis.get('fraud_risk_score')),
                'risk_level': self._safe_string(ml_analysis.get('risk_level')),
                'model_confidence': self._parse_amount(ml_analysis.get('model_confidence')),
                # AI Analysis results
                'ai_recommendation': self._safe_string(ai_recommendation),
                'ai_confidence': self._parse_amount(ai_analysis.get('confidence_score')) if ai_analysis else None,
                'ai_summary': self._safe_string(ai_analysis.get('summary')) if ai_analysis else None,
                # Anomalies (as JSONB)
                'anomalies': json.dumps(anomalies_list) if anomalies_list else None,
                'anomaly_count': len(anomalies_list),
                'top_anomalies': json.dumps(anomalies_list[:5]) if anomalies_list else None,
                # Fraud types - store as human-readable label (primary fraud type only)
                # Note: This column may not exist yet - will be added via migration
                'fraud_types': self._safe_string(primary_fraud_type_label),
                # Timestamps
                'created_at': now.isoformat(),
                # Note: updated_at column doesn't exist in bank_statements table
                'timestamp': now.isoformat()
            }

            # Try to insert (handle customer_id being None and fraud_types column)
            try:
                # Prepare data for insert
                statement_data_to_insert = statement_data.copy()
                
                # Remove customer_id if None
                if customer_id is None:
                    statement_data_to_insert.pop('customer_id', None)
                
                # Try insert
                self.supabase.table('bank_statements').insert([statement_data_to_insert]).execute()
                logger.info(f"Stored bank statement: {statement_id}")
                
            except Exception as insert_error:
                error_str = str(insert_error).lower()
                error_msg = str(insert_error)
                
                # Handle missing columns (fraud_types, updated_at, etc.)
                missing_columns = []
                if 'fraud_types' in error_msg and ('not found' in error_str or 'column' in error_str):
                    missing_columns.append('fraud_types')
                if 'updated_at' in error_msg and ('not found' in error_str or 'column' in error_str):
                    missing_columns.append('updated_at')
                
                if missing_columns:
                    logger.warning(f"Missing columns detected: {missing_columns}, retrying without them: {insert_error}")
                    for col in missing_columns:
                        statement_data_to_insert.pop(col, None)
                    try:
                        self.supabase.table('bank_statements').insert([statement_data_to_insert]).execute()
                        logger.info(f"Stored bank statement without columns {missing_columns}: {statement_id}")
                    except Exception as retry_error:
                        logger.error(f"Retry insert also failed: {retry_error}")
                        raise retry_error
                # Handle customer_id constraint
                elif 'customer_id' in error_str and ('not null' in error_str or 'null value' in error_str):
                    logger.warning(f"Insert failed due to customer_id constraint, retrying without it: {insert_error}")
                    statement_data_to_insert.pop('customer_id', None)
                    try:
                        self.supabase.table('bank_statements').insert([statement_data_to_insert]).execute()
                        logger.info(f"Stored bank statement without customer_id (retry): {statement_id}")
                    except Exception as retry_error:
                        logger.error(f"Retry insert also failed: {retry_error}")
                        raise retry_error
                else:
                    logger.error(f"Error inserting bank statement: {insert_error}", exc_info=True)
                    logger.error(f"Statement data keys: {list(statement_data.keys())}")
                    raise insert_error

            # Update document status to success
            if document_id:
                try:
                    from database.document_storage import DocumentStorage
                    doc_storage = DocumentStorage()
                    doc_storage._update_document_status(document_id, 'success')
                except Exception as e:
                    logger.warning(f"Could not update document status: {e}")

            return document_id or statement_id

        except Exception as e:
            logger.error(f"Error storing bank statement: {e}", exc_info=True)
            if document_id:
                try:
                    from database.document_storage import DocumentStorage
                    doc_storage = DocumentStorage()
                    doc_storage._update_document_status(document_id, 'failed')
                except Exception:
                    pass
            return None

