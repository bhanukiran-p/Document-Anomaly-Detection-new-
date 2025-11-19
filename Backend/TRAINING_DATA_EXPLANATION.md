# How ML Model Training Works

## Overview

The ML model training system **generates synthetic training data programmatically** - it does NOT require CSV or Excel files to start. However, the training data is now **automatically saved** to CSV/Excel files for your review and future use.

## How Training Works

### 1. **Synthetic Data Generation** (No CSV/Excel Required Initially)

The training script (`train_risk_model.py`) generates dummy/synthetic data **in memory** using Python functions:

- `generate_dummy_check_data()` - Creates 2000 synthetic check samples
- `generate_dummy_paystub_data()` - Creates 2000 synthetic paystub samples

Each sample includes:
- **Features**: Field presence flags, amounts, dates, text quality scores, etc.
- **Risk Score**: Calculated ground truth risk score (0-100) based on the features

### 2. **Automatic Data Export** (NEW!)

When you run the training script, it now **automatically saves** the generated training data:

- **CSV Files**: `Backend/models/check_training_data.csv` and `Backend/models/paystub_training_data.csv`
- **Excel Files**: `Backend/models/check_training_data.xlsx` and `Backend/models/paystub_training_data.xlsx` (if openpyxl is installed)

### 3. **Model Training**

The script:
1. Generates synthetic data in memory (pandas DataFrame)
2. Saves data to CSV/Excel files (for your review)
3. Prepares features for ML training
4. Trains RandomForest models
5. Saves trained models as `.pkl` files

## Training Data Structure

### Check Training Data Columns:
- `has_bank_name` (0 or 1)
- `has_payee` (0 or 1)
- `has_amount` (0 or 1)
- `has_date` (0 or 1)
- `has_signature` (0 or 1)
- `amount_value` (numeric)
- `amount_suspicious` (0 or 1)
- `date_valid` (0 or 1)
- `date_future` (0 or 1)
- `text_quality` (0.0 to 1.0)
- `suspicious_chars` (count)
- `missing_fields_count` (count)
- `risk_score` (0-100) - **Target variable**

### Paystub Training Data Columns:
- `has_company` (0 or 1)
- `has_employee` (0 or 1)
- `has_gross` (0 or 1)
- `has_net` (0 or 1)
- `has_date` (0 or 1)
- `gross_pay` (numeric)
- `net_pay` (numeric)
- `tax_error` (0 or 1)
- `text_quality` (0.0 to 1.0)
- `missing_fields_count` (count)
- `risk_score` (0-100) - **Target variable**

## How to Run Training

```bash
cd Backend
python train_risk_model.py
```

This will:
1. Generate 2000 check samples + 2000 paystub samples
2. **Save training data to CSV/Excel** (in `Backend/models/` directory)
3. Train ML models
4. Save models to `Backend/models/` directory

## Using Real Document Data for Training

If you want to train on **real document extraction data** instead of synthetic data:

### Option 1: Load from CSV/Excel
```python
def load_real_check_data():
    # Load your real extraction data
    df = pd.read_csv('real_checks_extraction_data.csv')
    # Ensure it has the same columns as training data
    return df

# In train_all_models():
df = load_real_check_data()  # Instead of generate_dummy_check_data()
```

### Option 2: Collect Real Data Over Time
1. Extract features from real documents using the API
2. Manually label risk scores (or use historical fraud data)
3. Save to CSV/Excel
4. Load and train on real data

## Files Created After Training

After running `train_risk_model.py`, you'll have:

### Training Data Files:
- `check_training_data.csv` - All check training samples
- `check_training_data.xlsx` - Excel version (if openpyxl installed)
- `paystub_training_data.csv` - All paystub training samples
- `paystub_training_data.xlsx` - Excel version (if openpyxl installed)

### Model Files:
- `check_risk_model_latest.pkl` - Trained check risk model
- `check_scaler_latest.pkl` - Feature scaler for checks
- `check_model_metadata_latest.json` - Model metadata
- Similar files for paystub

## Why Synthetic Data?

1. **No Initial Data Required**: You can start training immediately without collecting real documents
2. **Controlled Risk Patterns**: Synthetic data includes various risk scenarios (missing fields, suspicious amounts, etc.)
3. **Privacy**: No real document data needed for initial training
4. **Scalability**: Generate as many samples as needed

## Next Steps

1. **Review Training Data**: Open the CSV/Excel files to see what features are being used
2. **Train Models**: Run `python train_risk_model.py`
3. **Use Real Data**: As you collect real document extractions, you can replace synthetic data with real data
4. **Retrain Periodically**: Update models with new real data as it becomes available

## Disabling Data Export

If you don't want to save CSV/Excel files, set environment variable:
```bash
export SAVE_TRAINING_DATA=false
python train_risk_model.py
```

Or modify the code to set `save_training_data = False` in the functions.

