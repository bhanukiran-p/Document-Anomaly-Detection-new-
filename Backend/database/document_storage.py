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
        """Get or create money order customer, return customer_id"""
        if not customer_data:
            return None

        name = customer_data.get('name')
        if not name:
            return None

        try:
            name = self._safe_string(name)
            if not name:
                return None

            # Check if customer exists with same name and address (for exact match)
            address = self._safe_string(customer_data.get('address'))
            payee_name = self._safe_string(customer_data.get('payee_name'))

            query = self.supabase.table('money_order_customers').select('customer_id').eq('name', name)

            if address:
                query = query.eq('address', address)

            response = query.execute()

            if response.data:
                logger.info(f"Found existing money order customer: {name}")
                return response.data[0]['customer_id']

            # Create new customer
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
                'email': self._safe_string(customer_data.get('email'))
            }

            self.supabase.table('money_order_customers').insert([new_customer]).execute()
            logger.info(f"Created new money order customer: {name} ({customer_id})")
            return customer_id

        except Exception as e:
            logger.warning(f"Error getting/creating money order customer: {e}")
            return None

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

            # Prepare bank statement data
            statement_data = {
                'statement_id': str(uuid.uuid4()),
                'document_id': document_id,
                'account_holder_name': self._safe_string(extracted.get('account_holder')),
                'account_holder_address': self._safe_string(extracted.get('account_holder_address')),
                'account_holder_city': None,
                'account_holder_state': None,
                'account_holder_zip': None,
                'bank_name': self._safe_string(extracted.get('bank_name')),
                'institution_id': institution_id,
                'bank_address': self._safe_string(extracted.get('bank_address')),
                'bank_city': None,
                'bank_state': None,
                'bank_zip': None,
                'routing_number': self._safe_string(extracted.get('routing_number')),
                'account_number': self._safe_string(extracted.get('account_number')),
                'account_type': self._safe_string(extracted.get('account_type')),
                'currency': self._safe_string(extracted.get('currency', 'USD')),
                'statement_period': self._safe_string(extracted.get('statement_period_start')),
                'opening_balance': self._parse_amount(extracted.get('opening_balance')),
                'ending_balance': self._parse_amount(extracted.get('closing_balance')),
                'available_balance': self._parse_amount(extracted.get('available_balance')),
                'total_transactions': len(transactions),
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
                'timestamp': datetime.utcnow().isoformat()
            }

            # Insert bank statement record
            self.supabase.table('bank_statements').insert([statement_data]).execute()
            logger.info(f"Stored bank statement: {statement_data['statement_id']}")

            # Update document status
            self._update_document_status(document_id, 'success')

            return document_id

        except Exception as e:
            logger.error(f"Error storing bank statement: {e}")
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

            # Prepare paystub data
            paystub_data = {
                'paystub_id': str(uuid.uuid4()),
                'document_id': document_id,
                'employee_name': self._safe_string(extracted.get('employee_name')),
                'employee_first_name': self._safe_string(extracted.get('employee_first_name')),
                'employee_last_name': self._safe_string(extracted.get('employee_last_name')),
                'employee_address': self._safe_string(extracted.get('employee_address')),
                'employee_id_number': self._safe_string(extracted.get('employee_id')),
                'employer_id': employer_id,
                'employer_name': self._safe_string(extracted.get('employer_name')),
                'employer_address': self._safe_string(extracted.get('employer_address')),
                'employer_city': self._safe_string(extracted.get('employer_city')),
                'employer_state': self._safe_string(extracted.get('employer_state')),
                'employer_zip': self._safe_string(extracted.get('employer_zip')),
                'employer_country': self._safe_string(extracted.get('employer_country', 'USA')),
                'employer_phone': self._safe_string(extracted.get('employer_phone')),
                'employer_email': self._safe_string(extracted.get('employer_email')),
                'pay_period_start': self._parse_date(extracted.get('pay_period_start')),
                'pay_period_end': self._parse_date(extracted.get('pay_period_end')),
                'pay_date': self._parse_date(extracted.get('pay_date')),
                'gross_pay': self._parse_amount(extracted.get('gross_pay')),
                'net_pay': self._parse_amount(extracted.get('net_pay')),
                'ytd_gross': self._parse_amount(extracted.get('ytd_gross')),
                'ytd_net': self._parse_amount(extracted.get('ytd_net')),
                'deductions': json.dumps(deductions),
                # ML Analysis results
                'fraud_risk_score': self._parse_amount(ml_analysis.get('fraud_risk_score')),
                'risk_level': self._safe_string(ml_analysis.get('risk_level')),
                'model_confidence': self._parse_amount(ml_analysis.get('model_confidence')),
                # AI Analysis results
                'ai_recommendation': self._safe_string(ai_analysis.get('recommendation')) if ai_analysis else None,
                # Anomaly data
                'anomaly_count': len(analysis_data.get('anomalies', [])),
                'top_anomalies': json.dumps(analysis_data.get('anomalies', [])[:5])
            }

            # Insert paystub record
            self.supabase.table('paystubs').insert([paystub_data]).execute()
            logger.info(f"Stored paystub: {paystub_data['paystub_id']}")

            # Update document status
            self._update_document_status(document_id, 'success')

            return document_id

        except Exception as e:
            logger.error(f"Error storing paystub: {e}")
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
            check_data = {
                'check_id': str(uuid.uuid4()),
                'document_id': document_id,
                'check_number': self._safe_string(extracted.get('check_number')),
                'amount': self._parse_amount(extracted.get('amount')),
                'check_date': self._parse_date(extracted.get('check_date')),
                'payer_name': self._safe_string(extracted.get('payer_name')),
                'payer_address': self._safe_string(extracted.get('payer_address')),
                'payee_name': self._safe_string(extracted.get('payee_name')),
                'bank_name': self._safe_string(extracted.get('bank_name')),
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
    """Store bank statement analysis to database"""
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
