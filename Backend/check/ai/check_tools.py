"""
Check Data Access Tools for AI Agent
Provides tools for the AI agent to query historical data, customer info, etc.
"""

import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CheckDataAccessTools:
    """
    Tools for accessing check-related data for AI fraud analysis
    Separate from money order tools
    """

    def __init__(self, use_mock=False):
        """
        Initialize data access tools

        Args:
            use_mock: If True, use mock data. If False, use real database
        """
        self.mock_mode = use_mock
        self.customer_storage = None

        if not use_mock:
            try:
                # Use local check database module
                from ..database.check_customer_storage import CheckCustomerStorage
                self.customer_storage = CheckCustomerStorage()
                logger.info("Initialized CheckDataAccessTools with database connection")
            except Exception as e:
                logger.warning(f"Failed to initialize database connection: {e}. Using mock mode.")
                self.mock_mode = True
        else:
            logger.info("Initialized CheckDataAccessTools in mock mode")

    def get_customer_history(self, payer_name: str) -> Dict:
        """
        Get customer history by payer name

        Args:
            payer_name: Name of the payer/customer

        Returns:
            Customer history dict with fraud counts, escalations, etc.
        """
        if self.mock_mode or not self.customer_storage:
            return self._get_mock_customer_history(payer_name)

        # Use real database
        return self.customer_storage.get_customer_history(payer_name)

    def get_similar_fraud_cases(self, bank_name: str, amount: float, fraud_score: float) -> List[Dict]:
        """
        Find similar fraud cases from historical data

        Args:
            bank_name: Bank name
            amount: Check amount
            fraud_score: ML fraud score

        Returns:
            List of similar fraud cases
        """
        if self.mock_mode:
            return self._get_mock_similar_cases(bank_name, amount, fraud_score)

        # TODO: Query historical fraud cases
        return []

    def check_duplicate(self, check_number: str, payer_name: str) -> bool:
        """
        Check if this check has been submitted before

        Args:
            check_number: Check number
            payer_name: Payer name

        Returns:
            True if duplicate found, False otherwise
        """
        if self.mock_mode or not self.customer_storage:
            return False  # Mock: no duplicates

        # Use real database
        return self.customer_storage.check_duplicate_check(check_number, payer_name)

    def get_bank_fraud_stats(self, bank_name: str) -> Dict:
        """
        Get fraud statistics for a specific bank

        Args:
            bank_name: Bank name

        Returns:
            Stats dict with fraud rate, common patterns, etc.
        """
        if self.mock_mode:
            return self._get_mock_bank_stats(bank_name)

        # TODO: Query aggregated fraud stats
        return {}

    def get_amount_risk_profile(self, amount: float) -> str:
        """
        Get risk profile for a given amount

        Args:
            amount: Check amount

        Returns:
            Risk profile string (LOW, MEDIUM, HIGH)
        """
        if amount < 100:
            return "LOW"
        elif amount < 1000:
            return "MEDIUM"
        elif amount < 5000:
            return "MEDIUM-HIGH"
        elif amount < 10000:
            return "HIGH"
        else:
            return "CRITICAL"

    # === MOCK DATA METHODS ===

    def _get_mock_customer_history(self, payer_name: str) -> Dict:
        """Mock customer history data"""
        # Simulate some customers with history
        mock_customers = {
            'JOHN DOE': {
                'customer_id': 'CUST_CHECK_001',
                'has_fraud_history': True,
                'fraud_count': 2,
                'escalate_count': 0,
                'last_recommendation': 'REJECT',
                'last_analysis_date': '2025-11-15',
                'total_transactions': 5
            },
            'JANE SMITH': {
                'customer_id': 'CUST_CHECK_002',
                'has_fraud_history': False,
                'fraud_count': 0,
                'escalate_count': 1,
                'last_recommendation': 'ESCALATE',
                'last_analysis_date': '2025-10-20',
                'total_transactions': 3
            },
            'CLEAN CUSTOMER': {
                'customer_id': 'CUST_CHECK_003',
                'has_fraud_history': False,
                'fraud_count': 0,
                'escalate_count': 0,
                'last_recommendation': 'APPROVE',
                'last_analysis_date': '2025-11-01',
                'total_transactions': 10
            }
        }

        payer_upper = payer_name.upper() if payer_name else ''
        return mock_customers.get(payer_upper, {
            'customer_id': None,
            'has_fraud_history': False,
            'fraud_count': 0,
            'escalate_count': 0,
            'last_recommendation': None,
            'last_analysis_date': None,
            'total_transactions': 0
        })

    def _get_mock_similar_cases(self, bank_name: str, amount: float, fraud_score: float) -> List[Dict]:
        """Mock similar fraud cases"""
        cases = []

        # If high fraud score, show similar cases
        if fraud_score > 0.7:
            cases.append({
                'case_id': 'FRAUD_001',
                'bank_name': bank_name,
                'amount': amount * 1.1,
                'fraud_score': 0.92,
                'outcome': 'REJECTED',
                'reason': 'Missing signature, suspicious amount'
            })

        if fraud_score > 0.5:
            cases.append({
                'case_id': 'FRAUD_002',
                'bank_name': bank_name,
                'amount': amount * 0.9,
                'fraud_score': 0.68,
                'outcome': 'ESCALATED',
                'reason': 'High amount, new customer'
            })

        return cases

    def _get_mock_bank_stats(self, bank_name: str) -> Dict:
        """Mock bank fraud statistics"""
        stats = {
            'Bank of America': {
                'total_checks_processed': 1250,
                'fraud_rate': 0.08,  # 8%
                'average_fraud_score': 0.25,
                'common_fraud_patterns': [
                    'Missing signatures',
                    'Altered amounts',
                    'Duplicate submissions'
                ]
            },
            'Chase': {
                'total_checks_processed': 980,
                'fraud_rate': 0.06,  # 6%
                'average_fraud_score': 0.22,
                'common_fraud_patterns': [
                    'Future-dated checks',
                    'Invalid routing numbers',
                    'Suspicious amounts'
                ]
            }
        }

        return stats.get(bank_name, {
            'total_checks_processed': 0,
            'fraud_rate': 0.0,
            'average_fraud_score': 0.0,
            'common_fraud_patterns': []
        })

    def format_customer_summary(self, customer_info: Dict) -> str:
        """Format customer info for AI prompt"""
        if not customer_info or not customer_info.get('customer_id'):
            return "New customer - no prior history"

        summary = f"Customer ID: {customer_info.get('customer_id')}\n"
        summary += f"Total Transactions: {customer_info.get('total_transactions', 0)}\n"
        summary += f"Fraud History: {'Yes' if customer_info.get('has_fraud_history') else 'No'}\n"
        summary += f"Fraud Count: {customer_info.get('fraud_count', 0)}\n"
        summary += f"Escalation Count: {customer_info.get('escalate_count', 0)}\n"

        if customer_info.get('last_recommendation'):
            summary += f"Last Decision: {customer_info.get('last_recommendation')}\n"

        return summary
