# Mindee to Normalized Field Mapping - Complete Guide

## Overview

This document shows exactly how the **17 Mindee fields** are transformed into **normalized fields** during the normalization process.

---

## The 17 Mindee Fields (Input)

These are the fields extracted directly from Mindee OCR:

1. `bank_name`
2. `bank_address`
3. `account_type`
4. `account_holder_names`
5. `account_number`
6. `currency`
7. `statement_period_start_date`
8. `statement_period_end_date`
9. `statement_date`
10. `beginning_balance`
11. `ending_balance`
12. `total_credits`
13. `total_debits`
14. `list_of_transactions`
15. `account_holder_address`
16. `branch_code` (optional)
17. `daily_balances` (optional)

---

## Complete Field Mapping Table

| # | Mindee Field (Input) | Normalized Field (Output) | Transformation Applied | Example Input → Output |
|---|----------------------|---------------------------|----------------------|------------------------|
| 1 | `bank_name` | `bank_name` | String cleaning | `"CHASE"` → `"Chase"` |
| 2 | `bank_address` | `bank_address` | Address normalization | See Address Transformation below |
| 3 | `account_type` | `account_type` | String cleaning | `"Checking Account"` → `"Checking Account"` |
| 4 | `account_holder_names` | `account_holder_names` | List normalization | `["John Michael Anderson"]` → `["John Michael Anderson"]` |
| 4 | `account_holder_names` | `account_holder_name` | Extract first name (post-processing) | `["John Michael Anderson"]` → `"John Michael Anderson"` |
| 5 | `account_number` | `account_number` | String cleaning | `"****-2345"` → `"****-2345"` |
| 6 | `currency` | `currency` | String cleaning | `"USD"` → `"USD"` |
| 7 | `statement_period_start_date` | `statement_period_start_date` | Date normalization | `"2024-11-01"` → `"2024-11-01"` |
| 8 | `statement_period_end_date` | `statement_period_end_date` | Date normalization | `"2024-11-30"` → `"2024-11-30"` |
| 9 | `statement_date` | `statement_date` | Date normalization | `"2024-11-30"` → `"2024-11-30"` |
| 10 | `beginning_balance` | `beginning_balance` | Amount normalization | `8542.75` → `{"value": 8542.75, "currency": "USD"}` |
| 11 | `ending_balance` | `ending_balance` | Amount normalization | `12384.50` → `{"value": 12384.50, "currency": "USD"}` |
| 12 | `total_credits` | `total_credits` | Amount normalization | `15230.00` → `{"value": 15230.00, "currency": "USD"}` |
| 13 | `total_debits` | `total_debits` | Amount normalization | `11388.25` → `{"value": 11388.25, "currency": "USD"}` |
| 14 | `list_of_transactions` | `transactions` | Transaction normalization | See Transaction Transformation below |
| 15 | `account_holder_address` | `account_holder_address` | Address normalization | See Address Transformation below |
| 16 | `branch_code` | (Not in normalized schema) | Discarded | N/A |
| 17 | `daily_balances` | (Not in normalized schema) | Discarded | N/A |

---

## Detailed Transformation Logic

### 1. Bank Name (`bank_name`)

**Input:** `"CHASE"` (from Mindee)  
**Output:** `"Chase"` (normalized)

**Transformation:**
```python
# String cleaning (removes extra whitespace)
_clean_string("CHASE") → "Chase"
```

**Code:** `_clean_string()` method

---

### 2. Bank Address (`bank_address`)

**Input (Mindee):**
```json
{
  "address": "270 Park Avenue, New York, NY 10017",
  "street": "270 Park Avenue",
  "city": "New York",
  "state": "NY",
  "postal_code": "10017",
  "country": null
}
```

**Output (Normalized):**
```json
{
  "address": "270 Park Avenue, New York, NY 10017",
  "street": "270 Park Avenue",
  "city": "New York",
  "state": "NY",
  "postal_code": "10017",
  "country": "US"  // Default added in post-processing
}
```

**Transformation:**
1. Extract nested address components
2. Set default `country = "US"` if missing (Chase post-processing)

**Code:** `_normalize_address()` method

---

### 3. Account Type (`account_type`)

**Input:** `"Checking Account"`  
**Output:** `"Checking Account"`

**Transformation:**
```python
_clean_string("Checking Account") → "Checking Account"
```

**Code:** `_clean_string()` method

---

### 4. Account Holder Names (`account_holder_names`)

**Input (Mindee):**
```json
["John Michael Anderson"]
```

**Output (Normalized):**
```json
["John Michael Anderson"]
```

**Transformation:**
1. If already a list → Clean each name
2. If string → Split by comma/newline → Convert to list
3. Clean each name (remove extra whitespace)

**Code:** `_normalize_account_holder_names()` method

**Additional Post-Processing (Chase):**
```python
# Extract primary account holder name
if account_holder_names and not account_holder_name:
    account_holder_name = account_holder_names[0]
```

**Result:** Also creates `account_holder_name` = `"John Michael Anderson"`

---

### 5. Account Number (`account_number`)

**Input:** `"****-2345"`  
**Output:** `"****-2345"`

