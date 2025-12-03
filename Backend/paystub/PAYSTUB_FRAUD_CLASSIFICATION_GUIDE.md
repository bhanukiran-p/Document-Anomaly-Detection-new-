# Paystub Fraud Classification Guide

## Overview

The paystub fraud detection system classifies documents into **5 fraud types** using a combination of:
1. **ML Feature Analysis** (18 features extracted from the document)
2. **Rule-Based Classification** (specific detection rules for each fraud type)
3. **Employee History** (for REPEAT_OFFENDER classification)

---

## The 5 Fraud Types

### 1. FABRICATED_DOCUMENT
**Description:** Completely fake paystub with non-existent employer or synthetic identity

**Detection Rules:**
- **Rule 1:** Missing company name (`has_company = 0`) AND low text quality (`text_quality < 0.6`)
  - **Reason:** "Missing employer name combined with low extraction quality suggests this may be a fabricated document."
  
- **Rule 2:** Missing company name AND missing employee name AND missing 3+ critical fields
  - **Reason:** "Missing critical identifying information (employer and employee names) suggests a fabricated document."

**Severity:** 4 (Highest)

**Features Used:**
- `has_company` (Feature 1)
- `has_employee` (Feature 2)
- `text_quality` (Feature 9)
- `missing_fields_count` (Feature 10)

---

### 2. UNREALISTIC_PROPORTIONS
**Description:** Net/gross ratios and tax/deduction percentages that don't make sense

**Detection Rules:**
- **Rule 1:** Net pay > 95% of gross pay (`net_to_gross_ratio > 0.95`)
  - **Reason:** "Net pay represents {X}% of gross pay, which is unrealistic for W-2 style paystubs (typically 60-85% after taxes and deductions)."
  
- **Rule 2:** Tax withholdings < 2% of gross pay (`tax_to_gross_ratio < 0.02`) AND gross > $1,000
  - **Reason:** "Tax withholdings represent only {X}% of gross pay, which is unrealistically low (typically 15-30% for W-2 employees)."
  
- **Rule 3:** Deductions > 50% of gross pay (`deduction_percentage > 0.50`)
  - **Reason:** "Deductions represent {X}% of gross pay, which is unusually high (typically 15-40% including taxes)."

**Severity:** 2

**Features Used:**
- `gross_pay` (Feature 6)
- `net_pay` (Feature 7)
- `net_to_gross_ratio` (Feature 17)
- `tax_to_gross_ratio` (Feature 16)
- `deduction_percentage` (Feature 18)

---

### 3. ZERO_WITHHOLDING_SUSPICIOUS
**Description:** No federal/state tax or mandatory deductions where they should exist

**Detection Rules:**
- **Rule 1:** Gross pay > $1,000 AND no taxes at all (no federal, state, Social Security, or Medicare)
  - **Reason:** "No tax withholdings detected (federal, state, Social Security, or Medicare) for gross pay of ${X}, which is suspicious for W-2 style paystubs in taxable jurisdictions."
  
- **Rule 2:** Missing mandatory FICA taxes (no Social Security AND no Medicare)
  - **Reason:** "Missing mandatory Social Security and Medicare withholdings (FICA taxes), which are required for W-2 employees."
  
- **Rule 3:** Total taxes < 2% of gross pay (`total_tax_amount < gross * 0.02`)
  - **Reason:** "Total tax withholdings (${X}) represent only {Y}% of gross pay, which is unrealistically low for W-2 employees (typically 15-30%)."

**Severity:** 3

**Features Used:**
- `gross_pay` (Feature 6)
- `has_federal_tax` (Feature 11)
- `has_state_tax` (Feature 12)
- `has_social_security` (Feature 13)
- `has_medicare` (Feature 14)
- `total_tax_amount` (Feature 15)
- `tax_to_gross_ratio` (Feature 16)

---

### 4. ALTERED_LEGITIMATE_DOCUMENT
**Description:** Real paystub that has been manually edited or tampered with

