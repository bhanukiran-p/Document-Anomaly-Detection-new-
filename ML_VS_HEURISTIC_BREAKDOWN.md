# ML vs Heuristic Breakdown for Document Analysis

This document provides a comprehensive breakdown of what relies on Machine Learning (ML) versus heuristic/rule-based approaches for each document type.

---

## 📋 **CHECKS**

### **ML Components** ✅
1. **Fraud Detection** (`Backend/check/ml/check_fraud_detector.py`)
   - **Models**: Random Forest + XGBoost ensemble (40% RF, 60% XGB)
   - **Features**: 30 features extracted by `CheckFeatureExtractor`
   - **Output**: Fraud risk score (0.0-1.0), risk level, model confidence, feature importance
   - **Model Files**: 
     - `check/ml/models/check_random_forest.pkl`
     - `check/ml/models/check_xgboost.pkl`
     - `check/ml/models/check_feature_scaler.pkl`
   - **Fallback**: If models not loaded, uses mock/heuristic scoring (`_predict_mock`)

2. **AI Analysis** (`Backend/check/ai/check_fraud_analysis_agent.py`)
   - Uses OpenAI API to analyze ML scores + extracted data
   - Makes final recommendation (APPROVE/REJECT/ESCALATE)

### **Heuristic Components** 🔧
1. **OCR Extraction** (`Backend/check/check_extractor.py`)
   - Uses Mindee API (ClientV2) for OCR - **NOT ML-based extraction**
   - Field mapping and extraction from Mindee response

2. **Normalization** (`Backend/check/normalization/`)
   - Bank-specific normalizers (Chase, Bank of America, Wells Fargo, etc.)
   - Rule-based field standardization and validation
   - Completeness scoring based on required fields

3. **Validation Rules** (`Backend/check/check_extractor.py::_collect_validation_issues`)
   - Missing signature detection
   - Missing critical fields (check number, payer, payee)
   - Payer/payee same person check
   - High amount threshold (>$10,000)
   - Stale check detection (age > 180 days)
   - Future date detection
   - Duplicate check detection (database lookup)

4. **Feature Extraction** (`Backend/check/ml/check_feature_extractor.py`)
   - Converts extracted data into 30 numerical features
   - Rule-based feature engineering (bank validity, routing validity, date age, etc.)

---

## 💰 **MONEY ORDERS**

### **ML Components** ✅
1. **Fraud Detection** (`Backend/money_order/ml/money_order_fraud_detector.py`)
   - **Models**: Random Forest + XGBoost ensemble (40% RF, 60% XGB)
   - **Features**: 30 features extracted by `MoneyOrderFeatureExtractor`
   - **Output**: Fraud risk score (0.0-1.0), risk level, model confidence, fraud indicators
   - **Model Files**:
     - `money_order/ml/models/money_order_random_forest.pkl`
     - `money_order/ml/models/money_order_xgboost.pkl`
     - `money_order/ml/models/money_order_feature_scaler.pkl`
   - **Fallback**: If models not loaded, uses mock/heuristic scoring (`_mock_predict`)

2. **AI Analysis** (`Backend/money_order/ai/fraud_analysis_agent.py`)
   - Uses OpenAI API to analyze ML scores + extracted data
   - Makes final recommendation (APPROVE/REJECT/ESCALATE)
   - Validates amount spelling errors in raw OCR text

### **Heuristic Components** 🔧
1. **OCR Extraction** (`Backend/money_order/extractor.py`)
   - Uses Google Vision API for OCR - **NOT ML-based extraction**
   - Regex-based field extraction:
     - Issuer detection (USPS, Western Union, MoneyGram, etc.)
     - Serial number patterns
     - Amount extraction (numeric and written)
     - Payee/purchaser extraction
     - Date extraction with format normalization
     - Signature detection (pattern matching)

2. **Normalization** (`Backend/money_order/normalization/`)
   - Issuer-specific normalizers
   - Rule-based field standardization

3. **Validation Rules** (`Backend/money_order/ml/money_order_fraud_detector.py::_apply_strict_validation`)
   - Amount mismatch detection (numeric vs written)
   - Future date detection (+0.40 penalty)
   - Amount spelling validation (checks for misspelled number words)
   - Missing signature detection (+0.60 penalty - CRITICAL)
   - Critical missing fields (amount, serial, recipient)
   - Old date detection (>180 days)
   - Invalid serial format
   - Suspicious amount patterns

