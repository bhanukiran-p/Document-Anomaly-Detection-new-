# XFORIA DAD - Technical Quick Reference

**AI-Powered Fraud Detection System - Technical Documentation**

---

## 🏗️ System Architecture

### Technology Stack
- **Backend**: Flask 3.0.0, Python 3.12+, Supabase (PostgreSQL)
- **Frontend**: React 18.2.0, React Router 6.20.0, Recharts/ECharts
- **ML**: scikit-learn 1.4.2, XGBoost 2.0.3, Random Forest
- **AI**: OpenAI GPT-4 (gpt-4-mini), LangChain 0.1.0
- **OCR**: Mindee API 4.31.0+, Google Cloud Vision (fallback)

### Architecture Flow
```
React Frontend (Port 3002)
    ↕ HTTP/REST API
Flask API Server (Port 5001)
    ↕ Processing Pipeline
10-Stage Analysis Pipeline:
  1. OCR (Mindee ClientV2)
  2. Bank-Specific Normalization
  3. Validation Rules Collection
  4. ML Ensemble (RF + XGBoost)
  5. Customer History Query
  6. AI Analysis (GPT-4)
  7. Anomaly Generation
  8. Confidence Calculation
  9. Final Decision Logic
  10. Response Building
    ↕ External APIs
Mindee OCR | OpenAI GPT-4 | Supabase PostgreSQL
```

---

## 🤖 ML Models - Technical Details

### Ensemble Architecture
All document types use **Random Forest + XGBoost ensemble** with **40% RF + 60% XGB** weighting:

```python
ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)
```

### Model Specifications

| Document | Architecture | Features | Model Files | Training Script |
|----------|-------------|----------|-------------|----------------|
| **Checks** | RF + XGBoost | 30 | `check_random_forest.pkl`<br>`check_xgboost.pkl`<br>`check_feature_scaler.pkl` | `training/retrain_check_models_30features.py` |
| **Paystubs** | RF + XGBoost | 18 | `paystub_random_forest.pkl`<br>`paystub_xgboost.pkl`<br>`paystub_feature_scaler.pkl` | `training/train_paystub_models.py` |
| **Money Orders** | RF + XGBoost | 30 | `money_order_random_forest.pkl`<br>`money_order_xgboost.pkl`<br>`money_order_feature_scaler.pkl` | `training/train_money_order_models.py` |
| **Bank Statements** | RF + XGBoost | 35 | `bank_statement_random_forest.pkl`<br>`bank_statement_xgboost.pkl`<br>`bank_statement_feature_scaler.pkl` | `training/train_risk_model.py` |
| **Real-Time** | XGBoost (single) | 50+ | `transaction_fraud_model.pkl`<br>`transaction_scaler.pkl` | `real_time/model_trainer.py` |

### Feature Engineering

**Common Features (All Documents):**
- Amount: `amount_normalized`, `amount_log`, `amount_rounded`, `amount_zscore`
- Date: `day_of_week`, `month`, `is_weekend`, `days_since_epoch`, `date_age_days`
- Text Quality: `payer_name_length`, `text_quality_score`, `field_completeness`
- Missing Fields: `missing_payer`, `missing_payee`, `missing_amount`, `signature_present`
- Customer Behavior: `total_submissions`, `high_risk_count`, `is_repeat_customer`, `escalate_count`

**Document-Specific Features:**
- **Checks**: `bank_validity`, `routing_number_valid`, `amount_matching`, `stale_check`
- **Paystubs**: `gross_net_ratio`, `tax_deduction_ratio`, `federal_tax`, `state_tax`
- **Money Orders**: `issuer_valid`, `serial_format_valid`, `exact_amount_match`
- **Bank Statements**: `balance_consistency`, `transaction_count`, `transaction_pattern_anomaly`
- **Real-Time**: `customer_txn_count`, `country_mismatch`, `is_night`, `money_mule_pattern`

