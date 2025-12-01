# Check Analysis Normalization Layer - Complete Explanation

## Overview

The normalization layer standardizes check data from different banks into a unified schema, making it easier to process, analyze, and store in the database.

---

## Step-by-Step Flow

### **Step 1: Mindee OCR Extraction**

**What Happens:**
- Check image is sent to Mindee API
- Mindee extracts raw fields using its custom check model
- Fields are returned with Mindee-specific field names

**Fields Extracted by Mindee:**
```python
# Example Mindee response fields:
{
    'number_amount': 1500.00,           # Numeric amount
    'word_amount': 'One thousand five hundred...',  # Written amount
    'pay_to': 'John Doe',               # Payee name
    'sender_name': 'Jane Smith',        # Payer name
    'sender_address': '123 Main St...', # Payer address
    'routing_number': '021000021',       # Routing number
    'account_number': '123456789',      # Account number
    'check_number': '1001',             # Check number
    'date': '2024-12-01',               # Check date
    'signature': True,                   # Signature detected (boolean)
    'bank_name': 'Bank of America',     # Bank name
    'memo': 'Invoice payment'           # Memo field
}
```

**Location:** `Backend/check/check_extractor.py` → `_extract_with_mindee()`

---

### **Step 2: Field Name Mapping**

**What Happens:**
- Mindee field names are mapped to standard names
- This handles variations in field naming

**Field Mapping Examples:**
```python
# Mindee field → Standard field
'number_amount' → 'amount_numeric'
'word_amount' → 'amount_written'
'pay_to' → 'payee_name'
'sender_name' → 'payer_name'
'sender_address' → 'payer_address'
'signature' → 'signature_detected'
```

**Location:** `Backend/check/check_extractor.py` → Lines 240-249

---

### **Step 3: Bank Detection & Normalizer Selection**

**What Happens:**
- System detects bank name from extracted data
- `CheckNormalizerFactory` selects appropriate normalizer

**Supported Banks:**
- **Bank of America** → `BankOfAmericaNormalizer`
- **Chase** → `ChaseNormalizer`

**How It Works:**
```python
bank_name = extracted_data.get('bank_name')  # e.g., "Bank of America"
normalizer = CheckNormalizerFactory.get_normalizer(bank_name)
# Returns: BankOfAmericaNormalizer() instance
```

**Location:** `Backend/check/normalization/check_normalizer_factory.py`

---

### **Step 4: Bank-Specific Field Mapping**

**What Happens:**
- Each bank normalizer has its own field mapping dictionary
- Maps OCR field names → Standardized schema fields
- Handles bank-specific field name variations

**Example: Bank of America Normalizer**
```python
{
    # Bank identification
    'routing_number': 'routing_number',
    'routing': 'routing_number',              # Alternate name
    'account_number': 'account_number',
    'account': 'account_number',               # Alternate name
    
    # Check identification
    'check_number': 'check_number',
    'number': 'check_number',                 # Alternate name
    'date': 'check_date',
    
    # Payer (person writing check)
    'payer_name': 'payer_name',
    'payer': 'payer_name',                    # Alternate name
    'drawer': 'payer_name',                   # Banking term
    'payer_address': 'payer_address',
    
    # Payee (person receiving check)
    'payee_name': 'payee_name',
    'pay_to': 'payee_name',                   # "Pay to the order of"
    'recipient': 'payee_name',                # Alternate name
    
    # Monetary
    'amount': 'amount_numeric',
    'number_amount': 'amount_numeric',        # Mindee field
    'amount_words': 'amount_written',
    'word_amount': 'amount_written',          # Mindee field
    
    # Authorization
    'signature': 'signature_detected',
    'memo': 'memo'
}
```

**Location:** 
- `Backend/check/normalization/bank_of_america.py` → `get_field_mappings()`
- `Backend/check/normalization/chase.py` → `get_field_mappings()`

---

### **Step 5: Data Normalization**

