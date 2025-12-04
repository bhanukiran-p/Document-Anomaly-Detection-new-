# Bank Statement Extraction & Normalization - Complete Guide

## Overview

This document explains how bank statement extraction and normalization works in the DAD system.

---

## Part 1: OCR Service - Mindee Only

### **Answer: We use Mindee OCR, NOT Google OCR**

**Key Points:**
- ✅ **Primary OCR**: Mindee API (ClientV2)
- ❌ **No Google Vision**: Bank statements do NOT use Google Cloud Vision API
- ❌ **No Fallback**: If Mindee fails, the extraction fails (no fallback to Google)

### Implementation Details:

**Code Location:** `Backend/bank_statement/bank_statement_extractor.py`

```python
# Import Mindee - use ClientV2 API (requires mindee>=4.31.0)
from mindee import ClientV2, InferenceParameters, PathInput

# Initialize Mindee client
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_BANK_STATEMENT = os.getenv("MINDEE_MODEL_ID_BANK_STATEMENT", "2b6cc7a4-6b0b-4178-a8f8-00c626965d87").strip()

mindee_client = ClientV2(api_key=MINDEE_API_KEY)
```

**Extraction Process:**
```python
def _extract_with_mindee(self, file_path: str) -> Tuple[Dict, str]:
    """Extract bank statement data using Mindee API only (no fallback)"""
    # Create inference parameters with the model ID
    params = InferenceParameters(model_id=MINDEE_MODEL_ID_BANK_STATEMENT, raw_text=True)
    input_source = PathInput(file_path)
    
    # Parse document using ClientV2 with model ID
    response = mindee_client.enqueue_and_get_inference(input_source, params)
    
    # Extract fields from the response
    result = response.inference.result
    fields = result.fields or {}
    raw_text = getattr(result, "raw_text", "") or ""
    
    return extracted_data, raw_text
```

**Why Mindee Only?**
- Mindee has a specialized bank statement model (`2b6cc7a4-6b0b-4178-a8f8-00c626965d87`)
- Provides structured field extraction (not just raw text)
- Better accuracy for financial documents
- No need for Google Vision fallback

---

## Part 2: Fields Extracted from Mindee

### **17 Fields Extracted from Mindee API**

Based on Mindee's Bank Statement Data Schema, we extract the following fields:

#### **1. Bank Information (3 fields)**
1. **`bank_name`** (Text)
   - Example: "Chase", "Bank of America", "Wells Fargo"
   - Extracted from: Bank logo/header on statement

2. **`bank_address`** (Nested Object)
   - Structure:
     ```json
     {
       "address": "270 Park Avenue, New York, NY 10017",
       "street": "270 Park Avenue",
       "city": "New York",
       "state": "NY",
       "postal_code": "10017",
       "country": "United States"
     }
     ```
   - Extracted from: Bank address on statement

3. **`account_type`** (Text)
   - Example: "Checking Account", "Savings Account"
   - Extracted from: Account type label on statement

#### **2. Account Information (3 fields)**
4. **`account_holder_names`** (Array of Strings)
   - Example: `["John Michael Anderson"]` or `["John Doe", "Jane Doe"]`
   - Extracted from: Account holder name(s) on statement

5. **`account_number`** (Text)
   - Example: "4532-8871-2345" or "****-2345" (masked)
   - Extracted from: Account number field on statement

6. **`currency`** (Text)
   - Example: "USD", "EUR", "GBP"
   - Extracted from: Currency symbol or label on statement

#### **3. Statement Period (3 fields)**
7. **`statement_period_start_date`** (Date)
   - Format: YYYY-MM-DD
   - Example: "2024-11-01"
   - Extracted from: Statement period start date

8. **`statement_period_end_date`** (Date)
   - Format: YYYY-MM-DD
   - Example: "2024-11-30"
   - Extracted from: Statement period end date

9. **`statement_date`** (Date)
   - Format: YYYY-MM-DD
   - Example: "2024-11-30"
   - Extracted from: Date statement was issued

#### **4. Balance Information (4 fields)**
10. **`beginning_balance`** (Number)
    - Example: `8542.75`
    - Extracted from: Opening balance at start of period

