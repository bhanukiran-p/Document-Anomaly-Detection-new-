# 4. ER DIAGRAM & ETL DATA FLOW

This document describes the data model (Entity-Relationship), ETL pipeline, and data transformations in XFORIA DAD.

---

## Entity-Relationship (ER) Model

### **Core Entities**

```
┌─────────────────────────────────────────────────────────────────┐
│                    XFORIA DAD DATA MODEL                        │
└─────────────────────────────────────────────────────────────────┘

USERS TABLE
┌──────────────────────────────────────┐
│ users                                │
├──────────────────────────────────────┤
│ id (PK)              UUID            │ ← Primary Key
│ username             VARCHAR(255)    │ ← Unique, indexed
│ email                VARCHAR(255)    │ ← Unique
│ password_hash        VARCHAR(255)    │ ← Bcrypt encrypted
│ full_name            VARCHAR(255)    │
│ role                 VARCHAR(50)     │ ← analyst, risk_officer, admin
│ organization_id      VARCHAR(255)    │ ← FK to orgs (future)
│ last_login           TIMESTAMP       │
│ created_at           TIMESTAMP       │
│ updated_at           TIMESTAMP       │
│ is_active            BOOLEAN         │
└──────────────────────────────────────┘
           │
           │ (1 analyst processes many documents)
           │
           ▼
DOCUMENTS TABLE (Parent of all document types)
┌────────────────────────────────────────────┐
│ documents                                  │
├────────────────────────────────────────────┤
│ id (PK)                    UUID            │
│ user_id (FK)               UUID            │ → users.id
│ document_type              VARCHAR(50)     │ ← check, paystub, money_order, bank_statement
│ file_name                  VARCHAR(500)    │
│ file_path                  VARCHAR(1000)   │ ← S3 path
│ file_size_bytes            BIGINT          │
│ upload_timestamp           TIMESTAMP       │
│ processing_status          VARCHAR(50)     │ ← pending, processing, completed, failed
│ processing_start_time      TIMESTAMP       │
│ processing_end_time        TIMESTAMP       │
│ processing_time_ms         INTEGER         │ ← Duration (1000-5000ms typical)
│ error_message              TEXT            │ ← If failed
│ created_at                 TIMESTAMP       │
│ updated_at                 TIMESTAMP       │
└────────────────────────────────────────────┘
           │
           │ (1 document can have multiple analysis results)
           │
           ├─────────────────────────────────────────────┐
           │                                             │
           ▼                                             ▼
     CHECKS TABLE                           PAYSTUBS TABLE
┌────────────────────────┐            ┌──────────────────────────┐
│ checks                 │            │ paystubs                 │
├────────────────────────┤            ├──────────────────────────┤
│ id (PK)      UUID      │            │ id (PK)      UUID        │
│ doc_id (FK)  UUID      │ ──→ doc ←─ │ doc_id (FK)  UUID        │
│ user_id (FK) UUID      │            │ user_id (FK) UUID        │
│                        │            │                          │
│ EXTRACTED OCR DATA     │            │ EXTRACTED OCR DATA       │
│ bank_name    VARCHAR   │            │ employee_name VARCHAR    │
│ bank_code    VARCHAR   │            │ employer_name VARCHAR    │
│ payee        VARCHAR   │            │ employer_address VARCHAR │
│ payer        VARCHAR   │            │ pay_period_start DATE    │
│ amount       DECIMAL   │            │ pay_period_end DATE      │
│ amount_words VARCHAR   │            │ gross_pay DECIMAL        │
│ check_number VARCHAR   │            │ net_pay DECIMAL          │
│ routing_num  VARCHAR   │            │ YTD_gross DECIMAL        │
│ account_num  VARCHAR   │            │ YTD_net DECIMAL          │
│ check_date   DATE      │            │ federal_tax DECIMAL      │
│ memo         VARCHAR   │            │ state_tax DECIMAL        │
│ signature    BOOLEAN   │            │ FICA DECIMAL             │
│                        │            │ deductions JSONB         │
│ CONFIDENCE SCORES      │            │ consistency_score FLOAT  │
│ field_confidences JSONB│            │ authenticity_score FLOAT │
│ avg_confidence FLOAT   │            │                          │
│                        │            │ PREDICTION RESULTS       │
│ PREDICTION RESULTS     │            │ fraud_risk_pct FLOAT     │
│ ml_xgboost_score FLOAT │            │ ai_recommendation VARCHAR│
│ ml_rf_score FLOAT      │            │ confidence_level VARCHAR │
│ ml_ensemble_score FLOAT│            │                          │
│                        │            │ STATUS & AUDIT           │
│ AI RESULTS             │            │ status VARCHAR           │
│ ai_reasoning TEXT      │            │ created_at TIMESTAMP     │
│ ai_recommendation VARCHAR│           │ updated_at TIMESTAMP     │
│ confidence_level VARCHAR│           │ analyst_notes TEXT       │
│                        │            │ final_decision VARCHAR   │
│ STATUS & AUDIT         │            │ decision_override BOOLEAN│
│ status VARCHAR         │            │ override_reason TEXT     │
│ final_decision VARCHAR │            │ override_by_user_id UUID │
│ fraud_score_final INT  │            │ override_timestamp TS    │
│ created_at TIMESTAMP   │            └──────────────────────────┘
│ updated_at TIMESTAMP   │
│ analyst_notes TEXT     │
│ analyst_user_id UUID   │            MONEY_ORDERS TABLE
│ analyst_timestamp TS   │            ┌──────────────────────────┐
│ decision_override BOOL │            │ money_orders             │
│ override_reason TEXT   │            ├──────────────────────────┤
│ override_by_user_id UUID│           │ id (PK)      UUID        │
│ override_timestamp TS  │            │ doc_id (FK)  UUID        │
└────────────────────────┘            │ user_id (FK) UUID        │
           │                          │                          │
           │                          │ EXTRACTED OCR DATA       │
           │                          │ issuer VARCHAR           │
           ▼                          │ issuer_code VARCHAR      │
                                     │ amount DECIMAL           │
CHECK_CUSTOMERS TABLE                │ payee VARCHAR            │
┌──────────────────────────┐          │ purchaser VARCHAR        │
│ check_customers          │          │ serial_number VARCHAR    │
├──────────────────────────┤          │ issue_date DATE          │
│ id (PK)      UUID        │          │ expiration_date DATE     │
│ payer_name (UK)  VARCHAR │ Unique   │ transfer_location VARCHAR│
│ bank_name VARCHAR        │ Key      │                          │
│ routing_number VARCHAR   │          │ PREDICTION RESULTS       │
│ account_number VARCHAR   │          │ fraud_risk_pct FLOAT     │
│                          │          │ counterfeiting_score FL  │
│ FRAUD TRACKING           │          │ authenticity_score FLOAT │
│ fraud_count INT          │ ← Counter│ ai_recommendation VARCHAR│
│ escalation_count INT     │ ← Flag   │                          │
│ total_amount DECIMAL     │          │ STATUS & AUDIT           │
│ transaction_count INT    │          │ status VARCHAR           │
│ last_activity TIMESTAMP  │          │ final_decision VARCHAR   │
│ last_fraud_date TIMESTAMP│          │ created_at TIMESTAMP     │
│                          │          │ analyst_notes TEXT       │
│ ESCALATION POLICY        │          └──────────────────────────┘
│ escalation_threshold INT │ ← Rules  │
│ auto_reject BOOLEAN      │          BANK_STATEMENTS TABLE
│ block_reason TEXT        │          ┌──────────────────────────┐
│                          │          │ bank_statements          │
│ AUDIT TRAIL              │          ├──────────────────────────┤
│ created_at TIMESTAMP     │          │ id (PK)      UUID        │
│ updated_at TIMESTAMP     │          │ doc_id (FK)  UUID        │
│ last_updated_by UUID     │          │ user_id (FK) UUID        │
└──────────────────────────┘          │                          │
                                     │ EXTRACTED OCR DATA       │
                                     │ institution_name VARCHAR  │
                                     │ statement_period_start DT │
                                     │ statement_period_end DATE │
                                     │ account_number VARCHAR    │
                                     │ opening_balance DECIMAL   │
                                     │ closing_balance DECIMAL   │
                                     │ total_debits DECIMAL      │
                                     │ total_credits DECIMAL     │
                                     │ transaction_count INT     │
                                     │ transactions JSONB        │
                                     │  (array of tx details)    │
                                     │                          │
                                     │ PREDICTION RESULTS       │
                                     │ tampering_detected BOOL   │
                                     │ consistency_score FLOAT   │
                                     │ reconciliation_status VARCHAR
                                     │                          │
                                     │ STATUS & AUDIT           │
                                     │ status VARCHAR           │
                                     │ created_at TIMESTAMP     │
                                     │ analyst_notes TEXT       │
                                     └──────────────────────────┘

ANALYSIS_LOG TABLE (Audit trail)
┌────────────────────────────────┐
│ analysis_logs                  │
├────────────────────────────────┤
│ id (PK)             UUID       │
│ document_id (FK)    UUID       │
│ action              VARCHAR    │ ← uploaded, analyzed, escalated, approved, rejected, overridden
│ action_timestamp    TIMESTAMP  │
│ performed_by_user   UUID       │
│ details             JSONB      │ ← Full context of action
│ created_at          TIMESTAMP  │
└────────────────────────────────┘

ML_MODEL_VERSIONS TABLE (Model tracking)
┌────────────────────────────────┐
│ ml_model_versions              │
├────────────────────────────────┤
│ id (PK)             UUID       │
│ model_name          VARCHAR    │ ← xgboost, random_forest
│ version             VARCHAR    │ ← 1.0, 2.1, etc.
│ trained_date        TIMESTAMP  │
│ training_samples    INT        │
│ validation_accuracy FLOAT      │
│ validation_recall   FLOAT      │
│ validation_precision FLOAT     │
│ feature_count       INT        │
│ model_size_kb       INT        │
│ file_path           VARCHAR    │ ← /trained_models/xgboost_model_v2.pkl
│ is_active           BOOLEAN    │ ← Which model is in production
│ notes               TEXT       │
│ created_at          TIMESTAMP  │
│ deployed_at         TIMESTAMP  │
└────────────────────────────────┘

API_USAGE_LOG TABLE (Tracking external service calls)
┌────────────────────────────────┐
│ api_usage_logs                 │
├────────────────────────────────┤
│ id (PK)             UUID       │
│ service_name        VARCHAR    │ ← google_vision, openai_gpt4
│ api_endpoint        VARCHAR    │
│ request_timestamp   TIMESTAMP  │
│ response_timestamp  TIMESTAMP  │
│ response_time_ms    INT        │
│ status_code         INT        │ ← 200, 429, 503, etc.
│ request_tokens      INT        │
│ response_tokens     INT        │
│ cost_usd            DECIMAL    │
│ error_message       TEXT       │ ← If failed
│ document_id (FK)    UUID       │
│ created_at          TIMESTAMP  │
└────────────────────────────────┘
```

