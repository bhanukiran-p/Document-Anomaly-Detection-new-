"""
Fraud Analysis Agent using LangChain and OpenAI GPT-4
Provides intelligent fraud recommendations based on ML scores and extracted data
"""

import os
import re
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not installed. AI analysis will use fallback mode.")

from .prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_TEMPLATE,
    RECOMMENDATION_GUIDELINES
)
from .tools import DataAccessTools


class FraudAnalysisAgent:
    """
    AI-powered fraud analysis agent using OpenAI GPT-4
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "gpt-4",
                 data_tools: Optional[DataAccessTools] = None):
        """
        Initialize fraud analysis agent

        Args:
            api_key: OpenAI API key (if None, reads from env)
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)
            data_tools: Data access tools for CSV reading
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model
        self.data_tools = data_tools
        self.llm = None

        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    openai_api_key=self.api_key,
                    temperature=0.3,  # Lower temperature for consistent analysis
                    max_tokens=1500
                )
                print(f"Initialized LangChain agent with {self.model_name}")
            except Exception as e:
                print(f"Warning: Could not initialize LangChain: {e}")
                print("Falling back to rule-based analysis")
                self.llm = None
        else:
            if not LANGCHAIN_AVAILABLE:
                print("LangChain not available - using fallback analysis")
            elif not self.api_key:
                print("OpenAI API key not found - using fallback analysis")
            self.llm = None

    def analyze_fraud(self,
                      ml_analysis: Dict,
                      extracted_data: Dict,
                      customer_id: Optional[str] = None) -> Dict:
        """
        Perform AI-powered fraud analysis

        Args:
            ml_analysis: ML model fraud analysis results
            extracted_data: Extracted money order fields
            customer_id: Customer ID for history lookup

        Returns:
            Dictionary with AI analysis and recommendation
        """
        if self.llm is not None:
            try:
                return self._llm_analysis(ml_analysis, extracted_data, customer_id)
            except Exception as e:
                print(f"Error in LLM analysis: {e}")
                print("Falling back to rule-based analysis")
                return self._fallback_analysis(ml_analysis, extracted_data)
        else:
            return self._fallback_analysis(ml_analysis, extracted_data)

    def _llm_analysis(self,
                      ml_analysis: Dict,
                      extracted_data: Dict,
                      customer_id: Optional[str]) -> Dict:
        """
        Perform LLM-based fraud analysis using GPT-4
        """
        # Gather customer history if available
        customer_history = "No customer history available"
        if customer_id and self.data_tools:
            history_data = self.data_tools.get_customer_history(customer_id)
            customer_history = self.data_tools.format_customer_history_summary(customer_id)

        # Search for similar fraud cases
        similar_cases = "No similar cases found"
        if self.data_tools:
            issuer = extracted_data.get('issuer', '')
            amount_str = extracted_data.get('amount', '0')
            amount = float(amount_str.replace('$', '').replace(',', '') if amount_str else 0)

            if amount > 0:
                cases = self.data_tools.search_similar_fraud_cases(
                    issuer=issuer,
                    amount_range=(amount * 0.8, amount * 1.2),  # ±20% range
                    limit=3
                )
                similar_cases = self.data_tools.format_fraud_cases_summary(cases)

        # Get training dataset patterns
        training_patterns = "Training dataset not available"
        if self.data_tools:
            training_patterns = self.data_tools.format_training_patterns_summary()

        # Search for similar past analysis cases
        past_similar_cases = "No similar past analyses found"
        if self.data_tools:
            issuer = extracted_data.get('issuer', '')
            amount_str = extracted_data.get('amount', '0')
            amount = float(amount_str.replace('$', '').replace(',', '') if amount_str else 0)

            if amount > 0:
                past_analyses = self.data_tools.search_stored_analyses(
                    issuer=issuer,
                    amount_range=(amount * 0.8, amount * 1.2),  # ±20% range
                    limit=3
                )
                past_similar_cases = self.data_tools.format_past_analyses_summary(past_analyses)

        # Format fraud indicators
        fraud_indicators = "\n".join(
            [f"- {ind}" for ind in ml_analysis.get('feature_importance', [])]
        ) or "No specific indicators identified"

        # Create the prompt
        system_message = SystemMessagePromptTemplate.from_template(
            SYSTEM_PROMPT + "\n\n" + RECOMMENDATION_GUIDELINES
        )

        human_message = HumanMessagePromptTemplate.from_template(
            ANALYSIS_TEMPLATE
        )

        chat_prompt = ChatPromptTemplate.from_messages([
            system_message,
            human_message
        ])

        # Format the messages
        messages = chat_prompt.format_messages(
            fraud_risk_score=ml_analysis.get('fraud_risk_score', 0),
            risk_level=ml_analysis.get('risk_level', 'UNKNOWN'),
            model_confidence=ml_analysis.get('model_confidence', 0),
            rf_score=ml_analysis.get('model_scores', {}).get('random_forest', 0),
            xgb_score=ml_analysis.get('model_scores', {}).get('xgboost', 0),
            issuer=extracted_data.get('issuer', 'N/A'),
            serial_number=extracted_data.get('serial_number', 'N/A'),
            amount=extracted_data.get('amount', 'N/A'),
            amount_in_words=extracted_data.get('amount_in_words', 'N/A'),
            payee=extracted_data.get('payee', 'N/A'),
            purchaser=extracted_data.get('purchaser', 'N/A'),
            date=extracted_data.get('date', 'N/A'),
            location=extracted_data.get('location', 'N/A'),
            receipt_number=extracted_data.get('receipt_number', 'N/A'),
            signature=extracted_data.get('signature', 'N/A'),
            fraud_indicators=fraud_indicators,
            customer_id=customer_id or "N/A",
            customer_history=customer_history,
            similar_cases=similar_cases,
            training_patterns=training_patterns,
            past_similar_cases=past_similar_cases
        )

        # Get LLM response
        response = self.llm(messages)
        analysis_text = response.content

        # Parse the response
        return self._parse_llm_response(analysis_text, ml_analysis)

    def _parse_llm_response(self, response_text: str, ml_analysis: Dict) -> Dict:
        """
        Parse LLM response into structured format
        """
        # Extract recommendation
        recommendation_match = re.search(r'RECOMMENDATION:\s*(APPROVE|REJECT|ESCALATE)', response_text, re.IGNORECASE)
        recommendation = recommendation_match.group(1).upper() if recommendation_match else 'ESCALATE'

        # Extract confidence
        confidence_match = re.search(r'CONFIDENCE:\s*(\d+)%?', response_text)
        confidence = int(confidence_match.group(1)) / 100 if confidence_match else 0.75

        # Extract summary
        summary_match = re.search(r'SUMMARY:\s*([^\n]+)', response_text)
        summary = summary_match.group(1).strip() if summary_match else "Fraud analysis completed"

        # Extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.*?)(?=KEY_INDICATORS:|VERIFICATION_NOTES:|$)', response_text, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else response_text

        # Extract key indicators
        indicators_match = re.search(r'KEY_INDICATORS:\s*(.*?)(?=VERIFICATION_NOTES:|$)', response_text, re.DOTALL)
        indicators_text = indicators_match.group(1).strip() if indicators_match else ""
        key_indicators = [line.strip('- ').strip() for line in indicators_text.split('\n') if line.strip()]

        # Extract verification notes
        verification_match = re.search(r'VERIFICATION_NOTES:\s*(.*?)(?=ACTIONABLE_RECOMMENDATIONS:|TRAINING_INSIGHTS:|HISTORICAL_COMPARISON:|$)', response_text, re.DOTALL)
        verification_notes = verification_match.group(1).strip() if verification_match else ""

        # Extract actionable recommendations
        recommendations_match = re.search(r'ACTIONABLE_RECOMMENDATIONS:\s*(.*?)(?=TRAINING_INSIGHTS:|HISTORICAL_COMPARISON:|$)', response_text, re.DOTALL)
        recommendations_text = recommendations_match.group(1).strip() if recommendations_match else ""
        recommendations = [line.strip('- ').strip() for line in recommendations_text.split('\n') if line.strip()]
        
        # Ensure we have at least 3 recommendations if possible, or use defaults
        if not recommendations:
            recommendations = ["Verify customer identification", "Check for physical alteration signs", "Validate serial number pattern"]

        # Extract training insights
        training_insights_match = re.search(r'TRAINING_INSIGHTS:\s*(.*?)(?=HISTORICAL_COMPARISON:|$)', response_text, re.DOTALL)
        training_insights = training_insights_match.group(1).strip() if training_insights_match else ""

        # Extract historical comparison
        historical_comparison_match = re.search(r'HISTORICAL_COMPARISON:\s*(.*?)$', response_text, re.DOTALL)
        historical_comparison = historical_comparison_match.group(1).strip() if historical_comparison_match else ""

        return {
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'summary': summary,
            'reasoning': reasoning,
            'key_indicators': key_indicators[:5],  # Limit to top 5
            'key_indicators': key_indicators[:5],  # Limit to top 5
            'verification_notes': verification_notes,
            'actionable_recommendations': recommendations[:3],  # Limit to top 3
            'training_insights': training_insights,
            'historical_comparison': historical_comparison,
            'analysis_type': 'llm',
            'model_used': self.model_name
        }

    def _fallback_analysis(self, ml_analysis: Dict, extracted_data: Dict) -> Dict:
        """
        Rule-based fallback analysis when LLM is not available
        """
        fraud_score = ml_analysis.get('fraud_risk_score', 0)
        risk_level = ml_analysis.get('risk_level', 'UNKNOWN')
        model_confidence = ml_analysis.get('model_confidence', 0)

        # Determine recommendation based on score and risk level
        if fraud_score < 0.3 and model_confidence > 0.8:
            recommendation = 'APPROVE'
            confidence = 0.85
            summary = f"Low fraud risk ({fraud_score:.1%}). Transaction appears legitimate."
            reasoning = "ML models show low fraud probability with high confidence. All critical fields validated."
        elif fraud_score > 0.85 or risk_level == 'CRITICAL':
            recommendation = 'REJECT'
            confidence = 0.90
            summary = f"High fraud risk ({fraud_score:.1%}). Multiple red flags detected."
            reasoning = "ML models indicate high probability of fraud. Critical anomalies found."
        else:
            recommendation = 'ESCALATE'
            confidence = 0.75
            summary = f"Moderate fraud risk ({fraud_score:.1%}). Requires manual review."
            reasoning = "ML models show moderate risk. Some anomalies present but not conclusive."
            
        # Generate actionable recommendations based on risk
        if recommendation == 'APPROVE':
            actionable_recommendations = [
                "Proceed with transaction processing",
                "Verify customer ID matches payee/purchaser",
                "Ensure endorsement is present on back"
            ]
        elif recommendation == 'REJECT':
            actionable_recommendations = [
                "Decline transaction immediately",
                "Do not return document if confiscation policy applies",
                "Report incident to fraud department"
            ]
        else:  # ESCALATE
            actionable_recommendations = [
                "Request secondary form of identification",
                "Contact issuer verification hotline",
                "Hold funds for 24-hour verification period"
            ]

        # Use ML-identified indicators
        key_indicators = ml_analysis.get('feature_importance', [])[:5]

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'summary': summary,
            'reasoning': reasoning,
            'key_indicators': key_indicators,
            'key_indicators': key_indicators,
            'verification_notes': "Manual verification recommended for borderline cases",
            'actionable_recommendations': actionable_recommendations,
            'training_insights': "N/A (fallback mode - training data not analyzed)",
            'historical_comparison': "N/A (fallback mode - past cases not analyzed)",
            'analysis_type': 'rule_based',
            'model_used': 'fallback'
        }
