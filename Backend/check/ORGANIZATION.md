# Check Module Organization

## ✅ Completed Structure

All check-related code has been consolidated into the `Backend/check/` folder with complete independence from other document types.

### Module Structure

```
check/
├── check_extractor.py          # Main orchestrator
├── normalization/              # Bank-specific normalizers
├── ml/                         # Check-specific ML models
├── ai/                         # Check-specific AI agents
├── database/                   # Check-specific database operations
└── utils/                      # Check-specific utilities
```

## ✅ Independence Guarantees

1. **No shared ML models** - Check ML models are in `check/ml/`
2. **No shared AI agents** - Check AI agents are in `check/ai/`
3. **No shared database** - Check database operations are in `check/database/`
4. **No shared normalizers** - Check normalizers are in `check/normalization/`
5. **No shared utilities** - Check utilities are in `check/utils/`

## 📝 Files to Remove (Legacy)

The following files can be removed as they're now in `check/`:

### Root Level
- `Backend/check_extractor.py` (if exists)

### Other Folders
- `Backend/normalization/check_*.py` (moved to `check/normalization/`)
- `Backend/ml_models/check_*.py` (moved to `check/ml/`)
- `Backend/database/check_customer_storage.py` (moved to `check/database/`)
- `Backend/utils/check_fraud_indicators.py` (moved to `check/utils/`)
- `Backend/check_normalization/` (entire folder - moved to `check/normalization/`)
- `Backend/check_analysis/` (if exists - functionality moved to `check/`)

## 🔄 Migration Guide

### Old Imports (Deprecated)
```python
from normalization.check_normalizer_factory import CheckNormalizerFactory
from ml_models.check_fraud_detector import CheckFraudDetector
from database.check_customer_storage import CheckCustomerStorage
from utils.check_fraud_indicators import detect_check_fraud_indicators
```

### New Imports (Use These)
```python
from check.normalization import CheckNormalizerFactory
from check.ml import CheckFraudDetector
from check.database import CheckCustomerStorage
from check.utils import detect_check_fraud_indicators
```

## ✅ Verification

Run this to verify the module structure:
```python
from check import CheckExtractor, extract_check
from check.normalization import CheckNormalizerFactory
from check.ml import CheckFraudDetector, CheckFeatureExtractor
from check.ai import CheckFraudAnalysisAgent
from check.database import get_check_customer_history, CheckCustomerStorage
from check.utils import detect_check_fraud_indicators
```

All imports should work without errors.

