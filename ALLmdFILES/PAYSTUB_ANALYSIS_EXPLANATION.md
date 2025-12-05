# Paystub Analysis Backend Explanation

## How the Backend Works - Complete Pipeline

The paystub analysis system uses a **multi-stage fraud detection pipeline** that combines OCR extraction, ML models, and AI analysis. Here's how it works:

### Stage 1: OCR Extraction (Mindee API)
- **What it does**: Extracts text and structured data from the paystub image/PDF
- **Technology**: Mindee API with a specialized paystub model
- **Extracts**: Company name, employee name, pay dates, gross pay, net pay, taxes, deductions, YTD amounts, etc.
- **Location**: `Backend/paystub/paystub_extractor.py` → `_extract_with_mindee()`

### Stage 2: Data Normalization
- **What it does**: Standardizes the extracted data into a consistent format
- **Purpose**: Handles different paystub formats and converts data to standard schema
- **Location**: `Backend/paystub/normalization/` modules

### Stage 3: Validation Rules
- **What it does**: Checks for basic data quality issues
- **Checks**:
  - Missing critical fields (company_name, employee_name, gross_pay, net_pay, pay_period)
  - Impossible values (e.g., net pay > gross pay)
- **Location**: `Backend/paystub/paystub_extractor.py` → `_collect_validation_issues()`

### Stage 4: ML Fraud Detection (Random Forest Model)
- **What it does**: Uses a trained machine learning model to predict fraud risk
- **Model**: Random Forest classifier trained on historical paystub fraud data
- **Outputs**:
  - `fraud_risk_score`: 0.0-1.0 (0-100% risk)
  - `risk_level`: LOW, MEDIUM, HIGH, CRITICAL
  - `model_confidence`: 0.90 (90% confidence)
  - `fraud_types`: List of detected fraud types
  - `fraud_reasons`: Machine-generated reasons
- **Location**: `Backend/paystub/ml/paystub_fraud_detector.py`

**Fraud Types Detected by ML:**
1. `MISSING_CRITICAL_FIELDS` - Missing required paystub information
2. `PAY_AMOUNT_TAMPERING` - Net pay >= Gross pay (impossible)
3. `TAX_WITHHOLDING_ANOMALY` - Missing or abnormal tax withholdings
4. `TEMPORAL_INCONSISTENCY` - Future dates or date order issues
5. `YTD_INCONSISTENCY` - Year-to-date amounts inconsistent
6. `BASIC_DATA_QUALITY_ISSUE` - Low OCR quality or extraction issues

### Stage 5: Employee History Lookup
- **What it does**: Checks database for previous paystub submissions by this employee
- **Tracks**:
  - `fraud_count`: Number of times this employee was REJECTED
  - `escalate_count`: Number of times this employee was ESCALATED
  - `has_fraud_history`: Boolean flag
  - `last_recommendation`: Previous AI recommendation
- **Location**: `Backend/paystub/database/paystub_customer_storage.py` → `get_employee_history()`

### Stage 6: AI Fraud Analysis (OpenAI GPT-4)
- **What it does**: Uses AI to make final fraud determination
- **Inputs**:
  - Extracted paystub data
  - ML fraud risk score and detected fraud types
  - Employee history (fraud_count, escalate_count)
- **Outputs**:
  - `recommendation`: APPROVE, REJECT, or ESCALATE
  - `confidence_score`: AI confidence (0.0-1.0)
  - `fraud_explanations`: Business-friendly explanations
  - `key_indicators`: Critical fraud signals
  - `actionable_recommendations`: Next steps
- **Location**: `Backend/paystub/ai/paystub_fraud_analysis_agent.py`

**Decision Rules (from `paystub_prompts.py`):**
- **Repeat Offenders** (escalate_count > 0): **AUTO-REJECT** (before AI even processes)
- **New Employees** with risk < 30%: APPROVE
- **New Employees** with risk 30-95%: ESCALATE
- **Clean History** with risk > 85%: REJECT
- **Fraud History** with risk >= 30%: REJECT

