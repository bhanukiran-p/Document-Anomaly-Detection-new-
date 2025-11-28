"""
Tools for Real-Time Transaction Analysis Agent
Provides access to transaction data, statistics, and insights
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


class TransactionAnalysisTools:
    """
    Tools for accessing and analyzing transaction data
    """

    def __init__(self, analysis_result: Optional[Dict[str, Any]] = None):
        """
        Initialize transaction analysis tools

        Args:
            analysis_result: Complete analysis result from fraud detector
        """
        self.analysis_result = analysis_result or {}
        self.transactions_df = None

        if analysis_result and 'transactions' in analysis_result:
            self.transactions_df = pd.DataFrame(analysis_result['transactions'])

    def update_analysis_result(self, analysis_result: Dict[str, Any]):
        """Update the analysis result"""
        self.analysis_result = analysis_result
        if 'transactions' in analysis_result:
            self.transactions_df = pd.DataFrame(analysis_result['transactions'])

    def get_top_transactions(self, limit: int = 3, fraud_only: bool = True) -> List[Dict]:
        """
        Get top transactions by fraud probability

        Args:
            limit: Number of transactions to return
            fraud_only: Whether to only return fraud transactions

        Returns:
            List of transaction dictionaries
        """
        if self.transactions_df is None or self.transactions_df.empty:
            return []

        df = self.transactions_df.copy()

        if fraud_only:
            df = df[df['is_fraud'] == 1]

        # Sort by fraud probability
        df = df.sort_values('fraud_probability', ascending=False)

        return df.head(limit).to_dict('records')

    def get_transaction_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive transaction statistics

        Returns:
            Dictionary with statistics
        """
        if self.transactions_df is None or self.transactions_df.empty:
            return {
                'total_transactions': 0,
                'fraud_count': 0,
                'legitimate_count': 0,
                'fraud_percentage': 0,
                'total_amount': 0,
                'fraud_amount': 0,
                'legitimate_amount': 0
            }

        df = self.transactions_df
        fraud_df = df[df['is_fraud'] == 1]
        legit_df = df[df['is_fraud'] == 0]

        return {
            'total_transactions': len(df),
            'fraud_count': len(fraud_df),
            'legitimate_count': len(legit_df),
            'fraud_percentage': (len(fraud_df) / len(df) * 100) if len(df) > 0 else 0,
            'total_amount': float(df['amount'].sum()),
            'fraud_amount': float(fraud_df['amount'].sum()) if len(fraud_df) > 0 else 0,
            'legitimate_amount': float(legit_df['amount'].sum()) if len(legit_df) > 0 else 0,
            'avg_amount': float(df['amount'].mean()),
            'median_amount': float(df['amount'].median()),
            'max_amount': float(df['amount'].max()),
            'min_amount': float(df['amount'].min())
        }

    def get_fraud_patterns(self) -> Dict[str, Any]:
        """
        Analyze and return fraud patterns

        Returns:
            Dictionary with fraud patterns
        """
        if self.transactions_df is None or self.transactions_df.empty:
            return {'patterns': [], 'total_patterns': 0}

        df = self.transactions_df
        fraud_df = df[df['is_fraud'] == 1]

        if len(fraud_df) == 0:
            return {'patterns': [], 'total_patterns': 0}

        patterns = []

        # High-value fraud
        high_value_threshold = fraud_df['amount'].quantile(0.75)
        high_value_count = len(fraud_df[fraud_df['amount'] >= high_value_threshold])
        if high_value_count > 0:
            patterns.append({
                'type': 'high_value_transactions',
                'count': high_value_count,
                'threshold': float(high_value_threshold),
                'description': f"{high_value_count} high-value fraudulent transactions (≥${high_value_threshold:.2f})"
            })

        # Time-based patterns
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            fraud_df_time = fraud_df.dropna(subset=['timestamp'])

            if len(fraud_df_time) > 0:
                # Night-time fraud
                night_fraud = fraud_df_time[
                    (fraud_df_time['timestamp'].dt.hour < 6) |
                    (fraud_df_time['timestamp'].dt.hour > 22)
                ]
                if len(night_fraud) > 0:
                    patterns.append({
                        'type': 'night_time_fraud',
                        'count': len(night_fraud),
                        'description': f"{len(night_fraud)} fraudulent transactions during night hours (10 PM - 6 AM)"
                    })

                # Weekend fraud
                weekend_fraud = fraud_df_time[fraud_df_time['timestamp'].dt.dayofweek >= 5]
                if len(weekend_fraud) > 0:
                    patterns.append({
                        'type': 'weekend_fraud',
                        'count': len(weekend_fraud),
                        'description': f"{len(weekend_fraud)} fraudulent transactions during weekends"
                    })

        # Category patterns
        if 'category' in df.columns:
            fraud_categories = fraud_df['category'].value_counts()
            if len(fraud_categories) > 0:
                top_category = fraud_categories.index[0]
                patterns.append({
                    'type': 'category_concentration',
                    'category': top_category,
                    'count': int(fraud_categories.iloc[0]),
                    'description': f"Most fraud in '{top_category}' category ({fraud_categories.iloc[0]} cases)"
                })

        return {
            'patterns': patterns,
            'total_patterns': len(patterns)
        }

    def get_csv_features(self) -> Dict[str, Any]:
        """
        Get information about CSV features

        Returns:
            Dictionary with CSV feature information
        """
        return self.analysis_result.get('csv_info', {})

    def search_transactions(self,
                           amount_min: Optional[float] = None,
                           amount_max: Optional[float] = None,
                           category: Optional[str] = None,
                           fraud_only: bool = False) -> List[Dict]:
        """
        Search transactions with filters

        Args:
            amount_min: Minimum amount
            amount_max: Maximum amount
            category: Category to filter by
            fraud_only: Only return fraud transactions

        Returns:
            List of matching transactions
        """
        if self.transactions_df is None or self.transactions_df.empty:
            return []

        df = self.transactions_df.copy()

        # Apply filters
        if fraud_only:
            df = df[df['is_fraud'] == 1]

        if amount_min is not None:
            df = df[df['amount'] >= amount_min]

        if amount_max is not None:
            df = df[df['amount'] <= amount_max]

        if category and 'category' in df.columns:
            df = df[df['category'].str.contains(category, case=False, na=False)]

        return df.to_dict('records')

    def get_time_analysis(self) -> Dict[str, Any]:
        """
        Analyze transactions by time patterns

        Returns:
            Dictionary with time-based analysis
        """
        if self.transactions_df is None or 'timestamp' not in self.transactions_df.columns:
            return {'available': False, 'message': 'Timestamp data not available'}

        df = self.transactions_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df_time = df.dropna(subset=['timestamp'])

        if len(df_time) == 0:
            return {'available': False, 'message': 'No valid timestamps found'}

        fraud_df = df_time[df_time['is_fraud'] == 1]

        # Hourly distribution
        hourly_fraud = fraud_df.groupby(fraud_df['timestamp'].dt.hour).size().to_dict()
        hourly_total = df_time.groupby(df_time['timestamp'].dt.hour).size().to_dict()

        # Daily distribution
        daily_fraud = fraud_df.groupby(fraud_df['timestamp'].dt.dayofweek).size().to_dict()
        daily_total = df_time.groupby(df_time['timestamp'].dt.dayofweek).size().to_dict()

        # Peak times
        peak_hour = max(hourly_fraud.items(), key=lambda x: x[1]) if hourly_fraud else (None, 0)
        peak_day = max(daily_fraud.items(), key=lambda x: x[1]) if daily_fraud else (None, 0)

        return {
            'available': True,
            'hourly_fraud_distribution': hourly_fraud,
            'hourly_total_distribution': hourly_total,
            'daily_fraud_distribution': daily_fraud,
            'daily_total_distribution': daily_total,
            'peak_hour': {'hour': peak_hour[0], 'count': peak_hour[1]},
            'peak_day': {'day': peak_day[0], 'count': peak_day[1]},
            'date_range': {
                'start': df_time['timestamp'].min().isoformat(),
                'end': df_time['timestamp'].max().isoformat()
            }
        }

    def get_category_analysis(self) -> Dict[str, Any]:
        """
        Analyze transactions by category

        Returns:
            Dictionary with category-based analysis
        """
        if self.transactions_df is None or 'category' not in self.transactions_df.columns:
            return {'available': False, 'message': 'Category data not available'}

        df = self.transactions_df
        fraud_df = df[df['is_fraud'] == 1]

        # Category fraud rates
        category_stats = df.groupby('category').agg({
            'is_fraud': ['sum', 'count'],
            'amount': ['sum', 'mean']
        }).reset_index()

        category_stats.columns = ['category', 'fraud_count', 'total_count', 'total_amount', 'avg_amount']
        category_stats['fraud_rate'] = (category_stats['fraud_count'] / category_stats['total_count'] * 100)

        # Top fraud categories
        top_fraud_categories = category_stats.sort_values('fraud_rate', ascending=False).head(5)

        return {
            'available': True,
            'total_categories': len(category_stats),
            'top_fraud_categories': top_fraud_categories.to_dict('records'),
            'fraud_by_category': fraud_df['category'].value_counts().to_dict(),
            'total_by_category': df['category'].value_counts().to_dict()
        }

    def get_langchain_tools(self) -> List:
        """
        Get LangChain-compatible tools

        Returns:
            List of LangChain Tool objects
        """
        tools = []

        # Tool 1: Get top fraudulent transactions
        @tool
        def get_top_fraudulent_transactions(limit: int = 3) -> str:
            """
            Get the top fraudulent transactions by fraud probability.
            Useful for identifying the most suspicious transactions.

            Args:
                limit: Number of top transactions to return (default: 3)
            """
            top_txns = self.get_top_transactions(limit=limit, fraud_only=True)
            if not top_txns:
                return "No fraudulent transactions found"

            result = f"Top {len(top_txns)} Fraudulent Transactions:\n\n"
            for i, txn in enumerate(top_txns, 1):
                result += f"{i}. Amount: ${txn.get('amount', 0):.2f}\n"
                result += f"   Fraud Probability: {txn.get('fraud_probability', 0)*100:.1f}%\n"
                result += f"   Merchant: {txn.get('merchant', 'N/A')}\n"
                result += f"   Category: {txn.get('category', 'N/A')}\n"
                result += f"   Reason: {txn.get('fraud_reason', 'Unknown')}\n\n"

            return result

        tools.append(get_top_fraudulent_transactions)

        # Tool 2: Get transaction statistics
        @tool
        def get_transaction_statistics() -> str:
            """
            Get comprehensive statistics about all transactions including fraud counts,
            amounts, and percentages. Useful for understanding overall dataset characteristics.
            """
            stats = self.get_transaction_statistics()

            result = "Transaction Statistics:\n\n"
            result += f"Total Transactions: {stats['total_transactions']}\n"
            result += f"Fraudulent: {stats['fraud_count']} ({stats['fraud_percentage']:.2f}%)\n"
            result += f"Legitimate: {stats['legitimate_count']}\n\n"
            result += f"Total Amount: ${stats['total_amount']:,.2f}\n"
            result += f"Fraud Amount: ${stats['fraud_amount']:,.2f}\n"
            result += f"Legitimate Amount: ${stats['legitimate_amount']:,.2f}\n\n"
            result += f"Average Transaction: ${stats['avg_amount']:.2f}\n"
            result += f"Median Transaction: ${stats['median_amount']:.2f}\n"

            return result

        tools.append(get_transaction_statistics)

        # Tool 3: Get fraud patterns
        @tool
        def get_detected_fraud_patterns() -> str:
            """
            Get detected fraud patterns including high-value transactions, time-based patterns,
            and category concentrations. Useful for identifying fraud trends.
            """
            patterns = self.get_fraud_patterns()

            if patterns['total_patterns'] == 0:
                return "No specific fraud patterns detected"

            result = f"Detected {patterns['total_patterns']} Fraud Pattern(s):\n\n"

            for pattern in patterns['patterns']:
                result += f"• {pattern['type'].replace('_', ' ').title()}\n"
                result += f"  {pattern['description']}\n\n"

            return result

        tools.append(get_detected_fraud_patterns)

        # Tool 4: Get CSV features
        @tool
        def get_csv_features_info() -> str:
            """
            Get information about the CSV features/columns including data types,
            non-null counts, and statistics. Useful for understanding the dataset structure.
            """
            features = self.get_csv_features()

            if not features:
                return "CSV feature information not available"

            result = f"CSV Dataset Information:\n\n"
            result += f"Total Rows: {features.get('total_count', 0)}\n"
            result += f"Total Columns: {len(features.get('columns', []))}\n\n"
            result += "Columns:\n"

            for col in features.get('columns', []):
                result += f"  • {col['name']} ({col['type']})\n"
                result += f"    Non-null: {col['non_null_count']}, Null: {col['null_count']}\n"

            return result

        tools.append(get_csv_features_info)

        # Tool 5: Get time analysis
        @tool
        def get_time_based_analysis() -> str:
            """
            Get time-based analysis including hourly and daily fraud patterns,
            peak times, and date ranges. Useful for identifying when fraud occurs most.
            """
            time_analysis = self.get_time_analysis()

            if not time_analysis.get('available', False):
                return time_analysis.get('message', 'Time analysis not available')

            result = "Time-Based Fraud Analysis:\n\n"

            peak_hour = time_analysis['peak_hour']
            if peak_hour['hour'] is not None:
                result += f"Peak Fraud Hour: {peak_hour['hour']:02d}:00 ({peak_hour['count']} cases)\n"

            peak_day = time_analysis['peak_day']
            if peak_day['day'] is not None:
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_name = days[peak_day['day']] if 0 <= peak_day['day'] < 7 else 'Unknown'
                result += f"Peak Fraud Day: {day_name} ({peak_day['count']} cases)\n"

            date_range = time_analysis.get('date_range', {})
            if date_range:
                result += f"\nDate Range: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}\n"

            return result

        tools.append(get_time_based_analysis)

        # Tool 6: Get category analysis
        @tool
        def get_category_based_analysis() -> str:
            """
            Get category-based analysis including fraud rates by category,
            top fraud categories, and category distributions.
            """
            cat_analysis = self.get_category_analysis()

            if not cat_analysis.get('available', False):
                return cat_analysis.get('message', 'Category analysis not available')

            result = "Category-Based Fraud Analysis:\n\n"
            result += f"Total Categories: {cat_analysis['total_categories']}\n\n"

            result += "Top Fraud Categories:\n"
            for cat in cat_analysis['top_fraud_categories']:
                result += f"  • {cat['category']}: {cat['fraud_rate']:.1f}% fraud rate "
                result += f"({cat['fraud_count']}/{cat['total_count']} transactions)\n"

            return result

        tools.append(get_category_based_analysis)

        return tools