### Model Training Process
1. Generate synthetic training data (2000 samples)
2. Train/test split (80/20)
3. Handle imbalanced data with SMOTE (imbalanced-learn)
4. Hyperparameter tuning with GridSearchCV
5. Train RF and XGBoost separately
6. Save models as `.pkl` files with joblib

**Hyperparameters:**
- **RF**: `n_estimators=100`, `max_depth=10`, `min_samples_split=5`
- **XGBoost**: `max_depth=6`, `learning_rate=0.1`, `n_estimators=100`, `subsample=0.8`

---

## 🧠 AI Analysis - Technical Implementation

### AI Agent Architecture
Each document type has dedicated AI agent:
- `CheckFraudAnalysisAgent` (`Backend/check/ai/check_fraud_analysis_agent.py`)
- `PaystubFraudAnalysisAgent` (`Backend/paystub/ai/paystub_fraud_analysis_agent.py`)
- `MoneyOrderFraudAnalysisAgent` (`Backend/money_order/ai/fraud_analysis_agent.py`)
- `BankStatementFraudAnalysisAgent` (`Backend/bank_statement/ai/bank_statement_fraud_analysis_agent.py`)

### Prompt Engineering Structure
```python
SYSTEM_PROMPT = """
You are an expert fraud analyst specializing in [document type] verification.

You have access to:
1. ML model fraud scores (Random Forest + XGBoost ensemble)
2. Extracted document data
3. Customer transaction history
4. Database of known fraud patterns

CRITICAL INSTRUCTIONS - FRAUD TYPE TAXONOMY:
[List of fraud types with triggers]

CRITICAL INSTRUCTIONS - DECISION RULES:
[Mandatory decision rules]

Always provide:
1. recommendation: APPROVE/REJECT/ESCALATE
2. confidence_score: 0.0-1.0
3. summary: Natural language explanation
4. key_indicators: List of fraud indicators
5. fraud_types: List (only for REJECT/ESCALATE)
6. fraud_explanations: Structured explanations
"""
```

### Fraud Type Taxonomy

**Checks (5 types):**
1. `SIGNATURE_FORGERY` - Missing/forged signature (1st=ESCALATE, 2nd=REJECT)
2. `AMOUNT_ALTERATION` - Amount mismatch or suspicious patterns
3. `COUNTERFEIT_CHECK` - Fake/tampered document
4. `REPEAT_OFFENDER` - Payer with fraud history (fraud_count > 0)
5. `STALE_CHECK` - Check >180 days old or future-dated

**Money Orders (4 types):**
1. `REPEAT_OFFENDER` - Payer with escalation history
2. `COUNTERFEIT_FORGERY` - Fake/counterfeit money order
3. `AMOUNT_ALTERATION` - Amount mismatch or spelling errors
4. `SIGNATURE_FORGERY` - Missing signature (MANDATORY REJECT)

### AI Decision Logic
```python
# Priority order:
1. Mandatory rules (missing signature for money orders)
2. Repeat offender checks (fraud_count/escalate_count)
3. High fraud score (≥95%) → REJECT
4. AI recommendation based on ML + context
5. Fallback to ML score thresholds
```

---

## 📡 API Endpoints - Technical Details

### Document Analysis Endpoints

**POST `/api/check/analyze`**
- **Content-Type**: `multipart/form-data`
- **Request Body**: `file` (PNG/JPG/PDF), optional `user_id`
- **Response Structure**:
```json
{
  "success": true,
  "fraud_risk_score": 0.75,  // 0.0-1.0
  "risk_level": "HIGH",      // LOW/MEDIUM/HIGH/CRITICAL
  "model_confidence": 0.89,
  "fraud_type": "SIGNATURE_FORGERY",
  "fraud_type_label": "Signature Forgery",
  "fraud_explanations": [{
    "type": "SIGNATURE_FORGERY",
    "reasons": ["Missing signature detected"]
  }],
  "ai_recommendation": "REJECT",
  "ai_confidence": 0.92,
  "ml_analysis": {
    "model_scores": {
      "random_forest": 0.68,
      "xgboost": 0.79,
      "ensemble": 0.75,
      "adjusted": 0.75
    },
    "anomalies": [...]
  },
  "ai_analysis": {
    "recommendation": "REJECT",
    "confidence_score": 0.92,
    "summary": "...",
    "key_indicators": [...]
  },
  "document_id": "uuid"
}
```