### Stage 7: Post-AI Validation
- **What it does**: Overrides AI recommendation for repeat offenders with high fraud risk
- **Rule**: If `escalate_count > 0` AND `fraud_risk_score >= 20%` → Force REJECT
- **Location**: `Backend/paystub/paystub_extractor.py` → `_run_ai_analysis()` (lines 425-459)

### Stage 8: Final Response Assembly
- **What it does**: Combines all analysis results into final API response
- **Location**: `Backend/paystub/paystub_extractor.py` → `_build_complete_response()`

---

## Why You Got "MISSING CRITICAL FIELDS" Fraud Type

Based on your analysis results showing:
- **Fraud Risk Score**: 32.0%
- **Fraud Type**: MISSING CRITICAL FIELDS
- **Model Confidence**: 90.0%

### How "MISSING CRITICAL FIELDS" is Detected:

The ML model checks for these **critical fields** (code in `paystub_fraud_detector.py` lines 335-358):

1. **Company Name** (`has_company` feature)
2. **Employee Name** (`has_employee` feature)
3. **Gross Pay** (`has_gross` feature)
4. **Net Pay** (`has_net` feature)
5. **Pay Period Dates** (`has_date` feature - checks for pay_period_start OR pay_period_end)

**Detection Logic:**
```python
# From paystub_fraud_detector.py lines 335-358
missing_fields_list = []
if not has_company:
    missing_fields_list.append("employer name")
if not has_employee:
    missing_fields_list.append("employee name")
if not has_gross:
    missing_fields_list.append("gross pay")
if not has_net:
    missing_fields_list.append("net pay")
if not has_date:
    missing_fields_list.append("pay period dates")

if missing_fields_count > 0 or missing_fields_list:
    fraud_types.append("MISSING_CRITICAL_FIELDS")
```

### Why Your Paystub Got This:

Your paystub is missing one or more of these critical fields:
- Either the **company name** wasn't extracted properly
- Or the **employee name** wasn't found
- Or **gross pay** or **net pay** amounts are missing
- Or **pay period dates** (start/end) are missing

**Possible Reasons:**
1. **OCR Quality Issue**: Mindee API couldn't read the field clearly from the image
2. **Field Not Present**: The paystub image might be cropped or the field is actually missing
3. **Format Issue**: The paystub uses a non-standard format that Mindee doesn't recognize

---

## Why You Got "REJECT" Recommendation

Your analysis shows:
- **AI Recommendation**: REJECT
- **Employee Status**: Repeat Employee
- **Escalation Count**: 1
- **Fraud Count**: 1 incident

### The Rejection Logic:

**1. Repeat Offender Policy (Primary Reason):**
- Your employee has `escalate_count = 1` (from previous paystub submission)
- **Rule**: Any employee with `escalate_count > 0` is classified as a **"Repeat Offender"**
- **Action**: **AUTO-REJECT** (happens before AI even processes the paystub)

**Code Reference** (`paystub_extractor.py` lines 425-459):
```python
# Post-AI validation - Force REJECT for repeat offenders
if employee_info and employee_info.get('escalate_count', 0) > 0:
    escalate_count = employee_info.get('escalate_count', 0)
    fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)
    fraud_risk_percent = fraud_risk_score * 100
    
    if fraud_risk_percent >= 20:  # Your score is 32%, so >= 20%
        # Force REJECT
        ai_analysis['recommendation'] = 'REJECT'
```

**2. Missing Critical Fields + Repeat Employee:**
- Even though your fraud risk is only 32% (medium risk)
- The combination of:
  - Missing critical fields (fraud type detected)
  - Being a repeat employee (escalate_count = 1)
  - Fraud risk >= 20%
- Triggers the **automatic rejection policy**

