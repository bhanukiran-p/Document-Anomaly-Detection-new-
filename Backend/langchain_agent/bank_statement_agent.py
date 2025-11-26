"""
Specialized LangChain Agent for Bank Statement Fraud Analysis
Uses GPT-4 to provide intelligent fraud recommendations for bank statements
"""

import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not installed. Bank statement AI analysis will use fallback mode.")


BANK_STATEMENT_SYSTEM_PROMPT = """You are an expert financial fraud analyst specializing in bank statement anomaly detection.
Your role is to analyze bank statement data and provide informed fraud risk assessments.

When analyzing bank statements, consider:
1. Transaction patterns and unusual activity
2. Balance consistency and arithmetic accuracy
3. Large or suspicious transactions
4. Account activity intensity
5. Customer profile consistency
6. Seasonal and temporal anomalies
7. Geographic and behavioral inconsistencies

Provide clear, actionable recommendations with confidence levels.
Always explain the reasoning behind your assessment."""

BANK_STATEMENT_ANALYSIS_TEMPLATE = """Analyze this bank statement for fraud risk:

STATEMENT INFORMATION:
- Bank: {bank_name}
- Account Holder: {account_holder}
- Account Number: {account_number_masked}
- Statement Period: {statement_period}
- Statement Date: {statement_date}

BALANCE INFORMATION:
- Opening Balance: {opening_balance}
- Closing Balance: {closing_balance}
- Net Activity: {net_activity}
- Total Credits: {total_credits}
- Total Debits: {total_debits}

TRANSACTION ANALYSIS:
- Transaction Count: {transaction_count}
- Average Transaction Amount: {avg_transaction}
- Largest Transaction: {largest_transaction}
- Transaction Variance: {transaction_variance}
- Date Range Anomalies: {date_anomalies}

RISK ANALYSIS:
- ML Fraud Risk Score: {ml_risk_score}/100
- Risk Level: {risk_level}
- Identified Risk Factors:
{risk_factors}

EXTRACTED DATA QUALITY:
- Text Quality Score: {text_quality}
- Suspicious Keywords Found: {suspicious_keywords}
- Data Completeness: {data_completeness}%

Based on this analysis, provide:
1. Fraud Risk Assessment (HIGH/MEDIUM/LOW)
2. Confidence Level (0-100%)
3. Key Concerns (bullet points)
4. Recommendation (APPROVE/ESCALATE/REJECT)
5. Reasoning
6. Suggested Next Steps

Format your response as JSON with these exact fields:
{{
    "risk_assessment": "HIGH|MEDIUM|LOW",
    "confidence": 0-100,
    "key_concerns": ["concern1", "concern2", ...],
    "recommendation": "APPROVE|ESCALATE|REJECT",
    "reasoning": "explanation",
    "next_steps": ["step1", "step2", ...],
    "summary": "brief summary"
}}"""


