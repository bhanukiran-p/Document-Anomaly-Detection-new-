# Check Analysis ML & AI Components - Complete Explanation

## Overview

The check analysis system uses a **two-stage fraud detection approach**:
1. **ML (Machine Learning)**: Statistical fraud detection using ensemble models
2. **AI (Artificial Intelligence)**: Intelligent decision-making using LangChain + GPT-4

Both components work together to provide comprehensive fraud analysis.

---

## Part 1: ML (Machine Learning) Fraud Detection

### **Purpose**
ML models analyze check data statistically to calculate fraud risk scores based on patterns learned from historical fraud cases.

### **Architecture**

#### **1. Feature Extraction** (`CheckFeatureExtractor`)

**What It Does:**
- Converts raw check data into **30 numerical features** that ML models can process
- Features represent different aspects of check validity and fraud indicators

**30 Features Extracted:**

**Basic Features (1-15):**
1. `bank_validity` - Is bank supported? (1.0 = yes, 0.0 = no)
2. `routing_validity` - Is routing number valid? (9 digits = 1.0)
3. `account_present` - Account number present? (1.0 = yes)
4. `check_number_valid` - Check number format valid? (1.0 = valid)
5. `amount_value` - Numeric amount (capped at 50,000)
6. `amount_category` - Amount bracket (0-100, 100-1000, 1000-5000, 5000+)
7. `round_amount` - Is amount round? (e.g., $100.00 = 1.0)
8. `payer_present` - Payer name present? (1.0 = yes)
9. `payee_present` - Payee name present? (1.0 = yes)
10. `payer_address_present` - Address present? (1.0 = yes)
11. `date_present` - Date present? (1.0 = yes)
12. `future_date` - Is date in future? (1.0 = fraud indicator)
13. `date_age_days` - How old is check? (0-365 days)
14. `signature_detected` - Signature present? (1.0 = yes)
15. `memo_present` - Memo field present? (1.0 = yes)

**Advanced Features (16-30):**
16. `amount_matching` - Do numeric and written amounts match? (0.0-1.0)
17. `amount_parsing_confidence` - Confidence in amount extraction (0.0-1.0)
18. `suspicious_amount` - Suspicious patterns? (e.g., $9,999.99 = 1.0)
19. `date_format_valid` - Date format valid? (1.0 = yes)
20. `weekend_holiday` - Date on weekend? (1.0 = higher risk)
21. `critical_missing_count` - Count of missing critical fields (0-5)
22. `field_quality` - Overall data quality score (0.0-1.0)
23. `bank_routing_match` - Routing matches bank? (1.0 = yes)
24. `check_number_pattern` - Check number follows pattern? (1.0 = valid)
25. `address_valid` - Address format valid? (1.0 = yes)
26. `name_consistency` - Payer ≠ Payee? (1.0 = different, 0.0 = same = suspicious)
27. `signature_requirement` - Signature requirement met? (1.0 = yes)
28. `endorsement_present` - Endorsement detected? (0.5 = placeholder)
29. `check_type_risk` - Risk by type (Personal=0.3, Business=0.5, Cashier=0.1)
30. `text_quality` - OCR text quality (0.0-1.0)

**Example Feature Extraction:**
```python
# Input: Normalized check data
{
    'bank_name': 'Bank of America',
    'check_number': '1001',
    'amount_numeric': {'value': 1500.00, 'currency': 'USD'},
    'payer_name': 'Jane Smith',
    'payee_name': 'John Doe',
    'check_date': '2024-12-01',
    'signature_detected': True,
    'routing_number': '021000021'
}

# Output: 30 features
[1.0, 1.0, 1.0, 1.0, 1500.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 5.0, 1.0, 0.0,
 0.8, 1.0, 0.0, 1.0, 0.0, 0.0, 0.85, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.3, 0.9]
```

**Location:** `Backend/check/ml/check_feature_extractor.py`

---

#### **2. ML Models** (`CheckFraudDetector`)

