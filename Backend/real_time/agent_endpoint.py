"""
API Endpoint for Real-Time Transaction Analysis using LangChain Agent
"""

import logging
from typing import Dict, Any, Optional, List
from .realtime_agent import RealTimeAnalysisAgent
from .agent_tools import TransactionAnalysisTools

logger = logging.getLogger(__name__)


class AgentAnalysisService:
    """
    Service for generating AI-powered analysis using LangChain agent
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize agent analysis service

        Args:
            api_key: OpenAI API key (if None, reads from env)
        """
        self.agent = RealTimeAnalysisAgent(api_key=api_key)

    def generate_comprehensive_analysis(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive analysis using LangChain agent

        This provides:
        - Top 3 fraudulent transactions with detailed explanations
        - Key features in CSV and their importance
        - Detailed insights about fraud patterns
        - Fraud pattern explanations
        - Actionable recommendations

        Args:
            analysis_result: Complete analysis result from fraud detection

        Returns:
            Dictionary with AI-generated comprehensive analysis
        """
        try:
            logger.info("Generating comprehensive AI analysis")

            # Create analysis tools with the results
            tools = TransactionAnalysisTools(analysis_result)

            # Update agent with tools
            self.agent.analysis_tools = tools

            # Generate top transactions analysis
            top_transactions = self._analyze_top_transactions(tools)

            # Generate CSV features analysis
            csv_features = self._analyze_csv_features(tools)

            # Generate detailed insights
            detailed_insights = self.agent.generate_comprehensive_insights(analysis_result)

            # Generate fraud patterns explanation
            fraud_patterns = self.agent.explain_fraud_patterns(analysis_result)

            # Generate recommendations using LLM
            recommendations = self.agent.generate_recommendations(analysis_result)

            return {
                'success': True,
                'agent_analysis': {
                    'top_transactions': top_transactions,
                    'csv_features': csv_features,
                    'detailed_insights': detailed_insights.get('insights', ''),
                    'fraud_patterns': fraud_patterns.get('explanation', ''),
                    'recommendations': recommendations,
                    'analysis_type': detailed_insights.get('analysis_type', 'llm'),
                    'model_used': detailed_insights.get('model_used', 'gpt-3.5-turbo')
                }
            }

        except Exception as e:
            logger.error(f"Agent analysis failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate AI analysis'
            }

    def _analyze_top_transactions(self, tools: TransactionAnalysisTools) -> Dict[str, Any]:
        """Analyze top fraudulent transactions"""
        try:
            top_txns = tools.get_top_transactions(limit=10, fraud_only=True)

            analysis = {
                'count': len(top_txns),
                'transactions': []
            }

            for i, txn in enumerate(top_txns, 1):
                analysis['transactions'].append({
                    'rank': i,
                    'amount': float(txn.get('amount', 0)),
                    'fraud_probability': float(txn.get('fraud_probability', 0)),
                    'merchant': txn.get('merchant', 'N/A'),
                    'category': txn.get('category', 'N/A'),
                    'reason': txn.get('fraud_reason', 'Unknown'),
                    'transaction_id': txn.get('transaction_id', 'N/A'),
                    'timestamp': str(txn.get('timestamp', 'N/A'))
                })

            return analysis

        except Exception as e:
            logger.error(f"Top transactions analysis failed: {e}")
            return {'count': 0, 'transactions': []}

    def _analyze_csv_features(self, tools: TransactionAnalysisTools) -> Dict[str, Any]:
        """Analyze CSV features"""
        try:
            csv_info = tools.get_csv_features()

            features = {
                'total_columns': len(csv_info.get('columns', [])),
                'columns': csv_info.get('columns', []),
                'key_features': []
            }

            # Identify key features for fraud detection
            important_features = ['amount', 'merchant', 'category', 'timestamp', 'customer_id']

            for col in csv_info.get('columns', []):
                if col['name'] in important_features:
                    features['key_features'].append({
                        'name': col['name'],
                        'type': col['type'],
                        'completeness': f"{col['non_null_count']}/{col['non_null_count'] + col['null_count']}",
                        'unique_values': col.get('unique_values', 0)
                    })

            return features

        except Exception as e:
            logger.error(f"CSV features analysis failed: {e}")
            return {'total_columns': 0, 'columns': [], 'key_features': []}

    # REMOVED: _generate_recommendations - rule-based logic removed
    # All recommendations now come from LLM only via agent.generate_recommendations()

    def explain_plot(self, plot_data: Dict[str, Any]) -> str:
        """
        Generate explanation for a specific plot

        Args:
            plot_data: Plot information

        Returns:
            Detailed plot explanation
        """
        try:
            return self.agent.explain_plot(plot_data)
        except Exception as e:
            logger.error(f"Plot explanation failed: {e}")
            return f"Unable to generate plot explanation: {str(e)}"


# Singleton instance
_agent_service = None


def get_agent_service(api_key: Optional[str] = None) -> AgentAnalysisService:
    """
    Get singleton agent service instance

    Args:
        api_key: OpenAI API key

    Returns:
        AgentAnalysisService instance
    """
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentAnalysisService(api_key=api_key)
    return _agent_service