**Processing Flow:**
1. File validation (type, size)
2. Save to `temp_uploads/`
3. Call `CheckExtractor.extract_and_analyze()`
4. Store to Supabase (`checks` table)
5. Update customer fraud status
6. Return JSON response
7. Clean up temp file

### Data Retrieval Endpoints

**GET `/api/checks/list`**
- **Query Params**: `date_filter` (last_30/last_60/last_90/older), `limit` (default: 1000)
- **Pagination**: 1000 records per page, loops until all fetched
- **Response**: `{ "success": true, "data": [...], "count": 150, "total_records": 1500 }`

**GET `/api/documents/list`**
- **Query Params**: `date_filter`, `document_type`, `risk_level`, `status`
- **Uses View**: `v_documents_with_risk`
- **Response**: Filtered documents with risk scores

---

## 🗄️ Database Schema - Technical Details

### Core Tables Structure

**`documents` (Master Table)**
```sql
CREATE TABLE documents (
  document_id UUID PRIMARY KEY,
  file_name VARCHAR,
  document_type VARCHAR,  -- 'check', 'paystub', 'money_order', 'bank_statement'
  upload_date TIMESTAMP,
  user_id VARCHAR,
  status VARCHAR  -- 'pending', 'analyzed', 'rejected'
);
```

**`checks` Table**
```sql
CREATE TABLE checks (
  check_id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(document_id),
  check_number VARCHAR,
  amount DECIMAL,
  check_date DATE,
  payer_name VARCHAR,
  payee_name VARCHAR,
  bank_name VARCHAR,
  routing_number VARCHAR,
  account_number VARCHAR,
  fraud_risk_score DECIMAL(5,4),  -- 0.0000-1.0000
  model_confidence DECIMAL(5,4),
  ai_recommendation VARCHAR,  -- 'APPROVE', 'REJECT', 'ESCALATE'
  fraud_type VARCHAR,  -- Single fraud type
  fraud_types JSONB,  -- Array of fraud types
  fraud_explanations JSONB,  -- Structured explanations
  created_at TIMESTAMP,
  timestamp TIMESTAMP
);
```

**`check_customers` (Customer Tracking)**
```sql
CREATE TABLE check_customers (
  customer_id UUID PRIMARY KEY,
  payer_name VARCHAR UNIQUE,
  payee_name VARCHAR,
  address TEXT,
  total_submissions INTEGER,
  high_risk_count INTEGER,
  fraud_count INTEGER,  -- Count of REJECT recommendations
  escalate_count INTEGER,  -- Count of ESCALATE recommendations
  last_submission_date TIMESTAMP,
  fraud_status VARCHAR  -- 'APPROVE', 'REJECT', 'ESCALATE'
);
```

**Database Views:**
- `v_checks_analysis`: Aggregated check data with recommendations
- `v_money_orders_analysis`: Aggregated money order data
- `v_documents_with_risk`: All documents with risk scores
- `v_paystub_insights_clean`: Paystub insights for dashboards

---

## ⚙️ Processing Pipeline - Technical Flow

### 10-Stage Pipeline Implementation

**Stage 1: OCR Extraction**
```python
# Uses Mindee ClientV2 API
params = InferenceParameters(model_id=MINDEE_MODEL_ID_CHECK, raw_text=True)
input_source = PathInput(file_path)
response = mindee_client.enqueue_and_get_inference(input_source, params)
fields = response.inference.result.fields
# Field mapping to standardized schema
```