---

## Relationships & Constraints

### **Key Relationships**

| Relationship | Type | Cardinality | Notes |
|-------------|------|-------------|-------|
| users → documents | 1:N | One analyst processes many documents | Indexed on user_id |
| documents → checks | 1:1 | One document is one check (or paystub, etc) | Subtype relationship |
| checks → check_customers | N:1 | Many checks from same payer | Link fraud history |
| documents → analysis_logs | 1:N | One document has many audit log entries | Full history tracked |
| ml_model_versions | 1:N | Multiple versions of same model | Track model evolution |
| api_usage_logs → documents | N:1 | Multiple API calls per document | Cost/performance tracking |

### **Constraints & Indexes**

```sql
-- Primary Keys
PRIMARY KEY (users.id)
PRIMARY KEY (documents.id)
PRIMARY KEY (checks.id)
PRIMARY KEY (check_customers.id)
PRIMARY KEY (analysis_logs.id)

-- Foreign Keys
FOREIGN KEY (documents.user_id) REFERENCES users(id) ON DELETE RESTRICT
FOREIGN KEY (checks.doc_id) REFERENCES documents(id) ON DELETE CASCADE
FOREIGN KEY (checks.user_id) REFERENCES users(id) ON DELETE RESTRICT
FOREIGN KEY (check_customers.payer_name) -- No FK, soft link for performance

-- Unique Constraints
UNIQUE (users.username)
UNIQUE (users.email)
UNIQUE (check_customers.payer_name, check_customers.bank_name, check_customers.routing_number)

-- Indexes (for performance)
INDEX idx_documents_user_id ON documents(user_id)
INDEX idx_documents_created_at ON documents(created_at) -- For time-range queries
INDEX idx_documents_status ON documents(processing_status) -- Filter by status
INDEX idx_checks_fraud_score ON checks(fraud_score_final) -- Find high-risk
INDEX idx_check_customers_fraud_count ON check_customers(fraud_count) -- Find repeat offenders
INDEX idx_analysis_logs_document_id ON analysis_logs(document_id)
INDEX idx_analysis_logs_timestamp ON analysis_logs(action_timestamp)
INDEX idx_api_usage_service ON api_usage_logs(service_name, request_timestamp)
```

