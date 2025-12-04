# From 14 Normalized Fields → 35 ML Features → Fraud Score

## Overview

This document explains the complete flow from **14 normalized fields** → **35 ML features** → **Fraud Score**.

---

## Part 1: 14 Normalized Fields (Input to Feature Extractor)

After normalization, we have these **14 fields**:

1. `bank_name` - Bank name (e.g., "Chase")
2. `account_holder_name` - Account holder name
3. `account_holder_names` - List of account holders
4. `account_number` - Account number
5. `account_type` - Account type (Checking/Savings)
6. `currency` - Currency code (USD, EUR, etc.)
7. `statement_period_start_date` - Period start (YYYY-MM-DD)
8. `statement_period_end_date` - Period end (YYYY-MM-DD)
9. `statement_date` - Statement date (YYYY-MM-DD)
10. `beginning_balance` - `{"value": 8542.75, "currency": "USD"}`
11. `ending_balance` - `{"value": 12384.50, "currency": "USD"}`
12. `total_credits` - `{"value": 15230.00, "currency": "USD"}`
13. `total_debits` - `{"value": 11388.25, "currency": "USD"}`
14. `transactions` - Array of transaction objects

**Plus:**
- `bank_address` - Bank address (not used in ML)
- `account_holder_address` - Account holder address (not used in ML)
- `raw_text` - Raw OCR text (used for text quality feature)

---

## Part 2: 14 Fields → 35 ML Features (Feature Extraction)

The `BankStatementFeatureExtractor` transforms the **14 normalized fields** into **35 ML features**:

### Feature Extraction Process

**Location:** `Backend/bank_statement/ml/bank_statement_feature_extractor.py`

**Method:** `extract_features(extracted_data: Dict, raw_text: str) -> List[float]`

### Detailed Mapping: 14 Fields → 35 Features

#### **From `bank_name` field:**
- **Feature 1:** `bank_validity` (0.0 or 1.0)
  - `1.0` if bank is in supported list (Chase, Bank of America, etc.)
  - `0.0` if unsupported bank

#### **From `account_number` field:**
- **Feature 2:** `account_number_present` (0.0 or 1.0)
  - `1.0` if account number exists
  - `0.0` if missing
- **Feature 31:** `account_number_format_valid` (0.0, 0.5, or 1.0)
  - `1.0` if format is valid (8-17 digits)
  - `0.5` if present but format unclear
  - `0.0` if missing

#### **From `account_holder_name` field:**
- **Feature 3:** `account_holder_present` (0.0 or 1.0)
  - `1.0` if account holder name exists
  - `0.0` if missing
- **Feature 32:** `name_format_valid` (0.0, 0.5, or 1.0)
  - `1.0` if format is valid (contains letters, ≥3 chars)
  - `0.5` if present but format unclear
  - `0.0` if missing

#### **From `account_type` field:**
- **Feature 4:** `account_type_present` (0.0 or 1.0)
  - `1.0` if account type exists
  - `0.0` if missing

#### **From `beginning_balance` field:**
- **Feature 5:** `beginning_balance` (0.0 to 1,000,000)
  - Extracts numeric value: `{"value": 8542.75, "currency": "USD"}` → `8542.75`
  - Capped at 1,000,000

#### **From `ending_balance` field:**
- **Feature 6:** `ending_balance` (0.0 to 1,000,000)
  - Extracts numeric value
  - Capped at 1,000,000
- **Feature 18:** `negative_ending_balance` (0.0 or 1.0)
  - `1.0` if ending balance is negative
  - `0.0` if positive

#### **From `total_credits` field:**
- **Feature 7:** `total_credits` (0.0 to 1,000,000)
  - Extracts numeric value
  - Capped at 1,000,000

#### **From `total_debits` field:**
- **Feature 8:** `total_debits` (0.0 to 1,000,000)
  - Extracts numeric value
  - Capped at 1,000,000

#### **From `statement_period_start_date` field:**
- **Feature 9:** `period_start_present` (0.0 or 1.0)
  - `1.0` if period start date exists
  - `0.0` if missing
- **Feature 24:** `date_format_valid` (0.0 or 1.0)
  - `1.0` if date format is valid
  - `0.0` if invalid

#### **From `statement_period_end_date` field:**
- **Feature 10:** `period_end_present` (0.0 or 1.0)
  - `1.0` if period end date exists
  - `0.0` if missing

