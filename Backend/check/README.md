# Check Analysis Module

Complete self-contained check analysis pipeline with no dependencies on other document types.

## Structure

```
check/
├── __init__.py                 # Module entry point
├── README.md                   # This file
├── check_extractor.py          # Main orchestrator (OCR → Normalization → ML → AI)
├── extractor.py                # Legacy extractor (to be removed)
├── fraud_detector.py           # Legacy fraud detector (to be removed)
│
├── normalization/             # Check-specific normalizers
│   ├── __init__.py
│   ├── check_base_normalizer.py
│   ├── check_normalizer_factory.py
│   ├── check_schema.py
│   ├── bank_of_america.py
│   └── chase.py
│
├── ml/                        # Check-specific ML models
│   ├── __init__.py
│   ├── check_fraud_detector.py
│   └── check_feature_extractor.py
│
├── ai/                        # Check-specific AI agents
│   ├── __init__.py
│   ├── check_fraud_analysis_agent.py
│   ├── check_prompts.py
│   └── check_tools.py
│
├── database/                  # Check-specific database operations
│   ├── __init__.py
│   └── check_customer_storage.py
│
├── utils/                     # Check-specific utilities
│   ├── __init__.py
│   └── check_fraud_indicators.py
│
└── analysis_results/          # Check analysis output storage
```

## Features

### 1. OCR Extraction
- Uses **Mindee API** exclusively for check OCR
- No dependency on Google Vision or other OCR services
- Extracts: bank name, routing number, account number, check number, amount, dates, signatures, etc.

### 2. Normalization
- Bank-specific normalizers (Bank of America, Chase, etc.)
- Standardizes field names across different banks
- Returns `NormalizedCheck` dataclass

### 3. ML Fraud Detection
- **Check-specific** feature extractor (30 features)
- Ensemble model: Random Forest + XGBoost
- Risk levels: LOW, MEDIUM, HIGH, CRITICAL
- Completely independent from money order ML models

### 4. AI Fraud Analysis
- LangChain-based AI agent using GPT-4/o4-mini
- Check-specific prompts and reasoning
- Customer history integration
- Recommendations: APPROVE, REJECT, ESCALATE

### 5. Database Operations
- Check customer tracking
- Fraud history management
- Duplicate check detection
- Separate from money order customer tracking

## Usage

### Basic Usage

```python
from check import extract_check

# Analyze a check
results = extract_check('/path/to/check.jpg')

# Results include:
# - extracted_data: Raw OCR fields
# - normalized_data: Standardized fields
# - ml_analysis: ML fraud scores and risk level
# - ai_analysis: AI recommendation and reasoning
# - anomalies: List of detected issues
# - overall_decision: Final decision (APPROVE/REJECT/ESCALATE)
```

### Advanced Usage

```python
from check import CheckExtractor

extractor = CheckExtractor()
results = extractor.extract_and_analyze('/path/to/check.jpg')
```

### Using Individual Components

```python
# Normalization
from check.normalization import CheckNormalizerFactory
normalizer = CheckNormalizerFactory.get_normalizer('Bank of America')
normalized = normalizer.normalize(extracted_data)

# ML Detection
from check.ml import CheckFraudDetector
detector = CheckFraudDetector()
ml_results = detector.predict_fraud(check_data, raw_text)

# AI Analysis
from check.ai import CheckFraudAnalysisAgent
agent = CheckFraudAnalysisAgent(api_key=openai_key)
ai_results = agent.analyze_fraud(extracted_data, ml_analysis, payer_name='John Doe')

# Database Operations
from check.database import get_check_customer_history
history = get_check_customer_history('John Doe')
```

## Configuration

### Environment Variables

```bash
# Mindee API (required)
MINDEE_API_KEY=your_mindee_api_key
MINDEE_MODEL_ID_CHECK=your_model_id

# OpenAI API (required for AI analysis)
OPENAI_API_KEY=your_openai_key
AI_MODEL=gpt-4  # or o4-mini, o1, etc.
```

## Independence Guarantee

✅ **No shared code with money orders**
- Separate ML models
- Separate AI agents
- Separate database tables
- Separate normalizers
- Separate utilities

✅ **No shared code with other document types**
- Bank statements
- Paystubs
- Real-time transactions

✅ **Self-contained and deployable**
- All dependencies are within `check/` folder
- Can be extracted as standalone module
- No cross-module imports

## Testing

```python
# Test normalization
from check.normalization import CheckNormalizerFactory
normalizer = CheckNormalizerFactory.get_normalizer('Bank of America')
assert normalizer is not None

# Test ML detection
from check.ml import CheckFraudDetector
detector = CheckFraudDetector()
test_data = {'bank_name': 'Bank of America', 'amount': 100.0}
results = detector.predict_fraud(test_data)
assert 'fraud_risk_score' in results

# Test AI agent
from check.ai import CheckFraudAnalysisAgent
agent = CheckFraudAnalysisAgent(api_key=os.getenv('OPENAI_API_KEY'))
# ... test with real data
```

## Migration Notes

If you're migrating from the old structure:

1. **Old imports** (deprecated):
   ```python
   from normalization.check_normalizer_factory import CheckNormalizerFactory
   from ml_models.check_fraud_detector import CheckFraudDetector
   from database.check_customer_storage import CheckCustomerStorage
   ```

2. **New imports** (use these):
   ```python
   from check.normalization import CheckNormalizerFactory
   from check.ml import CheckFraudDetector
   from check.database import CheckCustomerStorage
   ```

## Model Files

ML models are stored in:
- `check/ml/models/` (preferred)
- Falls back to `Backend/ml_models/` if not found

Model files:
- `check_random_forest.pkl`
- `check_xgboost.pkl`
- `check_feature_scaler.pkl`

## Database Tables

Check module uses:
- `check_customers` - Customer fraud tracking
- `checks` - Check analysis records

Separate from:
- `money_order_customers` (money orders)
- `money_orders` (money orders)