---

## ETL Pipeline

### **Overview: Data Flow from Document to Decision**

```
┌─────────────────────────────────────────────────────────────────┐
│                      ETL PIPELINE FLOW                           │
└─────────────────────────────────────────────────────────────────┘

EXTRACT PHASE (Source: Document Upload)
├─ Input: User uploads check image/PDF
├─ File validation:
│  ├─ Type: .png, .jpg, .pdf only
│  ├─ Size: < 10 MB
│  ├─ Dimensions: > 200x200 pixels (for checks)
│  └─ Format: Valid image/PDF (not corrupted)
│
├─ Storage: Save to temporary location
│  ├─ /temp_uploads/{document_id}.{ext}
│  └─ Will be deleted after processing (or archived to S3)
│
├─ Log event: INSERT INTO analysis_logs
│  └─ Action: "uploaded", details: {filename, size, user_id, timestamp}
│
└─ Create document record: INSERT INTO documents
   ├─ id: UUID (generated)
   ├─ user_id: From authenticated user
   ├─ file_path: /temp_uploads/{id}
   ├─ processing_status: "pending"
   └─ upload_timestamp: NOW()

TRANSFORM PHASE 1: OCR EXTRACTION
├─ Read image from temp location
├─ Image preprocessing:
│  ├─ Convert to RGB (if grayscale)
│  ├─ Rotate to correct orientation (detect + fix)
│  ├─ Enhance contrast (if low contrast detected)
│  ├─ Deskew (fix angled images)
│  └─ Remove noise (optional)
│
├─ Send to Google Cloud Vision API:
│  ├─ Request: {image_bytes, features: [TEXT_DETECTION, OBJECT_DETECTION]}
│  ├─ Response: {text_annotations, confidence, label_annotations}
│  └─ Log API call: INSERT INTO api_usage_logs
│     ├─ service_name: "google_vision"
│     ├─ response_time_ms: (e.g., 1240)
│     ├─ status_code: 200
│     └─ cost_usd: 0.0015
│
├─ Parse OCR results to extract structured fields:
│  ├─ Bank name: Search for known banks in text
│  ├─ Payee: Extract name after "Pay to"
│  ├─ Amount: Find currency symbol + numbers
│  ├─ Check number: Extract MICR code
│  ├─ Routing number: First 9 digits of MICR
│  ├─ Account number: Extract account portion
│  ├─ Date: Parse check date
│  └─ Confidence: Mark confidence level per field (99%, 85%, etc.)
│
└─ Update document record:
   ├─ processing_status: "processing"
   ├─ processing_start_time: NOW()
   └─ Log: INSERT INTO analysis_logs (action: "ocr_completed")

TRANSFORM PHASE 2: DATA NORMALIZATION
├─ Load appropriate bank normalizer (e.g., Chase, BofA)
├─ For each extracted field:
│  ├─ Bank name: Normalize to standard format
│  │  └─ "CHASE BANK USA" → "Chase"
│  ├─ Amount: Parse to decimal
│  │  └─ "$5,000.00" → 5000.00
│  ├─ Date: Standardize to YYYY-MM-DD
│  │  └─ "12/15/24" → "2024-12-15"
│  ├─ Routing number: Validate checksum
│  │  └─ Verify against known routing number database
│  └─ Account number: Mask for storage (show last 4 only)
│     └─ "123456789" → "****6789"
│
├─ Consistency checks:
│  ├─ Does amount_words match amount_numbers?
│  │  └─ "Five Thousand" vs "$5000" → Match
│  ├─ Is date in past and recent?
│  │  └─ Check date can't be future or > 6 months old
│  └─ Is account/routing valid format?
│     └─ Routing: 9 digits, Account: 5-17 digits
│
├─ Create features for ML:
│  ├─ field_confidence_avg: Average of all field confidences
│  ├─ amount_confidence: Special attention to amount field
│  ├─ text_count: Number of text elements on document
│  ├─ has_signature: Boolean (detected or not)
│  ├─ document_clarity: Overall image quality score
│  └─ [45+ features total for ML models]
│
└─ INSERT INTO checks:
   ├─ extracted fields: bank_name, payee, amount, etc.
   ├─ field_confidences: JSONB with per-field scores
   ├─ avg_confidence: Average across all fields
   └─ processing_status: "features_ready"

TRANSFORM PHASE 3: CUSTOMER HISTORY LOOKUP
├─ Query check_customers table:
│  ├─ SELECT * FROM check_customers
│  ├─ WHERE payer_name LIKE extracted_payer
│  ├─ AND bank_name = extracted_bank
│  └─ AND routing_number = extracted_routing
│
├─ Results possible:
│  ├─ New customer (no match found)
│  │  └─ fraud_count: 0, escalation_count: 0
│  │
│  ├─ Existing customer with clean history
│  │  └─ fraud_count: 0, escalation_count: 0 → Trust signals
│  │
│  └─ Repeat offender (fraud_count > 0)
│     ├─ fraud_count: 2 (indicates pattern)
│     ├─ escalation_count: 1
│     └─ Automatic escalation/rejection flag set
│
└─ Add to check record:
   ├─ customer_fraud_count: (from lookup)
   ├─ customer_escalation_count: (from lookup)
   └─ known_offender: BOOLEAN

TRANSFORM PHASE 4: ML PREDICTION
├─ Feature vector prepared:
│  ├─ Numeric features: 45 total
│  │  ├─ OCR confidence scores
│  │  ├─ Customer history
│  │  ├─ Temporal features
│  │  ├─ Amount statistics
│  │  └─ Pattern matching scores
│  │
│  └─ Encoded as: [0.95, 0.87, 2, 0, 5000, ...]
│
├─ Load active ML model versions:
│  ├─ XGBoost: /trained_models/xgboost_model.pkl
│  ├─ Random Forest: /trained_models/random_forest_model.pkl
│  └─ Label encoders: /trained_models/label_encoders.pkl
│
├─ Run predictions:
│  ├─ XGBoost prediction: 0.73 (73% fraud probability)
│  ├─ Random Forest prediction: 0.71 (71% fraud probability)
│  ├─ Ensemble (average): 0.72 (72% fraud probability)
│  └─ Log: INSERT INTO api_usage_logs (no external API for local models)
│
├─ Interpret results:
│  ├─ 0-30%: Low risk (APPROVE)
│  ├─ 30-60%: Medium risk (ESCALATE)
│  ├─ 60-85%: High risk (ESCALATE/REJECT)
│  └─ 85-100%: Critical risk (REJECT)
│
└─ UPDATE checks:
   ├─ ml_xgboost_score: 0.73
   ├─ ml_rf_score: 0.71
   ├─ ml_ensemble_score: 0.72
   └─ processing_status: "ml_completed"

TRANSFORM PHASE 5: AI REASONING (GPT-4)
├─ Prepare context for LangChain agent:
│  ├─ Extracted fields: {bank, payee, amount, date, ...}
│  ├─ ML scores: {xgboost: 0.73, rf: 0.71, ensemble: 0.72}
│  ├─ Customer history: {fraud_count: 2, escalation_count: 1, last_fraud: "2024-10-15"}
│  ├─ Feature analysis: "Amount variance: +15% above normal for this customer"
│  ├─ Similar past cases: [
│  │    {check_id: "x", amount: 4950, decision: "rejected", reason: "altered"},
│  │    {check_id: "y", amount: 5100, decision: "escalated", reason: "duplicate"}
│  │  ]
│  └─ Overall risk assessment: "Medium-High risk. Repeat offender with increasing amount."
│
├─ Call GPT-4 via LangChain:
│  ├─ Prompt engineering:
│  │  ```
│  │  You are a fraud detection expert. Analyze this check:
│  │  [structured context above]
│  │
│  │  Provide:
│  │  1. Risk assessment (why is this risky?)
│  │  2. Recommendation: APPROVE / ESCALATE / REJECT
│  │  3. Confidence (HIGH/MEDIUM/LOW)
│  │  4. Suggested next step for analyst
│  │  ```
│  │
│  ├─ Response:
│  │  ```
│  │  RISK ASSESSMENT:
│  │  - Customer has 2 previous fraud attempts
│  │  - Amount ($5000) matches pattern from previous frauds
│  │  - ML score (72%) indicates medium-high risk
│  │  - Similar check was flagged as "altered" last month
│  │
│  │  RECOMMENDATION: ESCALATE
│  │
│  │  CONFIDENCE: HIGH
│  │
│  │  NEXT STEPS:
│  │  - Manual review by analyst recommended
│  │  - Compare with check #0988765 (rejected for alterations)
│  │  - Contact customer to verify legitimacy
│  │  ```
│  │
│  └─ Log: INSERT INTO api_usage_logs
│     ├─ service_name: "openai_gpt4"
│     ├─ request_tokens: 250
│     ├─ response_tokens: 145
│     ├─ cost_usd: 0.024 (approx)
│     └─ response_time_ms: 2100
│
├─ Parse AI response:
│  ├─ Extract recommendation: ESCALATE
│  ├─ Extract confidence: HIGH
│  └─ Store full reasoning text
│
└─ UPDATE checks:
   ├─ ai_recommendation: "ESCALATE"
   ├─ ai_reasoning: [full text above]
   ├─ confidence_level: "HIGH"
   └─ processing_status: "ai_completed"

TRANSFORM PHASE 6: FINAL DECISION LOGIC
├─ Apply escalation rules:
│  ├─ IF customer.escalation_count > 0 THEN decision = "REJECT"
│  │  └─ Reason: "Repeat offender - has been escalated before"
│  │
│  ├─ IF customer.fraud_count > 0 AND ml_score >= 0.30 THEN decision = "REJECT"
│  │  └─ Reason: "Previous fraud + current risk"
│  │
│  ├─ IF ai_recommendation = "REJECT" THEN decision = "REJECT"
│  │  └─ Reason: "AI detected critical risk"
│  │
│  ├─ IF (ai_recommendation = "ESCALATE" OR (0.30 <= ml_score < 0.85)) THEN decision = "ESCALATE"
│  │  └─ Reason: "Medium risk - requires human review"
│  │
│  └─ ELSE decision = "APPROVE"
│     └─ Reason: "Low risk - processing allowed"
│
├─ In this example:
│  ├─ customer.escalation_count = 1 (> 0)
│  └─ DECISION: REJECT
│
├─ Calculate final risk score (0-100):
│  ├─ Base from ML: 72
│  ├─ Adjustment for customer history: +15 (repeat offender)
│  ├─ Adjustment for pattern match: +5 (similar past case)
│  └─ FINAL SCORE: 92 (HIGH RISK)
│
└─ UPDATE checks:
   ├─ final_decision: "REJECT"
   ├─ fraud_score_final: 92
   ├─ status: "completed"
   └─ processing_end_time: NOW()

LOAD PHASE: PERSISTENCE & AUDIT
├─ Store check analysis:
│  └─ UPDATE checks SET
│     ├─ All extracted fields
│     ├─ ML predictions
│     ├─ AI reasoning
│     ├─ Final decision
│     ├─ Fraud score
│     ├─ Status = "completed"
│     └─ Timestamp
│
├─ Update customer history (if needed):
│  ├─ IF decision = "REJECT":
│  │  └─ UPDATE check_customers
│  │     ├─ fraud_count = fraud_count + 1
│  │     ├─ total_amount = total_amount + check.amount
│  │     ├─ last_fraud_date = NOW()
│  │     └─ last_activity = NOW()
│  │
│  └─ IF decision = "ESCALATE":
│     └─ UPDATE check_customers
│        ├─ escalation_count = escalation_count + 1
│        ├─ last_activity = NOW()
│        └─ [fraud_count unchanged until confirmed fraud]
│
├─ Log analysis completion:
│  └─ INSERT INTO analysis_logs
│     ├─ action: "analysis_completed"
│     ├─ decision: "REJECT"
│     ├─ final_score: 92
│     └─ timestamp: NOW()
│
├─ Archive document:
│  ├─ Option A: Copy to S3 for long-term storage
│  ├─ Option B: Delete local temp file (keep metadata)
│  └─ Retention: 6 months → Archive, 7 years → Delete
│
└─ Total processing time:
   ├─ OCR: ~2 seconds (Google Vision)
   ├─ Normalization: ~0.2 seconds
   ├─ ML: ~0.1 seconds
   ├─ AI: ~2.1 seconds (GPT-4 latency)
   ├─ Decision: ~0.1 seconds
   └─ TOTAL: ~4.5 seconds average
```