**Transformation:**
```python
_clean_string("****-2345") → "****-2345"
```

**Code:** `_clean_string()` method

---

### 6. Currency (`currency`)

**Input:** `"USD"` or `null`  
**Output:** `"USD"` (default if missing)

**Transformation:**
```python
_clean_string("USD") → "USD"
# If missing, defaults to "USD" in post-processing
```

**Code:** `_clean_string()` method + Chase post-processing

---

### 7-9. Dates (`statement_period_start_date`, `statement_period_end_date`, `statement_date`)

**Input (Various Formats):**
- `"2024-11-01"` (ISO format)
- `"11/01/2024"` (US format)
- `"November 1, 2024"` (Long format)

**Output (Normalized):**
- `"2024-11-01"` (Always ISO format: YYYY-MM-DD)

**Transformation:**
```python
def _normalize_date(date_value):
    # Try multiple date formats
    date_formats = [
        '%Y-%m-%d',        # ISO format
        '%m/%d/%Y',         # US format
        '%B %d, %Y',        # Long format
        ...
    ]
    # Parse and convert to YYYY-MM-DD
    return "2024-11-01"
```

**Code:** `_normalize_date()` method

---

### 10-13. Amounts (`beginning_balance`, `ending_balance`, `total_credits`, `total_debits`)

**Input (Various Formats):**
- `8542.75` (float)
- `"$8,542.75"` (string with currency)
- `{"value": 8542.75}` (dict)

**Output (Normalized):**
```json
{
  "value": 8542.75,
  "currency": "USD"
}
```

**Transformation:**
```python
def _normalize_amount(amount_value):
    # If float → Convert to dict
    if isinstance(amount_value, (int, float)):
        return {"value": float(amount_value), "currency": "USD"}
    
    # If string → Remove $ and commas → Parse to float
    if isinstance(amount_value, str):
        clean_amount = re.sub(r'[^\d.-]', '', amount_value)  # Remove $, commas
        return {"value": float(clean_amount), "currency": "USD"}
    
    # If dict → Extract value and currency
    if isinstance(amount_value, dict):
        return {
            "value": float(amount_value['value']),
            "currency": amount_value.get('currency', 'USD')
        }
```

**Code:** `_normalize_amount()` method

**Additional Post-Processing (Chase):**
```python
# Set currency from currency field if missing
if beginning_balance and not beginning_balance.get('currency'):
    beginning_balance['currency'] = currency or 'USD'
```

---

### 14. Transactions (`list_of_transactions` → `transactions`)

**Input (Mindee):**
```json
[
  {
    "date": "2024-11-01",
    "description": "SALARY DEPOSIT - TECH CORP INC",
    "amount": 4850.0
  },
  {
    "date": "2024-11-02",
    "description": "RENT PAYMENT",
    "amount": -2200.0
  }
]
```

**Output (Normalized):**
```json
[
  {
    "date": "2024-11-01",
    "description": "SALARY DEPOSIT - TECH CORP INC",
    "amount": {
      "value": 4850.0,
      "currency": "USD"
    }
  },
  {
    "date": "2024-11-02",
    "description": "RENT PAYMENT",
    "amount": {
      "value": -2200.0,
      "currency": "USD"
    }
  }
]
```

**Transformation:**
```python
def _normalize_transactions(transactions_value):
    normalized_transactions = []
    for transaction in transactions_value:
        normalized_txn = {
            'date': _normalize_date(transaction.get('date')),           # Normalize date
            'description': _clean_string(transaction.get('description')), # Clean string
            'amount': _normalize_amount(transaction.get('amount'))        # Normalize amount
        }
        normalized_transactions.append(normalized_txn)
    return normalized_transactions
```

**Code:** `_normalize_transactions()` method

**Key Changes:**
1. Field name: `list_of_transactions` → `transactions`
2. Date: Normalized to YYYY-MM-DD format
3. Description: Cleaned (remove extra whitespace)
4. Amount: Converted from float → `{"value": float, "currency": "USD"}`

---

### 15. Account Holder Address (`account_holder_address`)

**Input (Mindee):**
```json
{
  "street": "425 Park Avenue",
  "city": "New York",
  "state": "NY",
  "postal_code": "10022",
  "country": "United States"
}
```

**Output (Normalized):**
```json
{
  "address": "425 Park Avenue, New York, NY 10022",
  "street": "425 Park Avenue",
  "city": "New York",
  "state": "NY",
  "postal_code": "10022",
  "country": "US"  // Normalized from "United States"
}
```

**Transformation:**
1. Extract nested address components
2. Set default `country = "US"` if missing (Chase post-processing)
3. Construct full `address` string if not present

**Code:** `_normalize_address()` method

---

### 16-17. Optional Fields (`branch_code`, `daily_balances`)

**Status:** These fields are **NOT** included in the normalized schema.

**Reason:** Not required for fraud detection analysis.

---

## Complete Example: Chase Statement

### Input: Mindee Extracted Data (17 Fields)