**Detection Rules:**
- **Rule 1:** Low text quality (`text_quality < 0.6`) AND (unrealistic net/gross ratio OR unrealistic tax ratio)
  - **Reason:** "Low extraction quality combined with unrealistic proportions suggests this legitimate paystub may have been altered or tampered with."
  
- **Rule 2:** Low text quality (`text_quality < 0.7`) AND missing fields AND (tax error OR net > 95% of gross)
  - **Reason:** "Multiple indicators (low quality, missing fields, tax errors) suggest this document may have been manually edited."

**Severity:** 1 (Lowest)

**Features Used:**
- `text_quality` (Feature 9)
- `missing_fields_count` (Feature 10)
- `tax_error` (Feature 8)
- `net_to_gross_ratio` (Feature 17)
- `tax_to_gross_ratio` (Feature 16)

---

### 5. REPEAT_OFFENDER
**Description:** Employee with history of fraudulent submissions and escalations

**Detection Method:** 
- **NOT detected by ML features**
- **Detected by AI agent** based on employee history from database
- Requires `escalate_count > 0` in employee history

**Severity:** N/A (History-based, not document-based)

**Note:** This is the only fraud type that is NOT classified by the ML detector. It's added by the AI agent during the analysis phase.

---

## Complete Classification Flow

### Stage 1: Feature Extraction (18 Features)

The system extracts **18 numerical features** from the paystub:

#### Basic Presence Flags (Features 1-5):
1. `has_company` - Is company name present? (0 or 1)
2. `has_employee` - Is employee name present? (0 or 1)
3. `has_gross` - Is gross pay present? (0 or 1)
4. `has_net` - Is net pay present? (0 or 1)
5. `has_date` - Is pay period date present? (0 or 1)

#### Amounts (Features 6-7):
6. `gross_pay` - Gross pay amount (capped at $100k)
7. `net_pay` - Net pay amount (capped at $100k)

#### Errors and Quality (Features 8-10):
8. `tax_error` - Is net >= gross? (0 or 1) - **CRITICAL ERROR**
9. `text_quality` - Extraction quality score (0.5-1.0)
10. `missing_fields_count` - Count of missing critical fields (0-5)

#### Tax Features (Features 11-16):
11. `has_federal_tax` - Is federal tax present? (0 or 1)
12. `has_state_tax` - Is state tax present? (0 or 1)
13. `has_social_security` - Is Social Security tax present? (0 or 1)
14. `has_medicare` - Is Medicare tax present? (0 or 1)
15. `total_tax_amount` - Sum of all taxes (capped at $50k)
16. `tax_to_gross_ratio` - Total taxes / gross pay (0.0-1.0)

#### Proportion Features (Features 17-18):
17. `net_to_gross_ratio` - Net pay / gross pay (0.0-1.0)
18. `deduction_percentage` - (Gross - Net) / gross (0.0-1.0)

---

### Stage 2: ML Model Prediction

1. **Feature Scaling:** All 18 features are scaled using a pre-trained scaler
2. **Random Forest Model:** Predicts fraud risk score (0.0-1.0)
3. **Risk Level Classification:**
   - 0.0-0.3: LOW risk
   - 0.3-0.7: MEDIUM risk
   - 0.7-0.9: HIGH risk
   - 0.9-1.0: CRITICAL risk

---

### Stage 3: Fraud Type Classification

The `_classify_fraud_types()` method evaluates the document against all detection rules:

1. **Check FABRICATED_DOCUMENT rules** (Severity 4)
2. **Check UNREALISTIC_PROPORTIONS rules** (Severity 2)
3. **Check ZERO_WITHHOLDING_SUSPICIOUS rules** (Severity 3)
4. **Check ALTERED_LEGITIMATE_DOCUMENT rules** (Severity 1)

**Important:** If multiple fraud types are detected, only the **most severe** one is returned (based on severity order).

