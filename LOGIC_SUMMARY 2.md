# Document Fraud Detection Logic - Quick Summary

## Overview
All document types follow a **multi-stage pipeline**: OCR → Normalization → ML Detection → AI Analysis → Final Decision

---

## 🔵 CHECK Logic

### Pipeline Flow:
1. **OCR Extraction** (Mindee API)
   - Extracts: bank name, check number, amount, payer, payee, dates, signature
   - Cached for 2 hours

2. **Normalization** (Bank-specific)
   - Validates bank against database
   - Normalizes field formats
   - Calculates completeness score

3. **Validation Rules** (Collects issues, no early exit)
   - Missing signature → issue flagged
   - Missing check number → issue flagged
   - Same payer/payee → issue flagged
   - High amount (>$10k) → issue flagged
   - Duplicate check → issue flagged

4. **ML Fraud Detection** (Ensemble: Random Forest + XGBoost)
   - Extracts 30 features (bank validity, routing, signature, dates, amounts, etc.)
   - Generates fraud risk score (0-1)
   - Risk levels: LOW (<30%), MEDIUM (30-60%), HIGH (60-85%), CRITICAL (≥85%)
   - Cached for 1 hour

5. **Customer History Check**
   - Looks up payer in database
   - Gets fraud_count and escalate_count
   - Checks for duplicates

6. **AI Analysis** (LLM with guardrails)
   - **Policy Rules Applied First:**
     - `fraud_count > 0` → Auto-REJECT (REPEAT_OFFENDER)
     - `escalate_count = 0` + `fraud_score < 30%` → Auto-APPROVE
     - `escalate_count = 0` + `fraud_score ≥ 30%` → Auto-ESCALATE
     - `escalate_count > 0` → Proceed to LLM analysis
   
   - **LLM Analysis:**
     - Considers ML scores, validation issues, customer history
     - Fraud types: SIGNATURE_FORGERY, AMOUNT_ALTERATION, COUNTERFEIT_CHECK, REPEAT_OFFENDER, STALE_CHECK
     - Missing signature: 1st time → ESCALATE, 2nd time → REJECT

7. **Final Decision**
   - Critical issues (duplicate, missing check number) → REJECT
   - Otherwise → Defer to AI recommendation (APPROVE/REJECT/ESCALATE)

---

## 🟢 MONEY ORDER Logic

### Similar Pipeline with Key Differences:

1. **OCR Extraction** (Google Vision API)
   - Extracts: issuer, serial number, amount (numeric + written), payee, purchaser, date, signature

2. **ML Fraud Detection**
   - Features: issuer validity, serial format, amount matching, signature presence, text quality
   - Same ensemble approach (RF + XGBoost)

3. **AI Analysis** (Stricter Rules)
   - **Mandatory Signature Check:** Missing signature → Auto-REJECT (SIGNATURE_FORGERY)
   - **Amount Spelling Validation:** Checks raw OCR text for misspellings (e.g., "FOUN" instead of "FOUR") → REJECT if found
   - **Fraud Types:** REPEAT_OFFENDER, COUNTERFEIT_FORGERY, AMOUNT_ALTERATION, SIGNATURE_FORGERY
   - **High Fraud Score (≥95%)** → Auto-REJECT

4. **Key Differences from Check:**
   - Stricter signature enforcement (mandatory rejection)
   - Amount spelling validation in raw OCR text
   - Issuer/serial number validation (counterfeit detection)

---

## 🟡 PAYSTUB Logic

### Pipeline Flow:

1. **OCR Extraction** (Mindee API)
   - Extracts: company name, employee name, gross pay, net pay, taxes, dates

2. **ML Fraud Detection**
   - 18 features: has_company, has_employee, gross_pay, net_pay, tax_error, text_quality, missing_fields_count, tax ratios, etc.
   - Risk score mapped to: APPROVE (0-30), ESCALATE (30-70), REJECT (70-100)

