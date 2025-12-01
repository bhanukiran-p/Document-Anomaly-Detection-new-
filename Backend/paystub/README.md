# Paystub Analysis Module

Complete self-contained paystub analysis pipeline with no dependencies on other document types.

## Structure

```
paystub/
├── __init__.py                 # Module entry point
├── README.md                   # This file
├── extractor.py                # Main paystub extractor (Google Vision API)
├── extractor_legacy.py         # Legacy extractor (if exists)
│
├── normalization/              # Paystub-specific normalizers
│   ├── __init__.py
│   ├── paystub_base_normalizer.py
│   ├── paystub_normalizer.py
│   ├── paystub_normalizer_factory.py
│   └── paystub_schema.py
│
├── ml/                        # Paystub-specific ML models
│   ├── __init__.py
│   └── paystub_fraud_detector.py
│
└── analysis_results/          # Paystub analysis output storage
```

## Features

### 1. OCR Extraction
- Uses **Google Vision API** for paystub OCR
- Extracts: company name, employee info, pay dates, amounts, taxes, etc.

### 2. Normalization
- Paystub-specific normalizers
- Standardizes field names across different paystub formats
- Returns `NormalizedPaystub` dataclass
- **Completely independent from money order normalization**

### 3. ML Fraud Detection
- **Paystub-specific** feature extractor
- Heuristic-based fraud detection
- Risk levels: LOW, MEDIUM, HIGH, CRITICAL
- Completely independent from money order ML models

### 4. AI Fraud Analysis
- LangChain-based AI agent using GPT-4
- Paystub-specific prompts and reasoning
- Recommendations: APPROVE, REJECT, ESCALATE

## Usage

### Basic Usage

```python
from paystub import extract_paystub, PaystubExtractor

# Analyze a paystub
results = extract_paystub('/path/to/paystub.jpg', 'google-credentials.json')

# Or use the extractor class
extractor = PaystubExtractor('google-credentials.json')
results = extractor.extract('/path/to/paystub.jpg')
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
# Google Vision API (required)
GOOGLE_CREDENTIALS_PATH=google-credentials.json

# OpenAI API (required for AI analysis)
OPENAI_API_KEY=your_openai_key
AI_MODEL=gpt-4  # or o4-mini, o1, etc.
```

## Independence Guarantee

✅ **No shared code with money orders**
- Separate normalizers (PaystubBaseNormalizer, not BaseNormalizer)
- Separate schema (NormalizedPaystub, not NormalizedMoneyOrder)
- Separate ML models
- Separate AI agents

✅ **No shared code with other document types**
- Checks
- Bank statements
- Real-time transactions

✅ **Self-contained and deployable**
- All dependencies are within `paystub/` folder
- Can be extracted as standalone module
- No cross-module imports

## Migration Notes

If you're migrating from the old structure:

1. **Old imports** (deprecated):
   ```python
   from normalization.normalizer_factory import NormalizerFactory
   from ml_models.paystub_fraud_detector import PaystubFraudDetector
   from pages.paystub_extractor import PaystubExtractor
   ```

2. **New imports** (use these):
   ```python
   from paystub.normalization import PaystubNormalizerFactory
   from paystub.ml import PaystubFraudDetector
   from paystub import PaystubExtractor
   ```

## Testing

```python
# Test normalization
from paystub.normalization import PaystubNormalizerFactory
normalizer = PaystubNormalizerFactory.get_normalizer()
assert normalizer is not None

# Test ML detection
from paystub.ml import PaystubFraudDetector
detector = PaystubFraudDetector()
test_data = {'gross_pay': 5000.0, 'net_pay': 4000.0}
results = detector.predict_fraud(test_data)
assert 'fraud_risk_score' in results
```