---

### **Data Quality & Validation**

#### **ETL Validation Checks**

```
STAGE 1: File Upload
├─ Check: File exists and is readable
├─ Check: File size within limits (< 10 MB)
├─ Check: File type is allowed (.pdf, .jpg, .png)
├─ Check: File can be parsed (not corrupted)
└─ Failure action: Reject, notify user

STAGE 2: OCR Extraction
├─ Check: OCR confidence > 50% minimum
├─ Check: All required fields extracted
├─ Check: Extracted text is valid (not garbage)
├─ Check: Amount is numeric
├─ Check: Date is parseable
└─ Failure action: Flag for manual review, escalate

STAGE 3: Data Normalization
├─ Check: Bank name matches known bank database
├─ Check: Routing number is valid (correct length, checksum)
├─ Check: Account number is valid format
├─ Check: Amount > 0 and < $1,000,000 (reasonable)
├─ Check: Date is not future and not > 6 months old
└─ Failure action: Mark field as invalid, continue (don't block)

STAGE 4: Feature Engineering
├─ Check: No NaN/null values in feature vector
├─ Check: Features within expected ranges (e.g., confidence 0-1)
├─ Check: Feature vector has correct dimensionality (45 features)
└─ Failure action: Use defaults for missing features, continue

STAGE 5: ML Prediction
├─ Check: Model loaded successfully
├─ Check: Prediction is numeric (0-1 range)
├─ Check: Both models give reasonable predictions
├─ Check: Ensemble average is within bounds
└─ Failure action: Fall back to threshold-based decision, escalate

STAGE 6: AI Reasoning
├─ Check: GPT-4 API response received
├─ Check: Response contains required fields (recommendation, reasoning)
├─ Check: Recommendation is valid (APPROVE/ESCALATE/REJECT)
└─ Failure action: Use ML score only, apply default thresholds

STAGE 7: Database Storage
├─ Check: All required fields have values
├─ Check: Database transaction succeeds
├─ Check: Customer history table updated correctly
└─ Failure action: Log error, retry, alert admin
```

