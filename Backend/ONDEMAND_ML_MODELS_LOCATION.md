# On-Demand ML Model Files Location

This document outlines where the ML model files are stored for each on-demand document analysis type.

## Model File Locations

### 1. **Check Analysis Models**
**Primary Location:** `Backend/check/ml/models/`
- `check_risk_model_latest.pkl` - Random Forest model for fraud detection
- `check_scaler_latest.pkl` - Feature scaler for normalization
- `check_model_metadata_latest.json` - Model metadata

**Alternative Location:** `Backend/models/` (legacy/backup)
- `check_risk_model_latest.pkl`
- `check_scaler_latest.pkl`
- Historical versions with timestamps (e.g., `check_risk_model_20251202_185807.pkl`)

**Expected Files (if using ensemble):**
- `check_random_forest.pkl`
- `check_xgboost.pkl`
- `check_feature_scaler.pkl`

---

### 2. **Paystub Analysis Models**
**Primary Location:** `Backend/paystub/ml/models/`
- `paystub_risk_model_latest.pkl` - Random Forest Regressor model (~1.6-2.6 MB)
- `paystub_scaler_latest.pkl` - StandardScaler for feature normalization (~689 bytes)
- `paystub_model_metadata_latest.json` - Model metadata

**Alternative Location:** `Backend/models/` (legacy/backup)
- `paystub_risk_model_latest.pkl`
- `paystub_scaler_latest.pkl`
- Historical versions with timestamps

---

### 3. **Money Order Analysis Models**
**Expected Location:** `Backend/money_order/ml/models/` (directory may need to be created)
- `money_order_random_forest.pkl` - Random Forest Classifier
- `money_order_xgboost.pkl` - XGBoost Classifier
- `money_order_feature_scaler.pkl` - StandardScaler for 30 features

**Note:** This directory structure should be created if models are trained.

---

### 4. **Bank Statement Analysis Models**
**Expected Location:** `Backend/bank_statement/ml/models/` (directory may need to be created)
- `bank_statement_random_forest.pkl` - Random Forest Classifier
- `bank_statement_xgboost.pkl` - XGBoost Classifier
- `bank_statement_feature_scaler.pkl` - StandardScaler

**Note:** This directory structure should be created if models are trained.

---

## Model Loading Priority

Each document type uses a **self-contained approach**:

1. **Primary:** Looks in document-specific folder (e.g., `check/ml/models/`)
2. **Fallback:** Some may check `Backend/models/` if not found
3. **Error:** If models not found, the system will log warnings but may continue with mock/default scoring

---

## Model File Structure

All models use Python's `joblib` or `pickle` for serialization:
- `.pkl` files - Binary format containing trained models/scalers
- `.json` files - Metadata with model information (feature names, training date, etc.)

---

## Current Status

✅ **Check Models:** Available in `Backend/check/ml/models/`
✅ **Paystub Models:** Available in `Backend/paystub/ml/models/`
❌ **Money Order Models:** Directory structure exists but models may need training
❌ **Bank Statement Models:** Directory structure exists but models may need training

---

## Training Models

If models are missing, they can be trained using:
- `Backend/training/train_risk_model.py` - For risk-based models
- Document-specific training scripts in each module

