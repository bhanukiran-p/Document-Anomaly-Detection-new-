# ML Model Training Instructions

## Overview
This system supports training ML models on dummy/example data and using them for real-time risk scoring of actual documents.

## Training Process

### Step 1: Install Dependencies
```bash
pip install scikit-learn pandas numpy
# Optional: For XGBoost (better performance)
pip install xgboost
```

### Step 2: Train Models
Run the training script to generate and train models on dummy data:

```bash
cd Backend
python train_risk_model.py
```

This will:
- Generate 2000 dummy check samples
- Generate 2000 dummy paystub samples
- Train RandomForest models for each document type
- Save models to `Backend/models/` directory

### Step 3: Model Files Created
After training, you'll have:
- `check_risk_model_latest.pkl` - Trained check risk model
- `check_scaler_latest.pkl` - Feature scaler for checks
- `check_model_metadata_latest.json` - Model metadata
- Similar files for paystub

### Step 4: Real-Time Inference
Once models are trained, the `MLRiskScorer` will automatically:
1. Load trained models on startup
2. Use ML models for risk prediction on real documents
3. Fall back to weighted scoring if model unavailable

## Model Architecture

### Features Used
**For Checks:**
- Field presence: bank_name, payee_name, amount, date, signature
- Amount value and suspicious flag
- Date validity and future date flag
- Text quality score
- Suspicious character count
- Missing fields count

**For Paystubs:**
- Field presence: company, employee, gross_pay, net_pay, date
- Gross and net pay values
- Tax calculation error flag
- Text quality
- Missing fields count

### Model Type
- **RandomForestRegressor**: Predicts continuous risk score (0-100)
- 100 trees, max depth 10
- Trained on 2000 samples, validated on 20% holdout

## Using Real Data for Training

To train on real document data:

1. **Collect Training Data:**
   - Extract features from real documents
   - Label with actual risk scores (from experts or historical data)
   - Save as CSV or JSON

2. **Modify Training Script:**
   - Replace `generate_dummy_check_data()` with data loading function
   - Load your real data
   - Train on real examples

3. **Example:**
```python
def load_real_check_data():
    # Load from CSV, database, or JSON
    df = pd.read_csv('real_checks_training_data.csv')
    return df

# In train_all_models():
df = load_real_check_data()  # Instead of generate_dummy_check_data()
```

## Model Performance

After training, you'll see:
- **MSE (Mean Squared Error)**: Lower is better
- **R² Score**: Higher is better (1.0 = perfect)
- **RMSE**: Root mean squared error
- **Sample Predictions**: Compare actual vs predicted

## Updating Models

To retrain with new data:
1. Run training script again
2. New models will be saved with timestamps
3. Latest versions will be updated automatically
4. Restart API server to load new models

## Production Deployment

For production:
1. Train models on production data
2. Validate model performance
3. Deploy model files with application
4. Monitor model performance in production
5. Retrain periodically with new data

## Troubleshooting

**No models found:**
- Models will use weighted scoring fallback
- Check `Backend/models/` directory exists
- Verify model files are present

**Model prediction errors:**
- System automatically falls back to weighted scoring
- Check feature extraction matches training format
- Verify model metadata is correct

**Poor model performance:**
- Increase training samples
- Add more features
- Try different model types (XGBoost)
- Tune hyperparameters

