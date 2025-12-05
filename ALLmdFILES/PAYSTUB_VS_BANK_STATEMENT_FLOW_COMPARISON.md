# Paystub vs Bank Statement: Analysis Flow Comparison

## Overview

Both **Paystub** and **Bank Statement** analysis follow the **EXACT SAME 3-STAGE FLOW**:

1. **ML Model** → `fraud_risk_score` (0.0-1.0)
2. **Code-Based Rules** → `fraud_types` (FABRICATED_DOCUMENT, etc.)
3. **AI System Prompt** → Final recommendation (APPROVE/REJECT/ESCALATE)

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENT UPLOAD                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: ML MODEL                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Extract features (18 for paystub, 35 for bank statement) │
│  • Run trained model(s)                                     │
│  • Generate fraud_risk_score (0.0-1.0)                     │
│  • Determine risk_level (LOW/MEDIUM/HIGH/CRITICAL)          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: CODE-BASED RULES                                  │
│  ─────────────────────────────────────────────────────────  │
│  • Analyze features + anomalies                             │
│  • Apply rule-based classification                          │
│  • Generate fraud_types (FABRICATED_DOCUMENT, etc.)        │
│  • Generate fraud_reasons (explanations)                     │
│  • Return ONLY most severe fraud type                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: AI SYSTEM PROMPT                                   │
│  ─────────────────────────────────────────────────────────  │
│  • Receive: ML score + fraud_types + customer history        │
│  • Apply decision matrix (customer type + risk score)        │
│  • Generate final recommendation (APPROVE/REJECT/ESCALATE)   │
│  • Generate actionable_recommendations                        │
│  • Add REPEAT_OFFENDER if applicable (AI-only)              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    FINAL RESULT                              │
│  • fraud_risk_score                                          │
│  • fraud_types (from Stage 2)                                │
│  • ai_recommendation (from Stage 3)                          │
│  • actionable_recommendations (from Stage 3)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Comparison

### Stage 1: ML Model

| Aspect | Paystub | Bank Statement |
|--------|---------|----------------|
| **Model Type** | Random Forest (Classifier) | Ensemble: Random Forest + XGBoost (Regressors) |
| **Number of Models** | 1 | 2 (RF + XGB) |
| **Features** | 18 features | 35 features |
| **Output** | `fraud_risk_score` (0.0-1.0) | `fraud_risk_score` (0.0-1.0) |
| **Ensemble** | N/A (single model) | 40% RF + 60% XGB |
| **File** | `paystub/ml/paystub_fraud_detector.py` | `bank_statement/ml/bank_statement_fraud_detector.py` |
| **Method** | `predict_fraud()` | `predict_fraud()` |

**Key Difference:**
- **Paystub**: Single Random Forest classifier
- **Bank Statement**: Ensemble of 2 regressors (Random Forest + XGBoost)

**Same Output:**
- Both return `fraud_risk_score` (0.0-1.0)
- Both return `risk_level` (LOW/MEDIUM/HIGH/CRITICAL)

---

### Stage 2: Code-Based Rules (Fraud Type Classification)

| Aspect | Paystub | Bank Statement |
|--------|---------|----------------|
| **When** | Inside `predict_fraud()`, after ML score | Inside `predict_fraud()`, after ML score |
| **Method** | `_classify_fraud_types()` | `_classify_fraud_types()` |
| **Input** | Features (18) + normalized_data + anomalies | Features (35) + normalized_data + anomalies |
| **Output** | `fraud_types` (list) + `fraud_reasons` (list) | `fraud_types` (list) + `fraud_reasons` (list) |
| **Return Policy** | Only most severe fraud type | Only most severe fraud type |

**Fraud Types:**

**Paystub (5 types):**
1. `FABRICATED_DOCUMENT`
2. `UNREALISTIC_PROPORTIONS`
3. `ALTERED_LEGITIMATE_DOCUMENT`
4. `ZERO_WITHHOLDING_SUSPICIOUS`
5. `REPEAT_OFFENDER` (added by AI, not ML)

**Bank Statement (6 types):**
1. `FABRICATED_DOCUMENT`
2. `ALTERED_LEGITIMATE_DOCUMENT`
3. `SUSPICIOUS_TRANSACTION_PATTERNS`
4. `BALANCE_CONSISTENCY_VIOLATION`
5. `UNREALISTIC_FINANCIAL_PROPORTIONS`
6. `REPEAT_OFFENDER` (added by AI, not ML)

**Key Similarities:**
- Both use **rule-based logic** on features
- Both return **only the most severe** fraud type
- Both generate **fraud_reasons** (explanations)
- Both are called **inside** `predict_fraud()` method
- Both happen **before** AI analysis

**Key Difference:**
- Different fraud types (document-specific)
- Different feature counts (18 vs 35)

---

### Stage 3: AI System Prompt