```json
{
  "bank_name": "CHASE",
  "bank_address": {
    "address": "270 Park Avenue, New York, NY 10017",
    "street": "270 Park Avenue",
    "city": "New York",
    "state": "NY",
    "postal_code": "10017"
  },
  "account_type": "Checking Account",
  "account_holder_names": ["John Michael Anderson"],
  "account_number": "****-2345",
  "currency": "USD",
  "statement_period_start_date": "2024-11-01",
  "statement_period_end_date": "2024-11-30",
  "statement_date": "2024-11-30",
  "beginning_balance": 8542.75,
  "ending_balance": 12384.50,
  "total_credits": 15230.00,
  "total_debits": 11388.25,
  "list_of_transactions": [
    {
      "date": "2024-11-01",
      "description": "SALARY DEPOSIT - TECH CORP INC",
      "amount": 4850.0
    },
    {
      "date": "2024-11-02",
      "description": "RENT PAYMENT",
      "amount": -2200.0
    }
  ],
  "account_holder_address": {
    "street": "425 Park Avenue",
    "city": "New York",
    "state": "NY",
    "postal_code": "10022",
    "country": "United States"
  },
  "branch_code": "CH-NY-001",
  "daily_balances": []
}
```

### Output: Normalized Data (14 Fields)

```json
{
  "bank_name": "Chase",
  "bank_address": {
    "address": "270 Park Avenue, New York, NY 10017",
    "street": "270 Park Avenue",
    "city": "New York",
    "state": "NY",
    "postal_code": "10017",
    "country": "US"
  },
  "account_type": "Checking Account",
  "account_holder_name": "John Michael Anderson",
  "account_holder_names": ["John Michael Anderson"],
  "account_number": "****-2345",
  "currency": "USD",
  "statement_period_start_date": "2024-11-01",
  "statement_period_end_date": "2024-11-30",
  "statement_date": "2024-11-30",
  "beginning_balance": {
    "value": 8542.75,
    "currency": "USD"
  },
  "ending_balance": {
    "value": 12384.50,
    "currency": "USD"
  },
  "total_credits": {
    "value": 15230.00,
    "currency": "USD"
  },
  "total_debits": {
    "value": 11388.25,
    "currency": "USD"
  },
  "transactions": [
    {
      "date": "2024-11-01",
      "description": "SALARY DEPOSIT - TECH CORP INC",
      "amount": {
        "value": 4850.0,
        "currency": "USD"
      }
    },
    {
      "date": "2024-11-02",
      "description": "RENT PAYMENT",
      "amount": {
        "value": -2200.0,
        "currency": "USD"
      }
    }
  ],
  "account_holder_address": {
    "address": "425 Park Avenue, New York, NY 10022",
    "street": "425 Park Avenue",
    "city": "New York",
    "state": "NY",
    "postal_code": "10022",
    "country": "US"
  }
}
```

**Note:** `branch_code` and `daily_balances` are **discarded** (not in normalized schema).

---

## Summary of Transformations

### Field Name Changes:
- `list_of_transactions` → `transactions`

### Data Type Transformations:

1. **Amounts** (4 fields):
   - `float` → `{"value": float, "currency": "USD"}`
   - Fields: `beginning_balance`, `ending_balance`, `total_credits`, `total_debits`

2. **Dates** (3 fields):
   - Various formats → `"YYYY-MM-DD"` (ISO format)
   - Fields: `statement_period_start_date`, `statement_period_end_date`, `statement_date`

3. **Transactions** (1 field):
   - Array of transactions with normalized dates, descriptions, and amounts
   - Field: `list_of_transactions` → `transactions`

4. **Addresses** (2 fields):
   - Extract nested components, set default country
   - Fields: `bank_address`, `account_holder_address`

5. **Strings** (6 fields):
   - Clean whitespace, standardize format
   - Fields: `bank_name`, `account_type`, `account_number`, `currency`, `account_holder_names`

### Post-Processing (Chase-Specific):

1. **Account Holder Name:**
   - Extract primary name from list: `account_holder_names[0]` → `account_holder_name`

2. **Currency Defaults:**
   - Set `currency = "USD"` for all amounts if missing

3. **Country Defaults:**
   - Set `country = "US"` for addresses if missing

### Discarded Fields:
- `branch_code` (not in normalized schema)
- `daily_balances` (not in normalized schema)

---

## Normalization Flow

```
17 Mindee Fields
    ↓
Field Mapping (Chase Normalizer)
    ↓
Apply Transformations:
  - Amounts: float → {"value": float, "currency": "USD"}
  - Dates: Various → "YYYY-MM-DD"
  - Transactions: Normalize each transaction
  - Addresses: Extract components, set defaults
  - Strings: Clean whitespace
    ↓
Post-Processing (Chase-Specific):
  - Extract account_holder_name from list
  - Set currency defaults
  - Set country defaults
    ↓
14 Normalized Fields (NormalizedBankStatement)
```

---

## Code References

- **Base Normalizer:** `Backend/bank_statement/normalization/bank_statement_base_normalizer.py`
- **Chase Normalizer:** `Backend/bank_statement/normalization/chase.py`
- **Schema:** `Backend/bank_statement/normalization/bank_statement_schema.py`
- **Extraction:** `Backend/bank_statement/bank_statement_extractor.py` (lines 200-267)