**What Happens:**
- `CheckBaseNormalizer.normalize()` processes each field
- Applies field-specific transformations:
  - **Amounts**: Converts to `{'value': float, 'currency': 'USD'}` format
  - **Dates**: Normalizes to ISO format (YYYY-MM-DD)
  - **Booleans**: Converts signature to boolean
  - **Strings**: Cleans whitespace and formatting

**Normalization Examples:**

**Amount Normalization:**
```python
# Input: 1500.00 (float) or "$1,500.00" (string)
# Output: {'value': 1500.00, 'currency': 'USD'}
```

**Date Normalization:**
```python
# Input: "12/01/2024" or "December 1, 2024"
# Output: "2024-12-01" (ISO format)
```

**Signature Normalization:**
```python
# Input: True, "yes", "present", 1
# Output: True (boolean)
```

**Location:** `Backend/check/normalization/check_base_normalizer.py` → `normalize()`

---

### **Step 6: Standardized Schema Output**

**What Happens:**
- Normalized data is converted to `NormalizedCheck` dataclass
- This ensures consistent structure regardless of bank

**NormalizedCheck Schema:**
```python
@dataclass
class NormalizedCheck:
    # Bank Information
    bank_name: str                    # "Bank of America"
    routing_number: str                # "021000021"
    account_number: str                # "123456789"
    
    # Check Identification
    check_number: str                  # "1001"
    check_date: str                    # "2024-12-01"
    
    # Payer Information (person writing check)
    payer_name: str                    # "Jane Smith"
    payer_address: str                 # "123 Main St"
    payer_city: str                    # "Anytown"
    payer_state: str                   # "CA"
    payer_zip: str                     # "91234"
    
    # Payee Information (person receiving check)
    payee_name: str                    # "John Doe"
    payee_address: str                 # "456 Oak Ave"
    payee_city: str                    # "Somewhere"
    payee_state: str                   # "NY"
    payee_zip: str                     # "10001"
    
    # Monetary Information
    amount_numeric: Dict               # {'value': 1500.00, 'currency': 'USD'}
    amount_written: str                # "One thousand five hundred..."
    
    # Authorization
    signature_detected: bool            # True
    memo: str                          # "Invoice payment"
    
    # Additional
    check_type: str                    # "Personal" or "Business"
    country: str                        # "US"
    currency: str                       # "USD"
```

**Location:** `Backend/check/normalization/check_schema.py`

---

### **Step 7: Database Storage**

**What Happens:**
- Normalized data is stored in Supabase `checks` table
- Both extracted and normalized data are stored

**Database Table: `checks`**

**Columns Stored:**
```sql
-- Check Identification
check_id (UUID, PRIMARY KEY)
document_id (UUID, FK to documents)
check_number (TEXT)
check_date (DATE)

-- Bank Information
bank_name (TEXT)
institution_id (UUID, FK to financial_institutes)
routing_number (TEXT)
account_number (TEXT)

-- Payer Information
payer_name (TEXT)
payer_address (TEXT)
payer_customer_id (UUID, FK to check_customers)

-- Payee Information
payee_name (TEXT)

-- Monetary
amount (NUMERIC)  -- Extracted from amount_numeric.value

-- Analysis Results
fraud_risk_score (NUMERIC)      -- From ML analysis
risk_level (TEXT)               -- LOW, MEDIUM, HIGH, CRITICAL
model_confidence (NUMERIC)      -- ML model confidence
ai_recommendation (TEXT)        -- APPROVE, REJECT, ESCALATE
signature_detected (BOOLEAN)
anomaly_count (INTEGER)
top_anomalies (JSONB)           -- Top 5 anomalies as JSON array

-- Metadata
timestamp (TIMESTAMP)
```

**Storage Process:**
1. Extract normalized data from `analysis_data['normalized_data']`
2. Extract ML analysis from `analysis_data['ml_analysis']`
3. Extract AI analysis from `analysis_data['ai_analysis']`
4. Map to database columns
5. Insert into `checks` table

**Location:** `Backend/database/document_storage.py` → `store_check()`

---

## Complete Example Flow

### **Input: Bank of America Check Image**