**Ensemble Approach:**
- **Random Forest** (40% weight)
- **XGBoost** (60% weight)
- **Final Score** = (0.4 × RF_score) + (0.6 × XGB_score)

**Model Loading:**
- Models stored in `Backend/check/ml/models/` or `Backend/ml_models/`
- Files: `check_random_forest.pkl`, `check_xgboost.pkl`, `check_feature_scaler.pkl`
- If models not found → Uses **mock/heuristic scoring**

**Prediction Process:**

1. **Extract Features** → 30 features from check data
2. **Scale Features** → Normalize using feature scaler (if available)
3. **Model Prediction** → Get fraud probability from each model
4. **Ensemble Score** → Weighted average of both models
5. **Apply Validation Rules** → Adjust score based on strict rules
6. **Determine Risk Level** → Convert score to risk category
7. **Generate Anomalies** → List of detected issues

**Validation Rules Applied:**
```python
# These rules adjust the ML score upward if violated:
- Unsupported bank → +0.50 to score
- Future date → +0.40 to score
- No signature → +0.35 to score
- 4+ critical fields missing → +0.30 to score
```

**Risk Level Determination:**
```python
if score < 0.30:  → 'LOW'
elif score < 0.60: → 'MEDIUM'
elif score < 0.85: → 'HIGH'
else:              → 'CRITICAL'
```

**ML Output Structure:**
```python
{
    'fraud_risk_score': 0.45,           # 0.0-1.0 (45% fraud risk)
    'risk_level': 'MEDIUM',              # LOW, MEDIUM, HIGH, CRITICAL
    'model_confidence': 0.85,            # Model confidence (0.0-1.0)
    'model_scores': {
        'random_forest': 0.42,           # RF model score
        'xgboost': 0.47,                  # XGB model score
        'ensemble': 0.45,                 # Weighted average
        'adjusted': 0.50                  # After validation rules
    },
    'feature_importance': [               # Top risk factors
        'Invalid routing number',
        'Missing signature',
        'Future date detected'
    ],
    'anomalies': [                        # Detected issues
        'Invalid routing number',
        'Missing signature',
        'Future date detected'
    ]
}
```

**Mock/Heuristic Mode:**
If models aren't loaded, system uses rule-based scoring:
- Checks critical fields (bank, routing, signature, date)
- Applies risk penalties for missing/invalid data
- Generates conservative fraud scores

**Location:** `Backend/check/ml/check_fraud_detector.py`

---

## Part 2: AI (Artificial Intelligence) Fraud Analysis

### **Purpose**
AI agent uses LangChain + GPT-4 to make intelligent fraud decisions by:
- Analyzing ML scores in context
- Considering customer history
- Applying business rules
- Providing human-readable reasoning

### **Architecture**

#### **1. AI Agent** (`CheckFraudAnalysisAgent`)

**Technology Stack:**
- **LangChain**: Framework for LLM orchestration
- **ChatOpenAI**: OpenAI GPT-4 integration
- **Model**: `o4-mini` (configurable via `AI_MODEL` env var)

**Initialization:**
```python
agent = CheckFraudAnalysisAgent(
    api_key=OPENAI_API_KEY,
    model='o4-mini',
    data_tools=CheckDataAccessTools()  # For customer history queries
)
```

**Location:** `Backend/check/ai/check_fraud_analysis_agent.py`

---

#### **2. Policy Rules (Pre-LLM Checks)**

**Before calling LLM, the system enforces mandatory policies:**

**A. Repeat Offender Policy:**
```python
if escalate_count > 0:
    # AUTOMATIC REJECT - No LLM call
    return {
        'recommendation': 'REJECT',
        'reasoning': ['Repeat offender - escalate_count > 0'],
        'confidence_score': 1.0
    }
```

**B. Duplicate Check Policy:**
```python
if check_duplicate(check_number, payer_name):
    # AUTOMATIC REJECT - No LLM call
    return {
        'recommendation': 'REJECT',
        'reasoning': ['Duplicate check submission detected'],
        'confidence_score': 1.0
    }
```

