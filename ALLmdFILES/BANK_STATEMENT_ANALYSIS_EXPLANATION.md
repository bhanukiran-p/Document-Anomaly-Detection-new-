# Bank Statement Analysis - Detailed Explanation

## Overview
This document explains how each component of the bank statement analysis results is calculated and determined.

---

## 1. Fraud Risk Score (100%)

### How It's Calculated:

#### Step 1: Feature Extraction (35 Features)
The system extracts **35 features** from the bank statement:
- **Basic Features (1-20)**: Bank validity, account presence, balances, dates, transaction counts
- **Advanced Features (21-35)**: Transaction patterns, balance consistency, field quality, etc.

#### Step 2: ML Model Prediction
Two trained models make predictions:

1. **Random Forest Model**:
   - Takes the 35 features as input
   - Outputs a risk score (0-100)
   - Normalized to 0-1 range (divided by 100)

2. **XGBoost Model**:
   - Takes the same 35 features
   - Outputs a risk score (0-100)
   - Normalized to 0-1 range

#### Step 3: Ensemble Score
The final ML score combines both models:
```
Ensemble Score = (40% × Random Forest Score) + (60% × XGBoost Score)
```

#### Step 4: Validation Rules Adjustment
The system applies **strict validation rules** that can increase the score:

- **Unsupported Bank** (bank_validity = 0.0): Minimum score = 0.50 (50%)
- **Future Period** (future_period = 1.0): +0.40 (40%)
- **Negative Balance** (negative_ending_balance = 1.0): +0.35 (35%)
- **Balance Inconsistency** (balance_consistency < 0.5): +0.40 (40%)
- **Critical Missing Fields** (critical_missing_count >= 4): +0.30 (30%)

**Example for 100% Score:**
```
Base Ensemble Score: 0.60 (60%)
+ Future Period: +0.40 → 1.00 (100%)
+ Balance Inconsistency: +0.40 → Capped at 1.00 (100%)
+ Critical Missing Fields: +0.30 → Capped at 1.00 (100%)
Final Adjusted Score: 1.00 = 100%
```

#### Step 5: Risk Level Determination
Based on the final score:
- **0-30%**: LOW
- **31-60%**: MEDIUM
- **61-85%**: HIGH
- **86-100%**: CRITICAL

**Your Result: 100% = CRITICAL**

---

## 2. Model Confidence (89.1%)

### How It's Calculated:

Model confidence represents how **certain** the ML models are about their prediction.

#### Calculation:
```python
Model Confidence = max(Random Forest Score, XGBoost Score)
```

**Why 89.1%?**
- Random Forest predicted: **89.1%** (0.891)
- XGBoost predicted: **79.8%** (0.798)
- Model Confidence = **max(0.891, 0.798) = 0.891 = 89.1%**

#### Interpretation:
- **High Confidence (80-100%)**: Models agree and are certain
- **Medium Confidence (60-80%)**: Models somewhat agree
- **Low Confidence (<60%)**: Models disagree or uncertain

**Your Result: 89.1% = High Confidence** (Both models agree the risk is very high)

---

## 3. AI Recommendation (ESCALATE)

### How It's Determined:

The AI uses a **decision matrix** based on:
1. **Customer Type** (New, Clean History, Fraud History, Repeat Offender)
2. **ML Fraud Risk Score** (0-100%)
3. **Customer History** (fraud_count, escalate_count)

### Decision Matrix:

| Customer Type | Risk Score | Decision |
|--------------|------------|----------|
| **New Customer** | 1-100% | **ESCALATE** |
| Clean History | < 30% | APPROVE |
| Clean History | 30-85% | ESCALATE |
| Clean History | > 85% | REJECT |
| Fraud History | < 30% | APPROVE |
| Fraud History | ≥ 30% | REJECT |
| Repeat Offender | Any | REJECT (auto) |

### Your Case:
- **Customer Type**: New Customer (no prior history)
- **Risk Score**: 100%
- **Decision**: **ESCALATE** (per policy: new customers with high risk must be escalated, not rejected)

### Why ESCALATE (Not REJECT)?
**Policy Rule**: New customers should **NEVER** get REJECT on first upload. They must be escalated for human review first.

### AI Process:
1. **Check Customer History**: Is this a new customer? → Yes
2. **Check Risk Score**: 100% → Very high
3. **Apply Decision Matrix**: New Customer + 100% Risk → **ESCALATE**
4. **Generate Reasoning**: AI explains why escalation is needed
5. **Generate Recommendations**: AI suggests next steps

---

## 4. Fraud Type (BALANCE_CONSISTENCY_VIOLATION)

### How It's Classified:

The ML system uses **rule-based classification** on the 35 features to detect fraud types.

### Fraud Types (5 Document-Level + 1 History-Based):

1. **FABRICATED_DOCUMENT**: Missing bank name + missing account holder + low quality
2. **ALTERED_LEGITIMATE_DOCUMENT**: Low quality + balance inconsistencies
3. **SUSPICIOUS_TRANSACTION_PATTERNS**: Duplicates, round numbers, unusual timing
4. **BALANCE_CONSISTENCY_VIOLATION**: Balance calculations don't match
5. **UNREALISTIC_FINANCIAL_PROPORTIONS**: Unrealistic ratios or volatility
6. **REPEAT_OFFENDER**: Added by AI (not ML)

