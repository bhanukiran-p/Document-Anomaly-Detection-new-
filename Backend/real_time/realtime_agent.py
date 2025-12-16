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
from .fraud_detector import STANDARD_FRAUD_REASONS


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
                # Generate basic recommendations as fallback
                logger.warning("OpenAI API failed. Generating basic recommendations for all fraud patterns.")
                fraud_pattern_entries = self._build_fraud_pattern_entries(analysis_result)
                return [self._build_basic_recommendation(entry) for entry in fraud_pattern_entries]
        else:
            # No LLM configured - generate basic recommendations
            logger.warning("OpenAI API not configured. Generating basic recommendations for all fraud patterns.")
            fraud_pattern_entries = self._build_fraud_pattern_entries(analysis_result)
            return [self._build_basic_recommendation(entry) for entry in fraud_pattern_entries]

    def _llm_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate structured recommendations using LLM for ALL standard fraud patterns"""
        import json
        import re

        # Extract key metrics
        fraud_count = analysis_result.get('fraud_detection', {}).get('fraud_count', 0)
        fraud_percentage = analysis_result.get('fraud_detection', {}).get('fraud_percentage', 0)
        total_amount = analysis_result.get('fraud_detection', {}).get('total_amount', 0)
        fraud_amount = analysis_result.get('fraud_detection', {}).get('total_fraud_amount', 0)

        # Build comprehensive fraud pattern list (standard + detected)
        fraud_pattern_entries = self._build_fraud_pattern_entries(analysis_result)
        fraud_types_count = len(fraud_pattern_entries)
        fraud_types_text = self._format_fraud_entries_for_prompt(fraud_pattern_entries)

        prompt = f"""You are a fraud prevention expert. Generate EXACTLY {fraud_types_count} structured recommendations in JSON format ? ONE for EACH fraud pattern listed below.

**Fraud Overview:**
- Fraud Rate: {fraud_percentage:.2f}%
- Fraudulent Transactions: {fraud_count}
- Fraudulent Amount: ${fraud_amount:,.2f} out of ${total_amount:,.2f}

**Fraud Patterns ({fraud_types_count} total):**
{fraud_types_text}

MANDATORY RULES:
1. Output MUST contain exactly {fraud_types_count} recommendation objects ? one for EACH fraud pattern in the list above (in the same order).
2. Title format: "SEVERITY: Exact Fraud Pattern Name" (use the exact spelling provided).
3. Severity levels: CRITICAL (>50% of fraud), HIGH (10-50%), MEDIUM (1-10%), LOW (<1% or zero cases). If no cases were detected, use LOW and describe preventative guidance.
4. Description must mention that pattern's percentage and case count (even if zero: "0 cases detected").
5. Immediate actions and prevention steps must contain 4 concise, pattern-specific bullet points.
6. Monitor field must describe what telemetry to watch for that specific pattern.
7. Return ONLY a valid JSON array, no markdown fences or commentary.