4. **Feature Extraction** (`Backend/money_order/ml/money_order_feature_extractor.py`)
   - Converts extracted data into 30 numerical features
   - Rule-based feature engineering (issuer validity, serial format, amount matching, etc.)

---

## 💼 **PAYSTUBS**

### **ML Components** ✅
1. **Fraud Detection** (`Backend/paystub/ml/paystub_fraud_detector.py`)
   - **Model**: Random Forest (single model, not ensemble)
   - **Features**: 18 features extracted by `PaystubFeatureExtractor`
   - **Output**: Fraud risk score (0.0-1.0), risk level, model confidence, fraud types
   - **Model Files**:
     - `paystub/ml/models/paystub_risk_model_latest.pkl`
     - `paystub/ml/models/paystub_scaler_latest.pkl`
     - `paystub/ml/models/paystub_model_metadata_latest.json`
   - **NO Fallback**: Raises RuntimeError if models not loaded (models are REQUIRED)
   - **⚠️ FIXED**: Previously only caught `ImportError` but not `RuntimeError` when models fail to load. Now properly catches both and fails fast with clear error message.

2. **AI Analysis** (`Backend/paystub/ai/paystub_fraud_analysis_agent.py`)
   - Uses OpenAI API to analyze ML scores + extracted data
   - Makes final recommendation (APPROVE/REJECT/ESCALATE)
   - Post-AI validation for repeat offenders

### **Heuristic Components** 🔧
1. **OCR Extraction** (`Backend/paystub/paystub_extractor.py`)
   - Uses Mindee API (ClientV2) for OCR - **NOT ML-based extraction**
   - Field mapping from Mindee Payslip schema
   - Tax/deduction extraction from arrays

2. **Normalization** (`Backend/paystub/normalization/paystub_normalizer_factory.py`)
   - Paystub-specific normalizer
   - Rule-based field standardization
   - Completeness scoring

3. **Validation Rules** (`Backend/paystub/paystub_extractor.py::_collect_validation_issues`)
   - Missing critical fields (company_name, employee_name, gross_pay, net_pay, pay_period)
   - Net pay > Gross pay check (impossible value)
   - Duplicate paystub detection (database lookup)

4. **Feature Extraction** (`Backend/paystub/ml/paystub_feature_extractor.py`)
   - Converts extracted data into 18 numerical features
   - Rule-based feature engineering (has_company, has_employee, tax_error, net_to_gross_ratio, etc.)

5. **Fraud Type Classification** (`Backend/paystub/ml/paystub_fraud_detector.py::_classify_fraud_types`)
   - Rule-based classification into 4 document-level fraud types:
     - FABRICATED_DOCUMENT
     - UNREALISTIC_PROPORTIONS
     - ZERO_WITHHOLDING_SUSPICIOUS
     - ALTERED_LEGITIMATE_DOCUMENT

---

## 🏦 **BANK STATEMENTS**

### **ML Components** ✅
1. **Fraud Detection** (`Backend/bank_statement/ml/bank_statement_fraud_detector.py`)
   - **Models**: Random Forest + XGBoost ensemble (40% RF, 60% XGB)
   - **Features**: 35 features extracted by `BankStatementFeatureExtractor`
   - **Output**: Fraud risk score (0.0-1.0), risk level, model confidence, fraud types
   - **Model Files**:
     - `bank_statement/ml/models/bank_statement_random_forest.pkl`
     - `bank_statement/ml/models/bank_statement_xgboost.pkl`
     - `bank_statement/ml/models/bank_statement_feature_scaler.pkl`
   - **NO Fallback**: Raises RuntimeError if models not loaded (models are REQUIRED)

2. **AI Analysis** (`Backend/bank_statement/ai/bank_statement_fraud_analysis_agent.py`)
   - Uses OpenAI API to analyze ML scores + extracted data
   - Makes final recommendation (APPROVE/REJECT/ESCALATE)

### **Heuristic Components** 🔧
1. **OCR Extraction** (`Backend/bank_statement/extractor.py`)
   - Uses Mindee API (ClientV2) for OCR - **NOT ML-based extraction**
   - Regex-based fallback extraction from raw text:
     - Bank name patterns
     - Account holder patterns
     - Account number patterns
     - Statement period dates
     - Balance extraction

