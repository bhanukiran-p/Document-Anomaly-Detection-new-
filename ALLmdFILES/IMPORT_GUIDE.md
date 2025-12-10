# Money Order Module - Import Guide

Quick reference for importing and using the money order module components.

## Quick Imports

### For API/Main Application
```python
# Import the main extractor
from money_order import MoneyOrderExtractor

# Or explicitly from submodule
from money_order.extractor import MoneyOrderExtractor

# Usage
extractor = MoneyOrderExtractor(credentials_path)
result = extractor.extract_money_order(filepath)
```

### For AI Analysis Components
```python
# Import AI agent and tools
from money_order.ai import FraudAnalysisAgent, DataAccessTools, ResultStorage

# Usage
agent = FraudAnalysisAgent()
analysis = agent.analyze_fraud(ml_analysis, extracted_data, customer_id, is_repeat_customer)
```

## Detailed Import Reference

### 1. Main Extractor Class

**File:** `money_order/extractor.py`

```python
from money_order.extractor import MoneyOrderExtractor

# Initialize with Google Cloud credentials
extractor = MoneyOrderExtractor("path/to/credentials.json")

# Extract and analyze a money order
result = extractor.extract_money_order("path/to/image.jpg")

# Result structure:
# {
#     'status': 'success',
#     'extracted_data': {...},      # OCR'd fields
#     'normalized_data': {...},     # Standardized format
#     'ml_analysis': {...},         # Fraud risk score
#     'ai_analysis': {...},         # AI recommendation
#     'anomalies': [...],           # Issues found
#     'analysis_id': 'analysis_...'
# }
```

### 2. Fraud Analysis Agent

**File:** `money_order/ai/fraud_analysis_agent.py`

```python
from money_order.ai.fraud_analysis_agent import FraudAnalysisAgent

# Initialize agent (automatically loads GPT-4)
agent = FraudAnalysisAgent(
    credentials_path='path/to/credentials.json',  # Optional
    model_name='gpt-4'
)

# Analyze fraud
ai_analysis = agent.analyze_fraud(
    ml_analysis={
        'fraud_risk_score': 0.95,
        'risk_level': 'CRITICAL',
        'confidence_score': 0.99,
        'model_scores': {'random_forest': 0.99, 'xgboost': 0.99}
    },
    extracted_data={
        'issuer': 'MoneyGram',
        'amount': '$500',
        'purchaser': 'John Doe',
        'payee': 'Jane Smith'
    },
    customer_id='CUST001',
    is_repeat_customer=True
)

# AI Analysis result:
# {
#     'recommendation': 'REJECT',  # or 'APPROVE', 'ESCALATE'
#     'confidence_score': 0.95,
#     'summary': 'High fraud risk...',
#     'reasoning': ['Reason 1', 'Reason 2', ...],
#     'key_indicators': ['Indicator 1', ...],
#     'actionable_recommendations': ['Action 1', 'Action 2', ...]
# }
```

### 3. Data Access Tools

**File:** `money_order/ai/tools.py`

```python
from money_order.ai.tools import DataAccessTools

# Initialize tools
tools = DataAccessTools(
    ml_scores_path='ml_scores.csv',
    customer_history_path='customer_history.csv',
    fraud_cases_path='fraud_cases.csv',
    training_data_path='training_data.csv'
)

# Get customer history
history = tools.get_customer_history('CUST001')
# {
#     'customer_id': 'CUST001',
#     'num_transactions': 5,
#     'num_fraud_incidents': 1,
#     'avg_amount': 350.0,
#     'fraud_rate': '20%',
#     'transactions': [...]
# }

# Search similar fraud cases
cases = tools.search_similar_fraud_cases(
    issuer='MoneyGram',
    amount_range=(400, 600)
)

# Search stored analyses
analyses = tools.search_stored_analyses(
    issuer='Western Union',
    amount_range=(450, 550),
    limit=5
)

# Format customer history as string
summary = tools.format_customer_history_summary('CUST001')
```

### 4. Result Storage

**File:** `money_order/ai/result_storage.py`

```python
from money_order.ai.result_storage import ResultStorage

# Initialize storage
storage = ResultStorage(storage_dir='analysis_results')

# Save analysis result
analysis_id = storage.save_analysis_result(
    analysis_data={
        'extracted_data': {...},
        'ml_analysis': {...},
        'ai_analysis': {...},
        'anomalies': [...]
    },
    serial_number='9875647821'
)
# Returns: 'analysis_20251128_150000_123_9875647821'

# Retrieve result by ID
result = storage.get_analysis_by_id('analysis_20251128_150000_123_9875647821')

# Get recent results
recent = storage.get_recent_results(limit=10)

# Search by issuer
moneygram_results = storage.search_by_issuer('MoneyGram', limit=5)

# Search by amount range
high_value = storage.search_by_amount_range(min_amount=1000, max_amount=5000)
```

### 5. Prompts (For Reference)

**File:** `money_order/ai/prompts.py`

