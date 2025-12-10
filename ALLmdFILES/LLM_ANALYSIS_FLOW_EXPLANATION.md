# Bank Statement LLM Analysis Flow - Complete Explanation

## Overview
This document explains how bank statement data flows through the system to the LLM (Large Language Model) and how the AI determines fraud types and recommendations.

---

## 1. What Data is Passed to the LLM?

The LLM receives a **formatted prompt** containing three main sections:

### A. Bank Statement Information
All extracted data from the document (via Mindee OCR):

```python
## BANK STATEMENT INFORMATION
- Bank Name: e.g., "Chase", "Bank of America"
- Account Number: e.g., "1234-5678-9012"
- Account Holder Name: e.g., "John Doe"
- Account Type: e.g., "Checking", "Savings"
- Statement Period: Start date to End date
- Statement Date: Date of statement
- Beginning Balance: $X,XXX.XX
- Ending Balance: $X,XXX.XX
- Total Credits: $X,XXX.XX
- Total Debits: $X,XXX.XX
- Transaction Count: Number of transactions
- Currency: e.g., "USD"

## BALANCE VERIFICATION
- Expected Ending Balance = Beginning + Credits - Debits
- Calculated: $X,XXX.XX
- Reported: $X,XXX.XX
- Balance Match: MATCH or MISMATCH (with difference)

## TRANSACTION SAMPLES (up to 10 transactions)
1. Date: YYYY-MM-DD | Type: Credit/Debit | Amount: $XXX.XX | Description: ...
2. Date: YYYY-MM-DD | Type: Credit/Debit | Amount: $XXX.XX | Description: ...
...
```

### B. ML Fraud Analysis Results
The ML models' predictions and insights:

```python
## ML FRAUD ANALYSIS
- Fraud Risk Score: XX.XX% (e.g., "86.50%")
- Risk Level: LOW / MEDIUM / HIGH / CRITICAL
- Model Confidence: XX.XX% (e.g., "89.10%")
- Random Forest Score: XX.XX%
- XGBoost Score: XX.XX%
- Key Risk Factors:
  - Feature 1: Explanation
  - Feature 2: Explanation
  - ...
```

### C. Customer Information
Historical data from the database:

```python
## CUSTOMER INFORMATION
- Customer Type: NEW or REPEAT
- Customer ID: UUID or "NEW_CUSTOMER"
- Has Fraud History: true/false
- Previous Fraud Count: 0, 1, 2, ...
- Previous Escalation Count: 0, 1, 2, ...
- Last Recommendation: APPROVE / REJECT / ESCALATE / None
```

### D. Decision Matrix Rules
The LLM also receives the **decision matrix** as mandatory rules:

```python
## DECISION MATRIX
| Customer Type | Risk Score | Decision |
|---|---|---|
| New Customer | 1-100% | ESCALATE |
| Clean History | < 30% | APPROVE |
| Clean History | > 85% | REJECT |
| Fraud History | < 30% | APPROVE |
| Fraud History | ≥ 30% | REJECT |
| Repeat Offender | Any | REJECT (auto, before LLM) |
```

---

## 2. How the LLM is Called

### Step-by-Step Process:

1. **Pre-LLM Checks** (in `bank_statement_fraud_analysis_agent.py`):
   - Check if customer is a **Repeat Offender** (`escalate_count > 0`)
     - If yes → **Auto-REJECT** (skip LLM entirely)
   - Check for **Duplicate Statements**
     - If yes → **Auto-REJECT** (skip LLM entirely)

2. **Format the Prompt**:
   - Combine `ANALYSIS_TEMPLATE` (with actual data) + `RECOMMENDATION_GUIDELINES` (decision matrix)
   - Create two messages:
     - **System Message**: Role definition ("You are an expert bank statement fraud analyst...")
     - **User Message**: The formatted prompt with all data

3. **Call OpenAI via LangChain**:
   ```python
   response = self.llm.invoke(messages)
   ai_response = response.content  # Raw JSON string from LLM
   ```

