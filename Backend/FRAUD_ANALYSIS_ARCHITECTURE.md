# Fraud Analysis Backend Architecture

## Overview

The fraud analysis system is a **two-stage pipeline** that combines machine learning models with AI-powered contextual analysis to detect money order fraud.

```
Money Order Image
        ↓
   [Stage 1: ML Models]  → Fraud Risk Score (0-100%)
        ↓
   [Stage 2: GPT-4 AI]   → Recommendation (APPROVE/REJECT/ESCALATE)
        ↓
   Final Recommendation + Actionable Insights
```

---

## Stage 1: ML Models (Fraud Risk Scoring)

### Purpose
Generate an **objective, data-driven fraud probability score** based on document features and validation rules.

### Components

#### A. Ensemble Model (Deterministic)
**File:** `Backend/ml_models/fraud_detector.py`

Combines two machine learning models trained on 2000+ money order cases:

- **Random Forest (40% weight)**: Captures non-linear patterns in fraud indicators
- **XGBoost (60% weight)**: More powerful at detecting complex fraud patterns

**Formula:**
```
fraud_score = (0.4 × random_forest_score) + (0.6 × xgboost_score)
```

**Output:** Float between 0.0 and 1.0
- 0.0 = No fraud detected
- 1.0 = Definite fraud

#### B. Strict Validation Rules (Rule-Based)
Applied on top of the ensemble scores to penalize critical fraud indicators:

**CRITICAL Rules (+0.40 each):**
- Amount mismatch: Numeric amount ≠ written amount (e.g., "$450" vs "FOUR HUNDRED DOLLARS")
- Future dated documents: Issue date is in the future

**HIGH Priority Rules (+0.20-0.30):**
- Missing serial number: +0.25
- Missing recipient/payee: +0.20
- Missing amount: +0.30
- Document age > 180 days: +0.20

**MEDIUM Priority Rules (+0.10-0.15):**
- Invalid date format: +0.15
- Suspicious amount pattern: +0.10
- Large amounts (>$2000) issued on weekends: +0.15
- Invalid serial number format: +0.15

**LOW Priority Rules (+0.10):**
- Poor OCR quality: +0.10
- Missing signature: +0.10

### Example: Your 100% Fraud Case

Your money order received **100.0% fraud risk** because:
- The ML ensemble detected multiple critical fraud indicators
- The strict validation rules added penalties for detected anomalies
- This indicates the document has characteristics strongly associated with fraud

---

## Stage 2: GPT-4 AI Analysis (Final Recommendation)

### Purpose
**Contextualize the fraud score** with:
- Extracted document data
- Customer transaction history
- Historical similar cases
- Known fraud patterns
- Training dataset insights

### Process Flow

```
┌─────────────────────────────────────────┐
│  ML Fraud Score (e.g., 100.0%)          │
│  + Extracted Data                       │
│  + Customer History                     │
│  + Similar Cases                        │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│   Format into Prompt for GPT-4          │
│   (ANALYSIS_TEMPLATE in prompts.py)     │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│   GPT-4 Analyzes with System Prompt     │
│   (SYSTEM_PROMPT in prompts.py)         │
│                                         │
│   CRITICAL INSTRUCTION:                 │
│   "If score >= 95%, MUST recommend     │
│    REJECT"                              │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  GPT-4 Response:                        │
│  RECOMMENDATION: REJECT                 │
│  CONFIDENCE: 95%                        │
│  SUMMARY: [Detailed explanation]        │
│  REASONING: [Bullet points]             │
│  KEY_INDICATORS: [Fraud signs found]    │
│  ACTIONABLE_RECOMMENDATIONS:            │
│    - Verify ID                          │
│    - Call issuer bank                   │
│    - Check signature                    │
└─────────────────────────────────────────┘
```

**File:** `Backend/langchain_agent/fraud_analysis_agent.py`

### Key Features

#### 1. Prompts Configuration
**File:** `Backend/langchain_agent/prompts.py`

- **SYSTEM_PROMPT**: Defines GPT-4's role and critical instructions
- **ANALYSIS_TEMPLATE**: Structures the data sent to GPT-4
- **RECOMMENDATION_GUIDELINES**: Rules for APPROVE/REJECT/ESCALATE

#### 2. GPT-4 Recommendation Rules

**APPROVE** (Fraud Score < 30%):
- Low fraud probability
- All critical fields present
- No significant inconsistencies
- Clean customer history
- High model confidence (>80%)

**REJECT** (Fraud Score > 85%, especially >= 95%):
- **CRITICAL: If score is 100.0% or >= 95%, MUST recommend REJECT**
- Multiple critical red flags
- Known fraud pattern match
- Amount or date inconsistencies
- High confidence in fraud detection

**ESCALATE** (Fraud Score 30-85%):
- Moderate risk indicators
- Unusual but not conclusive patterns
- Requires manual verification
- Customer history has minor concerns