**C. First-Time Escalation Policy:**
```python
if payer_name is None or customer not found:
    # AUTOMATIC ESCALATE - No LLM call
    return {
        'recommendation': 'ESCALATE',
        'reasoning': ['First-time customer - requires manual review'],
        'confidence_score': 1.0
    }
```

**Location:** `Backend/check/ai/check_fraud_analysis_agent.py` → `_apply_policy_rules()`

---

#### **3. LLM Analysis Process**

**If policies pass, LLM is called:**

**Step 1: Gather Context**
```python
# Customer History
customer_info = {
    'customer_id': 'CUST_001',
    'fraud_count': 0,
    'escalate_count': 0,
    'has_fraud_history': False,
    'last_recommendation': 'APPROVE'
}

# ML Analysis
ml_analysis = {
    'fraud_risk_score': 0.45,
    'risk_level': 'MEDIUM',
    'model_confidence': 0.85,
    'anomalies': ['Missing signature', 'Future date']
}

# Check Data
extracted_data = {
    'bank_name': 'Bank of America',
    'check_number': '1001',
    'amount_numeric': {'value': 1500.00},
    'payer_name': 'Jane Smith',
    'payee_name': 'John Doe',
    'check_date': '2024-12-01',
    'signature_detected': False
}
```

**Step 2: Format Prompt**
The system formats a comprehensive prompt with:
- Check information (bank, amount, dates, parties)
- ML fraud analysis (scores, risk factors)
- Customer history (fraud count, escalation count)
- Decision guidelines (mandatory decision table)

**Step 3: Call LLM**
```python
messages = [
    SystemMessage(content=SYSTEM_PROMPT),  # Role definition
    HumanMessage(content=formatted_prompt)  # Analysis request
]

response = llm.invoke(messages)
```

**Step 4: Parse Response**
LLM returns JSON:
```json
{
    "recommendation": "ESCALATE",
    "confidence_score": 0.85,
    "summary": "Moderate fraud risk - missing signature and future date",
    "reasoning": [
        "Signature not detected - high fraud indicator",
        "Check dated in future - post-dated checks are suspicious",
        "ML fraud score of 45% indicates moderate risk"
    ],
    "key_indicators": [
        "Missing signature",
        "Future date detected",
        "Moderate ML fraud score"
    ],
    "actionable_recommendations": [
        "Route to manual review queue",
        "Verify signature with payer",
        "Confirm check date validity"
    ]
}
```

**Step 5: Validate & Format**
- Ensures recommendation is valid (APPROVE, REJECT, ESCALATE)
- Validates confidence score (0.0-1.0)
- Adds ML context (fraud score, risk level)
- Adds customer history context

**Location:** `Backend/check/ai/check_fraud_analysis_agent.py` → `_llm_analysis()`

---

#### **4. Decision Guidelines (Mandatory Rules)**

**The LLM must follow this decision table:**

| Customer Type | ML Risk Score | Decision |
|---|---|---|
| **New Customer** | < 30% | APPROVE |
| **New Customer** | 30-95% | ESCALATE |
| **New Customer** | ≥ 95% | ESCALATE |
| **Clean History** | < 30% | APPROVE |
| **Clean History** | 30-85% | ESCALATE |
| **Clean History** | > 85% | REJECT |
| **Fraud History** | < 30% | APPROVE |
| **Fraud History** | ≥ 30% | REJECT |
| **Repeat Offender** | Any | REJECT (auto, before LLM) |

**Customer Classification:**
- **New Customer**: No record OR `escalate_count = 0 AND fraud_count = 0`
- **Clean History**: `fraud_count = 0 AND escalate_count = 0`
- **Fraud History**: `fraud_count > 0 AND escalate_count = 0`
- **Repeat Offender**: `escalate_count > 0` (auto-rejected before LLM)

**Automatic Rejection Conditions (Regardless of ML Score):**
1. Unsupported Bank → REJECT
2. Missing Critical Fields (check number, payer, payee) → REJECT
3. Invalid Routing Number (not 9 digits) → REJECT
4. Future-Dated Check → REJECT
5. Duplicate Check → REJECT