3. **AI Analysis**
   - Validates tax calculations
   - Checks date consistency
   - Verifies company/employee names
   - Fraud types: TAX_FRAUD, COUNTERFEIT_PAYSTUB, MISSING_FIELDS, DATE_INCONSISTENCY

---

## 🔴 BANK STATEMENT Logic

### Pipeline Flow:

1. **PDF Validation** (PyMuPDF + pdfplumber)
   - Metadata checks (creator, creation date)
   - Structure validation (pages, objects)
   - Content analysis (formatting, text overlay, fonts)
   - Financial validation (balance calculations, transaction dates)

2. **Rule-Based Scoring**
   - Metadata suspiciousness (15% weight)
   - Structure issues (20% weight)
   - Content anomalies (35% weight)
   - Financial inconsistencies (30% weight)
   - **Risk Score:** <0.25 = CLEAN, 0.25-0.45 = LOW RISK, 0.45-0.7 = MEDIUM RISK, ≥0.7 = HIGH RISK

3. **Fraud Indicators:**
   - Spelling errors in amounts
   - Missing critical data
   - Balance calculation errors
   - Suspicious transaction patterns
   - Text overlay detection

---

## 🔄 Common Architecture Patterns

### 1. **Caching Layer**
- **OCR Results:** Cached by file hash (2 hour TTL)
- **ML Predictions:** Cached by data hash (1 hour TTL)
- **Backend:** Redis (with in-memory fallback)

### 2. **LLM Guardrails**
- **PII Redaction:** Email, phone, SSN, credit card numbers
- **Input Length Validation:** Max 15,000 chars (truncates if needed)
- **Applied Before:** All LLM calls

### 3. **Customer Tracking**
- Tracks: `fraud_count`, `escalate_count`, transaction history
- Used for: Repeat offender detection, escalation logic

### 4. **Decision Hierarchy**
1. **Critical Issues** → REJECT (duplicates, missing critical fields)
2. **Policy Rules** → Auto-decision (repeat offenders, first-time customers)
3. **AI Analysis** → Contextual decision (considers all factors)
4. **ML Fallback** → If AI unavailable, use ML score thresholds

---

## 📊 Key Metrics

### Check:
- **Features:** 30
- **Models:** Random Forest (40%) + XGBoost (60%)
- **Risk Thresholds:** LOW <30%, MEDIUM 30-60%, HIGH 60-85%, CRITICAL ≥85%

### Money Order:
- **Features:** ~25
- **Models:** Same ensemble
- **Special:** Mandatory signature, amount spelling validation

### Paystub:
- **Features:** 18
- **Risk Mapping:** 0-30 = APPROVE, 30-70 = ESCALATE, 70-100 = REJECT

### Bank Statement:
- **Validation Rules:** 4 categories (metadata, structure, content, financial)
- **Risk Score:** Composite weighted score

---

## 🎯 Decision Logic Summary

| Document Type | Auto-REJECT Triggers | Auto-APPROVE Triggers | Escalation Triggers |
|--------------|---------------------|----------------------|---------------------|
| **Check** | Duplicate, missing check number, fraud_count > 0 | First-time + fraud_score < 30% | First-time + fraud_score ≥ 30%, missing signature (1st time) |
| **Money Order** | Missing signature, fraud_count > 0, fraud_score ≥ 95%, amount spelling errors | Low fraud score + all validations pass | Medium fraud score, weak signature |
| **Paystub** | Tax fraud, counterfeit, fraud_count > 0 | Low risk score + validations pass | Medium risk score, missing fields |
| **Bank Statement** | Risk score ≥ 0.7, critical tampering detected | Risk score < 0.25, all validations pass | Risk score 0.25-0.7, minor concerns |

---

## 🔐 Security Features

1. **PII Protection:** All data sanitized before LLM calls
2. **Input Validation:** Length limits, format checks
3. **Caching Security:** Hashed keys, TTL expiration
4. **Customer Tracking:** Prevents repeat fraud attempts

---

**Last Updated:** Based on current implementation
**Status:** All document types follow similar multi-stage pipeline with document-specific rules

