# Fresh Start Guide - Training From Scratch

## Model Training Has Been Reset

All previous models have been deleted. You're starting fresh with a clean slate!

## What Was Deleted

- `transaction_fraud_model.pkl` - Fraud detection model
- `transaction_scaler.pkl` - Feature scaler
- `fraud_type_classifier.pkl` - Fraud type classifier
- `fraud_type_encoder.pkl` - Fraud type label encoder
- `training_data.csv` - Old training data
- `model_metadata.json` - Old training metrics

## How to Train with Your New Dataset

### Step 1: Prepare Your Dataset

Your CSV file must have these columns:

**Required:**
- `amount` - Transaction amount (numeric)
- `is_fraud` - Fraud label (0 = legitimate, 1 = fraud)

**Recommended (for better accuracy):**
- `merchant` - Merchant name
- `category` - Transaction category
- `timestamp` - Transaction timestamp
- `customer_id` - Customer identifier
- `account_balance` - Account balance
- `transaction_type` - Type of transaction
- `currency` - Transaction currency
- `home_country` - Customer's home country
- `transaction_country` - Transaction location
- `login_country` - Login location

**Optional (for fraud type classification):**
- `fraud_reason` or `fraud_type` - Specific fraud type for fraudulent transactions

### Step 2: Train the Model

**Option 1: Use the Retraining Script**

```bash
python retrain_model.py "path\to\your\dataset.csv"
```

Example:
```bash
python retrain_model.py "C:\Users\bhanukaranP\Desktop\my_fraud_data.csv"
```

**Option 2: Upload in Real-Time Analysis Page**

1. Go to Real-Time Analysis page in the frontend
2. Upload your labeled CSV file
3. The system will automatically train a new model on first upload
4. The model will be saved for future use

### Step 3: Verify the Training

After training, you'll see:

- Total samples used for training
- Fraud percentage in training data
- Model performance metrics:
  - Accuracy
  - Precision
  - Recall
  - F1-Score
  - AUC

### Step 4: Test the Model

1. Upload a test dataset (can be the same dataset or new data)
2. Check that the fraud detection rate matches your data's fraud distribution
3. Review fraud type classifications

## What Happens During Training

### First Upload (Auto-Training)

When you upload your first dataset:

1. **Fraud Detection Model Training:**
   - Extracts 40+ features from your transactions
   - Trains Random Forest + Gradient Boosting ensemble
   - Uses your actual fraud labels (`is_fraud` column)
   - Saves the trained model

2. **Fraud Type Classifier Training:**
   - Only trains if you have `fraud_reason` or `fraud_type` column
   - Uses 25+ engineered features
   - Learns to classify fraud into specific types
   - Falls back to rule-based classification if not trained

### Subsequent Uploads

- Uses the trained model for predictions
- No retraining unless you use the retrain endpoint

## Expected Results

With a properly labeled dataset:

| Your Data | Expected Detection |
|-----------|-------------------|
| 60% fraud | ~60% detected |
| 50% fraud | ~50% detected |
| 10% fraud | ~10% detected |
| 5% fraud  | ~5% detected  |

The model will adapt to your data's fraud distribution!

## Example Dataset Structure

```csv
transaction_id,customer_id,amount,merchant,category,timestamp,is_fraud,fraud_reason
TXN001,CUST123,150.00,Amazon,Shopping,2024-01-01 10:30:00,0,
TXN002,CUST456,5000.00,Wire Transfer,Transfer,2024-01-01 02:15:00,1,Night-time activity
TXN003,CUST789,75.50,McDonald's,Food,2024-01-01 12:00:00,0,
TXN004,CUST123,2500.00,Crypto Exchange,Cryptocurrency,2024-01-01 14:20:00,1,High-risk merchant
```

## Tips for Best Results

1. **Label Quality:** Ensure your `is_fraud` labels are accurate
2. **Feature Richness:** Include as many columns as possible (merchant, category, location, etc.)
3. **Fraud Types:** If you want specific fraud type classification, include `fraud_reason` column
4. **Data Balance:** The model will adapt to any fraud distribution (5%, 50%, 60%, etc.)
5. **Data Size:** More data = better model (minimum 100 transactions, recommended 1,000+)

## Troubleshooting

### Error: "Missing required column: amount"
- Make sure your CSV has an `amount` column

### Error: "Missing fraud labels"
- Make sure your CSV has an `is_fraud` column with 0/1 values

### Low Detection Rate
- Retrain the model using your actual data distribution
- Ensure your training data's fraud % matches your real-world fraud %

### Wrong Fraud Types
- Include `fraud_reason` column in your training data
- Use the 15 standard fraud types (see MODEL_ACCURACY_ISSUE.md)
- Or let the system learn from your custom fraud type labels

## Standard Fraud Types

The system can classify fraud into these types:

1. Suspicious login
2. Account takeover
3. Unusual location
4. Unusual device
5. Velocity abuse
6. Transaction burst
7. High-risk merchant
8. Unusual amount
9. New payee spike
10. Cross-border anomaly
11. Card-not-present risk
12. Money mule pattern
13. Structuring / smurfing
14. Round-dollar pattern
15. Night-time activity

## Ready to Start!

Your system is now ready for fresh training. Simply upload your labeled dataset and the system will automatically train on your data's distribution.

Backend is running on: http://localhost:5001
Frontend is running on: http://localhost:3002

Good luck with your new dataset!