---

## Data Warehouse & Analytics (Future)

### **Proposed Data Warehouse Schema**

```
For future business intelligence and reporting, XFORIA DAD can include:

FACT_FRAUD_DECISIONS
├─ document_id (FK)
├─ decision_date
├─ decision (APPROVE/ESCALATE/REJECT)
├─ fraud_score
├─ ml_score
├─ ai_recommendation
├─ analyst_override
├─ processing_time_ms
└─ [Measures: count, sum(amount), avg(processing_time)]

DIM_CUSTOMERS
├─ customer_id (SK)
├─ customer_name
├─ bank_name
├─ fraud_history
├─ risk_classification
├─ [Slowly Changing Dimension]

DIM_TIME
├─ date_id
├─ year
├─ quarter
├─ month
├─ day_of_week
└─ [Standard date dimension]

DIM_DOCUMENT_TYPE
├─ doc_type_id
├─ doc_type (check, paystub, money_order, bank_statement)
├─ category
└─ [Slowly Changing Dimension]

ANALYTICS QUERIES
├─ "What % of documents are fraudulent by month?"
├─ "Which customers have highest fraud rate?"
├─ "What's the ROI of XFORIA vs manual review?"
├─ "Which document types are most risky?"
├─ "How accurate are our ML models vs AI recommendations?"
└─ [Used for executive reporting & KPI tracking]
```