4. **Parse JSON Response**:
   - Try multiple strategies to extract JSON:
     - Direct JSON parse
     - Extract from markdown code blocks (```json ... ```)
     - Find JSON object in text
     - Fix common JSON issues (trailing commas)
   - **If parsing fails → Raise error** (no fallback)

5. **Validate and Format Result**:
   - Ensure all required fields exist
   - For **NEW customers**: Clear `fraud_types` and `fraud_explanations` (empty arrays)
   - Validate recommendation is one of: APPROVE, REJECT, ESCALATE
   - Ensure confidence score is 0.0-1.0

6. **Post-LLM Validation**:
   - If customer is **NEW** and LLM returned `APPROVE` or `REJECT`:
     - **Override to ESCALATE** (new customers must always escalate)
     - Clear fraud_types and actionable_recommendations

---

## 3. How AI Result (Recommendation) is Determined

The LLM makes its decision based on:

### A. Decision Matrix Rules (MANDATORY)
The LLM **must** follow the decision matrix:

1. **New Customer** → Always `ESCALATE` (1-100% risk)
2. **Clean History + < 30% risk** → `APPROVE`
3. **Clean History + > 85% risk** → `REJECT`
4. **Fraud History + < 30% risk** → `APPROVE`
5. **Fraud History + ≥ 30% risk** → `REJECT`

### B. Document-Specific Analysis
The LLM analyzes:
- **Balance Consistency**: Does calculated balance match reported balance?
- **Transaction Patterns**: Round numbers, duplicates, unusual frequency
- **Account Number Format**: Valid for the bank?
- **Missing Fields**: Critical fields present?
- **Future-Dated Statements**: Statement date in the future?

### C. ML Score Context
The LLM considers:
- **Risk Score**: How high is the fraud risk? (0-100%)
- **Model Confidence**: How certain are the models? (0-100%)
- **Risk Factors**: What specific features triggered high risk?

### D. Customer History Context
The LLM considers:
- **Previous Fraud Count**: Has this customer been flagged before?
- **Previous Escalation Count**: Has this customer been escalated before?
- **Last Recommendation**: What was the previous decision?

### Example Decision Flow:

```
Customer: "John Doe"
Customer Type: NEW (no customer_id)
Risk Score: 86.50%
ML Confidence: 89.10%

LLM Reasoning:
1. Check Decision Matrix → New Customer + 86.50% risk → ESCALATE
2. Analyze Document:
   - Balance inconsistency detected
   - Multiple round-number transactions
   - High ML confidence (89.10%)
3. Generate Recommendation: ESCALATE
4. Generate Reasoning: ["New customer requires manual review", "Balance inconsistency needs verification", ...]
5. Generate Fraud Types: [] (empty for new customers)
```

---

## 4. How Fraud Types are Determined

### A. For NEW Customers:
- **Always returns empty arrays** for `fraud_types` and `fraud_explanations`
- Even if ML detected fraud, LLM does not assign fraud types to new customers
- This is enforced in code after LLM response

### B. For REPEAT Customers:
The LLM analyzes the document and assigns fraud types based on **specific document issues**:

#### Valid Fraud Types:
1. **BALANCE_CONSISTENCY_VIOLATION**
   - When: Calculated balance ≠ Reported balance
   - Example: "Ending balance ($12,384.50) doesn't match calculated balance ($12,384.50) based on transactions."

2. **FABRICATED_DOCUMENT**
   - When: Document appears completely fake
   - Example: "Account number format invalid: 1234567890 doesn't match Chase account number standards"

3. **ALTERED_LEGITIMATE_DOCUMENT**
   - When: Document was real but tampered with
   - Example: "Balance amounts show signs of tampering: Font inconsistencies detected in ending balance field"

4. **SUSPICIOUS_TRANSACTION_PATTERNS**
   - When: Unusual transaction patterns detected
   - Example: "15 transactions of exactly $5,280.00 within 7 days"