**3. Decision Matrix** (from `paystub_prompts.py`):
```
| Employee Type | Risk Score | Decision |
|---|---|---|
| Repeat Offender (escalate_count > 0) | Any | REJECT (auto) |
```

---

## Why "Repeat Employee" Status?

### Employee History Tracking:

The system tracks every paystub submission in the `paystub_customers` table:

**Your Employee's History:**
- **Previous Submission**: Had a paystub that was **ESCALATED** (not rejected)
- **Result**: `escalate_count = 1` was set
- **Current Status**: Now classified as "Repeat Employee" because `escalate_count > 0`

**How Counts Work:**
- **`fraud_count`**: Increments when recommendation is **REJECT**
- **`escalate_count`**: Increments when recommendation is **ESCALATE**
- **`has_fraud_history`**: True if `fraud_count > 0`

**Code Reference** (`paystub_customer_storage.py` lines 217-223):
```python
if recommendation == 'REJECT':
    new_fraud_count = previous_fraud_count + 1
    has_fraud_history = True
elif recommendation == 'ESCALATE':
    new_escalate_count = previous_escalate_count + 1
```

### Why This Matters:

**Repeat Offender Policy:**
- Once an employee has `escalate_count > 0`, they're flagged as a **repeat offender**
- Future submissions are **automatically rejected** if fraud risk >= 20%
- This prevents employees from repeatedly submitting problematic paystubs

---

## Summary: Why Your Specific Result

1. **MISSING CRITICAL FIELDS** detected because:
   - One or more required fields (company name, employee name, gross/net pay, or pay period dates) were missing from the OCR extraction

2. **32.0% Fraud Risk Score** because:
   - The ML model calculated medium risk based on missing fields and other features

3. **REJECT Recommendation** because:
   - Employee is a **repeat offender** (`escalate_count = 1`)
   - Fraud risk score (32%) >= 20% threshold
   - System automatically overrides to REJECT per repeat offender policy

4. **Repeat Employee Status** because:
   - Previous paystub submission was **ESCALATED** (not rejected)
   - This set `escalate_count = 1`
   - Any employee with `escalate_count > 0` is classified as "Repeat Employee"

---

## How to Fix This

### For the Current Paystub:
1. **Check the Image Quality**: Ensure the paystub image is clear and all fields are visible
2. **Verify Fields Present**: Make sure company name, employee name, gross pay, net pay, and pay period dates are clearly visible on the paystub
3. **Re-upload**: If fields are present but not extracted, try a clearer/higher resolution image

### For Future Submissions:
- Once an employee is flagged as a repeat offender, they need to submit **clean paystubs** with all fields present
- The system will continue to auto-reject if fraud risk >= 20% for repeat offenders
- To reset the status, the employee would need to be manually cleared from the database (not recommended for security)

---

## Technical Flow Diagram

```
1. Upload Paystub Image
   ↓
2. Mindee OCR Extraction
   ↓
3. Data Normalization
   ↓
4. Validation Rules Check
   ↓ (Missing fields detected)
5. ML Fraud Detection
   ↓ (32% risk, MISSING_CRITICAL_FIELDS)
6. Employee History Lookup
   ↓ (escalate_count = 1, Repeat Employee)
7. AI Analysis (if not repeat offender)
   ↓
8. Post-AI Validation
   ↓ (escalate_count > 0 AND risk >= 20% → Force REJECT)
9. Final Response: REJECT
```

---

## Files Referenced

- **Main Pipeline**: `Backend/paystub/paystub_extractor.py`
- **ML Detection**: `Backend/paystub/ml/paystub_fraud_detector.py`
- **AI Analysis**: `Backend/paystub/ai/paystub_fraud_analysis_agent.py`
- **Employee Tracking**: `Backend/paystub/database/paystub_customer_storage.py`
- **API Endpoint**: `Backend/api_server.py` (line 333)
- **Decision Rules**: `Backend/paystub/ai/paystub_prompts.py`