11. **`ending_balance`** (Number)
    - Example: `12384.50`
    - Extracted from: Closing balance at end of period

12. **`total_credits`** (Number)
    - Example: `15230.00`
    - Extracted from: Total deposits/credits summary

13. **`total_debits`** (Number)
    - Example: `11388.25`
    - Extracted from: Total withdrawals/debits summary

#### **5. Transactions (1 field - Complex)**
14. **`list_of_transactions`** (Array of Transaction Objects)
    - Structure:
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
        },
        ...
      ]
      ```
    - Extracted from: Transaction table/list on statement
    - Each transaction contains:
      - `date`: Transaction date (YYYY-MM-DD)
      - `description`: Transaction description/text
      - `amount`: Transaction amount (positive for credits, negative for debits)

#### **6. Additional Fields (3 fields)**
15. **`account_holder_address`** (Nested Object)
    - Structure:
      ```json
      {
        "street": "425 Park Avenue",
        "city": "New York",
        "state": "NY",
        "postal_code": "10022",
        "country": "United States"
      }
      ```
    - Extracted from: Account holder address on statement

16. **`branch_code`** (Text, Optional)
    - Example: "CH-NY-001"
    - Extracted from: Branch code/routing number (if available)

17. **`daily_balances`** (Array, Optional)
    - Example: `[{"date": "2024-11-01", "balance": 8542.75}, ...]`
    - Extracted from: Daily balance history (if available)

### **Raw Text Extraction**

In addition to structured fields, Mindee also provides:
- **`raw_text`**: Complete OCR text extraction from the entire document
- Used for: Fallback extraction, text quality analysis, fraud detection

---

## Part 3: Normalization Implementation

### **What is Normalization?**

Normalization converts bank-specific field names and formats into a **standardized schema** that works for all banks.

**Why Normalize?**
- Different banks use different field names (e.g., "Opening Balance" vs "Beginning Balance")
- Different formats (e.g., dates: "11/01/2024" vs "2024-11-01")
- Standardization enables consistent ML/AI analysis across all banks

### **Normalization Architecture**

#### **1. Standardized Schema**

**Location:** `Backend/bank_statement/normalization/bank_statement_schema.py`

**Class:** `NormalizedBankStatement`

**Standardized Fields:**
```python
@dataclass
class NormalizedBankStatement:
    # Bank Information
    bank_name: Optional[str] = None
    bank_address: Optional[Dict] = None
    
    # Account Information
    account_holder_name: Optional[str] = None
    account_holder_names: Optional[List[str]] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    currency: Optional[str] = None
    
    # Statement Period
    statement_period_start_date: Optional[str] = None  # YYYY-MM-DD
    statement_period_end_date: Optional[str] = None    # YYYY-MM-DD
    statement_date: Optional[str] = None               # YYYY-MM-DD
    
    # Balance Information (Normalized Format)
    beginning_balance: Optional[Dict] = None      # {'value': float, 'currency': str}
    ending_balance: Optional[Dict] = None        # {'value': float, 'currency': str}
    total_credits: Optional[Dict] = None        # {'value': float, 'currency': str}
    total_debits: Optional[Dict] = None          # {'value': float, 'currency': str}
    
    # Transactions (Normalized Format)
    transactions: Optional[List[Dict]] = None    # [{'date': str, 'description': str, 'amount': {'value': float}}]
    
    # Additional
    account_holder_address: Optional[Dict] = None
```

#### **2. Bank-Specific Normalizers**

**Location:** `Backend/bank_statement/normalization/`

**Supported Banks:**
- `chase.py` - Chase Bank normalizer
- `bank_of_america.py` - Bank of America normalizer
- `bank_statement_base_normalizer.py` - Base class for all normalizers

**Factory Pattern:**
```python
# Location: bank_statement_normalizer_factory.py
class BankStatementNormalizerFactory:
    NORMALIZERS = {
        'chase': ChaseNormalizer,
        'bank of america': BankOfAmericaNormalizer,
        'wells fargo': ChaseNormalizer,  # Uses Chase as template
        'citibank': ChaseNormalizer,      # Uses Chase as template
    }
    
    @classmethod
    def get_normalizer(cls, bank_name: str):
        # Returns appropriate normalizer for the bank
        return normalizer_class()