**Stage 2: Normalization**
```python
# Bank-specific normalizer factory pattern
normalizer = CheckNormalizerFactory.get_normalizer(bank_name)
normalized_obj = normalizer.normalize(extracted_data)
# Normalizes: amounts, dates, names
# Calculates: completeness_score, is_valid, critical_missing_fields
```

**Stage 3: Validation Rules**
```python
# Collects issues without early exit
issues = []
if not signature_detected:
    issues.append("Missing signature")
if not check_number:
    issues.append("Check number missing")
if payer_name == payee_name:
    issues.append("Payer and payee cannot be the same")
# Pipeline continues regardless
```

**Stage 4: ML Fraud Detection**
```python
# Extract features
features = feature_extractor.extract_features(data, raw_text)
# Scale features
X_scaled = scaler.transform([features])
# Run ensemble
rf_score = rf_model.predict_proba(X_scaled)[0][1]
xgb_score = xgb_model.predict_proba(X_scaled)[0][1]
ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)
# Apply validation adjustments
if missing_signature:
    ensemble_score = min(1.0, ensemble_score + 0.3)
```

**Stage 5: Customer History**
```python
# Query Supabase
customer_info = supabase.table('check_customers')\
    .select('*')\
    .eq('payer_name', payer_name)\
    .execute()
# Returns: total_submissions, high_risk_count, fraud_count, escalate_count
```

**Stage 6: AI Analysis**
```python
# Build prompt with context
prompt = build_prompt(extracted_data, ml_analysis, customer_info)
# Call GPT-4
response = openai_client.chat.completions.create(
    model="gpt-4-mini",
    messages=[{"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": prompt}]
)
# Parse response
ai_analysis = parse_ai_response(response)
```

**Stage 7: Anomaly Generation**
```python
anomalies = []
anomalies.extend(ml_analysis.get('anomalies', []))
anomalies.extend(ai_analysis.get('key_indicators', []))
anomalies.extend(validation_issues)
# Remove duplicates, sort by severity
```

**Stage 8: Confidence Calculation**
```python
confidence = (
    0.3 * completeness_score +
    0.3 * ml_model_confidence +
    0.4 * ai_confidence_score
)
```

**Stage 9: Final Decision**
```python
# Priority order:
if critical_validation_issues:
    return "REJECT"
if duplicate_detected:
    return "REJECT"
if ai_analysis:
    return ai_analysis['recommendation']
# Fallback to ML thresholds
if fraud_score >= 0.7:
    return "REJECT"
elif fraud_score >= 0.3:
    return "ESCALATE"
else:
    return "APPROVE"
```

**Stage 10: Response Building**
```python
return {
    'extracted_data': extracted_data,
    'normalized_data': normalized_data,
    'ml_analysis': ml_analysis,
    'ai_analysis': ai_analysis,
    'fraud_risk_score': ensemble_score,
    'ai_recommendation': decision,
    'fraud_type': fraud_type,
    'validation_issues': validation_issues,
    'confidence_score': confidence_score,
    'document_id': document_id
}
```

---

## 🎯 Decision Rules - Technical Implementation

### Check Decision Logic
```python
def determine_final_decision(validation_issues, ml_analysis, ai_analysis, normalized_data):
    # 1. Critical validation issues
    if any("missing check number" in issue.lower() for issue in validation_issues):
        return "REJECT"
    
    # 2. Duplicate check
    if duplicate_detected:
        return "REJECT"
    
    # 3. AI recommendation (handles missing signature with escalation logic)
    if ai_analysis:
        return ai_analysis['recommendation']  # APPROVE/REJECT/ESCALATE
    
    # 4. ML score thresholds (fallback)
    fraud_score = ml_analysis['fraud_risk_score']
    if fraud_score >= 0.7:
        return "REJECT"
    elif fraud_score >= 0.3:
        return "ESCALATE"
    else:
        return "APPROVE"
```