---

## Data Lineage & Audit Trail

### **Complete Data Lineage Example**

```
DOCUMENT UPLOAD (2024-12-15 09:30:00)
↓
INPUT: /temp_uploads/check_20241215_001.jpg (450 KB)
Analysis_Log: {action: "uploaded", user: "frank_analyst", timestamp}
↓
OCR EXTRACTION (2024-12-15 09:30:15)
↓
API Call: google_vision_api
- Request: image bytes
- Response: {text: "...", confidence: 0.99}
- Cost: $0.0015
Analysis_Log: {action: "ocr_completed", extracted_fields: {...}}
↓
NORMALIZATION (2024-12-15 09:30:17)
↓
Data transformation: Chase Bank → Chase
Amount: "$5,000.00" → 5000.00
Date: "12/15/24" → "2024-12-15"
Analysis_Log: {action: "normalized"}
↓
CUSTOMER HISTORY LOOKUP (2024-12-15 09:30:18)
↓
Query: check_customers WHERE payer_name LIKE "Alice Corp"
Result: found, fraud_count=2, escalation_count=1
Analysis_Log: {action: "history_lookup", customer_found: true}
↓
ML PREDICTION (2024-12-15 09:30:19)
↓
Features: [0.95, 0.87, 2, 0, 5000, ...]
XGBoost: 0.73
Random Forest: 0.71
Ensemble: 0.72
Analysis_Log: {action: "ml_prediction", scores: {xgb: 0.73, rf: 0.71}}
↓
AI REASONING (2024-12-15 09:30:21)
↓
API Call: openai_gpt4
- Tokens: 250 input, 145 output
- Cost: $0.024
- Response: "ESCALATE - repeat offender"
Analysis_Log: {action: "ai_reasoning", recommendation: "ESCALATE"}
↓
DECISION (2024-12-15 09:30:23)
↓
Logic: escalation_count > 0 → AUTO REJECT
Final Decision: REJECT
Final Score: 92
Analysis_Log: {action: "decision_made", decision: "REJECT", score: 92}
↓
PERSISTENCE (2024-12-15 09:30:23)
↓
UPDATE checks: all fields stored
UPDATE check_customers: fraud_count++ (2→3)
INSERT analysis_logs: decision logged
Timestamp: 2024-12-15 09:30:23
Total Processing Time: 4.5 seconds
↓
OUTPUT: API Response to Frontend
{
  "decision": "REJECT",
  "fraud_score": 92,
  "confidence": "HIGH",
  "reason": "Repeat offender with 3 previous frauds",
  "extracted_data": {...},
  "ai_reasoning": "...",
  "processing_time_ms": 4500
}

AUDIT TRAIL: Complete lineage captured for compliance/regulatory review
```

---

## Summary

XFORIA DAD's data architecture combines:

1. **Normalized ER Schema**: Well-designed tables with clear relationships
2. **Comprehensive ETL**: 6-phase transformation from document to decision
3. **Audit Trail**: Full lineage for compliance and explainability
4. **Data Quality**: Validation checks at each stage
5. **Scalability**: Indexed for performance, ready for data warehouse
6. **Security**: Sensitive data masked, encrypted storage ready

This ensures data integrity, regulatory compliance, and clear decision traceability.