#### **From `statement_date` field:**
- **Feature 11:** `statement_date_present` (0.0 or 1.0)
  - `1.0` if statement date exists
  - `0.0` if missing

#### **From `statement_period_start_date` + `statement_period_end_date`:**
- **Feature 12:** `future_period` (0.0 or 1.0)
  - `1.0` if statement period is in the future
  - `0.0` if past/present
- **Feature 13:** `period_age_days` (0.0 to 365)
  - Age of statement in days (how old is it)
  - Capped at 365 days
- **Feature 25:** `period_length_days` (0.0 to 365)
  - Length of statement period in days
  - Capped at 365 days

#### **From `transactions` array:**
- **Feature 14:** `transaction_count` (0.0 to 1000)
  - Number of transactions
  - Capped at 1000
- **Feature 15:** `avg_transaction_amount` (0.0 to 50,000)
  - Average transaction amount
  - Calculated from all transactions
- **Feature 16:** `max_transaction_amount` (0.0 to 100,000)
  - Largest single transaction
  - Capped at 100,000
- **Feature 21:** `suspicious_transaction_pattern` (0.0 or 1.0)
  - `1.0` if many small transactions detected (>50% are <$100)
  - `0.0` if normal pattern
- **Feature 22:** `large_transaction_count` (0.0 to 50)
  - Number of transactions > $10,000
  - Capped at 50
- **Feature 23:** `round_number_transactions` (0.0 to 100)
  - Number of transactions with round numbers ($100, $1000, etc.)
  - Capped at 100
- **Feature 28:** `transaction_date_consistency` (0.0 to 1.0)
  - Percentage of transactions within statement period
  - `1.0` if all transactions are in period
- **Feature 29:** `duplicate_transactions` (0.0 or 1.0)
  - `1.0` if duplicate transactions detected
  - `0.0` if no duplicates
- **Feature 30:** `unusual_timing` (0.0 to 1.0)
  - Percentage of transactions on weekends/holidays
  - `0.0` = no weekend transactions
  - `1.0` = all weekend transactions

#### **From calculated values (beginning_balance, ending_balance, total_credits, total_debits):**
- **Feature 17:** `balance_change` (0.0 to 1,000,000)
  - Calculated: `ending_balance - beginning_balance`
  - Capped at 1,000,000
- **Feature 19:** `balance_consistency` (0.0 to 1.0)
  - Calculated: Check if `ending = beginning + credits - debits`
  - `1.0` if perfect match (difference ≤ $1)
  - `0.5` if close match (difference ≤ $10)
  - `0.0` if inconsistent (difference > $10)
- **Feature 34:** `credit_debit_ratio` (0.0 to 100.0)
  - Calculated: `total_credits / total_debits`
  - Capped at 100.0
- **Feature 33:** `balance_volatility` (0.0 to 10.0)
  - Calculated: Largest balance swing relative to beginning balance
  - Capped at 10.0

#### **From `currency` field:**
- **Feature 20:** `currency_present` (0.0 or 1.0)
  - `1.0` if currency field exists
  - `0.0` if missing

#### **From all fields combined:**
- **Feature 26:** `critical_missing_count` (0.0 to 7)
  - Count of missing critical fields:
    - bank_name, account_number, account_holder_name
    - statement_period_start_date, statement_period_end_date
    - beginning_balance, ending_balance
  - Maximum 7 critical fields
- **Feature 27:** `field_quality` (0.0 to 1.0)
  - Overall data quality score
  - Percentage of fields populated
  - `1.0` = all fields present
  - `0.0` = no fields present

#### **From `raw_text` (OCR text):**
- **Feature 35:** `text_quality` (0.0 to 1.0)
  - Quality of OCR text extraction
  - Based on text length:
    - `< 100 chars` → `0.3` (poor)
    - `< 500 chars` → `0.6` (medium)
    - `≥ 500 chars` → `0.9` (good)

---

## Part 3: Training Process (35 Features → Model)

### Training Data Generation

**Location:** `Backend/training/train_risk_model.py`

**Method:** `generate_dummy_bank_statement_data(n_samples=2000)`

### How Training Works:

1. **Generate 2000 synthetic bank statements**
   - Each statement has **35 features**
   - Features are generated based on risk category (low, medium, high, critical)

