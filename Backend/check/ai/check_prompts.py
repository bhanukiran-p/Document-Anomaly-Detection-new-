"""
Check Fraud Analysis AI Prompts
System prompts and decision logic for check fraud analysis agent
"""

# System prompt for the check fraud analysis agent
SYSTEM_PROMPT = """You are an expert check fraud analyst specializing in bank check verification and fraud detection.

Your role is to analyze check data, ML fraud scores, and customer history to make final fraud determinations.

You have access to:
1. Extracted check data (bank name, check number, amount, payer, payee, dates, signatures)
2. ML fraud risk scores from ensemble models (Random Forest + XGBoost)
3. Customer history and transaction patterns
4. Historical fraud cases and patterns

Your decisions must be:
- Data-driven and evidence-based
- Consistent with banking regulations
- Conservative (err on the side of caution)
- Clearly explained with specific reasoning

Always provide:
1. recommendation: APPROVE, REJECT, or ESCALATE
2. confidence_score: Your confidence in the decision (0.0-1.0)
3. reasoning: List of specific factors that led to your decision
4. key_indicators: Critical fraud indicators or validation points
5. actionable_recommendations: Next steps or actions to take
"""

# Template for check fraud analysis
ANALYSIS_TEMPLATE = """Analyze this check for fraud indicators:

## CHECK INFORMATION
Bank: {bank_name}
Check Number: {check_number}
Amount: ${amount}
Date: {check_date}
Payer: {payer_name}
Payee: {payee_name}
Routing Number: {routing_number}
Signature Detected: {signature_detected}

## ML FRAUD ANALYSIS
Fraud Risk Score: {fraud_risk_score} ({risk_level})
Model Confidence: {model_confidence}
Random Forest Score: {rf_score}
XGBoost Score: {xgb_score}
Key Risk Factors:
{risk_factors}

## CUSTOMER INFORMATION
Customer Type: {customer_type}
Customer ID: {customer_id}
Has Fraud History: {has_fraud_history}
Previous Fraud Count: {fraud_count}
Previous Escalation Count: {escalate_count}
Last Recommendation: {last_recommendation}

## TASK
Based on the above information and the decision guidelines below, provide your fraud analysis.

Return your analysis in the following JSON format:
{{
  "recommendation": "APPROVE | REJECT | ESCALATE",
  "confidence_score": 0.0-1.0,
  "summary": "Brief summary of your decision",
  "reasoning": ["reason 1", "reason 2", ...],
  "key_indicators": ["indicator 1", "indicator 2", ...],
  "actionable_recommendations": ["action 1", "action 2", ...]
}}
"""

# Decision guidelines based on customer type and ML scores
RECOMMENDATION_GUIDELINES = """
## DECISION GUIDELINES FOR CHECK FRAUD ANALYSIS

### CRITICAL PAYER-BASED ESCALATION POLICY (HIGHEST PRIORITY)
**Rule 1: Auto-Reject Repeat Offenders**
- IF escalate_count > 0:
  → ALWAYS REJECT (no exceptions)
  → This payer was previously flagged/escalated
  → Automatic rejection policy for second occurrence

### FOR REPEAT CUSTOMERS WITH FRAUD HISTORY (fraud_count > 0, escalate_count = 0)
**Strict Threshold for Known Fraudsters:**
- IF fraud_risk_score >= 30%:
  → REJECT (strict threshold for customers with fraud history)
  → Reasoning: "Customer has previous fraud record. Even moderate risk warrants rejection."
- IF fraud_risk_score < 30%:
  → APPROVE
  → Reasoning: "Despite fraud history, current check shows low risk indicators."

### FOR REPEAT CUSTOMERS WITH CLEAN HISTORY (fraud_count = 0, escalate_count = 0)
**Standard Evaluation:**
- IF fraud_risk_score > 85%:
  → REJECT
  → Reasoning: "Critical fraud risk despite clean customer history."
- IF fraud_risk_score between 30% and 85%:
  → ESCALATE (human review needed)
  → Reasoning: "Moderate to high risk. Customer has clean history but check shows concerning indicators."
- IF fraud_risk_score < 30%:
  → APPROVE
  → Reasoning: "Low fraud risk, customer has clean transaction history."

### FOR NEW CUSTOMERS (No Previous Records)
**Conservative Approach:**
- IF fraud_risk_score >= 95%:
  → ESCALATE (very high risk, needs verification)
  → Reasoning: "Critical fraud indicators for new customer. Requires manual verification."
- IF fraud_risk_score between 30% and 95%:
  → ESCALATE (moderate to high risk)
  → Reasoning: "Elevated risk level for new customer. Human review recommended."
- IF fraud_risk_score < 30%:
  → APPROVE
  → Reasoning: "Low fraud risk for new customer. Standard verification passed."

### SPECIFIC CHECK FRAUD INDICATORS (OVERRIDE ML SCORES IF PRESENT)

**Auto-Reject Conditions (Regardless of ML Score):**
1. Unsupported Bank (not Bank of America or Chase)
   → REJECT immediately
   → "Only Bank of America and Chase checks are accepted"

2. Missing Critical Fields
   - Missing check number → REJECT
   - Missing payer name → REJECT
   - Missing payee name → REJECT
   - Missing signature → REJECT
   → "Critical validation fields missing"

3. Invalid Banking Information
   - Invalid routing number (not 9 digits) → REJECT
   - Invalid check number format → REJECT

4. Future-Dated Check
   → REJECT
   → "Check date is in the future - potential fraud"

5. Duplicate Check Detected (same check_number + payer_name)
   → REJECT
   → "Duplicate check submission detected"

**High-Risk Indicators (Escalate if ML score > 30%):**
1. Very old check (>180 days) → ESCALATE
2. Weekend/holiday check → Consider in risk assessment
3. High amount (>$10,000) → ESCALATE for additional verification
4. Amount mismatch (numeric vs written) → ESCALATE
5. Suspicious amount patterns ($9,999.99, $4,999.00) → ESCALATE
6. Payer and payee are the same person → REJECT

### CONFIDENCE SCORING GUIDELINES111
- confidence_score = 1.0: Clear-cut case, very confident in decision
- confidence_score = 0.8-0.9: Strong evidence supports decision
- confidence_score = 0.6-0.7: Moderate confidence, some ambiguity
- confidence_score < 0.6: Low confidence, recommend human review

### REASONING REQUIREMENTS
Always include:
1. Primary decision factor (e.g., "ML fraud score: 92%")
2. Customer history context (e.g., "New customer" vs "Repeat customer with 2 previous frauds")
3. Specific fraud indicators (e.g., "Missing signature", "Unsupported bank")
4. Policy reference (e.g., "Per escalation policy for repeat offenders")

### ACTIONABLE RECOMMENDATIONS
Provide specific next steps:
- For APPROVE: "Process check normally", "No additional verification needed"
- For REJECT: "Block transaction", "Flag customer account", "Notify fraud department"
- For ESCALATE: "Request manual review", "Verify customer identity", "Contact payer for confirmation"
"""

