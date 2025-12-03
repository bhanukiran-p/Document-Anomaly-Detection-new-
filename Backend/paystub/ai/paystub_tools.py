"""
Paystub Data Access Tools for AI Agent
Provides tools for the AI agent to query historical data, employee info, etc.
Completely independent from other document type tools
"""

import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PaystubDataAccessTools:
    """
    Tools for accessing paystub-related data for AI fraud analysis
    Separate from money order, check, and bank statement tools
    """

    def __init__(self, use_mock=False):
        """
        Initialize data access tools

        Args:
            use_mock: If True, use mock data. If False, use real database
        """
        self.mock_mode = use_mock
        self.employee_storage = None

        if not use_mock:
            try:
                # Use local paystub database module
                from ..database.paystub_customer_storage import PaystubCustomerStorage
                self.employee_storage = PaystubCustomerStorage()
                logger.info("Initialized PaystubDataAccessTools with database connection")
            except Exception as e:
                logger.warning(f"Failed to initialize database connection: {e}. Using mock mode.")
                self.mock_mode = True
        else:
            logger.info("Initialized PaystubDataAccessTools in mock mode")

    def get_employee_history(self, employee_name: str) -> Dict:
        """
        Get employee history by employee name

        Args:
            employee_name: Name of the employee

        Returns:
            Employee history dict with fraud counts, escalations, etc.
        """
        if self.mock_mode or not self.employee_storage:
            return self._get_mock_employee_history(employee_name)

        # Use real database
        return self.employee_storage.get_employee_history(employee_name)

    def get_similar_fraud_cases(self, company_name: str, amount: float, fraud_score: float) -> List[Dict]:
        """
        Find similar fraud cases from historical data

        Args:
            company_name: Company name
            amount: Paystub amount (net pay)
            fraud_score: ML fraud score

        Returns:
            List of similar fraud cases
        """
        if self.mock_mode:
            return self._get_mock_similar_cases(company_name, amount, fraud_score)

        # TODO: Query historical fraud cases
        return []

    def check_duplicate(self, employee_name: str, pay_date: str, pay_period_start: str) -> bool:
        """
        Check if this paystub has been submitted before

        Args:
            employee_name: Employee name
            pay_date: Pay date
            pay_period_start: Pay period start date

        Returns:
            True if duplicate found, False otherwise
        """
        if self.mock_mode or not self.employee_storage:
            return False  # Mock: no duplicates

        # Use real database
        return self.employee_storage.check_duplicate_paystub(employee_name, pay_date, pay_period_start)

    def get_company_fraud_stats(self, company_name: str) -> Dict:
        """
        Get fraud statistics for a specific company

        Args:
            company_name: Company name

        Returns:
            Stats dict with fraud rate, common patterns, etc.
        """
        if self.mock_mode:
            return self._get_mock_company_stats(company_name)

        # TODO: Query aggregated fraud stats
        return {}

    def get_amount_risk_profile(self, amount: float) -> str:
        """
        Get risk profile for a given amount

        Args:
            amount: Paystub net pay amount

        Returns:
            Risk profile string (LOW, MEDIUM, HIGH)
        """
        if amount < 1000:
            return "LOW"
        elif amount < 5000:
            return "MEDIUM"
        elif amount < 10000:
            return "MEDIUM-HIGH"
        elif amount < 50000:
            return "HIGH"
        else:
            return "CRITICAL"

    # === MOCK DATA METHODS ===

    def _get_mock_employee_history(self, employee_name: str) -> Dict:
        """Mock employee history data"""
        # Simulate some employees with history
        mock_employees = {
            'JOHN DOE': {
                'employee_id': 'EMP_PS_001',
                'has_fraud_history': True,
                'fraud_count': 2,
                'escalate_count': 0,
                'last_recommendation': 'REJECT',
                'last_analysis_date': '2025-11-15',
                'total_paystubs': 5
            },
            'JANE SMITH': {
                'employee_id': 'EMP_PS_002',
                'has_fraud_history': False,
                'fraud_count': 0,
                'escalate_count': 1,
                'last_recommendation': 'ESCALATE',
                'last_analysis_date': '2025-10-20',
                'total_paystubs': 3
            },
            'CLEAN EMPLOYEE': {
                'employee_id': 'EMP_PS_003',
                'has_fraud_history': False,
                'fraud_count': 0,
                'escalate_count': 0,
                'last_recommendation': 'APPROVE',
                'last_analysis_date': '2025-11-01',
                'total_paystubs': 10
            }
        }

        employee_upper = employee_name.upper() if employee_name else ''
        return mock_employees.get(employee_upper, {
            'employee_id': None,
            'has_fraud_history': False,
            'fraud_count': 0,
            'escalate_count': 0,
            'last_recommendation': None,
            'last_analysis_date': None,
            'total_paystubs': 0
        })

    def _get_mock_similar_cases(self, company_name: str, amount: float, fraud_score: float) -> List[Dict]:
        """Mock similar fraud cases"""
        cases = []

        # If high fraud score, show similar cases
        if fraud_score > 0.7:
            cases.append({
                'case_id': 'FRAUD_PS_001',
                'company_name': company_name,
                'amount': amount * 1.1,
                'fraud_score': 0.92,
                'outcome': 'REJECTED',
                'reason': 'Net pay > Gross pay, missing tax withholdings'
            })

        if fraud_score > 0.5:
            cases.append({
                'case_id': 'FRAUD_PS_002',
                'company_name': company_name,
                'amount': amount * 0.9,
                'fraud_score': 0.68,
                'outcome': 'ESCALATED',
                'reason': 'Round number amounts, suspicious patterns'
            })

        return cases

    def _get_mock_company_stats(self, company_name: str) -> Dict:
        """Mock company fraud statistics"""
        stats = {
            'ACME Corporation': {
                'total_paystubs_processed': 850,
                'fraud_rate': 0.05,  # 5%
                'average_fraud_score': 0.20,
                'common_fraud_patterns': [
                    'Missing tax withholdings',
                    'Round number amounts',
                    'Future-dated paystubs'
                ]
            },
            'Tech Solutions Inc': {
                'total_paystubs_processed': 620,
                'fraud_rate': 0.03,  # 3%
                'average_fraud_score': 0.18,
                'common_fraud_patterns': [
                    'Net pay inconsistencies',
                    'Missing critical fields',
                    'YTD inconsistencies'
                ]
            }
        }

        return stats.get(company_name, {
            'total_paystubs_processed': 0,
            'fraud_rate': 0.0,
            'average_fraud_score': 0.0,
            'common_fraud_patterns': []
        })

    def format_employee_summary(self, employee_info: Dict) -> str:
        """Format employee info for AI prompt"""
        if not employee_info or not employee_info.get('employee_id'):
            return "New employee - no prior history"

        summary = f"Employee ID: {employee_info.get('employee_id')}\n"
        summary += f"Total Paystubs: {employee_info.get('total_paystubs', 0)}\n"
        summary += f"Fraud History: {'Yes' if employee_info.get('has_fraud_history') else 'No'}\n"
        summary += f"Fraud Count: {employee_info.get('fraud_count', 0)}\n"
        summary += f"Escalation Count: {employee_info.get('escalate_count', 0)}\n"

        if employee_info.get('last_recommendation'):
            summary += f"Last Decision: {employee_info.get('last_recommendation')}\n"

        return summary