| Aspect | Paystub | Bank Statement |
|--------|---------|----------------|
| **When** | After ML analysis completes | After ML analysis completes |
| **Agent** | `PaystubFraudAnalysisAgent` | `BankStatementFraudAnalysisAgent` |
| **Method** | `analyze_fraud()` | `analyze_fraud()` |
| **Input** | `extracted_data` + `ml_analysis` + `employee_name` | `extracted_data` + `ml_analysis` + `account_holder_name` |
| **Output** | `ai_recommendation` (APPROVE/REJECT/ESCALATE) | `ai_recommendation` (APPROVE/REJECT/ESCALATE) |
| **LLM Model** | o4-mini (default) | o4-mini (default) |
| **Decision Matrix** | Customer type + risk score | Customer type + risk score |

**What AI Receives:**
1. **ML Analysis Results:**
   - `fraud_risk_score` (0.0-1.0)
   - `risk_level` (LOW/MEDIUM/HIGH/CRITICAL)
   - `fraud_types` (from Stage 2)
   - `fraud_reasons` (from Stage 2)
   - `anomalies` (from ML)

2. **Customer/Employee History:**
   - `customer_type` (New/Clean History/Fraud History/Repeat Offender)
   - `fraud_count`
   - `escalate_count`
   - `last_recommendation`

3. **Document Data:**
   - All extracted fields
   - Normalized data

**What AI Generates:**
1. **Final Recommendation:**
   - `APPROVE` - Low risk, proceed
   - `REJECT` - High risk, deny
   - `ESCALATE` - Needs human review

2. **Actionable Recommendations:**
   - List of specific actions to take
   - Based on detected issues

3. **Additional Fraud Types:**
   - `REPEAT_OFFENDER` (if applicable, AI-only)

**Key Similarities:**
- Both use **same LLM model** (o4-mini)
- Both use **same decision matrix** structure
- Both follow **customer type + risk score** rules
- Both generate **actionable recommendations**

**Key Differences:**
- Different customer history tables (`employees` vs `bank_statement_customers`)
- Different decision thresholds (slightly different)
- Different fraud types (document-specific)

---

## Code Flow Comparison

### Paystub Flow (Code)

```python
# Stage 1: ML Model
ml_analysis = paystub_detector.predict_fraud(normalized_data, raw_text)
# Inside predict_fraud():
#   1. Extract 18 features
#   2. Run Random Forest model
#   3. Get fraud_risk_score (0.0-1.0)
#   4. Call _classify_fraud_types() → fraud_types (Stage 2)
#   5. Return: {fraud_risk_score, fraud_types, fraud_reasons, ...}

# Stage 3: AI Analysis
ai_analysis = paystub_ai_agent.analyze_fraud(
    extracted_data=normalized_data,
    ml_analysis=ml_analysis,  # Contains fraud_types from Stage 2
    employee_name=employee_name
)
# Returns: {recommendation, actionable_recommendations, ...}
```

### Bank Statement Flow (Code)

```python
# Stage 1: ML Model
ml_analysis = bank_detector.predict_fraud(normalized_data, raw_text)
# Inside predict_fraud():
#   1. Extract 35 features
#   2. Run Random Forest + XGBoost models
#   3. Ensemble: 40% RF + 60% XGB
#   4. Get fraud_risk_score (0.0-1.0)
#   5. Call _classify_fraud_types() → fraud_types (Stage 2)
#   6. Return: {fraud_risk_score, fraud_types, fraud_reasons, ...}

# Stage 3: AI Analysis
ai_analysis = bank_ai_agent.analyze_fraud(
    extracted_data=normalized_data,
    ml_analysis=ml_analysis,  # Contains fraud_types from Stage 2
    account_holder_name=account_holder_name
)
# Returns: {recommendation, actionable_recommendations, ...}
```

---

## Summary

### ✅ **SAME FLOW:**

1. **ML Model** → `fraud_risk_score` (0.0-1.0)
2. **Code-Based Rules** → `fraud_types` (inside `predict_fraud()`)
3. **AI System Prompt** → Final recommendation (APPROVE/REJECT/ESCALATE)

### ✅ **SAME STRUCTURE:**

- Both call `_classify_fraud_types()` **inside** `predict_fraud()`
- Both return **only the most severe** fraud type
- Both pass `fraud_types` to AI agent
- Both use **decision matrix** for final recommendation

### ⚠️ **DIFFERENCES:**

| Aspect | Paystub | Bank Statement |
|--------|---------|----------------|
| **ML Models** | 1 (Random Forest) | 2 (RF + XGBoost ensemble) |
| **Features** | 18 | 35 |
| **Fraud Types** | 5 types | 6 types |
| **Customer Table** | `employees` | `bank_statement_customers` |

---

## Conclusion

**The flow is EXACTLY THE SAME for both Paystub and Bank Statement!**

The only differences are:
- **Number of features** (18 vs 35)
- **Number of ML models** (1 vs 2)
- **Specific fraud types** (document-specific)
- **Customer history tables** (document-specific)

But the **3-stage flow** is identical:
1. ML → Score
2. Rules → Fraud Types
3. AI → Final Recommendation