2. **PDF Validation** (`Backend/utils/pdf_statement_validator.py`)
   - **COMPLETELY HEURISTIC** - Rule-based PDF tampering detection
   - **Metadata Checks**:
     - Suspicious creator/producer
     - Future creation dates
     - Recent modifications
   - **Structure Checks**:
     - Missing pages
     - Page order suspicious
     - Corrupted objects
   - **Content Checks**:
     - Inconsistent formatting
     - Text overlay detected
     - Unusual spacing
     - Broken fonts
   - **Financial Checks**:
     - Balance calculation errors
     - Transaction date inconsistencies
     - Suspicious amounts
     - Missing transactions
   - **Behavioral Checks**:
     - Transaction patterns
     - Round number transactions
     - Weekend/holiday transactions
   - **Spelling/Formatting Checks**:
     - Spelling errors
     - Formatting inconsistencies
   - **Missing Data Checks**:
     - Missing dates
     - Invalid dates
     - Missing balances

3. **Feature Extraction** (`Backend/bank_statement/ml/bank_statement_feature_extractor.py`)
   - Converts extracted data into 35 numerical features
   - Rule-based feature engineering:
     - Bank validity
     - Account number presence
     - Balance consistency
     - Transaction pattern analysis
     - Duplicate transaction detection
     - Round number detection
     - Credit/debit ratio
     - Balance volatility

4. **Fraud Type Classification** (`Backend/bank_statement/ml/bank_statement_fraud_detector.py::_classify_fraud_types`)
   - Rule-based classification into 5 document-level fraud types:
     - FABRICATED_DOCUMENT
     - ALTERED_LEGITIMATE_DOCUMENT
     - SUSPICIOUS_TRANSACTION_PATTERNS
     - BALANCE_CONSISTENCY_VIOLATION
     - UNREALISTIC_FINANCIAL_PROPORTIONS

---

## 📊 **Summary Table**

| Document Type | ML Components | Heuristic Components |
|--------------|---------------|---------------------|
| **Checks** | ✅ Fraud Detection (RF+XGB ensemble)<br>✅ AI Analysis | 🔧 OCR (Mindee API)<br>🔧 Normalization<br>🔧 Validation Rules<br>🔧 Feature Extraction |
| **Money Orders** | ✅ Fraud Detection (RF+XGB ensemble)<br>✅ AI Analysis | 🔧 OCR (Google Vision API)<br>🔧 Regex Field Extraction<br>🔧 Normalization<br>🔧 Validation Rules<br>🔧 Feature Extraction |
| **Paystubs** | ✅ Fraud Detection (RF single model)<br>✅ AI Analysis | 🔧 OCR (Mindee API)<br>🔧 Normalization<br>🔧 Validation Rules<br>🔧 Feature Extraction<br>🔧 Fraud Type Classification |
| **Bank Statements** | ✅ Fraud Detection (RF+XGB ensemble)<br>✅ AI Analysis | 🔧 OCR (Mindee API)<br>🔧 PDF Validation (100% heuristic)<br>🔧 Regex Field Extraction<br>🔧 Feature Extraction<br>🔧 Fraud Type Classification |

---

## 🔑 **Key Insights**

1. **OCR is NOT ML-based**: All document types use external OCR APIs (Mindee or Google Vision), which are ML-based services but not part of this codebase's ML models.

2. **ML Models are Used for Fraud Detection**: All document types use trained ML models (Random Forest and/or XGBoost) to predict fraud risk scores.

3. **Feature Extraction is Heuristic**: Converting extracted data into numerical features is done using rule-based logic, not ML.

4. **Bank Statements Have Extensive Heuristic Validation**: The PDF validator for bank statements is completely rule-based with no ML components.

5. **AI Analysis is Separate**: All document types use OpenAI API for final decision-making, which combines ML scores with extracted data and customer history.

6. **Models Have Fallbacks (Except Paystubs & Bank Statements)**:
   - Checks: Has mock/heuristic fallback if models not loaded
   - Money Orders: Has mock/heuristic fallback if models not loaded
   - Paystubs: **NO fallback** - raises error if models not loaded
   - Bank Statements: **NO fallback** - raises error if models not loaded

---

## 📝 **Notes**

- **REPEAT_OFFENDER** fraud type is added by AI agents, not ML models (history-based)
- All ML models use feature scaling (StandardScaler) before prediction
- Fraud type classification is rule-based, not ML-based (uses feature thresholds)
- Normalization is always heuristic/rule-based, not ML-based