5. **UNREALISTIC_FINANCIAL_PROPORTIONS**
   - When: Financial ratios are unrealistic
   - Example: "Credits ($15,230.00) are 1.5 times debits ($10,000.00), which is unusual for this account type"

### C. Fraud Type Assignment Logic:

The LLM:
1. **Analyzes document data** (balances, transactions, account number, etc.)
2. **Matches issues to fraud types** based on specific criteria
3. **Generates fraud_explanations** with **specific** reasons tied to document data
4. **Only includes fraud_types if recommendation is REJECT or ESCALATE** (not for APPROVE)

### Example Fraud Type Assignment:

```json
{
  "recommendation": "REJECT",
  "fraud_types": ["BALANCE_CONSISTENCY_VIOLATION", "SUSPICIOUS_TRANSACTION_PATTERNS"],
  "fraud_explanations": [
    {
      "type": "BALANCE_CONSISTENCY_VIOLATION",
      "reasons": [
        "Ending balance ($12,384.50) doesn't match calculated balance ($12,384.50). Expected: Beginning ($8,542.75) + Credits ($15,230.00) - Debits ($11,388.25) = $12,384.50, but statement shows $12,384.50"
      ]
    },
    {
      "type": "SUSPICIOUS_TRANSACTION_PATTERNS",
      "reasons": [
        "15 transactions of exactly $5,280.00 within 7 days",
        "Multiple round-number transactions detected: 20 transactions are exact round numbers (e.g., $1,000.00, $5,000.00)"
      ]
    }
  ]
}
```

---

## 5. Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Document Upload (PDF/Image)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. OCR Extraction (Mindee)                                  │
│    - Extract bank name, account number, balances, etc.      │
│    - Extract transactions (up to 10 samples sent to LLM)    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. ML Fraud Detection                                        │
│    - Extract 35 features from document                      │
│    - Run Random Forest + XGBoost models                     │
│    - Generate fraud risk score (0-100%)                     │
│    - Classify fraud types (ML-level)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Customer History Lookup                                  │
│    - Query database for customer by account holder name     │
│    - Get fraud_count, escalate_count, last_recommendation   │
│    - Determine customer type: NEW or REPEAT                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Pre-LLM Policy Checks                                    │
│    - If escalate_count > 0 → Auto-REJECT (skip LLM)        │
│    - If duplicate statement → Auto-REJECT (skip LLM)       │
│    - Otherwise → Proceed to LLM                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Format LLM Prompt                                        │
│    - Combine: Bank Statement Data + ML Results + Customer  │
│    - Add Decision Matrix Rules                              │
│    - Create System + User messages                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Call OpenAI LLM (via LangChain)                          │
│    - Send messages to GPT-4 (or o4-mini)                    │
│    - Receive JSON response                                  │
│    - Parse JSON (multiple strategies)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Validate LLM Response                                    │
│    - Ensure all required fields exist                       │
│    - For NEW customers: Clear fraud_types                   │
│    - Validate recommendation is valid                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Post-LLM Validation                                     │
│    - If NEW customer + LLM returned APPROVE/REJECT          │
│      → Override to ESCALATE                                 │
│    - Add reasoning about override                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. Final Result                                            │
│     - recommendation: APPROVE / REJECT / ESCALATE           │
│     - confidence_score: 0.0-1.0                             │
│     - reasoning: List of reasons                            │
│     - fraud_types: [] (for NEW) or [types] (for REPEAT)    │
│     - fraud_explanations: [] (for NEW) or [explanations]    │
│     - actionable_recommendations: [] (for NEW) or [actions] │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Key Code Files

1. **`bank_statement_prompts.py`**:
   - Defines `ANALYSIS_TEMPLATE` (what data to send)
   - Defines `RECOMMENDATION_GUIDELINES` (decision matrix)
   - `format_analysis_template()` function (formats data into prompt)

