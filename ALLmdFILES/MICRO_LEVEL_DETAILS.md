# MICRO-LEVEL DETAILS: Paystub vs Money Order Processing

## Table of Contents
1. [Extraction (OCR) Process](#1-extraction-ocr-process)
2. [Normalization Process](#2-normalization-process)
3. [ML Model Working](#3-ml-model-working)
4. [ML Model Training](#4-ml-model-training)
5. [Model Storage](#5-model-storage)
6. [Database Storage](#6-database-storage)
7. [Customer Logic](#7-customer-logic)
8. [AI Analysis](#8-ai-analysis)
9. [How AI Uses ML Scores](#9-how-ai-uses-ml-scores)

---

## 1. EXTRACTION (OCR) PROCESS

### PAYSTUB EXTRACTION

**File:** `Backend/paystub/paystub_extractor.py` (lines 161-321)

**Method:** `_extract_with_mindee(file_path: str)`

**Step-by-Step Process:**

1. **Initialize Mindee Client**
   - Uses `ClientV2` API from Mindee library
   - Requires `MINDEE_API_KEY` from environment
   - Uses model ID: `MINDEE_MODEL_ID_PAYSTUB` (default: `15fab31e-ac0e-4ccc-83ed-39b9f65bb791`)

2. **Call Mindee API**
   ```python
   params = InferenceParameters(model_id=MINDEE_MODEL_ID_PAYSTUB, raw_text=True)
   input_source = PathInput(file_path)
   response = mindee_client.enqueue_and_get_inference(input_source, params)
   ```

3. **Parse Mindee Response**
   - Extracts `response.inference.result.fields` (dictionary of field objects)
   - Each field is a `SimpleField` object with `.value` attribute
   - Arrays (deductions, taxes) have `.items` attribute with nested objects

4. **Field Mapping (Direct)**
   - Mindee fields map directly to our schema:
     - `first_name` → `first_name`
     - `last_name` → `last_name`
     - `employer_name` → `employer_name` (also copied to `company_name`)
     - `pay_period_start_date` → `pay_period_start_date`
     - `pay_period_end_date` → `pay_period_end_date`
     - `gross_pay` → `gross_pay`
     - `net_pay` → `net_pay`
     - `deductions` → `deductions` (array)
     - `taxes` → `taxes` (array)

5. **Post-Processing**
   - Combines `first_name` + `last_name` → `employee_name`
   - Extracts tax amounts from deductions/taxes arrays:
     - Searches for "FEDERAL" → `federal_tax`
     - Searches for "STATE" → `state_tax`
     - Searches for "SOCIAL"/"SS"/"OASDI" → `social_security`
     - Searches for "MEDICARE"/"MED" → `medicare`

6. **Return**
   - Returns `(extracted_dict, raw_text)` tuple
   - `extracted_dict`: All extracted fields as dictionary
   - `raw_text`: Full OCR text from Mindee

**No Regex Parsing:** Mindee returns structured data, so no regex needed.

---

### MONEY ORDER EXTRACTION

**File:** `Backend/money_order/extractor.py` (lines 93-487)

**Method:** `extract_text_from_image()` + `_extract_*()` methods

**Step-by-Step Process:**

1. **Initialize Google Vision API**
   - Uses `vision.ImageAnnotatorClient()` from Google Cloud Vision
   - Requires Google Cloud credentials JSON file

2. **Extract Raw Text**
   ```python
   image = vision.Image(content=content)
   response = self.client.text_detection(image=image)
   raw_text = texts[0].description  # Full OCR text
   ```

3. **Regex-Based Field Extraction**
   Each field uses regex patterns to extract from raw text:

   - **Issuer** (line 211-236):
     - Patterns: `'UNITED STATES POSTAL'`, `'USPS'`, `'WESTERN UNION'`, `'MONEYGRAM'`, etc.
     - Returns issuer name string

   - **Serial Number** (line 238-252):
     - Pattern: `r'SERIAL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})'`
     - Also checks: `r'CONTROL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})'`

   - **Amount** (line 269-283):
     - Pattern: `r'AMOUNT[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))'`
     - Also checks: `r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})'`

   - **Amount in Words** (line 285-301):
     - Pattern: `r'([A-Z][A-Za-z\s]+(?:HUNDRED|THOUSAND|MILLION)\s+[A-Za-z\s]+AND\s+\d{1,2}/\d{2,3}\s+DOLLARS)'`

   - **Payee** (line 303-318):
     - Pattern: `r'PAY\s+TO(?:\s+THE\s+ORDER\s+OF)?[:\s]*([A-Z\s\.]+?)(?:\n|$)'`

   - **Purchaser** (line 320-335):
     - Pattern: `r'PURCHASER[:\s]*([A-Z][A-Za-z\s\.]+?)(?:\n|$)'`

   - **Date** (line 356-404):
     - Multiple patterns: `r'DATE[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'`
     - Also handles month names: `r'((?:JANUARY|FEBRUARY|...)\s+\d{1,2},?\s+\d{4})'`
     - Normalizes to MM/DD/YYYY format

   - **Signature** (line 436-486):
     - Checks for signature indicators: `'POSTAL CLERK'`, `'AGENT'`, `'AUTHORIZED'`, `'SIGNATURE'`
     - Extracts signature value if found

4. **Return Extracted Data**
   ```python
   extracted_data = {
       'issuer': issuer,
       'serial_number': serial_number,
       'amount': amount,
       'amount_in_words': amount_in_words,
       'payee': payee,
       'purchaser': purchaser,
       'date': date,
       'signature': signature,
       ...
   }
   ```

**Key Difference:** Paystub uses structured API (Mindee), Money Order uses regex parsing.

---

## 2. NORMALIZATION PROCESS

### PAYSTUB NORMALIZATION

**Files:**
- `Backend/paystub/normalization/paystub_base_normalizer.py` (base class)
- `Backend/paystub/normalization/paystub_normalizer.py` (implementation)
- `Backend/paystub/normalization/paystub_normalizer_factory.py` (factory)

**Layers of Normalization:**

#### Layer 1: Field Mapping
**File:** `paystub_normalizer.py` (lines 19-55)

Maps Mindee field names to standardized schema:
```python
{
    'employer_name': 'company_name',
    'employer_address': 'company_address',
    'employee_name': 'employee_name',
    'pay_period_start_date': 'pay_period_start',
    'pay_period_end_date': 'pay_period_end',
    'gross_pay': 'gross_pay',
    'net_pay': 'net_pay',
    'federal_tax': 'federal_tax',
    'state_tax': 'state_tax',
    ...
}
```

#### Layer 2: Type Normalization
**File:** `paystub_base_normalizer.py` (lines 37-86)

For each field, applies type-specific normalization:

- **Amounts** (lines 88-104):
  - Removes `$`, `,`, spaces
  - Converts to `float`
  - Example: `"$1,250.50"` → `1250.50`

- **Dates** (lines 106-132):
  - Parses multiple formats: `'%m-%d-%Y'`, `'%m/%d/%Y'`, `'%B %d, %Y'`, etc.
  - Converts to ISO format: `'2024-01-15T00:00:00'`
  - Example: `"01/15/2024"` → `"2024-01-15T00:00:00"`

- **Numeric** (lines 134-149):
  - Removes non-numeric characters
  - Converts to `float`
  - Example: `"40.5 hours"` → `40.5`

- **Strings** (lines 151-161):
  - Removes extra whitespace
  - Example: `"  John   Doe  "` → `"John Doe"`

#### Layer 3: Schema Creation
**File:** `paystub_base_normalizer.py` (line 86)

Creates `NormalizedPaystub` dataclass instance:
```python
normalized_data = {
    'company_name': 'Acme Corp',
    'employee_name': 'John Doe',
    'gross_pay': 2500.0,
    'net_pay': 1672.50,
    ...
}
return NormalizedPaystub(**normalized_data)
```

**Total Layers: 3** (Mapping → Type Normalization → Schema)

---

### MONEY ORDER NORMALIZATION

**Files:**
- `Backend/money_order/normalization/base_normalizer.py` (base class)
- `Backend/money_order/normalization/western_union.py` (issuer-specific)
- `Backend/money_order/normalization/moneygram.py` (issuer-specific)
- `Backend/money_order/normalization/normalizer_factory.py` (factory)

**Layers of Normalization:**

#### Layer 1: Issuer Detection
**File:** `extractor.py` (line 150-151)

Detects issuer from extracted data:
```python
issuer = extracted_data.get('issuer')  # e.g., 'USPS', 'Western Union'
normalizer = MoneyOrderNormalizerFactory.get_normalizer(issuer)
```

#### Layer 2: Issuer-Specific Field Mapping
**File:** `western_union.py` or `moneygram.py`

Each issuer has different field mappings:

**Western Union:**
```python
{
    'purchaser': 'sender_name',
    'payee': 'recipient',
    'amount': 'amount_numeric',
    'serial_number': 'serial_primary',
    ...
}
```

**MoneyGram:**
```python
{
    'from': 'sender_name',
    'to': 'recipient',
    'amount': 'amount_numeric',
    ...
}
```

#### Layer 3: Type Normalization
**File:** `base_normalizer.py` (lines 45-79)

- **Amounts** (lines 81-110):
  - Extracts numeric value: `"$750.00"` → `{'value': 750.0, 'currency': 'USD'}`
  - Handles formats: `"750.00 USD"`, `"USD 750.00"`, `"750,00"`

- **Dates** (lines 112-140):
  - Parses multiple formats
  - Converts to ISO format

- **Strings** (lines 142-150):
  - Cleans whitespace

#### Layer 4: Schema Creation
**File:** `base_normalizer.py` (line 79)

Creates `NormalizedMoneyOrder` dataclass:
```python
normalized_data = {
    'issuer_name': 'Western Union',
    'sender_name': 'John Doe',
    'recipient': 'Jane Smith',
    'amount_numeric': {'value': 750.0, 'currency': 'USD'},
    ...
}
return NormalizedMoneyOrder.from_dict(normalized_data)
```

**Total Layers: 4** (Issuer Detection → Field Mapping → Type Normalization → Schema)

**Key Difference:** Money Order has issuer-specific normalizers (more complex), Paystub has single generic normalizer.

---

## 3. ML MODEL WORKING

### PAYSTUB ML MODEL

**Files:**
- `Backend/paystub/ml/paystub_fraud_detector.py` (main detector)
- `Backend/paystub/ml/paystub_feature_extractor.py` (feature extraction)

**Step-by-Step Process:**

#### Step 1: Feature Extraction
**File:** `paystub_feature_extractor.py` (lines 34-108)

Extracts **10 features** from normalized paystub data:

1. `has_company` (0 or 1): Does `company_name` exist?
2. `has_employee` (0 or 1): Does `employee_name` exist?
3. `has_gross` (0 or 1): Does `gross_pay` exist?
4. `has_net` (0 or 1): Does `net_pay` exist?
5. `has_date` (0 or 1): Does `pay_period_start` OR `pay_period_end` exist?
6. `gross_pay` (float): Numeric gross pay amount (capped at $100k)
7. `net_pay` (float): Numeric net pay amount (capped at $100k)
8. `tax_error` (0 or 1): Is `net_pay >= gross_pay`? (impossible!)
9. `text_quality` (0.5-1.0): Calculated as `0.5 + (present_fields / 5) * 0.5`
10. `missing_fields_count` (0-5): Count of missing critical fields

**Example:**
```python
features = [1.0, 1.0, 1.0, 1.0, 1.0, 2500.0, 1672.50, 0.0, 0.9, 0.0]
#           ↑    ↑    ↑    ↑    ↑    ↑       ↑        ↑    ↑    ↑
#         comp emp gross net date gross    net    tax_err qual miss
```

#### Step 2: Model Loading
**File:** `paystub_fraud_detector.py` (lines 52-92)

Loads from `paystub/ml/models/`:
- `paystub_risk_model_latest.pkl` (Random Forest model)
- `paystub_scaler_latest.pkl` (StandardScaler)
- `paystub_model_metadata_latest.json` (metadata)

#### Step 3: Feature Scaling
**File:** `paystub_fraud_detector.py` (lines 130-132)

```python
X = np.array([features])  # Shape: (1, 10)
X_scaled = self.scaler.transform(X)  # Normalize features
```

#### Step 4: Prediction
**File:** `paystub_fraud_detector.py` (lines 135-138)

```python
risk_score_raw = self.model.predict(X_scaled)[0]  # Output: 0-100
fraud_risk_score = risk_score_raw / 100.0  # Convert to 0-1
```

#### Step 5: Risk Level Categorization
**File:** `paystub_fraud_detector.py` (lines 154-161)

```python
if fraud_risk_score < 0.3:
    risk_level = 'LOW'
elif fraud_risk_score < 0.7:
    risk_level = 'MEDIUM'
elif fraud_risk_score < 0.9:
    risk_level = 'HIGH'
else:
    risk_level = 'CRITICAL'
```

#### Step 6: Return Results
**File:** `paystub_fraud_detector.py` (lines 166-175)

```python
return {
    'fraud_risk_score': 0.10,  # 10%
    'risk_level': 'LOW',
    'model_confidence': 0.90,
    'model_scores': {'random_forest': 0.10},
    'feature_importance': ['missing_fields_count: 0.234', ...],
    'anomalies': ['Missing 1 critical field']
}
```

**Model Type:** Random Forest Regressor (predicts continuous 0-100 score)

---

### MONEY ORDER ML MODEL

**Files:**
- `Backend/money_order/ml/money_order_fraud_detector.py` (main detector)
- `Backend/money_order/ml/money_order_feature_extractor.py` (feature extraction)

**Step-by-Step Process:**

#### Step 1: Feature Extraction
**File:** `money_order_feature_extractor.py` (lines 36-136)

Extracts **30 features** (17 basic + 13 advanced):

**Basic Features (1-17):**
1. `issuer_valid` (0-1): Is issuer valid?
2. `serial_length` (float): Length of serial number
3. `serial_format_valid` (0-1): Does serial match format?
4. `amount_numeric` (float): Numeric amount value
5. `amount_consistent` (0-1): Do numeric and written amounts match?
6. `amount_is_round` (0-1): Is amount a round number?
7. `payee_present` (0-1): Does payee exist?
8. `purchaser_present` (0-1): Does purchaser exist?
9. `date_present` (0-1): Does date exist?
10. `date_is_future` (0-1): Is date in future? (red flag)
11. `date_age_days` (float): How old is the date?
12. `location_present` (0-1): Does location exist?
13. `signature_present` (0-1): Does signature exist?
14. `receipt_present` (0-1): Does receipt number exist?
15. `missing_fields_count` (float): Count of missing fields
16. `text_quality_score` (0-1): OCR text quality
17. `amount_category` (0-3): Amount range category

**Advanced Features (18-30):**
From `money_order_advanced_features.py`:
- `exact_amount_match` (0-1)
- `amount_parsing_confidence` (0-1)
- `suspicious_amount_pattern` (0-1)
- `date_format_consistency` (0-1)
- `weekend_holiday_flag` (0-1)
- `date_amount_correlation` (0-1)
- `critical_missing_score` (0-1)
- `field_quality_score` (0-1)
- `issuer_specific_validation` (0-1)
- `serial_pattern_match` (0-1)
- `address_validation` (0-1)
- `name_consistency` (0-1)
- `signature_required_score` (0-1)

#### Step 2: Model Loading
**File:** `money_order_fraud_detector.py` (lines 46-73)

Loads from `money_order/ml/models/`:
- `money_order_random_forest.pkl` (Random Forest model)
- `money_order_xgboost.pkl` (XGBoost model)
- `money_order_feature_scaler.pkl` (StandardScaler)

#### Step 3: Feature Scaling
**File:** `money_order_fraud_detector.py` (lines 193-196)

```python
X = np.array(features).reshape(1, -1)  # Shape: (1, 30)
X_scaled = self.scaler.transform(X)
```

#### Step 4: Ensemble Prediction
**File:** `money_order_fraud_detector.py` (lines 201-216)

```python
# Random Forest prediction
rf_proba = self.rf_model.predict_proba(X_scaled)[0][1]  # Probability of fraud

# XGBoost prediction
xgb_proba = self.xgb_model.predict_proba(X_scaled)[0][1]

# Ensemble (weighted average)
base_fraud_score = 0.4 * rf_proba + 0.6 * xgb_proba
```

#### Step 5: Strict Validation Rules
**File:** `money_order_fraud_detector.py` (lines 218-299)

Applies additional rules on top of ML prediction:
- Amount mismatch: +0.40
- Future date: +0.40
- Critical missing fields: +0.30
- Very old date (>180 days): +0.20
- Invalid serial format: +0.15
- Weekend/holiday + large amount: +0.15
- ... (many more rules)

```python
final_fraud_score = self._apply_strict_validation(base_fraud_score, features, ...)
```

#### Step 6: Risk Level Categorization
**File:** `money_order_fraud_detector.py` (lines 368-377)

```python
if score < 0.3:
    return 'LOW'
elif score < 0.6:
    return 'MEDIUM'
elif score < 0.85:
    return 'HIGH'
else:
    return 'CRITICAL'
```

#### Step 7: Return Results
**File:** `money_order_fraud_detector.py` (lines 233-245)

```python
return {
    'fraud_risk_score': 0.25,  # 25%
    'risk_level': 'MEDIUM',
    'model_confidence': 0.85,
    'model_scores': {
        'random_forest': 0.23,
        'xgboost': 0.27,
        'ensemble': 0.25,
        'adjusted': 0.25
    },
    'feature_importance': ['Amount mismatch detected', ...],
    'prediction_type': 'model'
}
```

**Model Type:** Ensemble (Random Forest + XGBoost) with strict validation rules

**Key Difference:** Money Order uses 2 models (RF + XGBoost) with 30 features, Paystub uses 1 model (RF) with 10 features.

---

## 4. ML MODEL TRAINING

### TRAINING SCRIPT

**File:** `Backend/training/train_risk_model.py`

**Step-by-Step Process:**

#### Step 1: Generate Synthetic Training Data
**File:** `train_risk_model.py` (lines 166-234 for paystub, lines 53-164 for check)

**For Paystub:**
```python
def generate_dummy_paystub_data(n_samples=2000):
    for i in range(n_samples):
        # Randomly generate features
        has_company = random.random() > 0.08  # 92% have company
        has_employee = random.random() > 0.05  # 95% have employee
        has_gross = random.random() > 0.03
        has_net = random.random() > 0.03
        has_date = random.random() > 0.08
        
        # Generate amounts
        if has_gross and has_net:
            gross = random.uniform(1000, 10000)
            net = random.uniform(500, gross * 0.9)  # Net < gross
            tax_error = 1 if net >= gross else 0
        else:
            gross = 0
            net = 0
            tax_error = 1
        
        # Calculate risk score (ground truth)
        missing_fields = sum([not has_company, not has_employee, not has_gross, not has_net, not has_date])
        risk_score = (missing_fields / 5) * 25  # Up to 25 points
        if tax_error:
            risk_score += 20  # +20 points
        risk_score += random.uniform(-3, 3)  # Random noise
        risk_score = max(0, min(100, risk_score))  # Cap at 0-100
        
        # Create feature vector
        features = {
            'has_company': 1 if has_company else 0,
            'has_employee': 1 if has_employee else 0,
            'has_gross': 1 if has_gross else 0,
            'has_net': 1 if has_net else 0,
            'has_date': 1 if has_date else 0,
            'gross_pay': gross,
            'net_pay': net,
            'tax_error': tax_error,
            'text_quality': random.uniform(0.5, 1.0),
            'missing_fields_count': missing_fields,
            'risk_score': risk_score  # TARGET VARIABLE
        }
```

**Result:** DataFrame with 11 columns (10 features + 1 target `risk_score`)

#### Step 2: Prepare Features
**File:** `train_risk_model.py` (lines 236-262)

```python
feature_cols = [
    'has_company', 'has_employee', 'has_gross', 'has_net', 'has_date',
    'gross_pay', 'net_pay', 'tax_error', 'text_quality', 'missing_fields_count'
]
X = df[feature_cols].values  # Features (2000 x 10)
y = df['risk_score'].values  # Target (2000 x 1)
```

#### Step 3: Split Data
**File:** `train_risk_model.py` (lines 418-421)

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
# X_train: 1600 samples, X_test: 400 samples
```

#### Step 4: Scale Features
**File:** `train_risk_model.py` (lines 269-270)

```python
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # Normalize to mean=0, std=1
```

#### Step 5: Train Model
**File:** `train_risk_model.py` (lines 272-282)

```python
model = RandomForestRegressor(
    n_estimators=100,      # 100 decision trees
    max_depth=10,           # Max depth of each tree
    min_samples_split=5,    # Min samples to split node
    min_samples_leaf=2,     # Min samples in leaf
    random_state=42,
    n_jobs=-1              # Use all CPU cores
)
model.fit(X_train_scaled, y_train)  # Train on 1600 samples
```

#### Step 6: Evaluate Model
**File:** `train_risk_model.py` (lines 297-312)

```python
X_test_scaled = scaler.transform(X_test)
y_pred = model.predict(X_test_scaled)

mse = mean_squared_error(y_test, y_pred)  # Mean squared error
r2 = r2_score(y_test, y_pred)             # R² score (0-1, higher is better)
rmse = np.sqrt(mse)                       # Root mean squared error
```

#### Step 7: Save Model
**File:** `train_risk_model.py` (lines 314-387)

Saves to **TWO locations**:

1. **Document-Specific Folder:**
   ```python
   doc_dir = 'paystub/ml/models'
   doc_latest_model = f"{doc_dir}/paystub_risk_model_latest.pkl"
   doc_latest_scaler = f"{doc_dir}/paystub_scaler_latest.pkl"
   doc_latest_metadata = f"{doc_dir}/paystub_model_metadata_latest.json"
   ```

2. **Global Models Folder:**
   ```python
   global_dir = 'models'
   latest_model = f"{global_dir}/paystub_risk_model_latest.pkl"
   latest_scaler = f"{global_dir}/paystub_scaler_latest.pkl"
   latest_metadata = f"{global_dir}/paystub_model_metadata_latest.json"
   ```

**Files Saved:**
- `.pkl` files: Binary Python pickle format (contains trained model/scaler)
- `.json` file: Metadata (model type, feature names, training date)

**Training Data Saved:**
- `paystub_training_data.csv` (2000 rows x 11 columns)
- `paystub_training_data.xlsx` (if openpyxl available)

---

## 5. MODEL STORAGE

### PAYSTUB MODELS

**Location:** `Backend/paystub/ml/models/`

**Files:**
1. `paystub_risk_model_latest.pkl` (~1.6 MB)
   - Random Forest Regressor model
   - Contains 100 decision trees
   - Can predict risk score (0-100) from 10 features

2. `paystub_scaler_latest.pkl` (~689 bytes)
   - StandardScaler object
   - Contains mean and std for each feature
   - Used to normalize features before prediction

3. `paystub_model_metadata_latest.json` (~500 bytes)
   ```json
   {
     "document_type": "paystub",
     "model_type": "random_forest",
     "feature_names": ["has_company", "has_employee", ...],
     "trained_at": "20241201_120000",
     "feature_count": 10
   }
   ```

**Loading Process:**
```python
import joblib
model = joblib.load('paystub/ml/models/paystub_risk_model_latest.pkl')
scaler = joblib.load('paystub/ml/models/paystub_scaler_latest.pkl')
```

---

### MONEY ORDER MODELS

**Location:** `Backend/money_order/ml/models/`

**Files:**
1. `money_order_random_forest.pkl`
   - Random Forest Classifier model
   - Predicts probability of fraud (0-1)

2. `money_order_xgboost.pkl`
   - XGBoost Classifier model
   - Predicts probability of fraud (0-1)

3. `money_order_feature_scaler.pkl`
   - StandardScaler for 30 features

**Loading Process:**
```python
import joblib
rf_model = joblib.load('money_order/ml/models/money_order_random_forest.pkl')
xgb_model = joblib.load('money_order/ml/models/money_order_xgboost.pkl')
scaler = joblib.load('money_order/ml/models/money_order_feature_scaler.pkl')
```

**Key Difference:** Paystub stores 1 model, Money Order stores 2 models (ensemble).

---

## 6. DATABASE STORAGE

### PAYSTUB DATABASE STORAGE

**When Data is Stored:**

**File:** `Backend/api_server.py` (lines 333-402)

**Flow:**
1. User uploads paystub → API endpoint `/api/paystub/analyze`
2. Extract and analyze (OCR → Normalize → ML → AI)
3. **Store to database** (line 369):
   ```python
   document_id = store_paystub_analysis(user_id, filename, details)
   ```
4. **Update employee fraud status** (lines 372-383):
   ```python
   storage.update_employee_fraud_status(employee_name, ai_recommendation, document_id)
   ```

**Storage Implementation:**

**File:** `Backend/database/document_storage.py` (lines 577-655)

**Table: `paystubs`**

**Columns (from code analysis):**
1. `paystub_id` (UUID, PRIMARY KEY)
2. `document_id` (UUID, FOREIGN KEY to `documents`)
3. `user_id` (TEXT)
4. `file_name` (TEXT)
5. `company_name` (TEXT)
6. `employee_name` (TEXT)
7. `employee_id` (TEXT)
8. `pay_date` (DATE)
9. `pay_period_start` (DATE)
10. `pay_period_end` (DATE)
11. `gross_pay` (NUMERIC)
12. `net_pay` (NUMERIC)
13. `ytd_gross` (NUMERIC)
14. `ytd_net` (NUMERIC)
15. `federal_tax` (NUMERIC)
16. `state_tax` (NUMERIC)
17. `social_security` (NUMERIC)
18. `medicare` (NUMERIC)
19. `deductions` (JSONB) - Array of deduction objects
20. `fraud_risk_score` (NUMERIC) - ML risk score (0-1)
21. `risk_level` (TEXT) - 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
22. `model_confidence` (NUMERIC) - ML model confidence (0-1)
23. `ai_recommendation` (TEXT) - 'APPROVE', 'REJECT', 'ESCALATE'
24. `anomaly_count` (INTEGER)
25. `top_anomalies` (JSONB) - Array of top 5 anomalies
26. `created_at` (TIMESTAMP)
27. `updated_at` (TIMESTAMP)

**Total: ~27 columns**

**Table: `paystub_customers`**

**File:** `Backend/database/create_paystub_customers_table.sql`

**Columns:**
1. `customer_id` (UUID, PRIMARY KEY)
2. `name` (TEXT) - Employee name
3. `has_fraud_history` (BOOLEAN)
4. `fraud_count` (INTEGER)
5. `escalate_count` (INTEGER)
6. `last_recommendation` (TEXT)
7. `last_analysis_date` (TIMESTAMP)
8. `total_paystubs` (INTEGER)
9. `created_at` (TIMESTAMP)
10. `updated_at` (TIMESTAMP)

**Total: 10 columns**

**When Updated:**
- `paystubs` table: Inserted **immediately after analysis** (line 643)
- `paystub_customers` table: Updated **after analysis** (line 380 in api_server.py)

---

### MONEY ORDER DATABASE STORAGE

**When Data is Stored:**

**File:** `Backend/api_server.py` (lines 404-538)

**Flow:**
1. User uploads money order → API endpoint `/api/money-order/analyze`
2. Extract and analyze (OCR → Normalize → ML → AI)
3. **Store to database** (line 516):
   ```python
   document_id = store_money_order_analysis(user_id, filename, result)
   ```

**Storage Implementation:**

**File:** `Backend/database/document_storage.py` (lines 367-442)

**Table: `money_orders`**

**Columns (from code analysis):**
1. `money_order_id` (UUID, PRIMARY KEY)
2. `document_id` (UUID, FOREIGN KEY)
3. `user_id` (TEXT)
4. `file_name` (TEXT)
5. `issuer` (TEXT)
6. `serial_number` (TEXT)
7. `amount` (NUMERIC)
8. `amount_in_words` (TEXT)
9. `payee` (TEXT)
10. `purchaser` (TEXT)
11. `date` (DATE)
12. `location` (TEXT)
13. `signature` (TEXT)
14. `fraud_risk_score` (NUMERIC)
15. `risk_level` (TEXT)
16. `model_confidence` (NUMERIC)
17. `ai_recommendation` (TEXT)
18. `anomaly_count` (INTEGER)
19. `top_anomalies` (JSONB)
20. `purchaser_customer_id` (UUID, FOREIGN KEY to `money_order_customers`)
21. `created_at` (TIMESTAMP)
22. `updated_at` (TIMESTAMP)

**Total: ~22 columns**

**Table: `money_order_customers`**

**File:** `Backend/database/create_money_order_customers.sql`

**Columns:**
1. `customer_id` (UUID, PRIMARY KEY)
2. `name` (TEXT) - Purchaser name
3. `payee_name` (TEXT)
4. `address` (TEXT)
5. `city` (TEXT)
6. `state` (TEXT)
7. `zip_code` (TEXT)
8. `phone` (TEXT)
9. `email` (TEXT)
10. `has_fraud_history` (BOOLEAN)
11. `fraud_count` (INTEGER)
12. `escalate_count` (INTEGER)
13. `last_recommendation` (TEXT)
14. `last_analysis_date` (TIMESTAMP)
15. `created_at` (TIMESTAMP)
16. `updated_at` (TIMESTAMP)

**Total: 16 columns**

**When Updated:**
- `money_orders` table: Inserted **immediately after analysis** (line 427)
- `money_order_customers` table: Updated **during analysis** (in `extractor.py`, line 502-562)

---

## 7. CUSTOMER LOGIC

### PAYSTUB CUSTOMER LOGIC

**File:** `Backend/paystub/database/paystub_customer_storage.py`

**Key Method: `get_employee_history()`** (lines 29-104)

**Logic:**

1. **Query ALL records for employee name:**
   ```python
   response = self.supabase.table('paystub_customers').select('*').eq('name', employee_name).execute()
   ```

2. **Find MAX escalate_count across ALL records:**
   ```python
   sorted_records = sorted(all_records, key=lambda x: x.get('escalate_count', 0), reverse=True)
   max_escalate_count = sorted_records[0].get('escalate_count', 0)
   ```

3. **Find MAX fraud_count across ALL records:**
   ```python
   max_fraud_count = max((r.get('fraud_count', 0) for r in all_records)
   ```

4. **Use latest record for other fields:**
   ```python
   latest_record = sorted(all_records, key=lambda x: x.get('created_at', ''), reverse=True)[0]
   employee_id = latest_record.get('customer_id')
   ```

5. **Return combined history:**
   ```python
   return {
       'employee_id': employee_id,
       'name': employee_name,
       'has_fraud_history': max_fraud_count > 0,
       'fraud_count': max_fraud_count,
       'escalate_count': max_escalate_count,  # MAX across all records
       'last_recommendation': latest_record.get('last_recommendation'),
       'total_paystubs': sum((r.get('total_paystubs', 0) for r in all_records)
   }
   ```

**Repeat Offender Logic:**

**File:** `Backend/paystub/ai/paystub_fraud_analysis_agent.py` (lines 133-152)

```python
def _apply_policy_rules(employee_name, employee_info):
    escalate_count = employee_info.get('escalate_count', 0)
    
    # If escalate_count > 0, auto-reject (repeat offender)
    if escalate_count > 0:
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Repeat offender: escalate_count={escalate_count}',
            ...
        }
    
    # Otherwise, proceed to LLM analysis
    return None
```

**Update Logic:**

**File:** `paystub_customer_storage.py` (lines 165-234)

```python
def update_employee_fraud_status(employee_name, recommendation, paystub_id):
    employee_history = self.get_employee_history(employee_name)
    
    update_data = {
        'last_recommendation': recommendation,
        'last_analysis_date': now,
        'total_paystubs': employee_history.get('total_paystubs', 0) + 1
    }
    
    if recommendation == 'REJECT':
        update_data['fraud_count'] = employee_history.get('fraud_count', 0) + 1
        update_data['has_fraud_history'] = True
    elif recommendation == 'ESCALATE':
        update_data['escalate_count'] = employee_history.get('escalate_count', 0) + 1
    
    # Update or create employee record
    if employee_id:
        self.supabase.table('paystub_customers').update(update_data).eq('customer_id', employee_id).execute()
    else:
        # Create new employee
        new_employee = {
            'customer_id': str(uuid4()),
            'name': employee_name,
            'has_fraud_history': recommendation == 'REJECT',
            'fraud_count': 1 if recommendation == 'REJECT' else 0,
            'escalate_count': 1 if recommendation == 'ESCALATE' else 0,
            ...
        }
        self.supabase.table('paystub_customers').insert([new_employee]).execute()
```

**Key Rules:**
- **New Employee** (no records): Proceed to LLM, but if LLM returns REJECT, override to ESCALATE
- **Repeat Offender** (escalate_count > 0): **AUTO-REJECT** (no LLM call)
- **Clean History** (fraud_count=0, escalate_count=0): Proceed to LLM
- **Fraud History** (fraud_count > 0): Proceed to LLM with stricter thresholds

---

### MONEY ORDER CUSTOMER LOGIC

**File:** `Backend/money_order/extractor.py` (lines 502-562)

**Key Method: Customer Lookup** (lines 502-562)

**Logic:**

1. **Query by purchaser name (payer-based tracking):**
   ```python
   purchaser_name = data.get('sender_name') or data.get('purchaser')
   query = supabase.table('money_order_customers').select('*').eq('name', purchaser_name)
   response = query.execute()
   ```

2. **Find MAX escalate_count:**
   ```python
   customer_record_with_max_escalate = response.data[0]  # Sorted by escalate_count DESC
   max_escalate_count = customer_record_with_max_escalate.get('escalate_count', 0)
   ```

3. **Pass to AI agent:**
   ```python
   customer_fraud_history = {
       'has_fraud_history': customer_record_with_max_escalate.get('has_fraud_history', False),
       'fraud_count': customer_record_with_max_escalate.get('fraud_count', 0),
       'escalate_count': max_escalate_count,  # MAX escalate_count
       ...
   }
   ai_analysis = self.ai_agent.analyze_fraud(ml_analysis, data, customer_id, is_repeat_customer, customer_fraud_history)
   ```

**Repeat Offender Logic:**

**File:** `Backend/money_order/ai/fraud_analysis_agent.py` (lines 146-180)

```python
def _llm_analysis(ml_analysis, extracted_data, customer_id, is_repeat_customer, customer_fraud_history):
    escalate_count = customer_fraud_history.get('escalate_count', 0)
    
    # CRITICAL CHECK: MANDATORY REJECT if escalate_count > 0
    if escalate_count > 0:
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Payer has escalate_count={escalate_count}. Forcing REJECT.',
            ...
        }
    
    # Otherwise, proceed to LLM analysis
    ...
```

**Key Rules:**
- **New Customer** (no records): Proceed to LLM
- **Repeat Offender** (escalate_count > 0): **AUTO-REJECT** (no LLM call)
- **Clean History** (fraud_count=0, escalate_count=0): Proceed to LLM
- **Fraud History** (fraud_count > 0): Proceed to LLM with stricter thresholds

**Key Difference:** Money Order tracks by **purchaser/payer name**, Paystub tracks by **employee name**. Logic is identical otherwise.

---

## 8. AI ANALYSIS

### PAYSTUB AI ANALYSIS

**File:** `Backend/paystub/ai/paystub_fraud_analysis_agent.py`

**Step-by-Step Process:**

#### Step 1: Policy Rules Check
**File:** `paystub_fraud_analysis_agent.py` (lines 133-152)

```python
def _apply_policy_rules(employee_name, employee_info):
    escalate_count = employee_info.get('escalate_count', 0)
    
    # Repeat offender: auto-reject
    if escalate_count > 0:
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Repeat offender: escalate_count={escalate_count}',
            ...
        }
    
    # New employee with missing name: escalate
    if not employee_name:
        return {
            'recommendation': 'ESCALATE',
            'confidence_score': 1.0,
            ...
        }
    
    # Otherwise, proceed to LLM
    return None
```

#### Step 2: Format Prompt
**File:** `paystub_fraud_analysis_agent.py` (lines 191-195)

Uses template from `paystub_prompts.py`:
```python
analysis_prompt = format_analysis_template(
    paystub_data=extracted_data,
    ml_analysis=ml_analysis,
    employee_info=employee_info
)
```

**Prompt includes:**
- Paystub fields (company, employee, amounts, dates, taxes)
- ML analysis (fraud_risk_score, risk_level, anomalies)
- Employee history (fraud_count, escalate_count, last_recommendation)
- Decision matrix (rules for APPROVE/REJECT/ESCALATE)

#### Step 3: Call LLM
**File:** `paystub_fraud_analysis_agent.py` (lines 200-207)

```python
system_msg = SystemMessage(content=SYSTEM_PROMPT)
user_msg = HumanMessage(content=full_prompt)
messages = [system_msg, user_msg]

response = self.llm.invoke(messages)  # LangChain ChatOpenAI
ai_response = response.content
```

#### Step 4: Parse Response
**File:** `paystub_fraud_analysis_agent.py` (lines 214-218)

```python
try:
    result = json.loads(ai_response)  # Try JSON first
except json.JSONDecodeError:
    result = self._parse_text_response(ai_response)  # Fallback to text parsing
```

#### Step 5: Validate and Format
**File:** `paystub_fraud_analysis_agent.py` (lines 221, 346-375)

```python
final_result = self._validate_and_format_result(result, ml_analysis, employee_info)
```

**Ensures:**
- `recommendation` is one of: 'APPROVE', 'REJECT', 'ESCALATE'
- `confidence_score` is 0.0-1.0
- `reasoning` is a list
- `key_indicators` is a list

#### Step 6: Post-LLM Validation
**File:** `paystub_fraud_analysis_agent.py` (lines 223-235)

```python
# New employees should NEVER get REJECT on first upload
is_new_employee = not employee_info.get('employee_id')
if is_new_employee and final_result.get('recommendation') == 'REJECT':
    logger.warning("LLM returned REJECT for new employee. Overriding to ESCALATE.")
    final_result = self._create_first_time_escalation(employee_name, is_new_employee=True)
```

#### Step 7: Return Result
**File:** `paystub_fraud_analysis_agent.py` (lines 237-238)

```python
return {
    'recommendation': 'ESCALATE',
    'confidence_score': 0.85,
    'summary': 'AI analysis summary',
    'reasoning': ['Reason 1', 'Reason 2', ...],
    'key_indicators': ['Indicator 1', 'Indicator 2', ...],
    'actionable_recommendations': ['Action 1', 'Action 2', ...]
}
```

---

### MONEY ORDER AI ANALYSIS

**File:** `Backend/money_order/ai/fraud_analysis_agent.py`

**Step-by-Step Process:**

#### Step 1: Policy Rules Check
**File:** `fraud_analysis_agent.py` (lines 146-180)

```python
def _llm_analysis(ml_analysis, extracted_data, customer_id, is_repeat_customer, customer_fraud_history):
    escalate_count = customer_fraud_history.get('escalate_count', 0)
    
    # CRITICAL CHECK: MANDATORY REJECT if escalate_count > 0
    if escalate_count > 0:
        return {
            'recommendation': 'REJECT',
            'confidence_score': 1.0,
            'summary': f'Payer has escalate_count={escalate_count}. Forcing REJECT.',
            ...
        }
```

#### Step 2: Format Prompt
**File:** `fraud_analysis_agent.py` (lines 260-283)

Uses template from `prompts.py`:
```python
prompt_vars = {
    "fraud_risk_score": ml_analysis.get('fraud_score', 0),
    "risk_level": ml_analysis.get('risk_level', 'UNKNOWN'),
    "issuer": extracted_data.get('issuer'),
    "serial_number": extracted_data.get('serial_number'),
    "amount": extracted_data.get('amount'),
    "customer_type": customer_type,  # "NEW CUSTOMER" or "REPEAT CUSTOMER"
    "escalation_status": escalation_status,
    ...
}
```

#### Step 3: Call LLM
**File:** `fraud_analysis_agent.py` (lines 285-296)

```python
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(ANALYSIS_TEMPLATE)
])

messages = prompt.format_messages(**prompt_vars)
response = self.llm.invoke(messages)
```

#### Step 4: Parse Response
**File:** `fraud_analysis_agent.py` (lines 298-373)

Parses structured text response:
```python
def _parse_llm_response(content: str):
    # Looks for lines like:
    # "RECOMMENDATION: REJECT"
    # "CONFIDENCE: 85%"
    # "REASONING:"
    # "- Reason 1"
    # "- Reason 2"
    ...
```

#### Step 5: Return Result
**File:** `fraud_analysis_agent.py` (lines 302-314)

```python
return {
    'recommendation': 'REJECT',
    'confidence_score': 0.85,
    'summary': 'AI analysis summary',
    'reasoning': ['Reason 1', 'Reason 2', ...],
    'key_indicators': ['Indicator 1', 'Indicator 2', ...],
    'verification_notes': '...',
    'actionable_recommendations': ['Action 1', 'Action 2', ...],
    'training_insights': '...',
    'historical_comparison': '...',
    'analysis_type': 'ai_enhanced',
    'model_used': 'gpt-4'
}
```

**Key Difference:** Money Order AI returns more fields (verification_notes, training_insights, etc.), Paystub AI returns simpler structure.

---

## 9. HOW AI USES ML SCORES

### PAYSTUB: AI USES ML SCORES

**File:** `Backend/paystub/ai/paystub_prompts.py`

**ML Score in Prompt:**

**Template:** `format_analysis_template()` (lines 154-245)

```python
# Extract ML analysis
fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)  # 0.0-1.0
risk_level = ml_analysis.get('risk_level', 'UNKNOWN')
model_confidence = ml_analysis.get('model_confidence', 0.0)
risk_factors = ml_analysis.get('feature_importance', [])

# Format for prompt
prompt_text = f"""
## ML FRAUD ANALYSIS
Fraud Risk Score: {fraud_risk_score:.2%} ({risk_level})
Model Confidence: {model_confidence:.2%}
Key Risk Factors:
{risk_factors_str}

## DECISION MATRIX
| Employee Type | Risk Score | Decision |
|---|---|---|
| New Employee | < 30% | APPROVE |
| New Employee | 30–95% | ESCALATE |
| Clean History | < 30% | APPROVE |
| Clean History | 30–85% | ESCALATE |
| Clean History | > 85% | REJECT |
| Fraud History | < 30% | APPROVE |
| Fraud History | ≥ 30% | REJECT |
"""
```

**AI Decision Logic:**

The AI uses ML score to determine which row in the decision matrix to use:

1. **Check employee type** (from `employee_info`):
   - New Employee: `employee_id is None`
   - Clean History: `fraud_count = 0 AND escalate_count = 0`
   - Fraud History: `fraud_count > 0`

2. **Check ML risk score**:
   - `< 30%`: Low risk
   - `30-85%`: Medium risk
   - `> 85%`: High risk

3. **Apply decision matrix:**
   - New Employee + 10% risk → **APPROVE**
   - New Employee + 50% risk → **ESCALATE**
   - Clean History + 90% risk → **REJECT**
   - Fraud History + 40% risk → **REJECT**

**Example:**
```python
# ML Analysis
ml_analysis = {
    'fraud_risk_score': 0.10,  # 10%
    'risk_level': 'LOW',
    'anomalies': ['Missing 1 critical field']
}

# Employee Info
employee_info = {
    'employee_id': None,  # New employee
    'fraud_count': 0,
    'escalate_count': 0
}

# AI sees:
# - Employee Type: NEW EMPLOYEE
# - ML Risk Score: 10% (< 30%)
# - Decision Matrix: New Employee + < 30% → APPROVE

# AI returns:
{
    'recommendation': 'APPROVE',
    'reasoning': [
        'ML risk score is low (10%)',
        'Employee is new with no fraud history',
        'Per decision matrix: New Employee + < 30% risk = APPROVE'
    ]
}
```

---

### MONEY ORDER: AI USES ML SCORES

**File:** `Backend/money_order/ai/prompts.py`

**ML Score in Prompt:**

**Template:** `ANALYSIS_TEMPLATE`

```python
prompt_vars = {
    "fraud_risk_score": ml_analysis.get('fraud_score', 0),  # 0-1
    "risk_level": ml_analysis.get('risk_level', 'UNKNOWN'),
    "rf_score": ml_analysis.get('model_scores', {}).get('random_forest', 0),
    "xgb_score": ml_analysis.get('model_scores', {}).get('xgboost', 0),
    "fraud_indicators": str(ml_analysis.get('anomalies', [])),
    "customer_type": customer_type,  # "NEW CUSTOMER" or "REPEAT CUSTOMER"
    ...
}
```

**AI Decision Logic:**

The AI uses ML score + customer history to make decision:

1. **Check customer type:**
   - New Customer: `is_repeat_customer = False`
   - Repeat Customer (Clean): `fraud_count = 0`
   - Repeat Customer (Fraud): `fraud_count > 0`

2. **Check ML risk score:**
   - `< 30%`: Low risk
   - `30-60%`: Medium risk
   - `> 60%`: High risk

3. **Apply decision rules:**
   - New Customer + Low risk → **APPROVE**
   - New Customer + Medium/High risk → **ESCALATE**
   - Repeat Customer (Clean) + Low risk → **APPROVE**
   - Repeat Customer (Clean) + Medium/High risk → **ESCALATE**
   - Repeat Customer (Fraud) + Any risk → **REJECT**

**Example:**
```python
# ML Analysis
ml_analysis = {
    'fraud_risk_score': 0.25,  # 25%
    'risk_level': 'MEDIUM',
    'model_scores': {
        'random_forest': 0.23,
        'xgboost': 0.27,
        'ensemble': 0.25
    },
    'anomalies': ['Amount mismatch detected']
}

# Customer Info
customer_fraud_history = {
    'has_fraud_history': False,
    'fraud_count': 0,
    'escalate_count': 0
}
is_repeat_customer = True  # Customer exists in DB

# AI sees:
# - Customer Type: REPEAT CUSTOMER WITH CLEAN HISTORY
# - ML Risk Score: 25% (MEDIUM)
# - Decision: Repeat Customer (Clean) + Medium risk → ESCALATE

# AI returns:
{
    'recommendation': 'ESCALATE',
    'reasoning': [
        'ML models indicate medium risk (25%)',
        'Random Forest: 23%, XGBoost: 27%',
        'Amount mismatch detected (critical indicator)',
        'Customer has clean history but risk factors present',
        'Recommendation: Escalate for manual review'
    ]
}
```

**Key Difference:** 
- **Paystub:** AI uses explicit decision matrix table
- **Money Order:** AI uses implicit rules based on customer type + risk score

**Both use ML score as primary input for decision-making, but apply different thresholds based on customer/employee history.**

---

## SUMMARY COMPARISON

| Aspect | Paystub | Money Order |
|--------|---------|-------------|
| **OCR Method** | Mindee API (structured) | Google Vision API (regex parsing) |
| **Normalization Layers** | 3 layers | 4 layers (issuer-specific) |
| **ML Features** | 10 features | 30 features |
| **ML Models** | 1 model (Random Forest) | 2 models (RF + XGBoost ensemble) |
| **Model Storage** | `paystub/ml/models/` | `money_order/ml/models/` |
| **Database Tables** | `paystubs` (27 cols), `paystub_customers` (10 cols) | `money_orders` (22 cols), `money_order_customers` (16 cols) |
| **Customer Tracking** | By employee name | By purchaser/payer name |
| **AI Prompt** | Decision matrix table | Implicit rules |
| **Repeat Offender** | `escalate_count > 0` → AUTO-REJECT | `escalate_count > 0` → AUTO-REJECT |

---

**END OF DOCUMENT**