```

#### **3. Normalization Process**

**Step-by-Step:**

**Step 1: Extract with Mindee**
```python
extracted_data, raw_text = self._extract_with_mindee(file_path)
# Returns: Dictionary with 17 Mindee fields
```

**Step 2: Get Bank-Specific Normalizer**
```python
bank_name = extracted_data.get('bank_name', '')
normalizer = BankStatementNormalizerFactory.get_normalizer(bank_name)
# Returns: ChaseNormalizer, BankOfAmericaNormalizer, etc.
```

**Step 3: Normalize Data**
```python
normalized_obj = normalizer.normalize(extracted_data)
# Returns: NormalizedBankStatement instance
```

**Step 4: Convert to Dictionary**
```python
normalized_data = normalized_obj.to_dict()
# Returns: Dictionary with standardized fields
```

### **Normalization Logic**

#### **A. Field Mapping**

Each bank normalizer defines field mappings:

**Example: Chase Normalizer**
```python
def get_field_mappings(self) -> Dict[str, str]:
    return {
        # Mindee field → Standardized field
        'bank_name': 'bank_name',
        'account_holder_names': 'account_holder_names',
        'beginning_balance': 'beginning_balance',
        'opening_balance': 'beginning_balance',  # Alternative name
        'ending_balance': 'ending_balance',
        'closing_balance': 'ending_balance',     # Alternative name
        'list_of_transactions': 'transactions',
        ...
    }
```

#### **B. Data Type Normalization**

**Amounts:**
```python
def _normalize_amount(self, amount_value) -> Optional[Dict]:
    """Convert to {'value': float, 'currency': str} format"""
    # Input: 8542.75 (float) or "$8,542.75" (string)
    # Output: {'value': 8542.75, 'currency': 'USD'}
```

**Dates:**
```python
def _normalize_date(self, date_value) -> Optional[str]:
    """Convert to YYYY-MM-DD format"""
    # Input: "11/01/2024" or "November 1, 2024"
    # Output: "2024-11-01"
```

**Transactions:**
```python
def _normalize_transactions(self, transactions) -> Optional[List[Dict]]:
    """Normalize transaction list"""
    # Input: Mindee transaction objects
    # Output: [{'date': '2024-11-01', 'description': '...', 'amount': {'value': 4850.0}}]
```

**Addresses:**
```python
def _normalize_address(self, address_value) -> Optional[Dict]:
    """Normalize address to standard format"""
    # Input: Mindee address object
    # Output: {'street': '...', 'city': '...', 'state': '...', 'postal_code': '...', 'country': '...'}
```

#### **C. Bank-Specific Post-Processing**

**Example: Chase Normalizer**
```python
def normalize(self, ocr_data: Dict):
    # Call parent normalize method
    normalized = super().normalize(ocr_data)
    
    # Chase-specific post-processing
    # Set primary account holder name from list
    if normalized.account_holder_names and not normalized.account_holder_name:
        normalized.account_holder_name = normalized.account_holder_names[0]
    
    # Set default currency if not present
    if not normalized.currency:
        normalized.currency = 'USD'
    
    return normalized