JSON OUTPUT TEMPLATE:
[
  {{
    "title": "SEVERITY: Exact Fraud Pattern Name",
    "description": "One sentence including the fraud percentage and case count for that pattern",
    "fraud_rate": "X.X% of fraud",
    "total_amount": "$XXX,XXX.XX total",
    "case_count": "XXX cases",
    "immediate_actions": ["Action 1", "Action 2", "Action 3", "Action 4"],
    "prevention_steps": ["Step 1", "Step 2", "Step 3", "Step 4"],
    "monitor": "Telemetry to monitor for that pattern"
  }}
  ... repeat for ALL {fraud_types_count} patterns ...
]"""

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

            # Try to extract JSON from response (handle cases where there's extra text)
            recommendations = None
            
            # First, try direct parsing
            try:
                recommendations = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON array/object in the response
                # Look for JSON array pattern
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    try:
                        recommendations = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
                
                # If still no luck, try to find JSON object
                if recommendations is None:
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        try:
                            recommendations = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            pass

            # If still can't parse, try to extract and fix common issues
            if recommendations is None:
                # Try to fix common JSON issues
                # Remove trailing commas before closing brackets/braces
                fixed_text = re.sub(r',\s*}', '}', response_text)
                fixed_text = re.sub(r',\s*]', ']', fixed_text)
                try:
                    recommendations = json.loads(fixed_text)
                except json.JSONDecodeError:
                    # Last resort: try to extract first valid JSON structure
                    # Find the start of JSON array
                    start_idx = response_text.find('[')
                    if start_idx != -1:
                        # Try to find matching closing bracket
                        bracket_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response_text)):
                            if response_text[i] == '[':
                                bracket_count += 1
                            elif response_text[i] == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i + 1
                                    break
                        if end_idx > start_idx:
                            try:
                                recommendations = json.loads(response_text[start_idx:end_idx])
                            except json.JSONDecodeError:
                                pass

            # If still None, raise error
            if recommendations is None:
                raise json.JSONDecodeError("Could not extract valid JSON from response", response_text, 0)

            if isinstance(recommendations, dict):
                recommendations = [recommendations]

            if not isinstance(recommendations, list):
                recommendations = []

            recommendations = self._ensure_full_pattern_coverage(
                recommendations,
                fraud_pattern_entries
            )

            return recommendations

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw LLM response: {response_text[:500]}")
            # Return basic recommendations for all patterns as fallback
            logger.warning("AI recommendations unavailable due to JSON parsing error. Generating basic recommendations.")
            return [self._build_basic_recommendation(entry) for entry in fraud_pattern_entries]

    # REMOVED: _fallback_recommendations - no rule-based fallbacks allowed
    # REMOVED: _fallback_structured_recommendations - no rule-based fallbacks allowed
    # REMOVED: _generate_pattern_specific_recommendations - no rule-based fallbacks allowed
    # All recommendations must come from AI only - no fallbacks

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

    def _build_fraud_pattern_entries(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Combine backend fraud breakdown with standard patterns for comprehensive coverage."""
        detection = analysis_result.get('fraud_detection', {}) or {}
        breakdown = detection.get('fraud_reason_breakdown') or detection.get('fraud_type_breakdown') or []

        entries_map: Dict[str, Dict[str, Any]] = {}
        total_cases = sum(entry.get('count', 0) for entry in breakdown) or 0

        def normalize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
            name = entry.get('type') or entry.get('label') or 'Unknown pattern'
            count = int(entry.get('count', 0) or 0)
            percentage = entry.get('percentage')
            total_amount = float(entry.get('total_amount', 0) or 0.0)
            avg_amount = total_amount / count if count else 0.0

            if percentage is None:
                percentage = (count / total_cases * 100) if total_cases else 0.0

            return {
                'name': name,
                'count': count,
                'percentage': float(percentage),
                'total_amount': total_amount,
                'avg_amount': avg_amount,
                'generated': False
            }

        for entry in breakdown:
            normalized = normalize_entry(entry)
            entries_map[normalized['name'].lower()] = normalized

        if not entries_map:
            transactions = analysis_result.get('transactions', [])
            fraud_transactions = [t for t in transactions if t.get('is_fraud') == 1]
            total_cases = len(fraud_transactions) or 1
            amount_map: Dict[str, float] = {}
            count_map: Dict[str, int] = {}

            for txn in fraud_transactions:
                reason = txn.get('fraud_reason') or txn.get('fraud_type') or 'Unknown pattern'
                reason_key = str(reason).lower()
                count_map[reason_key] = count_map.get(reason_key, 0) + 1
                amount_map[reason_key] = amount_map.get(reason_key, 0.0) + float(txn.get('amount', 0.0) or 0.0)

            for reason_key, count in count_map.items():
                total_amt = amount_map.get(reason_key, 0.0)
                entries_map[reason_key] = {
                    'name': reason_key.title(),
                    'count': count,
                    'percentage': (count / total_cases) * 100,
                    'total_amount': total_amt,
                    'avg_amount': total_amt / count if count else 0.0,
                    'generated': False
                }

        final_entries: List[Dict[str, Any]] = []

        for pattern in STANDARD_FRAUD_REASONS:
            key = pattern.lower()
            entry = entries_map.pop(key, None)
            if entry is None:
                entry = {
                    'name': pattern,
                    'count': 0,
                    'percentage': 0.0,
                    'total_amount': 0.0,
                    'avg_amount': 0.0,
                    'generated': True
                }
            else:
                entry['name'] = pattern
            final_entries.append(entry)

        for leftover in entries_map.values():
            final_entries.append(leftover)

        return final_entries

    def _format_fraud_entries_for_prompt(self, entries: List[Dict[str, Any]]) -> str:
        """Format fraud pattern entries for the LLM prompt."""
        lines = []
        for idx, entry in enumerate(entries, 1):
            lines.append(
                f"{idx}. {entry['name']}\n"
                f"   - Cases: {entry['count']} ({entry['percentage']:.1f}% of all fraud)\n"
                f"   - Total Amount: ${entry['total_amount']:,.2f}\n"
                f"   - Average Amount: ${entry['avg_amount']:,.2f}"
            )
        return "\n\n".join(lines)

    def _ensure_full_pattern_coverage(
        self,
        recommendations: List[Dict[str, Any]],
        entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Guarantee every fraud pattern has a recommendation."""
        remaining = recommendations.copy()
        assigned: List[Dict[str, Any]] = []

        for entry in entries:
            match_index = None
            entry_key = entry['name'].lower()

            for idx, rec in enumerate(remaining):
                title = (rec.get('title') or '').lower()
                if entry_key in title:
                    match_index = idx
                    break

            if match_index is not None:
                assigned.append(remaining.pop(match_index))
            else:
                assigned.append(self._build_basic_recommendation(entry))

        return assigned

    def _build_basic_recommendation(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create a baseline recommendation when the LLM omits a fraud pattern."""
        percentage = float(entry.get('percentage', 0.0) or 0.0)
        count = int(entry.get('count', 0) or 0)
        total_amount = float(entry.get('total_amount', 0.0) or 0.0)
        name = entry.get('name', 'Unknown pattern')

        if percentage > 50:
            severity = "CRITICAL"
        elif percentage > 10:
            severity = "HIGH"
        elif percentage > 1:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        percentage_text = f"{percentage:.1f}%"
        case_text = f"{count} case{'s' if count != 1 else ''}"
        amount_text = f"${total_amount:,.2f}"

        if count == 0:
            description = f"No recent cases of {name} detected, but controls must stay active ({percentage_text} of fraud historically)."
            case_display = "0 cases"
        else:
            description = f"Detected {case_text} ({percentage_text} of fraud) tied to {name}; immediate mitigation required."
            case_display = case_text

        template_action = f"Escalate suspected {name.lower()} activity to fraud operations"
        template_prevention = f"Update detection rules specific to {name.lower()} patterns"

        return {
            "title": f"{severity}: {name}",
            "description": description,
            "fraud_rate": f"{percentage_text} of fraud",
            "total_amount": f"{amount_text} total",
            "case_count": case_display,
            "immediate_actions": [
                template_action,
                f"Review recent transactions exhibiting {name.lower()} indicators",
                "Notify fraud analytics to monitor for emerging variants",
                "Document findings and link to active investigations"
            ],
            "prevention_steps": [
                template_prevention,
                "Tighten authentication or velocity limits tied to this pattern",
                "Add automated alerts for early warning signals",
                f"Train analysts on latest {name.lower()} red flags"
            ],
            "monitor": f"Trend lines, thresholds, and anomalies associated with {name.lower()}"
        }

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

