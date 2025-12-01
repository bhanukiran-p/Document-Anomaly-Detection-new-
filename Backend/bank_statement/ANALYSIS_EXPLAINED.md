# Bank Statement Analysis: ML & AI Logic Explained

## Overview

The bank statement analysis uses a **two-stage approach**:
1. **ML (Machine Learning) Analysis** - Statistical pattern detection
2. **AI (Artificial Intelligence) Analysis** - Intelligent decision-making with reasoning

---

## Stage 1: ML (Machine Learning) Analysis

### What ML Does

ML analyzes the bank statement data using **mathematical patterns** learned from historical fraud cases. It doesn't "think" - it calculates probabilities based on features.

### Step 1: Feature Extraction (35 Features)

The system extracts **35 numerical features** from the bank statement:

#### Basic Features (1-20):
1. **Bank Validity** (0 or 1): Is it a supported bank? (Bank of America, Chase, Wells Fargo, etc.)
2. **Account Number Present** (0 or 1): Does the statement have an account number?
3. **Account Holder Name Present** (0 or 1): Is the account holder name available?
4. **Account Type Present** (0 or 1): Is account type specified?
5. **Beginning Balance** (numeric): Starting balance amount
6. **Ending Balance** (numeric): Ending balance amount
7. **Total Credits** (numeric): Sum of all deposits
8. **Total Debits** (numeric): Sum of all withdrawals
9. **Statement Period Start** (0 or 1): Is start date present?
10. **Statement Period End** (0 or 1): Is end date present?
11. **Statement Date** (0 or 1): Is statement date present?
12. **Future-Dated Statement** (0 or 1): Is statement dated in the future? (fraud indicator)
13. **Statement Age** (days): How old is the statement?
14. **Transaction Count** (number): How many transactions?
15. **Average Transaction Amount** (numeric)
16. **Balance Change** (numeric): ending - beginning
17. **Credit/Debit Ratio** (ratio)
18. **Large Transaction Count** (number): Transactions > $10,000
19. **Negative Balance** (0 or 1): Is ending balance negative?
20. **Currency Present** (0 or 1): Is currency specified?

#### Advanced Features (21-35):
21. **Balance Consistency** (0 or 1): Does ending = beginning + credits - debits?
22. **Missing Critical Fields** (count): How many required fields are missing?
23. **Unsupported Bank** (0 or 1): Is bank not in supported list?
24. **Invalid Account Format** (0 or 1): Does account number match expected format?
25. **Suspicious Transaction Pattern** (0 or 1): Unusual transaction patterns?
26. **Date Validation** (0 or 1): Are dates valid and logical?
27. **Balance Range Check** (0 or 1): Are balances within expected ranges?
28. **Transaction Frequency** (numeric): Transactions per day
29. **High-Value Transaction Ratio** (ratio): % of large transactions
30. **Balance Fluctuation** (numeric): How much did balance change?
31. **Missing Transaction Data** (0 or 1): Are transactions missing?
32. **Incomplete Statement** (0 or 1): Is statement incomplete?
33. **Data Quality Score** (0-1): Overall data completeness
34. **Fraud Pattern Match** (0 or 1): Matches known fraud patterns?
35. **Risk Composite Score** (0-1): Combined risk indicators

### Step 2: ML Model Prediction

The system uses **two ML models** working together (Ensemble):

1. **Random Forest Model** (40% weight)
   - Uses decision trees to find patterns
   - Good at detecting complex relationships

2. **XGBoost Model** (60% weight)
   - Advanced gradient boosting
   - Excellent at fraud detection

**How They Work Together:**
```
Final Fraud Risk Score = (Random Forest Score × 0.4) + (XGBoost Score × 0.6)
```

### Step 3: Risk Level Classification

Based on the fraud risk score:
- **0-30%**: LOW risk
- **30-70%**: MEDIUM risk
- **70-95%**: HIGH risk
- **95-100%**: CRITICAL risk

### Example from Your Results:

**Your Statement:**
- Missing account holder name → Feature 3 = 0
- Missing account number → Feature 2 = 0
- Missing statement period → Features 9, 10 = 0
- Missing balances → Features 5, 6 = 0
- No transactions → Feature 14 = 0
- Unsupported bank (Wells Fargo) → Feature 1 = 0, Feature 23 = 1

**ML Calculation:**
- Many critical features = 0 (missing data)
- Multiple fraud indicators = 1 (unsupported bank, missing fields)
- **Result: Fraud Risk Score = 100% (CRITICAL)**

**Model Confidence: 75%**
- This means the models are 75% confident in their prediction
- Lower confidence = less certain about the result

---

## Stage 2: AI (Artificial Intelligence) Analysis

### What AI Does

AI uses **GPT-4 (via LangChain)** to make intelligent decisions with reasoning. It considers:
- ML scores
- Customer history
- Business rules
- Context and patterns

### Step 1: Policy Rules (BEFORE AI Analysis)

**These rules are checked FIRST and override everything:**