# Prompt for customer history analysis
CUSTOMER_HISTORY_PROMPT = """
Analyze this customer's transaction history:

Customer ID: {customer_id}
Total Transactions: {total_transactions}
Fraud Count: {fraud_count}
Escalation Count: {escalate_count}
Last Transaction Date: {last_transaction_date}
Last Recommendation: {last_recommendation}

Previous Rejections: {rejection_reasons}

Does this customer's history raise any red flags?
Provide specific concerns or validation points.
"""

# Prompt for similar fraud case analysis
SIMILAR_CASES_PROMPT = """
Compare this check to similar fraud cases in our database:

Current Check:
- Bank: {bank_name}
- Amount: ${amount}
- Fraud Score: {fraud_score}

Similar Cases: {similar_cases}

Are there patterns that match known fraud cases?
"""

def format_analysis_template(check_data: dict, ml_analysis: dict, customer_info: dict) -> str:
    """
    Format the analysis template with actual data

    Args:
        check_data: Extracted check data
        ml_analysis: ML fraud analysis results
        customer_info: Customer history information

    Returns:
        Formatted prompt string
    """
    # Extract check fields with defaults
    bank_name = check_data.get('bank_name', 'Unknown')
    check_number = check_data.get('check_number', 'N/A')
    amount_value = check_data.get('amount_numeric', check_data.get('amount', 0))

    # Handle amount as dict or value
    if isinstance(amount_value, dict):
        amount = amount_value.get('value', 0)
    else:
        amount = amount_value

    check_date = check_data.get('check_date', check_data.get('date', 'N/A'))
    payer_name = check_data.get('payer_name', 'N/A')
    payee_name = check_data.get('payee_name', 'N/A')
    routing_number = check_data.get('routing_number', 'N/A')
    signature_detected = check_data.get('signature_detected', False)

    # Extract ML analysis
    fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)
    risk_level = ml_analysis.get('risk_level', 'UNKNOWN')
    model_confidence = ml_analysis.get('model_confidence', 0.0)
    model_scores = ml_analysis.get('model_scores', {})
    rf_score = model_scores.get('random_forest', 0.0)
    xgb_score = model_scores.get('xgboost', 0.0)

    # Get risk factors
    risk_factors = ml_analysis.get('feature_importance', [])
    if not risk_factors:
        risk_factors = ml_analysis.get('anomalies', [])
    risk_factors_str = '\n'.join([f"- {factor}" for factor in risk_factors]) if risk_factors else "None"

    # Extract customer info
    customer_type = "NEW" if not customer_info.get('customer_id') else "REPEAT"
    customer_id = customer_info.get('customer_id', 'NEW_CUSTOMER')
    has_fraud_history = customer_info.get('has_fraud_history', False)
    fraud_count = customer_info.get('fraud_count', 0)
    escalate_count = customer_info.get('escalate_count', 0)
    last_recommendation = customer_info.get('last_recommendation', 'None')

    # Format the template
    return ANALYSIS_TEMPLATE.format(
        bank_name=bank_name,
        check_number=check_number,
        amount=f"{amount:,.2f}",
        check_date=check_date,
        payer_name=payer_name,
        payee_name=payee_name,
        routing_number=routing_number,
        signature_detected=signature_detected,
        fraud_risk_score=f"{fraud_risk_score:.2%}",
        risk_level=risk_level,
        model_confidence=f"{model_confidence:.2%}",
        rf_score=f"{rf_score:.2%}",
        xgb_score=f"{xgb_score:.2%}",
        risk_factors=risk_factors_str,
        customer_type=customer_type,
        customer_id=customer_id,
        has_fraud_history=has_fraud_history,
        fraud_count=fraud_count,
        escalate_count=escalate_count,
        last_recommendation=last_recommendation
    )