**Location:** `Backend/check/ai/check_prompts.py` → `RECOMMENDATION_GUIDELINES`

---

#### **5. Data Access Tools** (`CheckDataAccessTools`)

**Purpose:**
Provides AI agent with access to historical data and customer information.

**Methods:**
```python
# Get customer history
customer_info = tools.get_customer_history(payer_name)
# Returns: {'customer_id', 'fraud_count', 'escalate_count', ...}

# Check for duplicates
is_duplicate = tools.check_duplicate(check_number, payer_name)
# Returns: True if duplicate found

# Get bank fraud stats
stats = tools.get_bank_fraud_stats(bank_name)
# Returns: {'fraud_rate', 'common_patterns', ...}
```

**Location:** `Backend/check/ai/check_tools.py`

---

## Complete Flow: ML + AI Working Together

### **Step-by-Step Process**

```
1. Check Image Upload
   ↓
2. Mindee OCR Extraction
   ↓
3. Normalization (Bank-specific)
   ↓
4. ML Fraud Detection
   ├─ Feature Extraction (30 features)
   ├─ Model Prediction (RF + XGBoost)
   ├─ Ensemble Score Calculation
   ├─ Validation Rules Applied
   └─ Risk Level Determination
   ↓
5. Customer History Lookup
   ├─ Query check_customers table
   ├─ Get fraud_count, escalate_count
   └─ Check for duplicates
   ↓
6. Policy Enforcement (Pre-LLM)
   ├─ Repeat Offender? → REJECT (skip LLM)
   ├─ Duplicate? → REJECT (skip LLM)
   └─ First Time? → ESCALATE (skip LLM)
   ↓
7. AI Analysis (LLM Call)
   ├─ Format prompt with:
   │  - Check data
   │  - ML scores
   │  - Customer history
   │  - Decision guidelines
   ├─ Call GPT-4 via LangChain
   ├─ Parse JSON response
   └─ Validate & format result
   ↓
8. Final Decision
   ├─ Combine ML + AI results
   ├─ Generate anomalies list
   ├─ Calculate confidence score
   └─ Return complete analysis
```

---

## Example: Complete Analysis

### **Input:**
- Check image uploaded
- Bank: Bank of America
- Amount: $1,500.00
- Payer: Jane Smith
- Payee: John Doe
- Date: 2025-12-01 (future date)
- Signature: Not detected
- Check Number: 1001

### **Step 1: ML Analysis**
```python
# Features extracted: 30 features
# Model predictions:
#   Random Forest: 0.42 (42% fraud risk)
#   XGBoost: 0.47 (47% fraud risk)
#   Ensemble: 0.45 (45% fraud risk)

# Validation rules applied:
#   Future date → +0.40
#   No signature → +0.35
#   Adjusted score: 0.50 (50% fraud risk)

# ML Output:
{
    'fraud_risk_score': 0.50,
    'risk_level': 'MEDIUM',
    'model_confidence': 0.85,
    'anomalies': [
        'Future date detected',
        'Missing signature',
        'Moderate fraud risk'
    ]
}
```

### **Step 2: Customer History**
```python
# Query: check_customers table WHERE name = 'Jane Smith'
# Result:
{
    'customer_id': 'CUST_001',
    'fraud_count': 0,
    'escalate_count': 0,
    'has_fraud_history': False,
    'last_recommendation': 'APPROVE'
}
# Classification: Clean History
```

### **Step 3: Policy Check**
```python
# escalate_count = 0 → Pass
# Not duplicate → Pass
# Customer exists → Pass
# Proceed to LLM
```

