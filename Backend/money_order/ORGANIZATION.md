# Money Order Module Organization

All money order related files are now organized in the `Backend/money_order/` folder.

## Folder Structure

```
Backend/money_order/
├── __init__.py                    # Module exports
├── extractor.py                    # Main MoneyOrderExtractor class
├── money_order_extractor_legacy.py # Legacy file (backup)
├── README.md                       # Documentation
├── IMPORT_GUIDE.md                 # Import instructions
├── ORGANIZATION.md                 # This file
│
├── ai/                             # AI Analysis Components
│   ├── __init__.py
│   ├── fraud_analysis_agent.py    # LangChain + OpenAI fraud analysis
│   ├── prompts.py                 # System prompts and templates
│   ├── tools.py                   # DataAccessTools for LangChain
│   └── result_storage.py          # Analysis result storage
│
├── normalization/                  # Data Normalization
│   ├── __init__.py
│   ├── normalizer_factory.py     # MoneyOrderNormalizerFactory
│   ├── base_normalizer.py         # BaseNormalizer abstract class
│   ├── schema.py                  # NormalizedMoneyOrder schema
│   ├── moneygram.py              # MoneyGram normalizer
│   └── western_union.py          # Western Union normalizer
│
└── analysis_results/               # Stored analysis results (JSON files)
    └── [analysis_*.json files]
```

## Key Components

### 1. Main Extractor
- **File**: `extractor.py`
- **Class**: `MoneyOrderExtractor`
- **Purpose**: OCR extraction, ML fraud detection, AI analysis orchestration

### 2. AI Analysis
- **File**: `ai/fraud_analysis_agent.py`
- **Class**: `FraudAnalysisAgent`
- **Purpose**: LangChain + OpenAI GPT-4 fraud analysis

### 3. Normalization
- **Files**: `normalization/`
- **Purpose**: Convert issuer-specific OCR data to standardized schema
- **Supported Issuers**: Western Union, MoneyGram

### 4. Legacy File
- **File**: `money_order_extractor_legacy.py`
- **Purpose**: Old version kept as backup (uses global normalization)

## Import Examples

```python
# Main extractor
from money_order.extractor import MoneyOrderExtractor

# AI agent
from money_order.ai.fraud_analysis_agent import FraudAnalysisAgent

# Normalizers
from money_order.normalization import MoneyOrderNormalizerFactory
from money_order.normalization import MoneyGramNormalizer, WesternUnionNormalizer

# Schema
from money_order.normalization import NormalizedMoneyOrder
```

## Migration Notes

- All money order normalizers moved from `Backend/normalization/` to `Backend/money_order/normalization/`
- Legacy `money_order_extractor.py` moved to `money_order/money_order_extractor_legacy.py`
- The extractor now uses local `MoneyOrderNormalizerFactory` with fallback to global factory
- All imports updated to use local normalization module

