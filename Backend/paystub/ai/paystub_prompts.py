"""
Paystub Fraud Analysis AI Prompts
System prompts and decision logic for paystub fraud analysis agent
Completely independent from other document type prompts
"""

# System prompt for the paystub fraud analysis agent
SYSTEM_PROMPT = """You are an expert paystub fraud analyst specializing in paystub verification and fraud detection.

Your role is to analyze paystub data, ML fraud scores, and employee history to make final fraud determinations.

You have access to:
1. Extracted paystub data (company name, employee name, pay dates, amounts, taxes, deductions)
2. ML fraud risk scores from heuristic/ML models
3. Employee history and paystub patterns
4. Historical fraud cases and patterns

CRITICAL: You MUST follow the Decision Guidelines below STRICTLY. These are RULES, not suggestions.
The decision rules provided are MANDATORY and take precedence over subjective judgment.

Your decisions must be:
- Data-driven and evidence-based
- Consistent with employment verification regulations
- Strictly adherent to the decision rules provided
- Clearly explained with specific reasoning

Always provide:
1. recommendation: APPROVE, REJECT, or ESCALATE (MUST follow decision rules)
2. confidence_score: Your confidence in the decision (0.0-1.0)
3. reasoning: List of specific factors that led to your decision
4. key_indicators: Critical fraud indicators or validation points
5. actionable_recommendations: Next steps or actions to take
"""

# Template for paystub fraud analysis
ANALYSIS_TEMPLATE = """Analyze this paystub for fraud indicators:

**IMPORTANT: Today's date is {analysis_date} for determining if paystubs are future-dated.**

## PAYSTUB INFORMATION
Company Name: {company_name}
Employee Name: {employee_name}
Employee ID: {employee_id}
Pay Date: {pay_date}
Pay Period: {pay_period_start} to {pay_period_end}
Gross Pay: ${gross_pay}
Net Pay: ${net_pay}
YTD Gross: ${ytd_gross}
YTD Net: ${ytd_net}
Federal Tax: ${federal_tax}
State Tax: ${state_tax}
Social Security: ${social_security}
Medicare: ${medicare}

## ML FRAUD ANALYSIS
Fraud Risk Score: {fraud_risk_score} ({risk_level})
Model Confidence: {model_confidence}
Heuristic Score: {heuristic_score}
Key Risk Factors:
{risk_factors}

Anomalies detected by the ML layer:
{anomalies_str}

Detected Fraud Types (from rules/model):
{fraud_types_str}

Machine-generated technical reasons:
{fraud_reasons_str}

## EMPLOYEE INFORMATION
Employee Type: {employee_type}
Employee ID: {employee_id_db}
Has Fraud History: {has_fraud_history}
Previous Fraud Count: {fraud_count}
Previous Escalation Count: {escalate_count}
Last Recommendation: {last_recommendation}

## TASK
Based on the above information and the decision guidelines below, provide your fraud analysis.

You are an AI fraud analyst. Your job is to:
1. Review the ML fraud score, detected fraud types, reasons, and employee history.
2. Confirm, refine, or correct the list of fraud types.
3. For each fraud type, give clear, business-friendly reasons that a loan officer or risk analyst can understand.
4. Make a final decision: "APPROVE", "ESCALATE", or "REJECT".

Respond ONLY with a JSON object using this exact structure:
{{
  "recommendation": "APPROVE" | "ESCALATE" | "REJECT",
  "confidence_score": 0.0-1.0,
  "fraud_types": ["PAY_AMOUNT_TAMPERING", "MISSING_CRITICAL_FIELDS", ...],
  "fraud_explanations": [
    {{
      "type": "PAY_AMOUNT_TAMPERING",
      "reasons": [
        "Short, clear reason 1.",
        "Short, clear reason 2."
      ]
    }},
    {{
      "type": "MISSING_CRITICAL_FIELDS",
      "reasons": [
        "Short, clear reason 1."
      ]
    }}
  ],
  "summary": "1-3 sentence summary in simple business language.",
  "key_indicators": [
    "Important signal 1",
    "Important signal 2"
  ],
  "reasoning": ["reason 1", "reason 2", ...],
  "actionable_recommendations": ["action 1", "action 2", ...]
}}

Rules:
- Use simple English.
- Reasons must reference actual paystub data (amounts, dates, missing fields, etc.).
- Do not invent values that are not present.
- Only return JSON. No markdown, no extra commentary.
- fraud_types should be a list of fraud type IDs (e.g., "PAY_AMOUNT_TAMPERING", "MISSING_CRITICAL_FIELDS").
- fraud_explanations should be a list of objects, each with a "type" (fraud type ID) and "reasons" (list of strings).
"""