### **Step 4: AI Analysis**
```python
# Prompt sent to LLM:
"""
Analyze this check for fraud indicators:

CHECK INFORMATION
Bank: Bank of America
Check Number: 1001
Amount: $1,500.00
Date: 2025-12-01
Payer: Jane Smith
Payee: John Doe
Signature Detected: False

ML FRAUD ANALYSIS
Fraud Risk Score: 50% (MEDIUM)
Model Confidence: 85%
Key Risk Factors:
- Future date detected
- Missing signature

CUSTOMER INFORMATION
Customer Type: REPEAT
Has Fraud History: No
Previous Fraud Count: 0
Previous Escalation Count: 0

DECISION GUIDELINES:
Clean History + 30-85% risk → ESCALATE
"""

# LLM Response:
{
    "recommendation": "ESCALATE",
    "confidence_score": 0.88,
    "summary": "Moderate fraud risk - future date and missing signature require manual review",
    "reasoning": [
        "Check dated in future (2025-12-01) - post-dated checks are suspicious",
        "Signature not detected - high fraud indicator",
        "ML fraud score of 50% indicates moderate risk",
        "Customer has clean history but risk factors warrant escalation"
    ],
    "key_indicators": [
        "Future date detected",
        "Missing signature",
        "Moderate ML fraud score (50%)"
    ],
    "actionable_recommendations": [
        "Route to manual review queue",
        "Verify signature with payer",
        "Confirm check date validity",
        "Contact payer to verify transaction"
    ]
}
```

### **Step 5: Final Output**
```python
{
    'ml_analysis': {
        'fraud_risk_score': 0.50,
        'risk_level': 'MEDIUM',
        'model_confidence': 0.85,
        'anomalies': ['Future date', 'Missing signature']
    },
    'ai_analysis': {
        'recommendation': 'ESCALATE',
        'confidence_score': 0.88,
        'summary': 'Moderate fraud risk - future date and missing signature',
        'reasoning': [...],
        'key_indicators': [...],
        'actionable_recommendations': [...]
    },
    'final_decision': 'ESCALATE',
    'confidence_score': 0.88,
    'anomalies': [
        'Future date detected',
        'Missing signature',
        'Moderate ML fraud score'
    ]
}
```

---

## Key Differences: ML vs AI

| Aspect | ML (Machine Learning) | AI (Artificial Intelligence) |
|---|---|---|
| **Purpose** | Statistical fraud detection | Intelligent decision-making |
| **Input** | 30 numerical features | Natural language context |
| **Output** | Fraud risk score (0.0-1.0) | Recommendation + reasoning |
| **Models** | Random Forest + XGBoost | GPT-4 (LangChain) |
| **Decision** | Risk level (LOW/MEDIUM/HIGH/CRITICAL) | APPROVE/REJECT/ESCALATE |
| **Reasoning** | Feature importance list | Human-readable explanations |
| **Context** | Current check only | Current check + customer history |
| **Rules** | Statistical patterns | Business rules + decision table |

---

## Files Involved

1. **ML Components:**
   - `Backend/check/ml/check_fraud_detector.py` - Main ML detector
   - `Backend/check/ml/check_feature_extractor.py` - Feature extraction

2. **AI Components:**
   - `Backend/check/ai/check_fraud_analysis_agent.py` - Main AI agent
   - `Backend/check/ai/check_prompts.py` - System prompts & guidelines
   - `Backend/check/ai/check_tools.py` - Data access tools

3. **Orchestration:**
   - `Backend/check/check_extractor.py` - Coordinates ML + AI
   - `Backend/check/utils/check_fraud_indicators.py` - Additional fraud indicators

---

## Summary

**ML Layer:**
- Extracts 30 features from check data
- Uses ensemble models (RF + XGBoost) to calculate fraud risk score
- Applies validation rules to adjust scores
- Determines risk level (LOW/MEDIUM/HIGH/CRITICAL)

**AI Layer:**
- Enforces mandatory policy rules (repeat offenders, duplicates)
- Uses LangChain + GPT-4 for intelligent analysis
- Considers ML scores + customer history
- Follows mandatory decision table
- Provides human-readable reasoning and recommendations

**Together:**
- ML provides statistical fraud risk assessment
- AI provides intelligent decision-making with context
- Both work together to provide comprehensive fraud analysis

