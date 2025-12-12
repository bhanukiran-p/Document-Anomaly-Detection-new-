# Document Types & ML Models Summary

Complete breakdown of all document types and their ML model architectures.

---

## 📊 **Complete Model Architecture Summary**

| Document Type | Model Architecture | Ensemble? | Feature Count | Model Files | Training Script |
|--------------|-------------------|-----------|---------------|-------------|----------------|
| **Checks** | Random Forest + XGBoost | ✅ Yes (40% RF, 60% XGB) | 30 features | `check_random_forest.pkl`<br>`check_xgboost.pkl`<br>`check_feature_scaler.pkl` | `training/retrain_check_models_30features.py` |
| **Money Orders** | Random Forest + XGBoost | ✅ Yes (40% RF, 60% XGB) | 30 features | `money_order_random_forest.pkl`<br>`money_order_xgboost.pkl`<br>`money_order_feature_scaler.pkl` | `training/train_money_order_models.py` |
| **Paystubs** | Random Forest + XGBoost | ✅ Yes (40% RF, 60% XGB) | 18 features | `paystub_random_forest.pkl`<br>`paystub_xgboost.pkl`<br>`paystub_feature_scaler.pkl` | `training/train_paystub_models.py` |
| **Bank Statements** | Random Forest + XGBoost | ✅ Yes (40% RF, 60% XGB) | 35 features | `bank_statement_random_forest.pkl`<br>`bank_statement_xgboost.pkl`<br>`bank_statement_feature_scaler.pkl` | `training/train_risk_model.py` |

---

## 📋 **Detailed Breakdown by Document Type**

### 1. **CHECKS** ✅

**Model Architecture:**
- **Ensemble**: Random Forest + XGBoost
- **Weighting**: 40% RF + 60% XGB
- **Features**: 30 features

**Model Files Location:**
- `Backend/check/ml/models/check_random_forest.pkl`
- `Backend/check/ml/models/check_xgboost.pkl`
- `Backend/check/ml/models/check_feature_scaler.pkl`

**Training Script:**
- `Backend/training/retrain_check_models_30features.py`
- Generates synthetic training data (2000 samples)

**Code Reference:**
- `Backend/check/ml/check_fraud_detector.py`
- Line 155-156: `ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)`

**Fallback Behavior:**
- Has mock/heuristic fallback if models not loaded

---

### 2. **MONEY ORDERS** ✅

**Model Architecture:**
- **Ensemble**: Random Forest + XGBoost
- **Weighting**: 40% RF + 60% XGB
- **Features**: 30 features

**Model Files Location:**
- `Backend/money_order/ml/models/money_order_random_forest.pkl`
- `Backend/money_order/ml/models/money_order_xgboost.pkl`
- `Backend/money_order/ml/models/money_order_feature_scaler.pkl`

**Training Script:**
- `Backend/training/train_money_order_models.py`
- Generates synthetic training data (2000 samples)

**Code Reference:**
- `Backend/money_order/ml/money_order_fraud_detector.py`
- Line 222-223: `base_fraud_score = 0.4 * rf_score + 0.6 * xgb_score`

**Fallback Behavior:**
- Has mock/heuristic fallback if models not loaded

---

### 3. **PAYSTUBS** ✅

**Model Architecture:**
- **Ensemble**: Random Forest + XGBoost
- **Weighting**: 40% RF + 60% XGB
- **Features**: 18 features

**Model Files Location:**
- `Backend/paystub/ml/models/paystub_random_forest.pkl`
- `Backend/paystub/ml/models/paystub_xgboost.pkl`
- `Backend/paystub/ml/models/paystub_feature_scaler.pkl`
- `Backend/paystub/ml/models/paystub_model_metadata_latest.json`

**Training Script:**
- `Backend/training/train_paystub_models.py` (dedicated script)
- Generates synthetic training data (2000 samples)
- Trains both RF and XGBoost models

**Code Reference:**
- `Backend/paystub/ml/paystub_fraud_detector.py`
- Line 3: "Uses ensemble of Random Forest + XGBoost models"
- Line 234: `base_fraud_score = 0.4 * rf_score + 0.6 * xgb_score`
- Returns ensemble scores: `random_forest`, `xgboost`, `ensemble`, `adjusted`

**Fallback Behavior:**
- **NO Fallback**: Raises RuntimeError if models not loaded (models REQUIRED)

---

### 4. **BANK STATEMENTS** ✅

**Model Architecture:**
- **Ensemble**: Random Forest + XGBoost
- **Weighting**: 40% RF + 60% XGB
- **Features**: 35 features

**Model Files Location:**
- `Backend/bank_statement/ml/models/bank_statement_random_forest.pkl`
- `Backend/bank_statement/ml/models/bank_statement_xgboost.pkl`
- `Backend/bank_statement/ml/models/bank_statement_feature_scaler.pkl`

**Training Script:**
- `Backend/training/train_risk_model.py` (has separate `train_bank_statement_models()` function)
- Generates synthetic training data (2000 samples)

**Code Reference:**
- `Backend/bank_statement/ml/bank_statement_fraud_detector.py`
- Line 181-182: `ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)`

**Fallback Behavior:**
- **NO Fallback**: Raises RuntimeError if models not loaded (models REQUIRED)

---

## 🔑 **Key Insights**

### Model Architecture Distribution:
- **ALL 4** document types use **RF + XGBoost ensemble** (Checks, Money Orders, Paystubs, Bank Statements)
- **Consistent architecture**: All use 40% RF + 60% XGB weighting

### Training Data:
- **ALL** document types use **synthetic/dummy training data** (not real documents)
- Training scripts generate synthetic samples with risk score distributions

### Model Requirements:
- **Paystubs & Bank Statements**: Models are REQUIRED (no fallback)
- **Checks & Money Orders**: Have mock/heuristic fallback if models not loaded

### Feature Counts:
- **Checks**: 30 features
- **Money Orders**: 30 features
- **Paystubs**: 18 features (fewest)
- **Bank Statements**: 35 features (most)

---

## 📝 **Training Commands**

To train models for each document type:

```bash
# Train Checks (RF + XGBoost ensemble)
python Backend/training/retrain_check_models_30features.py

# Train Money Orders (RF + XGBoost ensemble)
python Backend/training/train_money_order_models.py

# Train Paystubs (RF + XGBoost ensemble)
python Backend/training/train_paystub_models.py

# Train Bank Statements (RF + XGBoost ensemble)
python Backend/training/train_risk_model.py
# Note: Bank statements are trained separately via train_bank_statement_models() function
```

---

## 🎯 **Summary**

| Aspect | Checks | Money Orders | Paystubs | Bank Statements |
|--------|--------|--------------|----------|-----------------|
| **Model Type** | RF + XGB | RF + XGB | RF + XGB | RF + XGB |
| **Ensemble** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Features** | 30 | 30 | 18 | 35 |
| **Fallback** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Training Data** | Synthetic | Synthetic | Synthetic | Synthetic |

**Key Finding:** All document types now use RF + XGBoost ensemble architecture with consistent 40% RF + 60% XGB weighting, ensuring uniform fraud detection capabilities across all document types.