**Step 1: Mindee Extraction**
```python
{
    'number_amount': 1500.00,
    'word_amount': 'One thousand five hundred and 00/100',
    'pay_to': 'John Doe',
    'sender_name': 'Jane Smith',
    'sender_address': '123 Main St, Anytown, CA 91234',
    'routing_number': '021000021',
    'account_number': '123456789',
    'check_number': '1001',
    'date': '12/01/2024',
    'signature': True,
    'bank_name': 'Bank of America',
    'memo': 'Invoice payment'
}
```

**Step 2: Field Mapping**
```python
{
    'amount_numeric': 1500.00,           # from 'number_amount'
    'amount_written': 'One thousand...',  # from 'word_amount'
    'payee_name': 'John Doe',            # from 'pay_to'
    'payer_name': 'Jane Smith',          # from 'sender_name'
    'payer_address': '123 Main St...',   # from 'sender_address'
    'routing_number': '021000021',
    'account_number': '123456789',
    'check_number': '1001',
    'check_date': '12/01/2024',          # from 'date'
    'signature_detected': True,           # from 'signature'
    'bank_name': 'Bank of America',
    'memo': 'Invoice payment'
}
```

**Step 3: Bank-Specific Normalization (Bank of America)**
```python
NormalizedCheck(
    bank_name='Bank of America',
    routing_number='021000021',
    account_number='123456789',
    check_number='1001',
    check_date='2024-12-01',              # Normalized to ISO format
    payer_name='Jane Smith',
    payer_address='123 Main St',
    payer_city='Anytown',                 # Parsed from address
    payer_state='CA',                     # Parsed from address
    payer_zip='91234',                    # Parsed from address
    payee_name='John Doe',
    amount_numeric={'value': 1500.00, 'currency': 'USD'},  # Normalized format
    amount_written='One thousand five hundred and 00/100',
    signature_detected=True,
    memo='Invoice payment',
    country='US',                         # Default
    currency='USD'                        # Default
)
```

**Step 4: Database Storage**
```sql
INSERT INTO checks (
    check_id,
    check_number,
    amount,                    -- 1500.00 (from amount_numeric.value)
    check_date,                -- '2024-12-01'
    payer_name,                -- 'Jane Smith'
    payer_address,             -- '123 Main St'
    payee_name,                -- 'John Doe'
    bank_name,                 -- 'Bank of America'
    routing_number,            -- '021000021'
    account_number,            -- '123456789'
    signature_detected,        -- true
    fraud_risk_score,          -- 0.35 (from ML)
    risk_level,                -- 'MEDIUM' (from ML)
    model_confidence,          -- 0.85 (from ML)
    ai_recommendation,         -- 'ESCALATE' (from AI)
    anomaly_count,             -- 2
    top_anomalies              -- JSON array
) VALUES (...);
```

---

## Key Benefits of Normalization

1. **Consistency**: All checks use the same field names regardless of bank
2. **Bank-Specific Handling**: Each bank's variations are handled by its normalizer
3. **Data Quality**: Fields are cleaned, validated, and formatted consistently
4. **Database Integrity**: Standardized schema ensures reliable storage
5. **ML/AI Compatibility**: Models receive consistent input format

---

## Files Involved

1. **Extraction**: `Backend/check/check_extractor.py` → `_extract_with_mindee()`
2. **Normalization**: 
   - `Backend/check/normalization/check_base_normalizer.py` (base class)
   - `Backend/check/normalization/bank_of_america.py` (BoA normalizer)
   - `Backend/check/normalization/chase.py` (Chase normalizer)
   - `Backend/check/normalization/check_normalizer_factory.py` (factory)
3. **Schema**: `Backend/check/normalization/check_schema.py` (NormalizedCheck)
4. **Storage**: `Backend/database/document_storage.py` → `store_check()`

---

## Summary

**Extraction** → **Field Mapping** → **Bank Detection** → **Bank-Specific Normalization** → **Standardized Schema** → **Database Storage**

The normalization layer ensures that regardless of which bank the check is from, the data is consistently structured and ready for ML/AI analysis and database storage.

