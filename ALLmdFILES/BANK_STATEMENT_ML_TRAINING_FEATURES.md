# Bank Statement ML Model - Training Features (35 Columns)

## Overview

The bank statement ML models (Random Forest + XGBoost) were trained on **35 features** extracted from bank statement documents. These features are divided into two categories:

- **Basic Features (1-20)**: Core bank statement data (bank, account, balances, dates, transactions)
- **Advanced Features (21-35)**: Validation, patterns, and fraud indicators

---

## Complete Feature List (35 Features)

### Basic Features (1-20)

| # | Feature Name | Type | Description | Example Values |
|---|--------------|------|-------------|----------------|
| 1 | `bank_validity` | Binary (0.0/1.0) | Whether bank is in supported list (Bank of America, Chase, etc.) | 1.0 = supported, 0.0 = unsupported |
| 2 | `account_number_present` | Binary (0.0/1.0) | Whether account number field exists | 1.0 = present, 0.0 = missing |
| 3 | `account_holder_present` | Binary (0.0/1.0) | Whether account holder name exists | 1.0 = present, 0.0 = missing |
| 4 | `account_type_present` | Binary (0.0/1.0) | Whether account type (checking/savings) exists | 1.0 = present, 0.0 = missing |
| 5 | `beginning_balance` | Numeric (0-1,000,000) | Opening balance at start of statement period | 5000.0, 100000.0 (capped at 1M) |
| 6 | `ending_balance` | Numeric (0-1,000,000) | Closing balance at end of statement period | 5200.0, 95000.0 (capped at 1M) |
| 7 | `total_credits` | Numeric (0-1,000,000) | Total amount of credits (deposits) | 10000.0, 50000.0 (capped at 1M) |
| 8 | `total_debits` | Numeric (0-1,000,000) | Total amount of debits (withdrawals) | 8000.0, 45000.0 (capped at 1M) |
| 9 | `period_start_present` | Binary (0.0/1.0) | Whether statement period start date exists | 1.0 = present, 0.0 = missing |
| 10 | `period_end_present` | Binary (0.0/1.0) | Whether statement period end date exists | 1.0 = present, 0.0 = missing |
| 11 | `statement_date_present` | Binary (0.0/1.0) | Whether statement date exists | 1.0 = present, 0.0 = missing |
| 12 | `future_period` | Binary (0.0/1.0) | Whether statement period is in the future (fraud indicator) | 1.0 = future date, 0.0 = past/present |
| 13 | `period_age_days` | Numeric (0-365) | Age of statement in days (how old is it) | 30.0 (30 days old), 365.0 (1 year old, capped) |
| 14 | `transaction_count` | Numeric (0-1000) | Number of transactions in statement | 50.0, 200.0 (capped at 1000) |
| 15 | `avg_transaction_amount` | Numeric (0-50,000) | Average transaction amount | 500.0, 2000.0 (capped at 50K) |
| 16 | `max_transaction_amount` | Numeric (0-100,000) | Largest single transaction amount | 5000.0, 10000.0 (capped at 100K) |
| 17 | `balance_change` | Numeric (0-1,000,000) | Change in balance (ending - beginning) | 200.0, -500.0 (capped at 1M) |
| 18 | `negative_ending_balance` | Binary (0.0/1.0) | Whether ending balance is negative (fraud indicator) | 1.0 = negative, 0.0 = positive |
| 19 | `balance_consistency` | Numeric (0.0-1.0) | Whether balance calculations match (ending = beginning + credits - debits) | 1.0 = consistent, 0.0 = inconsistent |
| 20 | `currency_present` | Binary (0.0/1.0) | Whether currency field exists | 1.0 = present, 0.0 = missing |

### Advanced Features (21-35)

| # | Feature Name | Type | Description | Example Values |
|---|--------------|------|-------------|----------------|
| 21 | `suspicious_transaction_pattern` | Binary (0.0/1.0) | Whether many small transactions detected (fraud indicator) | 1.0 = suspicious pattern, 0.0 = normal |
| 22 | `large_transaction_count` | Numeric (0-50) | Number of transactions > $10,000 | 5.0, 10.0 (capped at 50) |
| 23 | `round_number_transactions` | Numeric (0-100) | Number of transactions with round numbers ($100, $1000, etc.) | 10.0, 25.0 (capped at 100) |
| 24 | `date_format_valid` | Binary (0.0/1.0) | Whether date format is valid/parseable | 1.0 = valid, 0.0 = invalid |
| 25 | `period_length_days` | Numeric (0-365) | Length of statement period in days | 30.0 (monthly), 90.0 (quarterly, capped at 365) |
| 26 | `critical_missing_count` | Numeric (0-7) | Number of critical fields missing (bank, account, holder, dates, balances) | 0.0, 3.0, 6.0 (max 7 critical fields) |
| 27 | `field_quality` | Numeric (0.0-1.0) | Overall data quality score (how many fields populated) | 0.8 = 80% fields present, 0.3 = 30% fields present |
| 28 | `transaction_date_consistency` | Numeric (0.0-1.0) | Whether all transactions fall within statement period | 1.0 = all consistent, 0.5 = some outside period |
| 29 | `duplicate_transactions` | Binary (0.0/1.0) | Whether duplicate transactions detected (fraud indicator) | 1.0 = duplicates found, 0.0 = no duplicates |
| 30 | `unusual_timing` | Numeric (0.0-1.0) | Percentage of transactions on weekends/holidays | 0.3 = 30% on weekends, 0.0 = no weekend transactions |
| 31 | `account_number_format_valid` | Binary (0.0/1.0) | Whether account number format is valid (8-17 digits) | 1.0 = valid format, 0.5 = present but unclear format |
| 32 | `name_format_valid` | Binary (0.0/1.0) | Whether account holder name format is valid | 1.0 = valid, 0.5 = present but unclear |
| 33 | `balance_volatility` | Numeric (0.0-10.0) | Balance volatility (large swings relative to beginning balance) | 2.0 = 2x beginning balance swing, 0.0 = no volatility |
| 34 | `credit_debit_ratio` | Numeric (0.0-100.0) | Ratio of total credits to total debits | 1.5 = 50% more credits, 0.5 = 50% more debits (capped at 100) |
| 35 | `text_quality` | Numeric (0.0-1.0) | Quality of OCR text extraction | 0.9 = excellent, 0.6 = good, 0.3 = poor |

