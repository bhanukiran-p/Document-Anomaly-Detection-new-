"""
Paystub Customer/Employee Storage
Handles employee history tracking for paystubs
Completely independent from other document type customer storage
"""

import logging
from typing import Dict, Optional
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class PaystubCustomerStorage:
    """
    Manages paystub employee history in Supabase
    Tracks fraud counts, escalation counts, and employee information
    """

    def __init__(self):
        """Initialize with Supabase client"""
        try:
            self.supabase = get_supabase()
            logger.info("Initialized PaystubCustomerStorage with Supabase connection")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None

    def get_employee_history(self, employee_name: str) -> Dict:
        """
        Get employee history by employee name
        Matches money order logic: queries ALL records and finds MAX escalate_count

        Args:
            employee_name: Name of the employee

        Returns:
            Employee history dict with fraud_count, escalate_count, etc.
            Uses MAX escalate_count across all records (like money orders)
        """
        if not self.supabase or not employee_name:
            return {}

        try:
            # Query ALL records for this employee name (like money orders)
            # Don't use .limit(1) - we need ALL records to find MAX escalate_count
            response = self.supabase.table('paystub_customers').select('*').eq('name', employee_name).execute()

            if response.data and len(response.data) > 0:
                # Get ALL records for this employee
                all_records = response.data
                logger.info(f"[EMPLOYEE_LOOKUP] Found {len(all_records)} record(s) for employee: {employee_name}")
                
                # Find the record with MAX escalate_count (like money orders)
                # Sort by escalate_count DESC, then created_at DESC
                sorted_records = sorted(
                    all_records,
                    key=lambda x: (
                        x.get('escalate_count', 0) or 0,
                        x.get('created_at', '') or ''
                    ),
                    reverse=True
                )
                
                record_with_max_escalate = sorted_records[0]
                max_escalate_count = record_with_max_escalate.get('escalate_count', 0) or 0
                
                # Get the latest record for other fields (customer_id, etc.)
                latest_record = sorted(all_records, key=lambda x: x.get('created_at', '') or '', reverse=True)[0]
                employee_id = latest_record.get('customer_id')
                
                # Calculate max fraud_count across all records
                max_fraud_count = max((r.get('fraud_count', 0) or 0) for r in all_records)
                
                logger.info(f"[EMPLOYEE_LOOKUP] Record with max escalate_count: {max_escalate_count}")
                logger.info(f"[EMPLOYEE_LOOKUP] Using employee_id: {employee_id}")
                logger.info(f"[EMPLOYEE_LOOKUP] Max fraud_count: {max_fraud_count}")
                
                return {
                    'employee_id': employee_id,  # Use customer_id as employee_id
                    'name': employee_name,
                    'has_fraud_history': record_with_max_escalate.get('has_fraud_history', False) or max_fraud_count > 0,
                    'fraud_count': max_fraud_count,
                    'escalate_count': max_escalate_count,  # MAX escalate_count across all records
                    'last_recommendation': latest_record.get('last_recommendation'),
                    'last_analysis_date': latest_record.get('last_analysis_date'),
                    'total_paystubs': sum((r.get('total_paystubs', 0) or 0) for r in all_records)
                }
            else:
                # New employee
                logger.info(f"[EMPLOYEE_LOOKUP] No records found for employee: {employee_name} (new employee)")
                return {
                    'employee_id': None,
                    'name': employee_name,
                    'has_fraud_history': False,
                    'fraud_count': 0,
                    'escalate_count': 0,
                    'last_recommendation': None,
                    'last_analysis_date': None,
                    'total_paystubs': 0
                }
        except Exception as e:
            logger.error(f"Error getting employee history: {e}", exc_info=True)
            return {}

    def check_duplicate_paystub(self, employee_name: str, pay_date: str, pay_period_start: str) -> bool:
        """
        Check if this paystub has been submitted before

        Args:
            employee_name: Employee name
            pay_date: Pay date (can be string or date)
            pay_period_start: Pay period start date (can be string or date)

        Returns:
            True if duplicate found, False otherwise
        """
        if not self.supabase or not employee_name:
            return False

        try:
            # Normalize dates to strings for comparison
            # Handle various date formats
            from datetime import datetime
            
            def normalize_date(date_val):
                """Normalize date to YYYY-MM-DD format"""
                if not date_val:
                    return None
                if isinstance(date_val, str):
                    # Try to parse common date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                        try:
                            dt = datetime.strptime(date_val, fmt)
                            return dt.strftime('%Y-%m-%d')
                        except:
                            continue
                    # If parsing fails, return as-is (might be already in correct format)
                    return date_val
                elif hasattr(date_val, 'strftime'):
                    # datetime object
                    return date_val.strftime('%Y-%m-%d')
                return str(date_val)

            pay_date_normalized = normalize_date(pay_date)
            pay_period_start_normalized = normalize_date(pay_period_start)

            if not pay_date_normalized or not pay_period_start_normalized:
                logger.warning(f"Cannot check duplicate - missing dates: pay_date={pay_date}, pay_period_start={pay_period_start}")
                return False

            # Query paystubs table for duplicate
            # Check by employee_name + pay_date + pay_period_start
            response = self.supabase.table('paystubs').select('paystub_id').eq('employee_name', employee_name).eq('pay_date', pay_date_normalized).eq('pay_period_start', pay_period_start_normalized).execute()

            if response.data and len(response.data) > 0:
                # Found existing paystub with same employee, pay date, and period
                logger.info(f"Duplicate paystub detected for {employee_name}: pay_date={pay_date_normalized}, period_start={pay_period_start_normalized}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False

    def update_employee_fraud_status(
        self,
        employee_name: str,
        recommendation: str,
        paystub_id: Optional[str] = None
    ) -> bool:
        """
        Update employee fraud status based on recommendation

        Args:
            employee_name: Employee name
            recommendation: AI recommendation (APPROVE, REJECT, ESCALATE)
            paystub_id: Paystub ID if available

        Returns:
            True if update successful, False otherwise
        """
        if not self.supabase or not employee_name:
            return False

        try:
            # Get existing employee or create new
            employee_history = self.get_employee_history(employee_name)
            employee_id = employee_history.get('employee_id')

            from datetime import datetime
            now = datetime.utcnow().isoformat()

            update_data = {
                'last_recommendation': recommendation,
                'last_analysis_date': now,
                'updated_at': now
            }

            # Update counts based on recommendation
            if recommendation == 'REJECT':
                update_data['fraud_count'] = employee_history.get('fraud_count', 0) + 1
                update_data['has_fraud_history'] = True
            elif recommendation == 'ESCALATE':
                update_data['escalate_count'] = employee_history.get('escalate_count', 0) + 1
            
            # Increment total paystubs
            update_data['total_paystubs'] = employee_history.get('total_paystubs', 0) + 1

            if employee_id:
                # Update existing employee
                self.supabase.table('paystub_customers').update(update_data).eq('customer_id', employee_id).execute()
                logger.info(f"Updated employee {employee_name} fraud status")
            else:
                # Create new employee
                from uuid import uuid4
                new_employee = {
                    'customer_id': str(uuid4()),
                    'name': employee_name,
                    'has_fraud_history': recommendation == 'REJECT',
                    'fraud_count': 1 if recommendation == 'REJECT' else 0,
                    'escalate_count': 1 if recommendation == 'ESCALATE' else 0,
                    'last_recommendation': recommendation,
                    'last_analysis_date': now,
                    'total_paystubs': 1,
                    'created_at': now,
                    'updated_at': now
                }
                self.supabase.table('paystub_customers').insert([new_employee]).execute()
                logger.info(f"Created new employee {employee_name}")

            return True
        except Exception as e:
            logger.error(f"Error updating employee fraud status: {e}")
            return False

