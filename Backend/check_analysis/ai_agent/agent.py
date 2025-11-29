"""
Dedicated Check Fraud Analysis Agent
"""

import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .prompts import CHECK_SYSTEM_PROMPT, CHECK_ANALYSIS_TEMPLATE

logger = logging.getLogger(__name__)

class CheckFraudAnalysisAgent:
    """
    Agent for analyzing check fraud
    """

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.llm = ChatOpenAI(
            temperature=0,
            model=model,
            api_key=api_key
        )

    def analyze(self, extracted_data: Dict[str, Any], ml_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run AI analysis on check data
        """
        try:
            # Prepare prompt variables
            amount = extracted_data.get('amount_numeric')
            if isinstance(amount, dict):
                amount = amount.get('value')
            
            prompt_vars = {
                "bank_name": extracted_data.get('bank_name') or extracted_data.get('issuer_name'),
                "payee_name": extracted_data.get('payee_name') or extracted_data.get('recipient'),
                "amount": amount,
                "date": extracted_data.get('date'),
                "check_number": extracted_data.get('check_number') or extracted_data.get('serial_primary'),
                "signature_detected": extracted_data.get('signature_detected'),
                "fraud_score": ml_analysis.get('fraud_score', 0),
                "risk_level": ml_analysis.get('risk_level', 'UNKNOWN'),
                "risk_factors": ml_analysis.get('anomalies', [])
            }

            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", CHECK_SYSTEM_PROMPT),
                ("user", CHECK_ANALYSIS_TEMPLATE)
            ])

            # Run chain
            chain = prompt | self.llm
            response = chain.invoke(prompt_vars)
            
            # Parse response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"AI Analysis failed: {e}")
            return {
                "recommendation": "ESCALATE",
                "confidence_score": 0.0,
                "reasoning": f"AI Analysis failed: {str(e)}",
                "risk_factors": ["AI_FAILURE"]
            }
