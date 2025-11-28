# Money Order Module

Complete modularized package for money order extraction, normalization, fraud detection, and AI-powered analysis.

## Directory Structure

```
money_order/
├── __init__.py                 # Module exports
├── README.md                   # This file
├── extractor.py               # MoneyOrderExtractor class
├── normalizer.py              # (Optional) Data normalization logic
└── ai/
    ├── __init__.py            # AI submodule exports
    ├── fraud_analysis_agent.py # FraudAnalysisAgent class
    ├── prompts.py             # System prompts and templates
    ├── tools.py               # DataAccessTools and LangChain tools
    └── result_storage.py      # ResultStorage class for managing analysis results
```

## Components

### 1. **extractor.py** - MoneyOrderExtractor
Main class for extracting money order data from images/PDFs.

**Features:**
- Uses Google Vision API for OCR
- Integrates ML fraud detection (Random Forest + XGBoost)
- Performs AI-powered analysis using GPT-4
- Detects repeat customers from database
- Stores analysis results as JSON

**Usage:**
```python
from money_order.extractor import MoneyOrderExtractor

extractor = MoneyOrderExtractor("path/to/google-credentials.json")
result = extractor.extract_money_order("path/to/money_order.jpg")
```

### 2. **ai/fraud_analysis_agent.py** - FraudAnalysisAgent
LangChain-based agent for intelligent fraud analysis and recommendations.

**Features:**
- Analyzes ML fraud scores with contextual reasoning
- Differentiates between repeat customers with/without fraud history
- Provides recommendations: APPROVE, REJECT, or ESCALATE
- Includes confidence scores and actionable insights
- Integrates customer transaction history

**Key Methods:**
- `analyze_fraud(ml_analysis, extracted_data, customer_id, is_repeat_customer)` - Main analysis method

### 3. **ai/prompts.py** - System Prompts
GPT-4 system and analysis prompts for fraud detection.

**Contains:**
- `SYSTEM_PROMPT` - Role and capabilities of the AI analyst
- `ANALYSIS_TEMPLATE` - Structured prompt for fraud analysis
- `RECOMMENDATION_GUIDELINES` - Decision rules based on fraud score and customer type:
  - **REJECT**: For repeat fraudsters with fraud history (score >= 30%)
  - **ESCALATE**: For new customers with high risk (score >= 30%)
  - **APPROVE**: For legitimate transactions (score < 30%)

**Customer Type Logic:**
- **REPEAT CUSTOMER WITH FRAUD HISTORY**: Stricter rules (REJECT at >= 30%)
- **REPEAT CUSTOMER WITH CLEAN HISTORY**: Standard rules (REJECT at > 85%)
- **NEW CUSTOMER**: Conservative rules (ESCALATE for high scores)

### 4. **ai/tools.py** - DataAccessTools
Tools for accessing historical data, customer information, and fraud patterns.

**Features:**
- Get customer transaction history
- Search for similar fraud cases
- Access training dataset patterns
- Find similar past analyses

### 5. **ai/result_storage.py** - ResultStorage
Manages storage and retrieval of analysis results as JSON files.

**Features:**
- Save analysis results with metadata
- Retrieve results by ID
- Search by issuer or amount range
- Access recent analyses

## Usage Examples

### Basic Money Order Analysis
```python
from money_order import MoneyOrderExtractor

# Initialize extractor
extractor = MoneyOrderExtractor("credentials.json")

# Extract and analyze
result = extractor.extract_money_order("money_order.jpg")

# Result contains:
# - extracted_data: OCR'd fields
# - normalized_data: Standardized format
# - ml_analysis: Fraud risk score and model confidence
# - ai_analysis: AI recommendation and reasoning
# - anomalies: List of detected issues
```

### Using the Module in API
```python
from money_order.extractor import MoneyOrderExtractor

# In api_server.py
extractor = MoneyOrderExtractor(CREDENTIALS_PATH)
result = extractor.extract_money_order(filepath)
```

## Data Flow

```
Money Order Image
    ↓
[OCR Extraction via Google Vision API]
    ↓
[Field Extraction & Normalization]
    ↓
[ML Fraud Detection - RF + XGBoost]
    ↓
[Customer Lookup - Repeat vs New?]
    ↓
[AI Analysis with GPT-4]
    ├── Check Customer History
    ├── Evaluate Fraud Indicators
    ├── Generate Recommendation (APPROVE/REJECT/ESCALATE)
    └── Provide Reasoning & Actions
    ↓
[Store Results as JSON]
    ↓
Response with Analysis Results
```

## AI Recommendation Rules

### For New Customers
- **Fraud Score 100% or >= 95%**: ESCALATE (high risk, needs human review)
- **Fraud Score 85-95%**: ESCALATE
- **Fraud Score 30-85%**: ESCALATE (moderate risk)
- **Fraud Score < 30%**: APPROVE

### For Repeat Customers with Fraud History
- **Fraud Score >= 30%**: REJECT (known fraudster, be strict)
- **Fraud Score < 30%**: APPROVE

### For Repeat Customers with Clean History
- **Fraud Score > 85%**: REJECT
- **Fraud Score 30-85%**: ESCALATE
- **Fraud Score < 30%**: APPROVE

## Configuration

### Environment Variables
- `MINDEE_API_KEY` - API key for Mindee (optional, for money gram/western union details)
- `OPENAI_API_KEY` - OpenAI API key for GPT-4
- `GOOGLE_CREDENTIALS_PATH` - Path to Google Cloud service account JSON

### Database Schema
- `money_order_customers` - Table storing customer information
  - `customer_id` (primary key)
  - `name` (payer/purchaser name)
  - `address` (sender address)
  - `payee_name` (recipient name)
  - Other customer fields

## Testing

To test the modularized structure:

```bash
# Restart the API server
python api_server.py

# The server will automatically use the new modular structure
# All money order requests will go through the new module
```

## Future Enhancements

- [ ] Add more issuer-specific normalizers
- [ ] Implement ML model retraining pipeline
- [ ] Add vector DB for similar case retrieval
- [ ] Create dedicated money order API endpoints
- [ ] Add webhook support for real-time notifications
- [ ] Implement batch processing for multiple documents

## File Dependencies

```
money_order/
├── extractor.py
│   ├── Depends on: ml_models.fraud_detector
│   ├── Depends on: .ai.fraud_analysis_agent
│   ├── Depends on: normalization.NormalizerFactory
│   └── Depends on: database.supabase_client
│
└── ai/
    ├── fraud_analysis_agent.py
    │   ├── Depends on: .prompts
    │   └── Depends on: .tools
    │
    ├── tools.py
    │   └── Depends on: .result_storage
    │
    └── result_storage.py
        └── No internal dependencies
```

## Performance Notes

- ML inference: ~1-2 seconds
- AI analysis (GPT-4): ~3-5 seconds
- Total analysis time: ~5-10 seconds per document
- Database lookups: ~100-200ms

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError: No module named 'money_order'`:
1. Ensure you're running from the Backend directory
2. Check that `__init__.py` files exist in all subdirectories
3. Verify Python path includes the Backend directory

### AI Analysis Fails
1. Check `OPENAI_API_KEY` environment variable
2. Verify API key has GPT-4 access
3. Check network connectivity

### Customer Lookup Issues
1. Verify Supabase connection
2. Check that `money_order_customers` table exists
3. Ensure customer data is properly stored with name and address
