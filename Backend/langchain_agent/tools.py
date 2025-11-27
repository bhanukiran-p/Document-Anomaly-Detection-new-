"""
Custom Tools for LangChain Fraud Analysis Agent
Provides tools to access CSV data, customer history, and fraud patterns
"""

import os
import pandas as pd
from typing import Dict, List, Optional
from langchain_core.tools import tool
from .result_storage import ResultStorage


class DataAccessTools:
    """
    Tools for accessing CSV data for fraud analysis
    """

    def __init__(self,
                 ml_scores_path: str,
                 customer_history_path: str,
                 fraud_cases_path: str,
                 training_data_path: str = 'ml_models/training_data.csv',
                 results_storage_dir: str = '/Users/hareenedla/Hareen/Document-Anomaly-Detection-new--Testing/Backend/analysis_results'):
        """
        Initialize data access tools

        Args:
            ml_scores_path: Path to ML scores CSV
            customer_history_path: Path to customer history CSV
            fraud_cases_path: Path to fraud cases CSV
            training_data_path: Path to training dataset CSV
            results_storage_dir: Directory for stored analysis results
        """
        self.ml_scores_path = ml_scores_path
        self.customer_history_path = customer_history_path
        self.fraud_cases_path = fraud_cases_path
        self.training_data_path = training_data_path

        # Load CSV files (if they exist)
        self.ml_scores_df = self._load_csv(ml_scores_path)
        self.customer_history_df = self._load_csv(customer_history_path)
        self.fraud_cases_df = self._load_csv(fraud_cases_path)
        self.training_data_df = self._load_csv(training_data_path)

        # Initialize result storage
        self.result_storage = ResultStorage(results_storage_dir)

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
        # Initialize history from CSV or empty
        if self.customer_history_df is not None:
            customer_data = self.customer_history_df[
                self.customer_history_df['customer_id'] == customer_id
            ]
            if not customer_data.empty:
                # Use CSV data
                num_transactions = len(customer_data)
                num_fraud = len(customer_data[customer_data.get('is_fraud', False) == True])
                avg_amount = customer_data['amount'].mean() if 'amount' in customer_data.columns else 0.0
                recent = customer_data.tail(5).to_dict('records')
                
                return {
                    'customer_id': customer_id,
                    'num_transactions': num_transactions,
                    'num_fraud_incidents': num_fraud,
                    'avg_amount': float(avg_amount),
                    'transactions': recent,
                    'fraud_rate': f"{(num_fraud/num_transactions*100):.1f}%" if num_transactions > 0 else "0%"
                }

        # If not in CSV, scan analysis results folder
        return self._scan_results_for_history(customer_id)

    def _scan_results_for_history(self, customer_id: str) -> Dict:
        """
        Scan stored analysis results for a customer's history
        """
        all_results = self.result_storage.get_all_stored_results()
        customer_txns = []
        
        for result in all_results:
            # Check extracted data for customer name/ID match
            extracted = result.get('extracted_data', {})
            normalized = result.get('normalized_data', {})
            
            # Check purchaser name (since we don't have IDs in money orders usually)
            purchaser = extracted.get('purchaser', '').upper()
            sender = normalized.get('sender_name', '').upper()
            target_id = customer_id.upper()
            
            if target_id in purchaser or target_id in sender:
                txn = {
                    'date': extracted.get('date', 'Unknown'),
                    'amount': normalized.get('amount_numeric', {}).get('value', 0),
                    'is_fraud': result.get('ai_analysis', {}).get('recommendation') == 'REJECT'
                }
                customer_txns.append(txn)

        if not customer_txns:
             return {
                'customer_id': customer_id,
                'num_transactions': 0,
                'num_fraud_incidents': 0,
                'avg_amount': 0.0,
                'transactions': [],
                'note': 'New customer - no history found'
            }

        # Calculate stats from found results
        num_transactions = len(customer_txns)
        num_fraud = len([t for t in customer_txns if t['is_fraud']])
        total_amount = sum(t['amount'] for t in customer_txns)
        avg_amount = total_amount / num_transactions if num_transactions > 0 else 0

        return {
            'customer_id': customer_id,
            'num_transactions': num_transactions,
            'num_fraud_incidents': num_fraud,
            'avg_amount': float(avg_amount),
            'transactions': customer_txns[:5], # Last 5
            'fraud_rate': f"{(num_fraud/num_transactions*100):.1f}%",
            'source': 'analysis_history'
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

    def get_training_dataset_patterns(self) -> Dict:
        """
        Analyze training dataset for fraud patterns and statistics

        Returns:
            Dictionary with pattern insights
        """
        if self.training_data_df is None or self.training_data_df.empty:
            return {
                'available': False,
                'message': 'Training dataset not available'
            }

        df = self.training_data_df

        # Total counts
        total_samples = len(df)
        fraud_samples = len(df[df['is_fraud'] == 1])
        legit_samples = len(df[df['is_fraud'] == 0])

        # Fraud type distribution
        fraud_type_counts = df[df['is_fraud'] == 1]['fraud_type'].value_counts().to_dict()

        # Calculate pattern frequencies (% of fraud cases)
        patterns = {}
        if fraud_samples > 0:
            for fraud_type, count in fraud_type_counts.items():
                patterns[fraud_type] = {
                    'count': int(count),
                    'percentage': round((count / fraud_samples) * 100, 1)
                }

        return {
            'available': True,
            'total_samples': int(total_samples),
            'fraud_samples': int(fraud_samples),
            'legitimate_samples': int(legit_samples),
            'fraud_rate': round((fraud_samples / total_samples) * 100, 1),
            'fraud_patterns': patterns
        }

    def format_training_patterns_summary(self) -> str:
        """
        Format training dataset patterns as readable string

        Returns:
            Formatted string summary
        """
        patterns = self.get_training_dataset_patterns()

        if not patterns['available']:
            return "Training dataset patterns not available"

        summary = f"""Training Dataset Statistics ({patterns['total_samples']} samples):
- Fraud Cases: {patterns['fraud_samples']} ({patterns['fraud_rate']}%)
- Legitimate Cases: {patterns['legitimate_samples']} ({100 - patterns['fraud_rate']:.1f}%)

Fraud Pattern Distribution:
"""
        for fraud_type, stats in sorted(patterns['fraud_patterns'].items(),
                                       key=lambda x: x[1]['percentage'],
                                       reverse=True):
            summary += f"  • {fraud_type.replace('_', ' ').title()}: {stats['count']} cases ({stats['percentage']}%)\n"

        return summary

    def search_stored_analyses(self, issuer: str = None, amount_range: tuple = None, limit: int = 5) -> List[Dict]:
        """
        Search stored analysis results for similar past cases

        Args:
            issuer: Issuer name to filter by (optional)
            amount_range: (min, max) amount range (optional)
            limit: Maximum number of results

        Returns:
            List of similar past analyses
        """
        if amount_range:
            # Search by amount range
            min_amt, max_amt = amount_range
            results = self.result_storage.search_by_amount_range(min_amt, max_amt, limit=limit * 2)

            # Further filter by issuer if provided
            if issuer:
                filtered = []
                for result in results:
                    extracted_issuer = result.get('extracted_data', {}).get('issuer', '')
                    normalized_issuer = result.get('normalized_data', {}).get('issuer_name', '')
                    if issuer.lower() in extracted_issuer.lower() or issuer.lower() in normalized_issuer.lower():
                        filtered.append(result)
                results = filtered[:limit]
            else:
                results = results[:limit]
        elif issuer:
            # Search by issuer only
            results = self.result_storage.search_by_issuer(issuer, limit=limit)
        else:
            # Get recent results
            results = self.result_storage.get_recent_results(limit=limit)

        return results

    def format_past_analyses_summary(self, past_analyses: List[Dict]) -> str:
        """
        Format past analysis results as readable string

        Args:
            past_analyses: List of past analysis dictionaries

        Returns:
            Formatted string summary
        """
        if not past_analyses:
            return "No similar past analyses found"

        summary = f"Found {len(past_analyses)} similar past analysis case(s):\n\n"

        for i, analysis in enumerate(past_analyses, 1):
            # Extract key fields
            ml_analysis = analysis.get('ml_analysis', {})
            ai_analysis = analysis.get('ai_analysis', {})
            extracted_data = analysis.get('extracted_data', {})

            fraud_score = ml_analysis.get('fraud_risk_score', 0)
            risk_level = ml_analysis.get('risk_level', 'UNKNOWN')
            recommendation = ai_analysis.get('recommendation', 'N/A')
            issuer = extracted_data.get('issuer', 'N/A')
            amount = extracted_data.get('amount', 'N/A')

            summary += f"{i}. Issuer: {issuer} | Amount: {amount}\n"
            summary += f"   Risk: {fraud_score:.1%} ({risk_level}) | Recommendation: {recommendation}\n"

            # Include key indicators if available
            indicators = ai_analysis.get('key_indicators', [])
            if indicators:
                summary += f"   Indicators: {', '.join(indicators[:3])}\n"

            summary += "\n"

        return summary

    def analyze_fraud_pattern_frequency(self, fraud_type: str) -> Dict:
        """
        Analyze frequency of specific fraud pattern in training dataset

        Args:
            fraud_type: Type of fraud to analyze

        Returns:
            Dictionary with frequency statistics
        """
        if self.training_data_df is None or self.training_data_df.empty:
            return {'available': False, 'message': 'Training data not available'}

        df = self.training_data_df

        # Count fraud cases with this pattern
        fraud_cases = df[df['is_fraud'] == 1]
        total_fraud = len(fraud_cases)
        pattern_count = len(fraud_cases[fraud_cases['fraud_type'] == fraud_type])

        if total_fraud == 0:
            return {'available': False, 'message': 'No fraud cases in training data'}

        return {
            'available': True,
            'fraud_type': fraud_type,
            'occurrences': int(pattern_count),
            'percentage': round((pattern_count / total_fraud) * 100, 1),
            'total_fraud_cases': int(total_fraud)
        }


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