**Severity Order:**
1. FABRICATED_DOCUMENT (4) - Highest
2. ZERO_WITHHOLDING_SUSPICIOUS (3)
3. UNREALISTIC_PROPORTIONS (2)
4. ALTERED_LEGITIMATE_DOCUMENT (1) - Lowest

---

### Stage 4: AI Analysis (Adds REPEAT_OFFENDER)

The AI agent checks employee history:
- If `escalate_count > 0` → Adds `REPEAT_OFFENDER` to fraud types
- This is added **in addition to** any document-level fraud types detected by ML

---

## Example Classification Scenarios

### Scenario 1: Missing Company Name + Low Quality
**Features:**
- `has_company = 0`
- `text_quality = 0.5`
- `has_employee = 1`

**Classification:** `FABRICATED_DOCUMENT`
**Reason:** "Missing employer name combined with low extraction quality suggests this may be a fabricated document."

---

### Scenario 2: Net Pay = 98% of Gross Pay
**Features:**
- `gross_pay = $5,000`
- `net_pay = $4,900`
- `net_to_gross_ratio = 0.98`

**Classification:** `UNREALISTIC_PROPORTIONS`
**Reason:** "Net pay represents 98.0% of gross pay, which is unrealistic for W-2 style paystubs (typically 60-85% after taxes and deductions)."

---

### Scenario 3: No Taxes for $3,000 Gross Pay
**Features:**
- `gross_pay = $3,000`
- `has_federal_tax = 0`
- `has_state_tax = 0`
- `has_social_security = 0`
- `has_medicare = 0`

**Classification:** `ZERO_WITHHOLDING_SUSPICIOUS`
**Reason:** "No tax withholdings detected (federal, state, Social Security, or Medicare) for gross pay of $3,000.00, which is suspicious for W-2 style paystubs in taxable jurisdictions."

---

### Scenario 4: Low Quality + Unrealistic Ratios
**Features:**
- `text_quality = 0.55`
- `net_to_gross_ratio = 0.92`
- `tax_to_gross_ratio = 0.03`

**Classification:** `ALTERED_LEGITIMATE_DOCUMENT`
**Reason:** "Low extraction quality combined with unrealistic proportions suggests this legitimate paystub may have been altered or tampered with."

---

### Scenario 5: Employee with History
**Employee History:**
- `escalate_count = 2`
- `fraud_count = 1`

**Classification:** `REPEAT_OFFENDER` (added by AI agent)
**Note:** This is added regardless of document-level fraud types.

---

## Key Points

1. **Document-Level Fraud Types (1-4):** Detected by ML feature analysis
2. **History-Based Fraud Type (5):** Detected by AI agent based on employee history
3. **Only Most Severe:** If multiple types detected, only the highest severity is returned
4. **No Fallbacks:** All features must be extracted correctly, or the system raises an error
5. **18 Features Required:** The model expects exactly 18 features - no more, no less

---

## Classification Decision Tree

```
Upload Paystub
    ↓
Extract 18 Features
    ↓
ML Model Predicts Risk Score
    ↓
Check Fraud Type Rules:
    ├─ FABRICATED_DOCUMENT? (Severity 4)
    ├─ ZERO_WITHHOLDING_SUSPICIOUS? (Severity 3)
    ├─ UNREALISTIC_PROPORTIONS? (Severity 2)
    └─ ALTERED_LEGITIMATE_DOCUMENT? (Severity 1)
    ↓
Select Most Severe Type
    ↓
AI Agent Checks Employee History:
    └─ REPEAT_OFFENDER? (if escalate_count > 0)
    ↓
Final Fraud Types List
```

---

## Summary

The paystub fraud classification system uses:
- **18 ML features** extracted from the document
- **4 document-level fraud types** detected by rule-based classification
- **1 history-based fraud type** (REPEAT_OFFENDER) detected by AI agent
- **Severity-based selection** when multiple types are detected
- **No fallbacks** - strict error handling ensures accuracy