2. **Calculate Ground Truth Risk Score (0-100)**
   ```python
   risk_score = 0.0
   
   # Missing critical fields: up to 40 points
   if critical_missing_count >= 4:
       risk_score += 40
   
   # Unsupported bank: +30 points
   if bank_valid == 0.0:
       risk_score += 30
   
   # Future period: +25 points
   if future_period == 1.0:
       risk_score += 25
   
   # Balance inconsistency: +30 points
   if balance_consistency < 0.5:
       risk_score += 30
   
   # Negative balance: +20 points
   if negative_ending_balance == 1.0:
       risk_score += 20
   
   # ... more rules ...
   
   risk_score = max(0, min(100, risk_score))  # Cap at 0-100
   ```

3. **Create Training Dataset**
   - **Input (X):** 35 features per sample
   - **Target (y):** Risk score (0-100) per sample
   - **Shape:** (2000 samples, 35 features) → (2000 risk scores)

4. **Train Two Models:**
   - **Random Forest Regressor:** Predicts risk score (0-100)
   - **XGBoost Regressor:** Predicts risk score (0-100)

5. **Feature Scaling:**
   - Features are scaled using `StandardScaler` (mean=0, std=1)
   - Scaler is saved for use during prediction

6. **Save Models:**
   - `bank_statement_random_forest.pkl`
   - `bank_statement_xgboost.pkl`
   - `bank_statement_feature_scaler.pkl`

---

## Part 4: Prediction Process (35 Features → Fraud Score)

### Prediction Flow

**Location:** `Backend/bank_statement/ml/bank_statement_fraud_detector.py`

**Method:** `_predict_with_models(features, feature_names, bank_statement_data)`

### Step-by-Step:

#### **Step 1: Extract 35 Features**
```python
features = feature_extractor.extract_features(normalized_data, raw_text)
# Returns: [1.0, 1.0, 1.0, 1.0, 8542.75, 12384.50, ...] (35 values)
```

#### **Step 2: Scale Features**
```python
X = np.array([features])  # Shape: (1, 35)
X_scaled = scaler.transform(X)  # Normalize to mean=0, std=1
```

#### **Step 3: Get Predictions from Both Models**
```python
# Random Forest prediction
rf_pred = rf_model.predict(X_scaled)[0]  # Returns: 0-100 (risk score)
rf_score = rf_pred / 100.0  # Normalize to 0-1: 0.849

# XGBoost prediction
xgb_pred = xgb_model.predict(X_scaled)[0]  # Returns: 0-100 (risk score)
xgb_score = xgb_pred / 100.0  # Normalize to 0-1: 0.841
```

#### **Step 4: Ensemble Prediction**
```python
ensemble_score = (0.4 × rf_score) + (0.6 × xgb_score)
ensemble_score = (0.4 × 0.849) + (0.6 × 0.841)
ensemble_score = 0.3396 + 0.5046
ensemble_score = 0.8442
```

#### **Step 5: Final Fraud Score**
```python
final_score = ensemble_score  # No validation rules applied
fraud_risk_score = round(final_score, 4)  # 0.8442 = 84.42%
```

#### **Step 6: Determine Risk Level**
```python
if fraud_risk_score < 0.30:  # < 30%
    risk_level = "LOW"
elif fraud_risk_score < 0.61:  # 30-60%
    risk_level = "MEDIUM"
elif fraud_risk_score < 0.86:  # 61-85%
    risk_level = "HIGH"
else:  # ≥ 86%
    risk_level = "CRITICAL"
```

---

## Complete Example Flow

### Input: 14 Normalized Fields

```json
{
  "bank_name": "Chase",
  "account_holder_name": "John Michael Anderson",
  "account_number": "****-2345",
  "account_type": "Checking Account",
  "currency": "USD",
  "statement_period_start_date": "2024-11-01",
  "statement_period_end_date": "2024-11-30",
  "statement_date": "2024-11-30",
  "beginning_balance": {"value": 8542.75, "currency": "USD"},
  "ending_balance": {"value": 12384.50, "currency": "USD"},
  "total_credits": {"value": 15230.00, "currency": "USD"},
  "total_debits": {"value": 11388.25, "currency": "USD"},
  "transactions": [
    {"date": "2024-11-01", "description": "SALARY DEPOSIT", "amount": {"value": 4850.0, "currency": "USD"}},
    {"date": "2024-11-02", "description": "RENT PAYMENT", "amount": {"value": -2200.0, "currency": "USD"}}
  ]
}
```