```python
from money_order.ai.prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_TEMPLATE,
    RECOMMENDATION_GUIDELINES,
    CUSTOMER_HISTORY_PROMPT
)

# These are used internally by FraudAnalysisAgent
# They contain:
# - SYSTEM_PROMPT: Role and capabilities of AI analyst
# - ANALYSIS_TEMPLATE: Structured prompt with placeholders
# - RECOMMENDATION_GUIDELINES: Decision logic for different scenarios
# - CUSTOMER_HISTORY_PROMPT: Format for customer history analysis
```

## Usage Patterns

### Pattern 1: Full Money Order Analysis Pipeline
```python
from money_order import MoneyOrderExtractor

# Setup
credentials_path = "path/to/google-credentials.json"
extractor = MoneyOrderExtractor(credentials_path)

# Analyze
result = extractor.extract_money_order("money_order.jpg")

# Handle result
if result['status'] == 'success':
    extracted = result['extracted_data']
    ml_analysis = result['ml_analysis']
    ai_analysis = result['ai_analysis']

    print(f"ML Fraud Score: {ml_analysis['fraud_risk_score']:.1%}")
    print(f"AI Recommendation: {ai_analysis['recommendation']}")
    print(f"Reasoning: {', '.join(ai_analysis['reasoning'])}")
```

### Pattern 2: Using Individual Components
```python
from money_order.ai import FraudAnalysisAgent, DataAccessTools
from ml_models.fraud_detector import MoneyOrderFraudDetector

# Step 1: Get ML fraud score
ml_detector = MoneyOrderFraudDetector()
ml_analysis = ml_detector.predict_fraud(extracted_data, raw_text)

# Step 2: Look up customer
tools = DataAccessTools(...)
customer_history = tools.get_customer_history(customer_id)

# Step 3: Get AI analysis
agent = FraudAnalysisAgent()
ai_analysis = agent.analyze_fraud(
    ml_analysis, extracted_data, customer_id, is_repeat_customer
)

# Step 4: Make decision
if ai_analysis['recommendation'] == 'REJECT':
    block_transaction()
elif ai_analysis['recommendation'] == 'ESCALATE':
    send_to_human_review()
else:
    approve_transaction()
```

### Pattern 3: Batch Analysis
```python
from money_order import MoneyOrderExtractor
import os

extractor = MoneyOrderExtractor(credentials_path)
results_dir = 'money_orders/'

for filename in os.listdir(results_dir):
    filepath = os.path.join(results_dir, filename)
    result = extractor.extract_money_order(filepath)

    # Process result...
    print(f"{filename}: {result['ai_analysis']['recommendation']}")
```

## Import Organization

### External Dependencies
These imports happen automatically within the module:
```python
# Within money_order/extractor.py
from ml_models.fraud_detector import MoneyOrderFraudDetector
from normalization import NormalizerFactory
from database.supabase_client import get_supabase

# Within money_order/ai/fraud_analysis_agent.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Within money_order/ai/tools.py
import pandas as pd
```

### Internal Dependencies
```
money_order/
├── extractor.py
│   └── from .ai.fraud_analysis_agent import FraudAnalysisAgent
│   └── from .ai.tools import DataAccessTools
│
└── ai/
    ├── fraud_analysis_agent.py
    │   ├── from .prompts import SYSTEM_PROMPT, ANALYSIS_TEMPLATE
    │   └── from .tools import DataAccessTools
    │
    ├── tools.py
    │   └── from .result_storage import ResultStorage
    │
    └── (Other files have no internal dependencies)
```

## Common Issues & Solutions

### Issue: ImportError: No module named 'money_order'
**Solution:** Make sure you're running from the Backend directory:
```bash
cd /path/to/Backend
python api_server.py
```

### Issue: ImportError: No module named 'langchain'
**Solution:** Install LangChain:
```bash
pip install langchain langchain-openai
```

### Issue: OPENAI_API_KEY not found
**Solution:** Set the environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
```

### Issue: Cannot find Google credentials
**Solution:** Ensure the credentials JSON file path is correct:
```python
extractor = MoneyOrderExtractor(
    credentials_path="path/to/google-credentials.json"
)
```

## Version Compatibility

- Python: 3.9+
- LangChain: 0.1.0+
- OpenAI: 1.0+
- Google Cloud Vision: 3.0+
- Supabase: 2.0+

## Tips for Developers

1. **Always use relative imports within the module**
   ```python
   # Within money_order files
   from .prompts import SYSTEM_PROMPT  # ✓ Correct
   from money_order.prompts import ...  # ✗ Avoid
   ```

2. **Use the __init__.py exports**
   ```python
   from money_order import MoneyOrderExtractor  # ✓ Clean
   from money_order.extractor import ...        # ✓ Also fine
   ```

3. **Pass customer info to AI analysis**
   ```python
   # Always provide customer_id and is_repeat_customer
   # This affects the recommendation decision
   agent.analyze_fraud(
       ml_analysis, extracted_data,
       customer_id='CUST001',           # ← Important
       is_repeat_customer=True          # ← Important
   )
   ```

4. **Check recommendation context**
   ```python
   # Different recommendations mean different things:
   # REJECT - Definitely block (high confidence fraud)
   # ESCALATE - Send to human for review (moderate risk)
   # APPROVE - Allow (low risk)
   ```