2. **`bank_statement_fraud_analysis_agent.py`**:
   - `analyze_fraud()`: Main entry point
   - `_apply_policy_rules()`: Pre-LLM checks (repeat offenders, duplicates)
   - `_llm_analysis()`: Calls LLM and processes response
   - `_parse_json_response()`: Extracts JSON from LLM response
   - `_validate_and_format_result()`: Validates and formats result
   - `_create_first_time_escalation()`: Creates escalation for new customers

3. **`bank_statement_extractor.py`**:
   - Orchestrates the entire pipeline
   - Calls OCR → ML → AI in sequence
   - Combines all results into final response

---

## 7. Important Notes

### A. No Fallback Methods
- If LLM is unavailable → **Raises error** (no fallback)
- If LLM returns invalid JSON → **Raises error** (no fallback)
- If ML models fail → **Raises error** (no fallback)

### B. New Customer Handling
- New customers **always** get `ESCALATE` (regardless of risk score)
- New customers **never** get fraud types (empty arrays)
- New customers **never** get actionable recommendations (empty array)

### C. Fraud Type Rules
- Only assigned for **REPEAT customers**
- Only included if recommendation is **REJECT or ESCALATE** (not APPROVE)
- Must be **specific to document data**, not generic customer history

### D. Decision Matrix Enforcement
- LLM is instructed to follow the decision matrix **strictly**
- Post-LLM validation enforces rules programmatically
- New customer override happens **after** LLM response

---

## 8. Example LLM Request/Response

### Request (what LLM receives):
```
System Message: "You are an expert bank statement fraud analyst..."

User Message:
"Analyze this bank statement for fraud indicators:

## BANK STATEMENT INFORMATION
Bank: Chase
Account Number: 1234-5678-9012
Account Holder: John Doe
...
[All formatted data]

## ML FRAUD ANALYSIS
Fraud Risk Score: 86.50% (HIGH)
Model Confidence: 89.10%
...

## CUSTOMER INFORMATION
Customer Type: NEW
...

## DECISION MATRIX
[Decision matrix rules]

Return your analysis in JSON format..."
```

### Response (what LLM returns):
```json
{
  "recommendation": "ESCALATE",
  "confidence_score": 0.95,
  "summary": "New customer with high fraud risk requires manual review",
  "reasoning": [
    "New customer requires manual review per policy",
    "Balance inconsistency detected: Expected $12,384.50, reported $12,384.50",
    "High ML fraud risk score: 86.50%"
  ],
  "key_indicators": [
    "Balance mismatch detected",
    "High ML confidence: 89.10%"
  ],
  "actionable_recommendations": [],
  "fraud_types": [],
  "fraud_explanations": []
}
```

### After Post-Validation (final result):
```json
{
  "recommendation": "ESCALATE",  // Enforced for new customers
  "confidence_score": 0.95,
  "summary": "Automatic escalation: John Doe is a new customer per account-holder-based fraud policy.",
  "reasoning": [
    "Account holder John Doe has no recorded escalations (escalate_count = 0)",
    "First-time or clean-history uploads must be escalated for manual review",
    "Original LLM recommendation was ESCALATE, but overridden to ESCALATE because this is a new customer."
  ],
  "key_indicators": [
    "Customer escalation count: 0",
    "Policy: first-time uploads require escalation"
  ],
  "actionable_recommendations": [],  // Cleared for new customers
  "fraud_types": [],  // Cleared for new customers
  "fraud_explanations": []  // Cleared for new customers
}
```

---

## Summary

1. **What's passed to LLM**: Bank statement data, ML results, customer history, and decision matrix rules
2. **How AI result is determined**: LLM follows decision matrix + analyzes document + considers ML scores
3. **How fraud types are determined**: LLM analyzes document issues and assigns specific fraud types (only for repeat customers)
4. **Behind-the-scenes logic**: Pre-LLM checks → LLM call → JSON parsing → Validation → Post-LLM enforcement → Final result

The system ensures:
- **No fallback methods** (errors if LLM/ML fail)
- **New customers always escalate** (enforced programmatically)
- **Fraud types only for repeat customers** (enforced programmatically)
- **Specific fraud explanations** (enforced via prompt instructions)