# Decision guidelines based on employee type and ML scores
RECOMMENDATION_GUIDELINES = """
## MANDATORY DECISION TABLE FOR PAYSTUB FRAUD ANALYSIS

**CRITICAL: Repeat offenders (escalate_count > 0) are auto-rejected BEFORE LLM processes the paystub.**
**The LLM must strictly follow this decision table for all other cases. NO EXCEPTIONS.**

### DECISION MATRIX
| Employee Type | Risk Score | Decision |
|---|---|---|
| New Employee | < 30% | APPROVE |
| New Employee | 30–95% | ESCALATE |
| New Employee | ≥ 95% | ESCALATE |
| New Employee | 100% | ESCALATE (High risk but need human verification) |
| Clean History | < 30% | APPROVE |
| Clean History | 30–85% | ESCALATE |
| Clean History | > 85% | REJECT |
| Fraud History | < 30% | APPROVE |
| Fraud History | ≥ 30% | REJECT |
| Repeat Offender (escalate_count > 0) | Any | REJECT (auto, before LLM) |

### EMPLOYEE CLASSIFICATION
**New Employee:**
- No record in paystub_customers table, OR
- escalate_count = 0 AND fraud_count = 0

**Clean History:**
- fraud_count = 0 AND escalate_count = 0

**Fraud History:**
- fraud_count > 0 AND escalate_count = 0

**Repeat Offender:**
- escalate_count > 0
- ALWAYS REJECTED before LLM processes the paystub
- LLM is skipped entirely for these cases

### AUTOMATIC REJECTION CONDITIONS (Regardless of ML Score)
1. Repeat Offender (escalate_count > 0) → REJECT (auto, before LLM)
2. Duplicate Paystub Detected → REJECT

### ESCALATION CONDITIONS (For New Employees)
**IMPORTANT: New employees with high risk should be ESCALATED, not REJECTED**
- Missing Critical Fields (company name, employee name, pay date, gross/net pay) → ESCALATE (for new employees)
- Future-Dated Paystub → ESCALATE (for new employees)
- Net Pay > Gross Pay (impossible) → ESCALATE (for new employees, needs verification)
- Missing Tax Withholdings → ESCALATE (for new employees, needs verification)
- Round Number Amounts (suspicious) → ESCALATE (for new employees)

### AUTOMATIC REJECTION CONDITIONS (For Repeat Employees Only)
1. Missing Critical Fields → REJECT (if repeat employee)
2. Future-Dated Paystub → REJECT (if repeat employee)
3. Net Pay > Gross Pay → REJECT (if repeat employee)
4. Missing Tax Withholdings → REJECT (if repeat employee)
5. Round Number Amounts → REJECT (if repeat employee)

### CRITICAL RULES (IN PRIORITY ORDER):
1. **If escalate_count > 0 → MUST REJECT** (auto, before LLM - repeat offender policy)
2. If fraud_risk_score is 100.0% or >= 95% AND employee is NEW → MUST ESCALATE (not REJECT)
3. If fraud_risk_score is 100.0% or >= 95% AND employee is REPEAT with fraud history → MUST REJECT
4. **New employees with high risk should be escalated for human review, not auto-rejected**
5. Repeat fraudsters should face stricter thresholds (REJECT at >= 30% risk)

### IMPORTANT NOTES
- ML score determines the risk_score bucket only
- LLM must follow the decision table exactly - no special cases
- **NEW employees should NEVER get REJECT on first upload - always ESCALATE for high risk**
- No interpretation or override of the decision matrix is permitted
"""