### Step 1: Feature Extraction (14 Fields → 35 Features)

```python
features = [
    1.0,   # Feature 1: bank_validity (Chase is supported)
    1.0,   # Feature 2: account_number_present
    1.0,   # Feature 3: account_holder_present
    1.0,   # Feature 4: account_type_present
    8542.75,   # Feature 5: beginning_balance
    12384.50,  # Feature 6: ending_balance
    15230.00,  # Feature 7: total_credits
    11388.25,  # Feature 8: total_debits
    1.0,   # Feature 9: period_start_present
    1.0,   # Feature 10: period_end_present
    1.0,   # Feature 11: statement_date_present
    0.0,   # Feature 12: future_period (not future)
    33.0,  # Feature 13: period_age_days (33 days old)
    2.0,   # Feature 14: transaction_count
    1325.0, # Feature 15: avg_transaction_amount
    4850.0, # Feature 16: max_transaction_amount
    3841.75, # Feature 17: balance_change
    0.0,   # Feature 18: negative_ending_balance
    0.0,   # Feature 19: balance_consistency (INCONSISTENT - this is the issue!)
    1.0,   # Feature 20: currency_present
    0.0,   # Feature 21: suspicious_transaction_pattern
    0.0,   # Feature 22: large_transaction_count
    0.0,   # Feature 23: round_number_transactions
    1.0,   # Feature 24: date_format_valid
    30.0,  # Feature 25: period_length_days
    0.0,   # Feature 26: critical_missing_count
    0.88,  # Feature 27: field_quality
    1.0,   # Feature 28: transaction_date_consistency
    0.0,   # Feature 29: duplicate_transactions
    0.0,   # Feature 30: unusual_timing
    0.5,   # Feature 31: account_number_format_valid (masked)
    1.0,   # Feature 32: name_format_valid
    0.24,  # Feature 33: balance_volatility
    1.34,  # Feature 34: credit_debit_ratio
    0.92   # Feature 35: text_quality
]
```

### Step 2: Scale Features

```python
X_scaled = scaler.transform([features])
# Features normalized to mean=0, std=1
```

### Step 3: Model Predictions

```python
# Random Forest
rf_pred = 84.9  # Risk score 0-100
rf_score = 84.9 / 100.0 = 0.849

# XGBoost
xgb_pred = 84.1  # Risk score 0-100
xgb_score = 84.1 / 100.0 = 0.841
```

### Step 4: Ensemble Score

```python
ensemble_score = (0.4 × 0.849) + (0.6 × 0.841)
                = 0.3396 + 0.5046
                = 0.8442
```

### Step 5: Final Fraud Score

```python
fraud_risk_score = 0.8442 = 84.42%
risk_level = "HIGH"  # (61-85% range)
```

---

## Summary

### Flow Diagram:

```
14 Normalized Fields
    ↓
Feature Extractor
    ↓
35 ML Features
    ↓
Feature Scaling (StandardScaler)
    ↓
Random Forest Model → Risk Score (0-100) → Normalize to 0-1
XGBoost Model → Risk Score (0-100) → Normalize to 0-1
    ↓
Ensemble: (40% × RF) + (60% × XGB)
    ↓
Fraud Risk Score (0-1 = 0-100%)
    ↓
Risk Level: LOW / MEDIUM / HIGH / CRITICAL
```

### Key Points:

1. **14 normalized fields** are transformed into **35 ML features**
2. **35 features** are extracted using calculations, validations, and pattern detection
3. **Models are trained** on 2000 synthetic samples with 35 features each
4. **Prediction** uses both Random Forest and XGBoost, then combines them
5. **Final score** is the ensemble average (40% RF + 60% XGB)

### Why 35 Features from 14 Fields?

- **One field can generate multiple features:**
  - `transactions` → 9 features (count, avg, max, patterns, duplicates, etc.)
  - `beginning_balance` + `ending_balance` + `total_credits` + `total_debits` → 8 features (values, consistency, change, volatility, ratio)
  - Dates → 6 features (presence, format, age, length, future check)
  - Account info → 5 features (presence, format validation)

- **Derived features:**
  - Calculated from combinations (balance_consistency, credit_debit_ratio, etc.)
  - Pattern detection (suspicious transactions, duplicates, etc.)
  - Quality metrics (field_quality, text_quality)

This is why we get **35 features** from **14 fields**!


