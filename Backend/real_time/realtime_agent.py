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
                }

                # o4-mini doesn't support custom temperature, only uses default (1)
                if not self.model_name.startswith('o4'):
                    llm_kwargs['temperature'] = 0.3
                
                # Only set max_tokens for older models that support it
                # Newer models (o4, o1) don't support max_tokens or max_completion_tokens in LangChain
                if not (self.model_name.startswith('o4') or self.model_name.startswith('o1')):
                    llm_kwargs['max_tokens'] = 2000

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
                    'explanation': f'[WARNING] AI Pattern Analysis unavailable: {str(e)}',
                    'patterns_detected': 0
                }
        else:
            return {
                'success': False,
                'error': 'OpenAI API key not configured',
                'explanation': '[WARNING] AI Pattern Analysis unavailable: OpenAI API key not configured',
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

    def generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate actionable structured recommendations using OpenAI LLM ONLY

        Args:
            analysis_result: Complete analysis result

        Returns:
            List of structured recommendation objects from OpenAI
        """
        if self.llm is not None:
            try:
                return self._llm_recommendations(analysis_result)
            except Exception as e:
                logger.error(f"Error generating recommendations: {e}")
                # Return error instead of fallback
                return [{
                    'title': 'ERROR: AI Recommendations Unavailable',
                    'description': f'OpenAI API error: {str(e)}. Please check your API key, usage limits, or network connection.',
                    'fraud_rate': 'N/A',
                    'total_amount': 'N/A',
                    'case_count': 'N/A',
                    'immediate_actions': [
                        'Verify OpenAI API key is valid and active',
                        'Check OpenAI account has sufficient credits/quota',
                        'Verify network connectivity to OpenAI services',
                        'Review error logs for specific API error details'
                    ],
                    'prevention_steps': [
                        'Add OpenAI API credits to your account',
                        'Check API usage dashboard for rate limits',
                        'Ensure OPENAI_API_KEY environment variable is set correctly',
                        'Contact OpenAI support if issue persists'
                    ],
                    'monitor': 'OpenAI API status, account credits, rate limit quotas'
                }]
        else:
            # No LLM configured - return error
            return [{
                'title': 'ERROR: OpenAI API Not Configured',
                'description': 'OpenAI API key is required to generate AI-powered fraud prevention recommendations.',
                'fraud_rate': 'N/A',
                'total_amount': 'N/A',
                'case_count': 'N/A',
                'immediate_actions': [
                    'Set OPENAI_API_KEY in your environment variables or .env file',
                    'Obtain API key from https://platform.openai.com/api-keys',
                    'Verify API key has proper permissions',
                    'Restart backend server after adding API key'
                ],
                'prevention_steps': [
                    'Sign up for OpenAI API access if not already registered',
                    'Add payment method to OpenAI account',
                    'Configure API key in Backend/.env file',
                    'Install required packages: pip install langchain langchain-openai'
                ],
                'monitor': 'API key configuration, OpenAI account status'
            }]

    def _llm_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate structured recommendations using LLM based on TOP 3 fraud types"""
        import json
        import re

        # Extract key metrics
        fraud_count = analysis_result.get('fraud_detection', {}).get('fraud_count', 0)
        fraud_percentage = analysis_result.get('fraud_detection', {}).get('fraud_percentage', 0)
        total_amount = analysis_result.get('fraud_detection', {}).get('total_amount', 0)
        fraud_amount = analysis_result.get('fraud_detection', {}).get('total_fraud_amount', 0)

        # Get fraud transactions and analyze TOP 3 fraud types
        transactions = analysis_result.get('transactions', [])
        fraud_transactions = [t for t in transactions if t.get('is_fraud') == 1]
        top_fraud_types = self._get_top_fraud_types(fraud_transactions)

        # Enhanced prompt for structured recommendations based on TOP 3 fraud types
        prompt = f"""Based on this fraud analysis, generate exactly 3 detailed fraud prevention recommendations in JSON format - ONE for EACH of the TOP 3 fraud types detected.

**Fraud Overview:**
- Fraud Rate: {fraud_percentage:.2f}%
- Fraudulent Transactions: {fraud_count}
- Fraudulent Amount: ${fraud_amount:,.2f} out of ${total_amount:,.2f}

**TOP 3 Fraud Types Detected:**
{top_fraud_types}

IMPORTANT: Generate exactly 3 recommendations - one focused on EACH of the top 3 fraud types listed above.

Return a JSON array of exactly 3 recommendation objects. Each object MUST have this EXACT structure:
{{
  "title": "Severity: Fraud Type Name Detected" (e.g., 'CRITICAL: High Fraud Rate Detected in Entertainment Category' or 'HIGH: Unusually High Average Fraudulent Amount Detected'),
  "description": "One sentence description including the fraud type percentage and case count",
  "fraud_rate": "X.X% of fraud",
  "total_amount": "$XXX,XXX.XX total",
  "case_count": "XXX cases",
  "immediate_actions": ["Action 1 specific to this fraud type", "Action 2", "Action 3", "Action 4"],
  "prevention_steps": ["Step 1 specific to preventing this fraud type", "Step 2", "Step 3", "Step 4"],
  "monitor": "What to monitor for this specific fraud type"
}}

IMPORTANT REQUIREMENTS:
- Generate EXACTLY 3 recommendations - one for each of the TOP 3 fraud types
- Each recommendation title MUST mention the specific fraud type (e.g., "Entertainment category", "High-value transactions", "Night-time fraud")
- NO emojis or special characters
- Use severity indicators: CRITICAL, HIGH, MEDIUM based on the fraud type's impact
- Keep immediate_actions to 4 items - specific to that fraud type
- Keep prevention_steps to 4 items - specific to preventing that fraud type
- Monitor field must be specific to that fraud type
- Return ONLY valid JSON array, no markdown formatting"""

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]

        response = self.llm.invoke(messages)

        # Parse JSON response
        try:
            response_text = response.content.strip()
            # Remove markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*$', '', response_text)
            response_text = response_text.strip()

            recommendations = json.loads(response_text)

            # Validate structure and ensure exactly 3 recommendations
            if isinstance(recommendations, list):
                return recommendations[:3]  # Limit to exactly 3 (one per fraud type)
            else:
                return [recommendations] if isinstance(recommendations, dict) else []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw LLM response: {response_text[:500]}")
            # Raise error instead of falling back
            raise Exception(f"OpenAI returned invalid JSON format. Raw response: {response_text[:200]}...")

    # REMOVED: _fallback_recommendations - no rule-based fallbacks allowed
    # REMOVED: _fallback_structured_recommendations - no rule-based fallbacks allowed

    def _fallback_structured_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate structured fallback recommendations when LLM is not available"""

        fraud_percentage = analysis_result.get('fraud_detection', {}).get('fraud_percentage', 0)
        fraud_count = analysis_result.get('fraud_detection', {}).get('fraud_count', 0)
        fraud_amount = analysis_result.get('fraud_detection', {}).get('total_fraud_amount', 0)
        total_count = analysis_result.get('fraud_detection', {}).get('total_count', fraud_count)

        recommendations = []

        # Critical fraud rate
        if fraud_percentage > 20:
            recommendations.append({
                "title": "CRITICAL: Extremely High Fraud Rate Detected",
                "description": f"{fraud_percentage:.1f}% fraud rate ({fraud_count}/{total_count} transactions). Immediate action required.",
                "fraud_rate": f"{fraud_percentage:.1f}% of fraud",
                "total_amount": f"${fraud_amount:,.2f} total",
                "case_count": f"{fraud_count} cases",
                "immediate_actions": [
                    "Initiate emergency fraud response protocol",
                    "Suspend high-risk transaction processing temporarily",
                    "Conduct immediate security audit of authentication systems",
                    "Review all recent account changes and access logs"
                ],
                "prevention_steps": [
                    "Detect and flag sudden spikes in transaction volume",
                    "Implement burst detection algorithms (3+ transactions within minutes)",
                    "Set up alerts for accounts with no history suddenly active",
                    "Monitor for automated transaction patterns",
                    "Require manual approval for burst transactions above threshold"
                ],
                "monitor": "Transaction clustering, time gaps between transactions, volume spikes, automation indicators"
            })

        # High fraud amount
        if fraud_percentage > 10 and fraud_percentage <= 20:
            recommendations.append({
                "title": "HIGH PRIORITY: Significant Fraud Activity Detected",
                "description": f"Detected {fraud_count} cases of fraud representing {fraud_percentage:.1f}% of transactions. Enhanced monitoring required.",
                "fraud_rate": f"{fraud_percentage:.1f}% of fraud",
                "total_amount": f"${fraud_amount:,.2f} total",
                "case_count": f"{fraud_count} cases",
                "immediate_actions": [
                    "Hold burst transactions for fraud analyst review",
                    "Verify user intent through phone/email confirmation",
                    "Check if account credentials have been compromised",
                    "Review shipping addresses for fraud indicators"
                ],
                "prevention_steps": [
                    "Implement CVV/AVS checks for all transactions",
                    "Flag accounts with multiple card additions in short time",
                    "Review shipping addresses for fraud indicators",
                    "Set up alerts for accounts with no history suddenly active",
                    "Monitor for automated transaction patterns"
                ],
                "monitor": "Card-not-present risk indicators, fraud pattern evolution"
            })

        # Moderate fraud
        if fraud_percentage > 5 and fraud_percentage <= 10:
            recommendations.append({
                "title": "MODERATE: Elevated Fraud Levels Detected",
                "description": f"{fraud_count} fraudulent transactions detected ({fraud_percentage:.1f}% of total). Continue enhanced monitoring.",
                "fraud_rate": f"{fraud_percentage:.1f}% of fraud",
                "total_amount": f"${fraud_amount:,.2f} total",
                "case_count": f"{fraud_count} cases",
                "immediate_actions": [
                    "Review and update fraud detection thresholds",
                    "Implement additional transaction verification",
                    "Monitor high-value transaction patterns",
                    "Conduct security audit of affected accounts"
                ],
                "prevention_steps": [
                    "Enhance real-time transaction monitoring",
                    "Update fraud detection rules based on new patterns",
                    "Implement velocity checks for rapid transactions",
                    "Review authentication mechanisms",
                    "Set up automated fraud pattern alerts"
                ],
                "monitor": "Transaction velocity, unusual patterns, account behavior"
            })

        # Default if no recommendations yet
        if len(recommendations) == 0:
            recommendations.append({
                "title": "LOW: Fraud Levels Within Normal Range",
                "description": f"Detected {fraud_count} cases ({fraud_percentage:.1f}%). Maintain current protocols.",
                "fraud_rate": f"{fraud_percentage:.1f}% of fraud",
                "total_amount": f"${fraud_amount:,.2f} total",
                "case_count": f"{fraud_count} cases",
                "immediate_actions": [
                    "Continue routine monitoring",
                    "Review fraud detection logs regularly",
                    "Maintain current security protocols",
                    "Schedule regular fraud pattern reviews"
                ],
                "prevention_steps": [
                    "Continue collecting transaction data",
                    "Keep fraud detection models up to date",
                    "Monitor emerging fraud patterns",
                    "Maintain fraud prevention training for staff",
                    "Regular security audits"
                ],
                "monitor": "Overall fraud trends, new pattern emergence"
            })

        return recommendations[:3]  # Return top 3 recommendations

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
                return f"ERROR: Unable to generate plot explanation. OpenAI API error: {str(e)}. Please check your API key and network connection."
        else:
            return "ERROR: OpenAI API key not configured. Plot explanations require OpenAI API access. Please set OPENAI_API_KEY environment variable."

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

    def _get_top_fraud_types(self, fraud_transactions: List[Dict]) -> str:
        """Analyze and return the TOP 3 fraud types with details"""
        if not fraud_transactions:
            return "No fraud patterns detected"

        # Analyze fraud by reason/type
        fraud_types = {}
        for txn in fraud_transactions:
            fraud_reason = txn.get('fraud_reason', 'Unknown')
            amount = txn.get('amount', 0)

            if fraud_reason not in fraud_types:
                fraud_types[fraud_reason] = {
                    'count': 0,
                    'total_amount': 0,
                    'amounts': []
                }

            fraud_types[fraud_reason]['count'] += 1
            fraud_types[fraud_reason]['total_amount'] += amount
            fraud_types[fraud_reason]['amounts'].append(amount)

        # Sort by count (descending) and get top 3
        sorted_types = sorted(fraud_types.items(), key=lambda x: x[1]['count'], reverse=True)
        top_3 = sorted_types[:3]

        # Format top 3 fraud types
        result_lines = []
        total_fraud = len(fraud_transactions)

        for idx, (fraud_type, data) in enumerate(top_3, 1):
            count = data['count']
            total_amt = data['total_amount']
            percentage = (count / total_fraud * 100) if total_fraud > 0 else 0
            avg_amount = total_amt / count if count > 0 else 0

            result_lines.append(
                f"{idx}. {fraud_type}\n"
                f"   - Cases: {count} ({percentage:.1f}% of all fraud)\n"
                f"   - Total Amount: ${total_amt:,.2f}\n"
                f"   - Average Amount: ${avg_amount:,.2f}"
            )

        return "\n\n".join(result_lines)

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

    # REMOVED: All fallback functions - no rule-based fallbacks allowed
    # _fallback_insights - REMOVED
    # _fallback_fraud_patterns - REMOVED  
    # _fallback_plot_explanation - REMOVED
