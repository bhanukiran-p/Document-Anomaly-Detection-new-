"""
LangChain Agent for Real-Time Transaction Analysis
Provides intelligent insights about transactions, fraud patterns, and visualizations
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    # AgentExecutor is not needed for our simple use case
    # from langchain_core.tools import Tool
    LANGCHAIN_AVAILABLE = True
    logger.info("LangChain loaded successfully - GPT-4 mode enabled")
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logger.warning(f"LangChain not installed: {e}. Agent will use fallback mode.")

from .agent_tools import TransactionAnalysisTools
from .agent_prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_PROMPT,
    INSIGHTS_PROMPT,
    FRAUD_PATTERNS_PROMPT,
    PLOT_EXPLANATION_PROMPT,
    RECOMMENDATIONS_PROMPT
)


class RealTimeAnalysisAgent:
    """
    AI-powered agent for real-time transaction analysis
    Provides detailed insights, fraud pattern detection, and plot explanations
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 analysis_tools: Optional[TransactionAnalysisTools] = None):
        """
        Initialize real-time analysis agent

        Args:
            api_key: OpenAI API key (if None, reads from env)
            model: OpenAI model to use (if None, reads from AI_MODEL env var)
            analysis_tools: Transaction analysis tools
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model or os.getenv('AI_MODEL', 'gpt-3.5-turbo')
        self.analysis_tools = analysis_tools
        self.llm = None
        self.agent_executor = None

        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                # Build ChatOpenAI kwargs based on model capabilities
                llm_kwargs = {
                    'model': self.model_name,
                    'openai_api_key': self.api_key,
                    'max_tokens': 2000
                }

                # o4-mini doesn't support custom temperature, only uses default (1)
                if not self.model_name.startswith('o4'):
                    llm_kwargs['temperature'] = 0.3

                self.llm = ChatOpenAI(**llm_kwargs)
                logger.info(f"Initialized LangChain agent with {self.model_name} - GPT-4 mode active!")

            except Exception as e:
                logger.error(f"Could not initialize LangChain: {e}")
                logger.warning("Falling back to rule-based analysis")
                self.llm = None
        else:
            if not LANGCHAIN_AVAILABLE:
                logger.warning("LangChain not available - using fallback analysis")
            elif not self.api_key:
                logger.warning("OpenAI API key not found - using fallback analysis")
            self.llm = None

    def generate_comprehensive_insights(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive insights from analysis results

        Args:
            analysis_result: Complete analysis result from fraud detector

        Returns:
            Dictionary with AI-generated insights
        """
        if self.llm is not None:
            try:
                return self._llm_insights(analysis_result)
            except Exception as e:
                logger.error(f"Error in LLM insights generation: {e}")
                # Return error instead of falling back
                return {
                    'success': False,
                    'error': str(e),
                    'message': f'OpenAI API unavailable ({self.model_name}). Please check your OpenAI API key or usage limits.',
                    'insights': f'AI Analysis unavailable: {str(e)}',
                    'analysis_type': 'failed',
                    'model_used': self.model_name
                }
        else:
            return {
                'success': False,
                'error': 'OpenAI API key not configured',
                'message': 'OpenAI API key is required for AI analysis.',
                'insights': 'AI Analysis unavailable: OpenAI API key not configured',
                'analysis_type': 'failed',
                'model_used': 'none'
            }

    def _llm_insights(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights using LLM"""

        # Extract key metrics
        total_transactions = analysis_result.get('csv_info', {}).get('total_count', 0)
        fraud_count = analysis_result.get('fraud_detection', {}).get('fraud_count', 0)
        fraud_percentage = analysis_result.get('fraud_detection', {}).get('fraud_percentage', 0)
        total_amount = analysis_result.get('fraud_detection', {}).get('total_amount', 0)
        fraud_amount = analysis_result.get('fraud_detection', {}).get('total_fraud_amount', 0)

        # Get top transactions
        transactions = analysis_result.get('transactions', [])
        top_fraud = sorted(
            [t for t in transactions if t.get('is_fraud') == 1],
            key=lambda x: x.get('fraud_probability', 0),
            reverse=True
        )[:3]

        # Format top transactions for LLM
        top_transactions_text = self._format_transactions(top_fraud)

        # Get CSV features info
        csv_info = analysis_result.get('csv_info', {})
        features_text = self._format_csv_features(csv_info)

        # Create the prompt
        system_message = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)
        human_message = HumanMessagePromptTemplate.from_template(INSIGHTS_PROMPT)

        chat_prompt = ChatPromptTemplate.from_messages([
            system_message,
            human_message
        ])

        # Format the messages
        messages = chat_prompt.format_messages(
            total_transactions=total_transactions,
            fraud_count=fraud_count,
            fraud_percentage=fraud_percentage,
            total_amount=total_amount,
            fraud_amount=fraud_amount,
            top_transactions=top_transactions_text,
            csv_features=features_text
        )

        # Get LLM response
        response = self.llm.invoke(messages)
        insights_text = response.content

        # Parse response
        return self._parse_insights_response(insights_text)

    def explain_fraud_patterns(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed explanation of detected fraud patterns

        Args:
            analysis_result: Complete analysis result

        Returns:
            Dictionary with fraud pattern explanations
        """
        if self.llm is not None:
            try:
                return self._llm_fraud_patterns(analysis_result)
            except Exception as e:
                logger.error(f"Error in fraud pattern explanation: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'explanation': f'⚠️ AI Pattern Analysis unavailable: {str(e)}',
                    'patterns_detected': 0
                }
        else:
            return {
                'success': False,
                'error': 'OpenAI API key not configured',
                'explanation': '⚠️ AI Pattern Analysis unavailable: OpenAI API key not configured',
                'patterns_detected': 0
            }

    def _llm_fraud_patterns(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fraud pattern explanations using LLM"""

        transactions = analysis_result.get('transactions', [])
        fraud_transactions = [t for t in transactions if t.get('is_fraud') == 1]

        # Analyze patterns
        patterns_text = self._analyze_patterns(fraud_transactions)

        # Create prompt
        system_message = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)
        human_message = HumanMessagePromptTemplate.from_template(FRAUD_PATTERNS_PROMPT)

        chat_prompt = ChatPromptTemplate.from_messages([
            system_message,
            human_message
        ])

        messages = chat_prompt.format_messages(
            fraud_count=len(fraud_transactions),
            patterns=patterns_text
        )

        response = self.llm.invoke(messages)

        return {
            'success': True,
            'explanation': response.content,
            'patterns_detected': len(fraud_transactions)
        }

    def generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations using LLM

        Args:
            analysis_result: Complete analysis result

        Returns:
            List of recommendations
        """
        if self.llm is not None:
            try:
                return self._llm_recommendations(analysis_result)
            except Exception as e:
                logger.error(f"Error generating recommendations: {e}")
                return [f"⚠️ AI Recommendations unavailable: {str(e)}", "Please check your OpenAI API key or usage limits."]
        else:
            return ["⚠️ AI Recommendations unavailable: OpenAI API key not configured"]

    def _llm_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations using LLM"""

        # Extract key metrics
        fraud_count = analysis_result.get('fraud_detection', {}).get('fraud_count', 0)
        fraud_percentage = analysis_result.get('fraud_detection', {}).get('fraud_percentage', 0)
        total_amount = analysis_result.get('fraud_detection', {}).get('total_amount', 0)
        fraud_amount = analysis_result.get('fraud_detection', {}).get('total_fraud_amount', 0)

        # Get fraud patterns info
        transactions = analysis_result.get('transactions', [])
        fraud_transactions = [t for t in transactions if t.get('is_fraud') == 1]
        patterns_text = self._analyze_patterns(fraud_transactions)

        # Create prompt
        system_message = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)
        human_message = HumanMessagePromptTemplate.from_template(RECOMMENDATIONS_PROMPT)

        chat_prompt = ChatPromptTemplate.from_messages([
            system_message,
            human_message
        ])

        # Add context about the analysis
        context = f"""
**Fraud Overview:**
- Fraud Rate: {fraud_percentage:.2f}%
- Fraudulent Transactions: {fraud_count}
- Fraudulent Amount: ${fraud_amount:,.2f} out of ${total_amount:,.2f} ({(fraud_amount/total_amount*100) if total_amount > 0 else 0:.1f}%)

**Detected Patterns:**
{patterns_text}

Please provide 5-7 actionable recommendations prioritized by urgency and impact."""

        messages = chat_prompt.format_messages(context=context)

        response = self.llm.invoke(messages)

        # Parse recommendations (split by lines or bullet points)
        recommendations_text = response.content
        recommendations = [line.strip() for line in recommendations_text.split('\n') if line.strip() and not line.strip().startswith('#')]

        # Filter out empty lines and headers
        recommendations = [rec for rec in recommendations if rec and len(rec) > 10]

        return recommendations[:7]  # Limit to 7 recommendations

    def _fallback_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate fallback recommendations when LLM is not available"""

        fraud_percentage = analysis_result.get('fraud_detection', {}).get('fraud_percentage', 0)
        fraud_amount = analysis_result.get('fraud_detection', {}).get('total_fraud_amount', 0)
        total_amount = analysis_result.get('fraud_detection', {}).get('total_amount', 1)

        recommendations = []

        # Based on fraud rate
        if fraud_percentage > 20:
            recommendations.append("CRITICAL: Immediate security review required - fraud rate exceeds 20%")
            recommendations.append("SECURITY: Implement additional transaction verification for all high-value transactions")
        elif fraud_percentage > 10:
            recommendations.append("HIGH RISK: Enhanced monitoring and fraud detection rules needed")
            recommendations.append("ACTION: Review and update fraud detection thresholds")
        elif fraud_percentage > 5:
            recommendations.append("MODERATE RISK: Continue monitoring with current protocols")

        # Based on fraud amount
        if fraud_amount / total_amount > 0.15:
            recommendations.append(f"FINANCIAL IMPACT: {(fraud_amount/total_amount*100):.1f}% of total value is at risk")

        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("STATUS: Fraud levels within acceptable ranges - maintain current monitoring")

        recommendations.append("DATA COLLECTION: Continue collecting transaction data to improve detection accuracy")
        recommendations.append("REVIEW SCHEDULE: Schedule regular fraud pattern reviews")

        return recommendations

    def explain_plot(self, plot_data: Dict[str, Any]) -> str:
        """
        Generate detailed explanation for a specific plot

        Args:
            plot_data: Plot information including title, type, and details

        Returns:
            Detailed explanation string
        """
        if self.llm is not None:
            try:
                return self._llm_plot_explanation(plot_data)
            except Exception as e:
                logger.error(f"Error in plot explanation: {e}")
                return self._fallback_plot_explanation(plot_data)
        else:
            return self._fallback_plot_explanation(plot_data)

    def _llm_plot_explanation(self, plot_data: Dict[str, Any]) -> str:
        """Generate plot explanation using LLM"""

        plot_title = plot_data.get('title', 'Unknown Plot')
        plot_type = plot_data.get('type', 'unknown')
        plot_details = plot_data.get('details', [])
        plot_description = plot_data.get('description', '')

        # Format details
        details_text = "\n".join([f"- {d['label']}: {d['value']}" for d in plot_details])

        # Create prompt
        system_message = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)
        human_message = HumanMessagePromptTemplate.from_template(PLOT_EXPLANATION_PROMPT)

        chat_prompt = ChatPromptTemplate.from_messages([
            system_message,
            human_message
        ])

        messages = chat_prompt.format_messages(
            plot_title=plot_title,
            plot_type=plot_type,
            plot_description=plot_description,
            plot_details=details_text
        )

        response = self.llm.invoke(messages)
        return response.content

    def _format_transactions(self, transactions: List[Dict]) -> str:
        """Format transactions for LLM prompt"""
        if not transactions:
            return "No fraudulent transactions detected"

        formatted = []
        for i, txn in enumerate(transactions, 1):
            amount = txn.get('amount', 0)
            prob = txn.get('fraud_probability', 0)
            reason = txn.get('fraud_reason', 'Unknown')
            merchant = txn.get('merchant', 'N/A')
            category = txn.get('category', 'N/A')

            formatted.append(
                f"{i}. Amount: ${amount:.2f} | Probability: {prob*100:.1f}% | "
                f"Merchant: {merchant} | Category: {category}\n   Reason: {reason}"
            )

        return "\n".join(formatted)

    def _format_csv_features(self, csv_info: Dict) -> str:
        """Format CSV features for LLM prompt"""
        columns = csv_info.get('columns', [])
        total_count = csv_info.get('total_count', 0)

        features = []
        for col in columns:
            features.append(f"- {col['name']} ({col['type']}): {col['non_null_count']} non-null values")

        return f"Total rows: {total_count}\nColumns:\n" + "\n".join(features)

    def _analyze_patterns(self, fraud_transactions: List[Dict]) -> str:
        """Analyze patterns in fraud transactions"""
        if not fraud_transactions:
            return "No fraud patterns to analyze"

        patterns = []

        # Amount patterns
        amounts = [t.get('amount', 0) for t in fraud_transactions]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        max_amount = max(amounts) if amounts else 0

        patterns.append(f"Amount statistics: Average ${avg_amount:.2f}, Maximum ${max_amount:.2f}")

        # Time patterns if available
        timestamps = [t.get('timestamp') for t in fraud_transactions if t.get('timestamp')]
        if timestamps:
            patterns.append(f"Time-based patterns: {len(timestamps)} transactions with timestamps")

        # Category patterns
        categories = {}
        for t in fraud_transactions:
            cat = t.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1

        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            patterns.append(f"Most common category: {top_category[0]} ({top_category[1]} occurrences)")

        return "\n".join(patterns)

    def _parse_insights_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM insights response"""
        return {
            'success': True,
            'insights': response_text,
            'analysis_type': 'llm',
            'model_used': self.model_name
        }

    def _fallback_insights(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rule-based insights when LLM is not available"""

        fraud_count = analysis_result.get('fraud_detection', {}).get('fraud_count', 0)
        total_count = analysis_result.get('csv_info', {}).get('total_count', 0)
        fraud_percentage = analysis_result.get('fraud_detection', {}).get('fraud_percentage', 0)
        fraud_amount = analysis_result.get('fraud_detection', {}).get('total_fraud_amount', 0)

        insights = []

        # Overall assessment
        if fraud_percentage > 20:
            insights.append(f"HIGH ALERT: {fraud_percentage:.1f}% fraud rate detected with {fraud_count} fraudulent transactions")
        elif fraud_percentage > 10:
            insights.append(f"MEDIUM ALERT: {fraud_percentage:.1f}% fraud rate with {fraud_count} suspicious transactions")
        elif fraud_percentage > 5:
            insights.append(f"LOW ALERT: {fraud_percentage:.1f}% fraud rate detected")
        else:
            insights.append(f"STATUS: Fraud rate is within acceptable limits ({fraud_percentage:.1f}%)")

        # Amount insights
        if fraud_amount > 0:
            insights.append(f"FINANCIAL IMPACT: Total fraudulent amount: ${fraud_amount:,.2f}")

        # Key features
        csv_columns = analysis_result.get('csv_info', {}).get('columns', [])
        if csv_columns:
            insights.append(f"DATASET INFO: Contains {len(csv_columns)} features for analysis")

        # Recommendations
        if fraud_percentage > 15:
            insights.append("RECOMMENDATION: Immediate review of security measures required")
        elif fraud_percentage > 10:
            insights.append("RECOMMENDATION: Enhanced monitoring recommended")
        else:
            insights.append("RECOMMENDATION: Continue standard monitoring procedures")

        return {
            'success': True,
            'insights': "\n\n".join(insights),
            'analysis_type': 'rule_based',
            'model_used': 'fallback'
        }

    def _fallback_fraud_patterns(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rule-based fraud pattern explanation"""

        transactions = analysis_result.get('transactions', [])
        fraud_transactions = [t for t in transactions if t.get('is_fraud') == 1]

        patterns = []

        if not fraud_transactions:
            return {
                'success': True,
                'explanation': 'No fraud patterns detected in the dataset',
                'patterns_detected': 0
            }

        # High-value transactions
        high_value = [t for t in fraud_transactions if t.get('amount', 0) > 5000]
        if high_value:
            patterns.append(f"HIGH-VALUE FRAUD: {len(high_value)} transactions over $5,000")

        # Category patterns
        categories = {}
        for t in fraud_transactions:
            cat = t.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1

        if categories:
            top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            patterns.append("TOP FRAUD CATEGORIES: " + ", ".join([f"{cat} ({count})" for cat, count in top_cats]))

        explanation = "\n".join(patterns) if patterns else "Standard fraud patterns detected"

        return {
            'success': True,
            'explanation': explanation,
            'patterns_detected': len(fraud_transactions)
        }

    def _fallback_plot_explanation(self, plot_data: Dict[str, Any]) -> str:
        """Generate rule-based plot explanation"""

        plot_title = plot_data.get('title', 'Unknown Plot')
        plot_description = plot_data.get('description', '')
        plot_details = plot_data.get('details', [])

        explanation = f"**{plot_title}**\n\n"

        if plot_description:
            explanation += f"{plot_description}\n\n"

        if plot_details:
            explanation += "Key metrics:\n"
            for detail in plot_details:
                explanation += f"- {detail['label']}: {detail['value']}\n"

        return explanation