class BankStatementFraudAnalysisAgent:
    """
    AI-powered fraud analysis agent specialized for bank statements
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize bank statement fraud analysis agent

        Args:
            api_key: OpenAI API key (if None, reads from env)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.llm = None
        self.available = False

        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.llm = ChatOpenAI(
                    model="gpt-4",
                    openai_api_key=self.api_key,
                    temperature=0.3,  # Consistent analysis
                    max_tokens=1500
                )
                self.available = True
                print("Bank Statement AI Agent initialized with GPT-4")
            except Exception as e:
                print(f"Warning: Could not initialize bank statement AI agent: {e}")
                self.available = False
        else:
            if not LANGCHAIN_AVAILABLE:
                print("LangChain not available - bank statement AI analysis disabled")
            elif not self.api_key:
                print("OpenAI API key not found - bank statement AI analysis disabled")

    def analyze(self, ml_results: Dict, bank_data: Dict) -> Dict:
        """
        Perform AI-powered fraud analysis for bank statement

        Args:
            ml_results: ML model analysis results including risk score and factors
            bank_data: Extracted bank statement data

        Returns:
            Dictionary with AI analysis results
        """
        if not self.available or not self.llm:
            return self._fallback_analysis(ml_results, bank_data)

        try:
            # Prepare analysis prompt
            analysis_prompt = self._build_analysis_prompt(ml_results, bank_data)

            # Create messages
            messages = [
                SystemMessage(content=BANK_STATEMENT_SYSTEM_PROMPT),
                HumanMessage(content=analysis_prompt)
            ]

            # Get LLM response
            response = self.llm.invoke(messages)
            response_text = response.content

            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)
                    result['source'] = 'gpt-4'
                    result['success'] = True
                    return result
            except json.JSONDecodeError:
                # If JSON parsing fails, extract key info from text
                return self._parse_text_response(response_text, ml_results)

        except Exception as e:
            print(f"Error during bank statement AI analysis: {e}")
            return self._fallback_analysis(ml_results, bank_data)

    def _build_analysis_prompt(self, ml_results: Dict, bank_data: Dict) -> str:
        """Build the analysis prompt from data"""
        summary = bank_data.get('summary', {})
        balances = bank_data.get('balances', {})
        transactions = bank_data.get('transactions', [])

        # Calculate transaction statistics
        largest_txn = 0
        if transactions:
            for txn in transactions:
                if isinstance(txn, dict):
                    try:
                        amt = float(str(txn.get('amount_value', 0)).replace('$', '').replace(',', ''))
                        if abs(amt) > abs(largest_txn):
                            largest_txn = amt
                    except:
                        pass

        # Format risk factors
        factors = ml_results.get('risk_factors', [])
        factors_str = '\n'.join([f"  - {factor}" for factor in factors]) if factors else "  - None identified"

        # Mask account number
        account_num = bank_data.get('account_number', 'UNKNOWN')
        masked_account = f"****{account_num[-4:]}" if len(str(account_num)) > 4 else "****"

        return BANK_STATEMENT_ANALYSIS_TEMPLATE.format(
            bank_name=bank_data.get('bank_name', 'Unknown'),
            account_holder=bank_data.get('account_holder', 'Unknown'),
            account_number_masked=masked_account,
            statement_period=bank_data.get('statement_period', 'Unknown'),
            statement_date=bank_data.get('statement_date', 'Unknown'),
            opening_balance=balances.get('opening_balance', 'Unknown'),
            closing_balance=balances.get('closing_balance', 'Unknown'),
            net_activity=summary.get('net_activity', 'Unknown'),
            total_credits=summary.get('total_credits', 'Unknown'),
            total_debits=summary.get('total_debits', 'Unknown'),
            transaction_count=len(transactions),
            avg_transaction=f"${summary.get('avg_transaction_amount', 0):.2f}",
            largest_transaction=f"${largest_txn:.2f}",
            transaction_variance=f"${summary.get('transaction_variance', 0):.2f}",
            date_anomalies=summary.get('date_anomalies', 'None'),
            ml_risk_score=ml_results.get('risk_score', 0),
            risk_level=ml_results.get('risk_level', 'UNKNOWN'),
            risk_factors=factors_str,
            text_quality=f"{summary.get('text_quality', 0.8):.2f}",
            suspicious_keywords=summary.get('suspicious_keyword_count', 0),
            data_completeness=int(summary.get('data_completeness', 0) * 100)
        )

    def _fallback_analysis(self, ml_results: Dict, bank_data: Dict) -> Dict:
        """
        Fallback analysis when GPT-4 is unavailable

        Args:
            ml_results: ML model results
            bank_data: Bank statement data

        Returns:
            Dictionary with analysis results
        """
        score = ml_results.get('risk_score', 0)
        level = ml_results.get('risk_level', 'UNKNOWN')
        factors = ml_results.get('risk_factors', [])

        # Determine recommendation based on ML score
        if level == 'CRITICAL':
            recommendation = 'REJECT'
            confidence = 95
        elif level == 'HIGH':
            recommendation = 'ESCALATE'
            confidence = 85
        elif level == 'MEDIUM':
            recommendation = 'ESCALATE'
            confidence = 75
        else:
            recommendation = 'APPROVE'
            confidence = 70

        return {
            'risk_assessment': level,
            'confidence': confidence,
            'key_concerns': factors[:3] if factors else [],
            'recommendation': recommendation,
            'reasoning': f"Risk score of {score:.0f}/100 indicates {level.lower()} fraud risk based on transaction patterns and data consistency analysis.",
            'next_steps': [
                "Manual review recommended" if level in ['HIGH', 'CRITICAL'] else "Standard processing",
            ],
            'summary': f"{level} fraud risk ({score:.0f}%)",
            'source': 'rule_based_fallback',
            'success': True
        }

    def _parse_text_response(self, response_text: str, ml_results: Dict) -> Dict:
        """
        Parse text response when JSON parsing fails

        Args:
            response_text: LLM response text
            ml_results: ML results for fallback

        Returns:
            Structured analysis dictionary
        """
        # Fallback to rule-based if parsing fails
        return self._fallback_analysis(ml_results, {})
