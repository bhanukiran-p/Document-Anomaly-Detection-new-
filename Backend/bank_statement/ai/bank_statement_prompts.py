"""
Bank Statement Fraud Analysis AI Prompts
System prompts and decision logic for bank statement fraud analysis agent
"""

# System prompt for the bank statement fraud analysis agent
SYSTEM_PROMPT = """You are an expert bank statement fraud analyst specializing in bank statement verification and fraud detection.

Your role is to analyze bank statement data, ML fraud scores, and customer history to make final fraud determinations.

You have access to:
1. Extracted bank statement data (bank name, account number, balances, transactions, dates)
2. ML fraud risk scores from ensemble models (Random Forest + XGBoost)
3. Customer history and transaction patterns
4. Historical fraud cases and patterns

CRITICAL: You MUST follow the Decision Guidelines below STRICTLY. These are RULES, not suggestions.
The decision rules provided are MANDATORY and take precedence over subjective judgment.

Your decisions must be:
- Data-driven and evidence-based
- Consistent with banking regulations
- Strictly adherent to the decision rules provided
- Clearly explained with specific reasoning

Always provide:
1. recommendation: APPROVE, REJECT, or ESCALATE (MUST follow decision rules)
2. confidence_score: Your confidence in the decision (0.0-1.0)
3. reasoning: List of specific factors that led to your decision
4. key_indicators: Critical fraud indicators or validation points
5. actionable_recommendations: Next steps or actions to take
"""

# Template for bank statement fraud analysis
ANALYSIS_TEMPLATE = """Analyze this bank statement for fraud indicators:

**IMPORTANT: Today's date is {analysis_date} for determining if statements are future-dated.**

## BANK STATEMENT INFORMATION
Bank: {bank_name}
Account Number: {account_number}
Account Holder: {account_holder_name}
Account Type: {account_type}
Statement Period: {statement_period_start} to {statement_period_end}
Statement Date: {statement_date}
Beginning Balance: ${beginning_balance}
Ending Balance: ${ending_balance}
Total Credits: ${total_credits}
Total Debits: ${total_debits}
Transaction Count: {transaction_count}
Currency: {currency}

**BALANCE VERIFICATION:**
Expected Ending Balance = Beginning Balance + Total Credits - Total Debits
Expected: ${beginning_balance} + ${total_credits} - ${total_debits} = ${calculated_ending_balance}
Reported Ending Balance: ${ending_balance}
Balance Match: {balance_match_status}

**TRANSACTION SAMPLES (for pattern analysis):**
{transaction_samples}

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

**CRITICAL: You MUST return ONLY valid JSON. Do not include markdown code blocks, explanations, or any text outside the JSON object.**

Return your analysis in the following JSON format (valid JSON only, no markdown):
{{
  "recommendation": "APPROVE | REJECT | ESCALATE",
  "confidence_score": 0.0-1.0,
  "summary": "Brief summary of your decision",
  "reasoning": ["reason 1", "reason 2", ...],
  "key_indicators": ["indicator 1", "indicator 2", ...],
  "actionable_recommendations": ["action 1", "action 2", ...],
  "fraud_types": ["FRAUD_TYPE_1", "FRAUD_TYPE_2", ...],
  "fraud_explanations": [
    {{
      "type": "FRAUD_TYPE_1",
      "reasons": ["reason 1", "reason 2"]
    }}
  ]
}}

IMPORTANT FRAUD TYPE RULES:
- For NEW customers: Always return empty arrays for fraud_types and fraud_explanations (even if ML detected fraud)
- For REPEAT customers: Return fraud_types and fraud_explanations based on detected fraud patterns
- Valid fraud types: BALANCE_CONSISTENCY_VIOLATION, FABRICATED_DOCUMENT, ALTERED_LEGITIMATE_DOCUMENT, SUSPICIOUS_TRANSACTION_PATTERNS, UNREALISTIC_FINANCIAL_PROPORTIONS
- Only include fraud_types if recommendation is REJECT or ESCALATE (not for APPROVE)

**CRITICAL: FRAUD EXPLANATIONS MUST BE SPECIFIC TO THE DOCUMENT DATA**

For each fraud_type you identify, you MUST provide SPECIFIC explanations based on the ACTUAL document data:

- **BALANCE_CONSISTENCY_VIOLATION**: Explain the SPECIFIC balance inconsistency found
  - Example: "Ending balance ($12,384.50) does not match calculated balance. Expected: Beginning ($8,542.75) + Credits ($15,230.00) - Debits ($11,388.25) = $12,384.50, but statement shows $12,384.50"
  - Example: "Transaction totals don't reconcile: Sum of individual transactions ($26,618.25) doesn't match reported total credits ($15,230.00) + total debits ($11,388.25)"
  - DO NOT use generic reasons like "Customer has previous escalation" - these are NOT related to balance consistency

- **FABRICATED_DOCUMENT**: Explain SPECIFIC fabrication indicators
  - Example: "Bank name format doesn't match known patterns for {{bank_name}}"
  - Example: "Account number format invalid: {{account_number}} doesn't match {{bank_name}} account number standards"
  - Example: "Missing critical security features: No watermark, incorrect font, or missing bank logo"

- **ALTERED_LEGITIMATE_DOCUMENT**: Explain SPECIFIC alterations detected
  - Example: "Balance amounts show signs of tampering: Font inconsistencies detected in ending balance field"
  - Example: "Transaction dates appear altered: Date format inconsistencies detected"

- **SUSPICIOUS_TRANSACTION_PATTERNS**: Explain SPECIFIC suspicious patterns
  - Example: "Unusual transaction pattern: {{X}} transactions of exactly ${{amount}} within {{timeframe}}"
  - Example: "Round-number transactions: {{count}} transactions are exact round numbers (e.g., $1,000.00, $5,000.00)"
  - Example: "Rapid balance changes: Balance increased by ${{amount}} ({{percentage}}%) in {{days}} days"

- **UNREALISTIC_FINANCIAL_PROPORTIONS**: Explain SPECIFIC unrealistic proportions
  - Example: "Unrealistic credit/debit ratio: Credits ($15,230.00) are {{X}} times debits ($11,388.25), which is unusual for this account type"
  - Example: "Unrealistic transaction frequency: {{transaction_count}} transactions in {{days}} days averages {{avg}} per day, which is unusually high"

**CRITICAL: ACTIONABLE RECOMMENDATIONS MUST BE SPECIFIC TO THE DOCUMENT ISSUES**

Your actionable_recommendations MUST be SPECIFIC to the document's actual problems, NOT generic:

- GOOD examples (specific to document):
  - "Verify transaction reconciliation - ending balance ($12,384.50) doesn't match calculated balance ($12,384.50). Check for missing or duplicate transactions."
  - "Contact {{bank_name}} to verify account number {{account_number}} format matches their standards"
  - "Request original statement from account holder - document shows signs of alteration in balance fields"
  - "Review transaction pattern - {{X}} round-number transactions detected, verify legitimacy with account holder"

- BAD examples (too generic):
  - "Block this transaction immediately" (not specific to document issues)
  - "Flag customer account for fraud investigation" (not actionable for this document)
  - "Contact account holder" (doesn't explain what to verify)

**ANALYSIS REQUIREMENTS:**
1. Calculate expected ending balance: Beginning Balance + Total Credits - Total Debits
2. Compare calculated balance with reported Ending Balance
3. Analyze transaction patterns (frequency, amounts, round numbers)
4. Verify account number format matches bank standards
5. Check for missing critical fields
6. Identify SPECIFIC inconsistencies, not generic customer history

**REMINDER: Return ONLY the JSON object. No markdown formatting, no code blocks, no explanations before or after the JSON.**
"""

