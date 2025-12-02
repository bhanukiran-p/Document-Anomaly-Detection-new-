# Paystub Analysis Module

Complete self-contained paystub analysis pipeline with no dependencies on other document types.

## Structure

```
paystub/
├── __init__.py                 # Module entry point
├── README.md                   # This file
├── paystub_extractor.py        # Main paystub extractor (Mindee API)
├── extractor.py                # Legacy redirect (deprecated)
│
├── normalization/              # Paystub-specific normalizers
│   ├── __init__.py
│   ├── paystub_base_normalizer.py
│   ├── paystub_normalizer.py
│   ├── paystub_normalizer_factory.py
│   └── paystub_schema.py
│
├── ml/                         # Paystub-specific ML models
│   ├── __init__.py
│   ├── paystub_fraud_detector.py
│   └── paystub_feature_extractor.py
│
├── ai/                         # Paystub-specific AI analysis
│   ├── __init__.py
│   ├── paystub_fraud_analysis_agent.py
│   ├── paystub_prompts.py
│   └── paystub_tools.py
│
└── database/                   # Paystub-specific database storage
    ├── __init__.py
    └── paystub_customer_storage.py
```

## Features

### 1. OCR Extraction
- Uses **Mindee API** for paystub OCR
- Extracts structured fields: first_name, last_name, employee_address, pay_period_start_date, pay_period_end_date, gross_pay, net_pay, deductions, taxes, employer_name, employer_address, social_security_number, employee_id
- Returns structured data, no regex parsing needed

### 2. Normalization
- Paystub-specific normalizers
- Maps Mindee fields to standardized schema
- Standardizes field names across different paystub formats
- Returns `NormalizedPaystub` dataclass
- **Completely independent from other document type normalization**

### 3. ML Fraud Detection
- **Paystub-specific** feature extractor (10 features matching trained model)
- Uses trained Random Forest model (loads from `models/paystub_risk_model_latest.pkl`)
- Falls back to heuristic rules if model not available
- Risk levels: LOW, MEDIUM, HIGH, CRITICAL
- Completely independent from other document type ML models

### 4. AI Fraud Analysis
- LangChain-based AI agent using GPT-4/o4-mini
- Paystub-specific prompts and reasoning
- Employee history tracking
- Recommendations: APPROVE, REJECT, ESCALATE
- Matches customer logic from bank statements and checks

### 5. Database Storage
- Stores to `paystubs` table
- Tracks employee history in `paystub_customers` table
- Fraud tracking: `fraud_count`, `escalate_count`, `has_fraud_history`
- Duplicate detection

## Usage

### Basic Usage

```python
from paystub.paystub_extractor import PaystubExtractor

# Analyze a paystub (Mindee-based, no credentials needed)
extractor = PaystubExtractor()
results = extractor.extract_and_analyze('/path/to/paystub.pdf')
```

### Using Individual Components

```python
# Normalization
from paystub.normalization import PaystubNormalizerFactory
normalizer = PaystubNormalizerFactory.get_normalizer()
normalized = normalizer.normalize(extracted_data)

# ML Detection
from paystub.ml import PaystubFraudDetector
detector = PaystubFraudDetector()
ml_results = detector.predict_fraud(paystub_data, raw_text)
```

## Configuration

### Environment Variables

```bash
# Mindee API (required)
MINDEE_API_KEY=your_mindee_api_key
MINDEE_MODEL_ID_PAYSTUB=ba548707-66d2-48c3-83f3-599484b078c8

# OpenAI API (required for AI analysis)
OPENAI_API_KEY=your_openai_key
AI_MODEL=o4-mini  # or gpt-4, o1, etc.

# ML Models directory
ML_MODEL_DIR=models  # Default: models/
```

### Database Tables

Run these SQL migrations:
- `Backend/database/create_paystub_customers_table.sql` - Creates `paystub_customers` table
- `paystubs` table should already exist (created by main migration)

## Independence Guarantee

✅ **No shared code with other document types**
- Separate normalizers (PaystubBaseNormalizer)
- Separate schema (NormalizedPaystub)
- Separate ML models (PaystubFraudDetector, PaystubFeatureExtractor)
- Separate AI agents (PaystubFraudAnalysisAgent)
- Separate database storage (PaystubCustomerStorage)

✅ **Self-contained and deployable**
- All dependencies are within `paystub/` folder
- Can be extracted as standalone module
- No cross-module imports

## Migration Notes

### From Google Vision to Mindee

1. **Old imports** (deprecated):
   ```python
   from paystub.extractor import PaystubExtractor
   extractor = PaystubExtractor('google-credentials.json')
   ```

2. **New imports** (use these):
   ```python
   from paystub.paystub_extractor import PaystubExtractor
   extractor = PaystubExtractor()  # No credentials needed
   ```

3. **Removed dependencies**:
   - Google Cloud Vision API
   - `google-credentials.json` file
   - All regex-based field extraction

4. **New dependencies**:
   - Mindee API (ClientV2)
   - `MINDEE_API_KEY` environment variable
   - `MINDEE_MODEL_ID_PAYSTUB` environment variable

## Testing

```python
# Test normalization
from paystub.normalization import PaystubNormalizerFactory
normalizer = PaystubNormalizerFactory.get_normalizer()
assert normalizer is not None

# Test ML detection
from paystub.ml import PaystubFraudDetector
detector = PaystubFraudDetector()
test_data = {'gross_pay': 5000.0, 'net_pay': 4000.0, 'company_name': 'Test Corp', 'employee_name': 'John Doe', 'pay_date': '2024-01-01'}
results = detector.predict_fraud(test_data)
assert 'fraud_risk_score' in results
```