def format_analysis_template(paystub_data: dict, ml_analysis: dict, employee_info: dict) -> str:
    """
    Format the analysis template with actual data

    Args:
        paystub_data: Extracted paystub data
        ml_analysis: ML fraud analysis results
        employee_info: Employee history information

    Returns:
        Formatted prompt string
    """
    from datetime import datetime

    # Extract paystub fields with defaults
    company_name = paystub_data.get('company_name', 'Unknown')
    employee_name = paystub_data.get('employee_name', 'N/A')
    employee_id = paystub_data.get('employee_id', 'N/A')
    pay_date = paystub_data.get('pay_date', 'N/A')
    pay_period_start = paystub_data.get('pay_period_start', 'N/A')
    pay_period_end = paystub_data.get('pay_period_end', 'N/A')
    
    # Extract amounts
    def get_amount_value(amount):
        if isinstance(amount, (int, float)):
            return amount
        if isinstance(amount, str):
            return float(amount.replace(',', '').replace('$', '')) if amount.replace(',', '').replace('$', '').replace('.', '').isdigit() else 0
        return 0

    gross_pay = get_amount_value(paystub_data.get('gross_pay', 0))
    net_pay = get_amount_value(paystub_data.get('net_pay', 0))
    ytd_gross = get_amount_value(paystub_data.get('ytd_gross', 0))
    ytd_net = get_amount_value(paystub_data.get('ytd_net', 0))
    federal_tax = get_amount_value(paystub_data.get('federal_tax', 0))
    state_tax = get_amount_value(paystub_data.get('state_tax', 0))
    social_security = get_amount_value(paystub_data.get('social_security', 0))
    medicare = get_amount_value(paystub_data.get('medicare', 0))

    # Extract ML analysis
    fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)
    risk_level = ml_analysis.get('risk_level', 'UNKNOWN')
    model_confidence = ml_analysis.get('model_confidence', 0.0)
    model_scores = ml_analysis.get('model_scores', {})
    heuristic_score = model_scores.get('heuristic', 0.0)

    # Get risk factors
    risk_factors = ml_analysis.get('feature_importance', [])
    if not risk_factors:
        risk_factors = ml_analysis.get('anomalies', [])
    risk_factors_str = '\n'.join([f"- {factor}" for factor in risk_factors]) if risk_factors else "None"

    # Get fraud types and reasons from ML analysis
    fraud_types = ml_analysis.get('fraud_types', [])
    fraud_reasons = ml_analysis.get('fraud_reasons', [])
    anomalies = ml_analysis.get('anomalies', [])
    
    fraud_types_str = '\n'.join([f"- {t}" for t in fraud_types]) if fraud_types else "None detected."
    fraud_reasons_str = '\n'.join([f"- {r}" for r in fraud_reasons]) if fraud_reasons else "No specific reasons detected."
    anomalies_str = '\n'.join([f"- {a}" for a in anomalies]) if anomalies else "None explicitly detected."

    # Extract employee info
    employee_type = "NEW" if not employee_info.get('employee_id') else "REPEAT"
    employee_id_db = employee_info.get('employee_id', 'NEW_EMPLOYEE')
    has_fraud_history = employee_info.get('has_fraud_history', False)
    fraud_count = employee_info.get('fraud_count', 0)
    escalate_count = employee_info.get('escalate_count', 0)
    last_recommendation = employee_info.get('last_recommendation', 'None')

    # Get current date for analysis
    analysis_date = datetime.now().strftime('%Y-%m-%d')

    # Format the template
    return ANALYSIS_TEMPLATE.format(
        analysis_date=analysis_date,
        company_name=company_name,
        employee_name=employee_name,
        employee_id=employee_id,
        pay_date=pay_date,
        pay_period_start=pay_period_start,
        pay_period_end=pay_period_end,
        gross_pay=f"{gross_pay:,.2f}",
        net_pay=f"{net_pay:,.2f}",
        ytd_gross=f"{ytd_gross:,.2f}",
        ytd_net=f"{ytd_net:,.2f}",
        federal_tax=f"{federal_tax:,.2f}",
        state_tax=f"{state_tax:,.2f}",
        social_security=f"{social_security:,.2f}",
        medicare=f"{medicare:,.2f}",
        fraud_risk_score=f"{fraud_risk_score:.2%}",
        risk_level=risk_level,
        model_confidence=f"{model_confidence:.2%}",
        heuristic_score=f"{heuristic_score:.2%}",
        risk_factors=risk_factors_str,
        anomalies_str=anomalies_str,
        fraud_types_str=fraud_types_str,
        fraud_reasons_str=fraud_reasons_str,
        employee_type=employee_type,
        employee_id_db=employee_id_db,
        has_fraud_history=has_fraud_history,
        fraud_count=fraud_count,
        escalate_count=escalate_count,
        last_recommendation=last_recommendation
    )