```

### **Normalization Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Upload Bank Statement PDF/Image                         │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Mindee OCR Extraction                                     │
│    - Extract 17 structured fields                          │
│    - Extract raw_text                                       │
│    - Returns: extracted_data (dict), raw_text (str)        │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Identify Bank Name                                        │
│    - Extract bank_name from Mindee data                    │
│    - Example: "Chase", "Bank of America"                    │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Get Bank-Specific Normalizer                               │
│    - Factory.get_normalizer("Chase")                        │
│    - Returns: ChaseNormalizer instance                      │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Normalize Data                                            │
│    - Map Mindee fields → Standardized fields                │
│    - Normalize amounts: float → {'value': float, 'currency': str} │
│    - Normalize dates: various → YYYY-MM-DD                  │
│    - Normalize transactions: Mindee format → Standard format│
│    - Apply bank-specific post-processing                    │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Create NormalizedBankStatement Instance                   │
│    - All fields in standardized format                     │
│    - Validated and ready for ML/AI analysis                │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Continue to ML Fraud Detection                           │
│    - Extract 35 features from normalized data              │
│    - Calculate fraud risk score                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 4: Example: Chase Statement Normalization

### **Input: Mindee Extracted Data**
```json
{
  "bank_name": "CHASE",
  "account_holder_names": ["John Michael Anderson"],
  "account_number": "****-2345",
  "account_type": "Checking Account",
  "statement_period_start_date": "2024-11-01",
  "statement_period_end_date": "2024-11-30",
  "statement_date": "2024-11-30",
  "beginning_balance": 8542.75,
  "ending_balance": 12384.50,
  "total_credits": 15230.00,
  "total_debits": 11388.25,
  "list_of_transactions": [
    {"date": "2024-11-01", "description": "SALARY DEPOSIT", "amount": 4850.0},
    {"date": "2024-11-02", "description": "RENT PAYMENT", "amount": -2200.0}
  ],
  "bank_address": {
    "address": "270 Park Avenue, New York, NY 10017",
    "street": "270 Park Avenue",
    "city": "New York",
    "state": "NY",
    "postal_code": "10017"
  }
}
```

### **Output: Normalized Data**
```json
{
  "bank_name": "Chase",
  "account_holder_name": "John Michael Anderson",
  "account_holder_names": ["John Michael Anderson"],
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
    {
      "date": "2024-11-01",
      "description": "SALARY DEPOSIT",
      "amount": {"value": 4850.0, "currency": "USD"}
    },
    {
      "date": "2024-11-02",
      "description": "RENT PAYMENT",
      "amount": {"value": -2200.0, "currency": "USD"}
    }
  ],
  "bank_address": {
    "address": "270 Park Avenue, New York, NY 10017",
    "street": "270 Park Avenue",
    "city": "New York",
    "state": "NY",
    "postal_code": "10017",
    "country": null
  }
}
```

### **Key Normalization Changes:**
1. ✅ **Bank name**: "CHASE" → "Chase" (standardized)
2. ✅ **Account holder**: Extracted primary name from list
3. ✅ **Amounts**: `8542.75` → `{"value": 8542.75, "currency": "USD"}`
4. ✅ **Currency**: Added default "USD" if missing
5. ✅ **Transactions**: Normalized to standard format with amount dicts
6. ✅ **Field names**: `list_of_transactions` → `transactions`

---

## Part 5: Summary

### **OCR Service:**
- ✅ **Mindee Only** (ClientV2 API)
- ❌ **No Google Vision** (not used for bank statements)
- ❌ **No Fallback** (if Mindee fails, extraction fails)

### **Fields Extracted:**
- **17 fields** from Mindee Bank Statement model
- Includes: Bank info, account info, dates, balances, transactions, addresses
- Plus: Raw text for fallback/quality analysis

### **Normalization:**
- **Standardized Schema**: `NormalizedBankStatement` dataclass
- **Bank-Specific Normalizers**: Chase, Bank of America, etc.
- **Factory Pattern**: Automatically selects correct normalizer
- **Data Transformation**: Amounts, dates, transactions normalized to standard format
- **Post-Processing**: Bank-specific adjustments applied

### **Flow:**
```
Mindee OCR → Extract 17 Fields → Identify Bank → Get Normalizer → 
Normalize Data → Standardized Schema → ML/AI Analysis
```

---

## Code References

- **Extraction**: `Backend/bank_statement/bank_statement_extractor.py` (lines 162-271)
- **Normalization Factory**: `Backend/bank_statement/normalization/bank_statement_normalizer_factory.py`
- **Schema**: `Backend/bank_statement/normalization/bank_statement_schema.py`
- **Chase Normalizer**: `Backend/bank_statement/normalization/chase.py`
- **Base Normalizer**: `Backend/bank_statement/normalization/bank_statement_base_normalizer.py`