### BALANCE_CONSISTENCY_VIOLATION Detection:

The system checks if:
```
Ending Balance ≠ (Beginning Balance + Total Credits - Total Debits)
```

**Detection Logic:**
```python
if balance_consistency < 0.5:  # Balance doesn't match
    fraud_type = "BALANCE_CONSISTENCY_VIOLATION"
    reason = "Balance inconsistency detected: ending balance does not match expected balance based on beginning balance and transactions"
```

**Your Case:**
- **Balance Consistency Score**: < 0.5 (inconsistent)
- **Expected Ending**: Beginning + Credits - Debits
- **Actual Ending**: Different from expected
- **Result**: **BALANCE_CONSISTENCY_VIOLATION**

### Severity Order:
If multiple fraud types are detected, only the **most severe** is shown:
1. FABRICATED_DOCUMENT (most severe)
2. BALANCE_CONSISTENCY_VIOLATION
3. SUSPICIOUS_TRANSACTION_PATTERNS
4. UNREALISTIC_FINANCIAL_PROPORTIONS
5. ALTERED_LEGITIMATE_DOCUMENT (least severe)

---

## 5. Actionable Recommendations

### How They're Generated:

Actionable recommendations come from the **AI agent** (OpenAI LLM) based on:
1. **ML Analysis Results** (risk score, fraud type, anomalies)
2. **Customer History** (new customer, fraud history, etc.)
3. **Decision Matrix Rules** (what actions are appropriate)

### Generation Process:

1. **AI Receives Context**:
   - Bank statement data
   - ML fraud risk score (100%)
   - Fraud type (BALANCE_CONSISTENCY_VIOLATION)
   - Customer type (New Customer)
   - Risk level (CRITICAL)

2. **AI Applies Decision Guidelines**:
   - New customer with 100% risk → ESCALATE
   - Balance inconsistency detected → Needs verification
   - Critical risk → Requires manual review

3. **AI Generates Recommendations**:
   The AI uses its training to suggest appropriate actions:
   - **Forward to fraud operations team** (because risk is critical)
   - **Contact applicant** (to verify identity and funds)
   - **Request additional documentation** (to validate legitimacy)

### Example Recommendations for Your Case:

```
1. "Forward statement and risk analysis to the fraud operations team for manual review."
   → Because: 100% risk score requires human verification

2. "Contact the applicant to verify identity and source of funds."
   → Because: Balance inconsistency suggests potential fraud

3. "Request additional documentation (proof of income, utility bills) for further validation."
   → Because: New customer with critical risk needs more evidence
```

### Why These Specific Recommendations?

- **High Risk (100%)**: Requires immediate escalation to fraud team
- **Balance Inconsistency**: Suggests document may be altered or fabricated
- **New Customer**: Needs identity verification before rejection
- **Critical Level**: Cannot be auto-approved, must be reviewed

---

## Summary Flow

```
1. Bank Statement Uploaded
   ↓
2. Extract 35 Features (bank, account, balances, transactions, etc.)
   ↓
3. ML Models Predict Risk (RF: 89.1%, XGB: 79.8%)
   ↓
4. Ensemble Score: 83.5% → Validation Rules → 100%
   ↓
5. Fraud Type Classification: BALANCE_CONSISTENCY_VIOLATION
   ↓
6. AI Agent Analyzes:
   - Customer Type: New
   - Risk Score: 100%
   - Fraud Type: Balance Inconsistency
   ↓
7. AI Decision: ESCALATE (per decision matrix)
   ↓
8. AI Generates Recommendations (3 actionable steps)
   ↓
9. Results Displayed in Frontend
```

---

## Key Points

1. **Fraud Risk Score (100%)**: 
   - Calculated by ML models (RF + XGBoost ensemble)
   - Adjusted by validation rules (future period, balance inconsistency, missing fields)
   - Capped at 100%

2. **Model Confidence (89.1%)**:
   - Maximum of the two model scores
   - Indicates how certain the models are

3. **AI Recommendation (ESCALATE)**:
   - Based on decision matrix (customer type + risk score)
   - New customers with high risk → ESCALATE (not REJECT)

4. **Fraud Type (BALANCE_CONSISTENCY_VIOLATION)**:
   - Detected by ML rule-based classification
   - Based on balance consistency feature (< 0.5)

5. **Actionable Recommendations**:
   - Generated by AI based on context
   - Specific to the fraud type and risk level

---

## Why Your Specific Results?

- **100% Risk**: Multiple critical issues (unsupported bank, missing fields, balance inconsistency, future period)
- **89.1% Confidence**: Both models agree (high certainty)
- **ESCALATE**: New customer policy (cannot reject first time)
- **BALANCE_CONSISTENCY_VIOLATION**: Balance calculations don't match
- **3 Recommendations**: AI suggests escalation, verification, and documentation