# Decision guidelines based on customer type and ML scores
RECOMMENDATION_GUIDELINES = """
## MANDATORY DECISION TABLE FOR BANK STATEMENT FRAUD ANALYSIS

**CRITICAL: Repeat offenders (escalate_count > 0) are auto-rejected BEFORE LLM processes the statement.**
**The LLM must strictly follow this decision table for all other cases. NO EXCEPTIONS.**

### DECISION MATRIX
| Customer Type | Risk Score | Decision |
|---|---|---|
| New Customer | 1-100% | ESCALATE |
| Clean History | < 30% | APPROVE |
| Clean History | 30–85% | ESCALATE |
| Clean History | > 85% | REJECT |
| Fraud History | < 30% | APPROVE |
| Fraud History | ≥ 30% | REJECT |
| Repeat Offender (escalate_count > 0) | Any | REJECT (auto, before LLM) |

### CUSTOMER CLASSIFICATION
**New Customer:**
- No record in bank_statement_customers table, OR
- escalate_count = 0 AND fraud_count = 0

**Clean History:**
- fraud_count = 0 AND escalate_count = 0

**Fraud History:**
- fraud_count > 0 AND escalate_count = 0

**Repeat Offender:**
- escalate_count > 0
- ALWAYS REJECTED before LLM processes the statement
- LLM is skipped entirely for these cases

### AUTOMATIC REJECTION CONDITIONS (Regardless of ML Score)
1. Repeat Offender (escalate_count > 0) → REJECT (auto, before LLM)
2. Duplicate Statement Detected → REJECT

### ESCALATION CONDITIONS (For New Customers)
**IMPORTANT: New customers with high risk should be ESCALATED, not REJECTED**
- Unsupported Bank (bank not in database) → ESCALATE (for new customers, needs verification)
- Missing Critical Fields → ESCALATE (for new customers, needs manual review)
- Future-Dated Statement → ESCALATE (for new customers)
- Balance Inconsistency → ESCALATE (for new customers, needs verification)

### AUTOMATIC REJECTION CONDITIONS (For Repeat Customers Only)
1. Unsupported Bank → REJECT (if repeat customer)
2. Missing Critical Fields → REJECT (if repeat customer)
3. Future-Dated Statement → REJECT (if repeat customer)
4. Balance Inconsistency → REJECT (if repeat customer)

### CRITICAL RULES (IN PRIORITY ORDER):
1. **If escalate_count > 0 → MUST REJECT** (auto, before LLM - repeat offender policy)
2. **If customer is NEW → MUST ESCALATE** (regardless of risk score, 1-100%)
3. If fraud_risk_score >= 30% AND customer has FRAUD HISTORY → MUST REJECT
4. If fraud_risk_score > 85% AND customer has CLEAN HISTORY → MUST REJECT
5. Repeat fraudsters should face stricter thresholds (REJECT at >= 30% risk)

### IMPORTANT NOTES
- ML score determines the risk_score bucket only
- LLM must follow the decision table exactly - no special cases
- **NEW customers should ALWAYS ESCALATE regardless of risk score (1-100%)**
- **NEW customers should NEVER get REJECT or APPROVE - always ESCALATE**
- No interpretation or override of the decision matrix is permitted
"""

