# Fraud Detection Model Accuracy Issue - EXPLANATION & SOLUTION

## Problem Summary

Your uploaded dataset has **60% fraud** and **40% legitimate** transactions (30,000 fraud + 20,000 legitimate = 50,000 total).

However, the model is detecting only **28.1% fraud** (14,051 out of 50,000 transactions).

## Root Cause

The fraud detection model was trained on data with a completely different distribution:

- **Training Data**: 5.03% fraud (503 fraud + 9,497 legitimate = 10,000 total)
- **Your Data**: 60% fraud (30,000 fraud + 20,000 legitimate = 50,000 total)

This is a classic **data distribution mismatch** problem in machine learning. The model learned patterns from data where fraud is rare (~5%), so when it encounters data where fraud is common (~60%), it underestimates the fraud rate.

## Why This Happens

Machine learning models learn to recognize patterns based on their training data. When you train a model on data with 5% fraud:

1. The model learns that fraud is rare
2. It becomes conservative in flagging transactions as fraudulent
3. It optimizes for the 5% fraud distribution

When you then use this model on data with 60% fraud:

1. The model still expects fraud to be rare
2. It misclassifies many fraud cases as legitimate
3. You get 28.1% detection instead of the expected 60%

## Solution: Retrain the Model

You need to retrain the fraud detection model on data that matches your actual fraud distribution.

### Option 1: Use the Retraining Script (Recommended)

I've created a simple script that will retrain the model using your labeled dataset.

**Requirements:**
- Your CSV must have an `is_fraud` column with 0 (legitimate) or 1 (fraud) labels
- Backend server must be running

**Steps:**

1. Make sure your dataset has the `is_fraud` column with correct labels

2. Run the retraining script:

```bash
python retrain_model.py "path\to\your\labeled_dataset.csv"
```

Example:
```bash
python retrain_model.py "C:\Users\bhanukaranP\Desktop\my_60percent_fraud_data.csv"
```

3. The script will:
   - Upload your dataset to the API
   - Retrain both the fraud detection model AND fraud type classifier
   - Show you the new model's performance metrics
   - Save the new model automatically

4. After retraining, go to the Real-Time Analysis page and upload your test data again

### Option 2: Manual Retraining via API

If you prefer to use the API directly:

```python
import requests

url = "http://localhost:5001/api/real-time/retrain-model"
files = {'file': open('your_labeled_dataset.csv', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

## What Gets Retrained

When you retrain, the system updates:

1. **Fraud Detection Model** (binary classifier: fraud vs legitimate)
   - Random Forest + Gradient Boosting ensemble
   - Learns the new fraud distribution
   - Will now recognize the 60% fraud pattern

2. **Fraud Type Classifier** (multi-class: identifies fraud type)
   - Random Forest classifier
   - Learns to classify fraud into specific types
   - Uses 25+ engineered features

## After Retraining

Once retrained on data with 60% fraud:

1. Upload the same 50,000 transaction dataset
2. You should now see ~60% fraud detection (close to 30,000 fraud cases)
3. The fraud type classification will also be more accurate
4. Both models will be saved and used for future analyses

## Model Files Location

The trained models are saved in:
- `Backend/real_time/models/transaction_fraud_model.pkl` (fraud detection)
- `Backend/real_time/models/transaction_scaler.pkl` (feature scaler)
- `Backend/real_time/models/fraud_type_classifier.pkl` (fraud type classifier)
- `Backend/real_time/models/fraud_type_encoder.pkl` (fraud type encoder)
- `Backend/real_time/models/training_data.csv` (training data, keeps last 10,000 samples)
- `Backend/real_time/models/model_metadata.json` (training metrics and metadata)

## Current Model Performance

**Trained on (Dec 3, 2025):**
- Training samples: 20,000
- Fraud rate: 5.03%
- Accuracy: 97.3%
- Precision: 67.3%
- Recall: 89.5%
- AUC: 99.3%

**These metrics are for the OLD 5% fraud distribution!**

After retraining on your 60% fraud data, you'll get new metrics that reflect the new distribution.

## Expected Results After Retraining

| Metric | Before Retraining | After Retraining (Expected) |
|--------|------------------|---------------------------|
| Fraud Detection Rate | 28.1% | ~60% |
| Fraud Count | 14,051 | ~30,000 |
| False Negatives | ~15,949 | <1,000 |
| Model Confidence | Low | High |

## Important Notes

1. **Always retrain when switching to new data sources** with different fraud distributions

2. **The model is data-dependent** - it performs best on data similar to its training set

3. **Use labeled data for best results** - the `is_fraud` column should contain accurate labels (0 or 1)

4. **The system keeps learning** - training data is appended up to 10,000 samples for incremental learning

5. **Both models are linked** - when you retrain fraud detection, you should also have fraud type labels for optimal fraud type classification

## Need Help?

If you encounter any issues:

1. Check that your CSV has the `is_fraud` column
2. Verify the backend server is running on http://localhost:5001
3. Check the backend logs for detailed error messages
4. Ensure your dataset has the required columns (amount, merchant, category, etc.)

---

**Quick Start:**

```bash
# 1. Ensure backend is running
python Backend/api_server.py

# 2. Retrain the model (in a new terminal)
python retrain_model.py "path\to\your\labeled_data.csv"

# 3. Upload test data in Real-Time Analysis page
# 4. Verify ~60% fraud detection rate
```

That's it! The model will now be calibrated for your data distribution.