#### 3. GPT-4 Input Data

GPT-4 receives a comprehensive analysis prompt containing:

```
ML Model Analysis:
- Fraud Risk Score: 100.0% (CRITICAL)
- Risk Level: CRITICAL
- Model Confidence: 93.4%
- Random Forest Score: 95%
- XGBoost Score: 98%

Extracted Money Order Data:
- Issuer: MoneyGram
- Serial Number: 9021056789
- Amount: $450.00
- Payee: SARAH CHEN
- Purchaser: MICHAEL LEE
- Date: OCTOBER 26, 2024

ML-Identified Fraud Indicators:
- [List of 10+ indicators found]

Customer Information:
- Previous transactions
- Fraud history
- Transaction patterns

Similar Fraud Cases:
- [Cases matching this issuer/amount]

Training Dataset Patterns:
- [Statistical insights from 2000+ cases]

Historical Past Analysis:
- [Similar cases and outcomes]
```

### Why "ESCALATE" Was Incorrect

Your case showed **ESCALATE** instead of **REJECT** because:

1. **GPT-4 was following the 30-85% rule** for ESCALATE
2. **The prompt wasn't strict enough** about the 100% threshold
3. **GPT-4 may have been hedging** by recommending ESCALATE for contextual review

**Solution:** Updated prompts to explicitly state:
```
CRITICAL RULE: If fraud_risk_score is 100.0% or >= 95%,
your recommendation MUST be REJECT.
```

---

## Data Flow Example: Your Money Order

```
1. INPUT: Money order image of MICHAEL LEE → SARAH CHEN

2. EXTRACTION (Mindee API):
   - Issuer: MoneyGram
   - Serial: 9021056789
   - Amount: $450.00
   - Payee: SARAH CHEN
   - Purchaser: MICHAEL LEE
   - Date: October 26, 2024
   - Address: 456 PINE ST, ANYTOWN, CA 91234

3. ML FRAUD DETECTION:
   ML Models:
   - Random Forest: 95% fraud probability
   - XGBoost: 98% fraud probability
   - Ensemble: (0.4 × 0.95) + (0.6 × 0.98) = 97%

   Strict Validation Rules Applied:
   - Amount mismatch detected? → +0.20
   - Future date? → No
   - Missing critical fields? → No
   - Invalid serial? → Check
   - Final Score: 100.0% (capped at 1.0)

4. GPT-4 ANALYSIS:
   Input: ML score (100%), extracted data, customer history

   GPT-4 sees: "Fraud Risk Score: 100.0%"
   GPT-4 thinks: "Score >= 95%, MUST recommend REJECT"

   Output:
   - Recommendation: REJECT
   - Confidence: 95%
   - Reason: Multiple critical fraud indicators detected
   - Actions: Contact issuer, verify customer, block transaction

5. STORAGE:
   - Document stored in database
   - Fraud risk score: 1.0 (100%)
   - AI recommendation: REJECT
   - Risk level: CRITICAL
   - Anomalies: [List of 5-10 fraud indicators]
```

---

## System Architecture Files

| File | Purpose |
|------|---------|
| `fraud_detector.py` | ML ensemble model (Random Forest + XGBoost) |
| `fraud_analysis_agent.py` | GPT-4 AI analysis orchestration |
| `prompts.py` | System prompts and guidelines for GPT-4 |
| `ml_risk_scorer.py` | Fallback risk scoring if ML models unavailable |
| `document_storage.py` | Saves analysis results to database |
| `extractor.py` | Orchestrates entire extraction pipeline |

---

## Key Insights

### Why Two Stages?

1. **ML Models** provide:
   - Objective, reproducible scores
   - Fast processing
   - Trained on 2000+ cases
   - Consistent fraud detection

2. **GPT-4** provides:
   - Contextual understanding
   - Anomaly explanation
   - Customer history consideration
   - Actionable recommendations
   - Human-readable reasoning

### GPT-4 Authority

**GPT-4 is the final decision maker** because:
- It can understand context that raw ML scores cannot
- It can identify false positives
- It provides reasoning and actionable steps
- It's trained to follow explicit rules (like the >=95% REJECT rule)

### For Your 100% Case

With the updated prompts, GPT-4 will now:
1. See the 100.0% fraud score
2. Read the critical instruction: "If score >= 95%, MUST recommend REJECT"
3. Output: **REJECT** (not ESCALATE)
4. Provide detailed reasoning about why it's rejecting

---

## Testing Your Changes

When you reprocess the money order, you should see:

```
Fraud Risk Score: 100.0%
Model Confidence: 93.4%
AI Recommendation: REJECT  ← Changed from ESCALATE
Confidence: 95%
```

The key difference: GPT-4 now explicitly understands that scores >= 95% require a REJECT recommendation.