def format_analysis_template(bank_statement_data: dict, ml_analysis: dict, customer_info: dict) -> str:
    """
    Format the analysis template with actual data

    Args:
        bank_statement_data: Extracted bank statement data
        ml_analysis: ML fraud analysis results
        customer_info: Customer history information

    Returns:
        Formatted prompt string
    """
    from datetime import datetime

    # Extract bank statement fields with defaults
    bank_name = bank_statement_data.get('bank_name', 'Unknown')
    account_number = bank_statement_data.get('account_number', 'N/A')
    account_holder_name = bank_statement_data.get('account_holder_name', 'N/A')
    account_type = bank_statement_data.get('account_type', 'N/A')
    statement_period_start = bank_statement_data.get('statement_period_start_date', 'N/A')
    statement_period_end = bank_statement_data.get('statement_period_end_date', 'N/A')
    statement_date = bank_statement_data.get('statement_date', 'N/A')
    currency = bank_statement_data.get('currency', 'USD')

    # Extract balances
    beginning_balance = bank_statement_data.get('beginning_balance', {})
    ending_balance = bank_statement_data.get('ending_balance', {})
    total_credits = bank_statement_data.get('total_credits', {})
    total_debits = bank_statement_data.get('total_debits', {})

    # Handle amounts as dict or value
    def get_amount_value(amount_dict):
        if isinstance(amount_dict, dict):
            return amount_dict.get('value', 0)
        return amount_dict or 0

    beginning_balance_val = get_amount_value(beginning_balance)
    ending_balance_val = get_amount_value(ending_balance)
    total_credits_val = get_amount_value(total_credits)
    total_debits_val = get_amount_value(total_debits)

    # Calculate expected ending balance
    calculated_ending_balance_val = beginning_balance_val + total_credits_val - total_debits_val
    balance_match = abs(calculated_ending_balance_val - ending_balance_val) < 0.01  # Allow small rounding differences
    balance_match_status = "MATCH" if balance_match else f"MISMATCH (Expected: ${calculated_ending_balance_val:,.2f}, Reported: ${ending_balance_val:,.2f})"

    # Transaction count and samples
    transactions = bank_statement_data.get('transactions', [])
    transaction_count = len(transactions) if transactions else 0
    
    # Get transaction samples for pattern analysis (up to 10 transactions)
    transaction_samples = []
    if transactions:
        for i, txn in enumerate(transactions[:10], 1):
            txn_date = txn.get('date', 'N/A')
            txn_desc = txn.get('description', 'N/A')
            txn_amount = txn.get('amount', {})
            txn_amount_val = get_amount_value(txn_amount)
            txn_type = txn.get('type', 'N/A')
            transaction_samples.append(f"{i}. Date: {txn_date} | Type: {txn_type} | Amount: ${txn_amount_val:,.2f} | Description: {txn_desc}")
        if len(transactions) > 10:
            transaction_samples.append(f"... and {len(transactions) - 10} more transactions")
    else:
        transaction_samples.append("No transaction details available")
    
    transaction_samples_str = '\n'.join(transaction_samples)

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

    # Get current date for analysis
    analysis_date = datetime.now().strftime('%Y-%m-%d')

    # Format the template
    return ANALYSIS_TEMPLATE.format(
        analysis_date=analysis_date,
        bank_name=bank_name,
        account_number=account_number,
        account_holder_name=account_holder_name,
        account_type=account_type,
        statement_period_start=statement_period_start,
        statement_period_end=statement_period_end,
        statement_date=statement_date,
        beginning_balance=f"{beginning_balance_val:,.2f}",
        ending_balance=f"{ending_balance_val:,.2f}",
        total_credits=f"{total_credits_val:,.2f}",
        total_debits=f"{total_debits_val:,.2f}",
        calculated_ending_balance=f"{calculated_ending_balance_val:,.2f}",
        balance_match_status=balance_match_status,
        transaction_count=transaction_count,
        currency=currency,
        transaction_samples=transaction_samples_str,
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