---

## Feature Categories

### 1. **Presence/Validity Features** (Binary: 0.0 or 1.0)
- `bank_validity`, `account_number_present`, `account_holder_present`, `account_type_present`
- `period_start_present`, `period_end_present`, `statement_date_present`, `currency_present`
- `date_format_valid`, `account_number_format_valid`, `name_format_valid`

**Purpose**: Check if critical fields exist and are valid

### 2. **Balance Features** (Numeric)
- `beginning_balance`, `ending_balance`, `total_credits`, `total_debits`
- `balance_change`, `balance_consistency`, `balance_volatility`

**Purpose**: Analyze financial amounts and balance calculations

### 3. **Date/Period Features** (Numeric)
- `future_period`, `period_age_days`, `period_length_days`

**Purpose**: Validate statement dates and periods

### 4. **Transaction Features** (Numeric)
- `transaction_count`, `avg_transaction_amount`, `max_transaction_amount`
- `large_transaction_count`, `round_number_transactions`

**Purpose**: Analyze transaction patterns and amounts

### 5. **Fraud Indicator Features** (Binary/Numeric)
- `suspicious_transaction_pattern`, `duplicate_transactions`, `unusual_timing`
- `negative_ending_balance`, `future_period`

**Purpose**: Detect specific fraud patterns

### 6. **Quality Features** (Numeric: 0.0-1.0)
- `field_quality`, `text_quality`, `transaction_date_consistency`
- `balance_consistency`

**Purpose**: Measure data quality and consistency

### 7. **Derived Features** (Numeric)
- `critical_missing_count`, `credit_debit_ratio`, `balance_volatility`

**Purpose**: Calculate complex relationships and risk indicators

---

## Training Data Format

### Input (X): 35 Features
```python
X = [
    [1.0, 0.0, 0.0, 1.0, 5000.0, 5200.0, 10000.0, 8000.0, ...],  # Sample 1
    [0.0, 1.0, 1.0, 1.0, 10000.0, 9500.0, 5000.0, 5500.0, ...],  # Sample 2
    ...
]
# Shape: (2000 samples, 35 features)
```

### Target (y): Risk Score
```python
y = [45.2, 78.5, 12.3, 95.0, ...]
# Shape: (2000 samples,)
# Range: 0-100 (risk score percentage)
```

---

## Feature Extraction Process

1. **Extract raw data** from bank statement (via Mindee OCR)
2. **Calculate 35 features** using `BankStatementFeatureExtractor`
3. **Scale features** using StandardScaler (mean=0, std=1)
4. **Feed to models** for prediction

---

## Model Training

### Random Forest Model
- **Input**: 35 scaled features
- **Output**: Risk score (0-100)
- **Training**: 2000 samples, 80% train, 20% test

### XGBoost Model
- **Input**: 35 scaled features
- **Output**: Risk score (0-100)
- **Training**: 2000 samples, 80% train, 20% test

### Ensemble Prediction
```python
final_score = (0.4 × RF_prediction) + (0.6 × XGB_prediction)
```

---

## Feature Importance

The models learn which features are most important for fraud detection:

**Likely High Importance:**
- `balance_consistency` (Feature 19)
- `critical_missing_count` (Feature 26)
- `future_period` (Feature 12)
- `bank_validity` (Feature 1)
- `account_holder_present` (Feature 3)

**Likely Medium Importance:**
- `suspicious_transaction_pattern` (Feature 21)
- `duplicate_transactions` (Feature 29)
- `field_quality` (Feature 27)
- `text_quality` (Feature 35)

**Likely Lower Importance:**
- `currency_present` (Feature 20)
- `account_type_present` (Feature 4)
- `period_length_days` (Feature 25)

---

## Notes

1. **All 35 features are required** - Models expect exactly 35 features
2. **Features are scaled** before prediction (StandardScaler)
3. **Missing values** are handled as 0.0 (for binary features) or 0.0 (for numeric features)
4. **Feature order matters** - Must match the order in `get_feature_names()`
5. **Caps applied** - Large values are capped (e.g., balances at 1M, transactions at 1000)

---

## Verification

You can verify the features used by checking:
1. **Training script**: `Backend/training/train_risk_model.py` (lines 726-739)
2. **Feature extractor**: `Backend/bank_statement/ml/bank_statement_feature_extractor.py` (lines 512-525)
3. **Model metadata**: `Backend/bank_statement/ml/models/bank_statement_model_metadata.json`

All three sources should match exactly.