### Paystub Decision Logic
```python
# Post-AI validation override
if employee_info.get('fraud_count', 0) > 0:
    fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)
    if fraud_risk_score >= 0.5:  # 50% threshold
        # Override AI recommendation to REJECT
        ai_analysis['recommendation'] = 'REJECT'
        ai_analysis['reasoning'].insert(0, 
            f"Repeat fraud offender (fraud_count: {fraud_count})")
```

### Money Order Decision Logic
```python
# Mandatory signature check (highest priority)
if not signature_present:
    if escalate_count > 0:
        return "REJECT"  # 2nd time
    else:
        return "ESCALATE"  # 1st time

# Repeat offender check
if escalate_count > 0 and fraud_risk_score >= 0.3:  # 30% threshold
    return "REJECT"
```

### Bank Statement Decision Logic
```python
# New customer policy
if is_new_customer:
    # Never show fraud types (even if REJECT)
    fraud_type = None
    fraud_explanations = []

# Repeat customer policy
if not is_new_customer and ai_recommendation in ['REJECT', 'ESCALATE']:
    # Show fraud types only for REJECT/ESCALATE
    fraud_types = ai_analysis.get('fraud_types', [])
```

---

## 🔧 Configuration - Technical Details

### Environment Variables
```bash
# Required
MINDEE_API_KEY=your_key
OPENAI_API_KEY=your_key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional
MINDEE_MODEL_ID_CHECK=model_id
MINDEE_MODEL_ID_PAYSTUB=model_id
MINDEE_MODEL_ID_BANK_STATEMENT=model_id
MINDEE_MODEL_ID_MONEY_ORDER=model_id
AI_MODEL=gpt-4-mini
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
FLASK_ENV=development
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=52428800  # 50MB
```

### Configuration Class (`Backend/config.py`)
```python
from config import Config

# Centralized configuration
Config.OPENAI_API_KEY
Config.MINDEE_API_KEY
Config.SUPABASE_URL
Config.UPLOAD_FOLDER
Config.LOG_DIR
Config.FRAUD_THRESHOLD_HIGH = 0.7
Config.FRAUD_THRESHOLD_MEDIUM = 0.4
Config.FRAUD_THRESHOLD_LOW = 0.2
```

---

## 📊 Performance Metrics

### Processing Times
- **Check Analysis**: 5-15 seconds (OCR: 2-5s, ML: 1-2s, AI: 2-5s, DB: 1-2s)
- **Paystub Analysis**: 5-12 seconds
- **Money Order Analysis**: 6-15 seconds
- **Bank Statement Analysis**: 8-20 seconds
- **Real-Time CSV** (1000 transactions): 30-60 seconds

### Model Performance
- **ML Accuracy**: ~85-90% (synthetic training data)
- **AI Recommendation Accuracy**: ~90-95% (with GPT-4)
- **Ensemble Confidence**: 0.7-0.95 (typical range)

### Scalability
- **API Server**: Handles 100+ concurrent requests
- **Database**: Supabase handles 1000+ records efficiently
- **Frontend**: Optimized React rendering with memoization

---

## 🔐 Security Implementation

- **JWT Authentication**: PyJWT 2.10.1, token-based auth
- **Password Hashing**: bcrypt via Supabase Auth
- **CORS Protection**: Configured origins in Flask-CORS
- **File Upload Validation**: Type checking, size limits (50MB)
- **SQL Injection Prevention**: Supabase parameterized queries
- **API Key Encryption**: Environment variables, never in code

---

## 🚀 Quick Start

### Backend
```bash
cd Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with required keys
python api_server.py  # Port 5001
```

### Frontend
```bash
cd Frontend
npm install
npm start  # Port 3002
```

### Train Models
```bash
python Backend/training/train_paystub_models.py
python Backend/training/train_money_order_models.py
python Backend/training/retrain_check_models_30features.py
python Backend/training/train_risk_model.py
```

---

## 📞 Technical Support

For detailed documentation, see `README.md`  
For code examples, see `Backend/check/check_extractor.py`  
For API reference, see `Backend/api_server.py`

---

**Version:** 1.0.0 | **Last Updated:** December 2024

