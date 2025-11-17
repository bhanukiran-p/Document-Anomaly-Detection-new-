"""
Custom Tools for LangChain Fraud Analysis Agent
Provides tools to access CSV data, customer history, and fraud patterns
"""

import os
import pandas as pd
from typing import Dict, List, Optional
from langchain.tools import tool


class DataAccessTools:
    """
    Tools for accessing CSV data for fraud analysis
    """

    def __init__(self,
                 ml_scores_path: str,
                 customer_history_path: str,
                 fraud_cases_path: str):
        """
        Initialize data access tools

        Args:
            ml_scores_path: Path to ML scores CSV
            customer_history_path: Path to customer history CSV
            fraud_cases_path: Path to fraud cases CSV
        """
        self.ml_scores_path = ml_scores_path
        self.customer_history_path = customer_history_path
        self.fraud_cases_path = fraud_cases_path

        # Load CSV files (if they exist)
        self.ml_scores_df = self._load_csv(ml_scores_path)
        self.customer_history_df = self._load_csv(customer_history_path)
        self.fraud_cases_df = self._load_csv(fraud_cases_path)

    def _load_csv(self, path: str) -> Optional[pd.DataFrame]:
        """Load CSV file if it exists"""
        if os.path.exists(path):
            try:
                return pd.read_csv(path)
            except Exception as e:
                print(f"Warning: Could not load {path}: {e}")
                return None
        return None

    def get_customer_history(self, customer_id: str) -> Dict:
        """
        Get transaction history for a customer

        Args:
            customer_id: Customer ID to lookup

        Returns:
            Dictionary with customer history
        """
        if self.customer_history_df is None:
            return {
                'customer_id': customer_id,
                'num_transactions': 0,
                'num_fraud_incidents': 0,
                'avg_amount': 0.0,
                'transactions': []
            }

        # Filter transactions for this customer
        customer_data = self.customer_history_df[
            self.customer_history_df['customer_id'] == customer_id
        ]

        if customer_data.empty:
            return {
                'customer_id': customer_id,
                'num_transactions': 0,
                'num_fraud_incidents': 0,
                'avg_amount': 0.0,
                'transactions': [],
                'note': 'New customer - no history found'
            }

        # Calculate statistics
        num_transactions = len(customer_data)
        num_fraud = len(customer_data[customer_data.get('is_fraud', False) == True])
        avg_amount = customer_data['amount'].mean() if 'amount' in customer_data.columns else 0.0

        # Get recent transactions
        recent = customer_data.tail(5).to_dict('records')

        return {
            'customer_id': customer_id,
            'num_transactions': num_transactions,
            'num_fraud_incidents': num_fraud,
            'avg_amount': float(avg_amount),
            'transactions': recent,
            'fraud_rate': f"{(num_fraud/num_transactions*100):.1f}%" if num_transactions > 0 else "0%"
        }

    def search_similar_fraud_cases(self,
                                   issuer: Optional[str] = None,
                                   amount_range: Optional[tuple] = None,
                                   limit: int = 5) -> List[Dict]:
        """
        Search for similar fraud cases in the database

        Args:
            issuer: Issuer name to filter by
            amount_range: (min, max) amount range
            limit: Maximum number of results

        Returns:
            List of similar fraud cases
        """
        if self.fraud_cases_df is None:
            return []

        df = self.fraud_cases_df.copy()

        # Filter by issuer if provided
        if issuer and 'issuer' in df.columns:
            df = df[df['issuer'].str.contains(issuer, case=False, na=False)]

        # Filter by amount range if provided
        if amount_range and 'amount' in df.columns:
            min_amt, max_amt = amount_range
            df = df[(df['amount'] >= min_amt) & (df['amount'] <= max_amt)]

        # Limit results
        df = df.head(limit)

        return df.to_dict('records')

    def get_ml_score_by_document_id(self, document_id: str) -> Optional[Dict]:
        """
        Get ML score for a specific document

        Args:
            document_id: Document ID to lookup

        Returns:
            Dictionary with ML score data or None
        """
        if self.ml_scores_df is None:
            return None

        doc_data = self.ml_scores_df[
            self.ml_scores_df['document_id'] == document_id
        ]

        if doc_data.empty:
            return None

        return doc_data.iloc[0].to_dict()

    def format_customer_history_summary(self, customer_id: str) -> str:
        """
        Format customer history as a readable string

        Args:
            customer_id: Customer ID

        Returns:
            Formatted string summary
        """
        history = self.get_customer_history(customer_id)

        if history['num_transactions'] == 0:
            return f"Customer {customer_id}: New customer with no prior transaction history."

        summary = f"""Customer {customer_id} Transaction History:
- Total Transactions: {history['num_transactions']}
- Fraud Incidents: {history['num_fraud_incidents']} ({history['fraud_rate']})
- Average Transaction Amount: ${history['avg_amount']:.2f}

Recent Transactions:
"""
        for i, txn in enumerate(history['transactions'], 1):
            fraud_flag = " [FRAUD]" if txn.get('is_fraud', False) else ""
            summary += f"{i}. ${txn.get('amount', 0):.2f} - {txn.get('date', 'N/A')}{fraud_flag}\n"

        return summary

    def format_fraud_cases_summary(self, cases: List[Dict]) -> str:
        """
        Format similar fraud cases as a readable string

        Args:
            cases: List of fraud case dictionaries

        Returns:
            Formatted string summary
        """
        if not cases:
            return "No similar fraud cases found in database."

        summary = f"Found {len(cases)} similar fraud case(s):\n\n"
        for i, case in enumerate(cases, 1):
            summary += f"{i}. Issuer: {case.get('issuer', 'N/A')} | "
            summary += f"Amount: ${case.get('amount', 0):.2f} | "
            summary += f"Pattern: {case.get('fraud_type', 'Unknown')}\n"
            summary += f"   Description: {case.get('description', 'N/A')}\n\n"

        return summary


# Create LangChain tool functions

@tool
def get_customer_transaction_history(customer_id: str) -> str:
    """
    Get transaction history for a customer to assess fraud risk patterns.
    Returns formatted string with transaction history and fraud statistics.

    Args:
        customer_id: The customer ID to look up
    """
    # This will be injected with actual data access tools
    return f"Customer history lookup for {customer_id} - tool needs initialization"


@tool
def search_fraud_database(issuer: str, amount: float) -> str:
    """
    Search database for similar fraud cases based on issuer and amount.
    Returns formatted string with matching fraud patterns.

    Args:
        issuer: Money order issuer name
        amount: Transaction amount
    """
    return f"Fraud database search for {issuer} ${amount} - tool needs initialization"