#### Rule 1: Missing Account Holder Name
```
IF account_holder_name is missing:
    → ESCALATE (automatic)
    → Skip LLM analysis
    → Reason: "Unknown Account Holder is a new customer per policy"
```

#### Rule 2: Repeat Offender Check
```
IF customer has escalate_count > 0:
    → REJECT (automatic)
    → Skip LLM analysis
    → Reason: "Repeat offender - auto-rejected"
```

#### Rule 3: Duplicate Statement
```
IF same account_number + statement_period_start already exists:
    → REJECT (automatic)
    → Reason: "Duplicate submission detected"
```

### Step 2: Customer History Lookup

The system checks the database for:
- `fraud_count`: How many times this customer was rejected
- `escalate_count`: How many times this customer was escalated
- `has_fraud_history`: Does customer have fraud history?
- `last_recommendation`: What was the last decision?

**Your Case:**
- Account holder name: "Unknown Account Holder"
- Customer lookup: No record found (new customer)
- `escalate_count = 0`
- `fraud_count = 0`

### Step 3: Decision Matrix (If No Policy Rule Triggered)

If no automatic policy rule applies, the AI uses this decision table:

| Customer Type | ML Risk Score | AI Decision |
|--------------|---------------|-------------|
| **New Customer** | < 30% | APPROVE |
| **New Customer** | 30-95% | ESCALATE |
| **New Customer** | ≥ 95% | ESCALATE |
| **Clean History** | < 30% | APPROVE |
| **Clean History** | 30-85% | ESCALATE |
| **Clean History** | > 85% | REJECT |
| **Fraud History** | < 30% | APPROVE |
| **Fraud History** | ≥ 30% | REJECT |

### Step 4: LLM Analysis (GPT-4)

If policy rules don't apply, the AI agent:
1. **Formats a prompt** with:
   - Bank statement data
   - ML fraud score and risk level
   - Customer history
   - Decision guidelines

2. **Sends to GPT-4** via LangChain:
   - System prompt: "You are an expert bank statement fraud analyst..."
   - User prompt: All the data + decision matrix

3. **GPT-4 analyzes** and returns:
   - Recommendation (APPROVE/REJECT/ESCALATE)
   - Confidence score (0.0-1.0)
   - Reasoning (list of factors)
   - Key indicators
   - Actionable recommendations

### Your Results Explained:

**Why ESCALATE?**

1. **Policy Rule Triggered:**
   - Account holder name = "Unknown Account Holder" (missing)
   - **Rule**: Missing account holder → ESCALATE (automatic)
   - **Result**: AI skipped LLM analysis, returned automatic escalation

2. **Reasoning Provided:**
   ```
   "Account holder Unknown Account Holder has no recorded escalations (escalate_count = 0)"
   "First-time or clean-history uploads must be escalated for manual review"
   "LLM and ML outputs cannot override this customer-history rule"
   ```

3. **Why Not REJECT?**
   - Even though ML score = 100% (CRITICAL)
   - Policy says: "First-time customers with missing data → ESCALATE (not REJECT)"
   - This allows manual review before rejecting

---

## Complete Flow Diagram

```
Bank Statement Upload
    ↓
[Mindee Extraction] → Extract 17 fields from document
    ↓
[Normalization] → Standardize data format
    ↓
[Feature Extraction] → Convert to 35 numerical features
    ↓
[ML Models] → Random Forest + XGBoost
    ↓
[ML Fraud Score] → 100% (CRITICAL)
    ↓
[Customer Lookup] → Check database for history
    ↓
[Policy Rules Check] → Missing account holder? → YES
    ↓
[Automatic ESCALATE] → Skip LLM, return escalation
    ↓
[Final Result] → ESCALATE with reasoning
```

---

## Key Points

1. **ML is Statistical**: Uses mathematical patterns, not reasoning
2. **AI is Intelligent**: Uses GPT-4 for context-aware decisions
3. **Policy Rules Override**: Business rules come first, before AI
4. **Customer History Matters**: Previous escalations/rejections affect decisions
5. **Missing Data = Risk**: Missing critical fields increase fraud risk score

---

## Why Your Results Make Sense

1. **Fraud Risk Score: 100%**
   - Missing account holder name
   - Missing account number
   - Missing statement period
   - Missing balances
   - No transactions
   - Unsupported bank
   - **All critical features missing = Maximum risk**

2. **AI Recommendation: ESCALATE**
   - Policy rule: Missing account holder → ESCALATE
   - New customer (no history)
   - Allows manual review before rejection

3. **Model Confidence: 75%**
   - Models are confident but not 100%
   - Missing data makes prediction less certain

4. **Anomalies Detected**
   - All missing fields listed
   - Balance inconsistencies
   - Unsupported bank

---

## Summary

- **ML** = "What patterns does the data show?" (100% risk)
- **AI** = "What should we do about it?" (ESCALATE for manual review)
- **Policy** = "What are the business rules?" (Missing data → ESCALATE)

The system is working correctly! It detected all the issues and recommended escalation for manual review.

