# Testing Real-Time Analysis with Large Dataset (5000+ rows)

## What Was Updated

I've updated the system to handle your large dataset and added **adaptive training** that automatically adjusts model parameters based on dataset size.

### Key Updates:

1. **Flexible Column Mapping** ([csv_processor.py](Backend/real_time/csv_processor.py))
   - Automatically maps `merchant_name` → `merchant`
   - Maps `transaction_date` → `timestamp`
   - Maps `account_number` → `customer_id`
   - Maps `balance_after` → `account_balance`
   - And many more variations

2. **Adaptive Model Training** ([model_trainer.py](Backend/real_time/model_trainer.py))
   - **Small datasets (<1000 rows)**: 100 estimators, depth 10/5
   - **Medium datasets (1000-5000 rows)**: 150 estimators, depth 12/6
   - **Large datasets (>5000 rows)**: 200 estimators, depth 15/8
   - Adaptive contamination rate based on statistical outlier analysis

3. **Test Scripts**:
   - [test_api_endpoint.py](Backend/test_api_endpoint.py) - Test with 10-row sample
   - [test_large_dataset.py](Backend/test_large_dataset.py) - Test with 5000-row dataset

---

## How to Test with Your Large Dataset

### Step 1: Restart Backend Server

The backend server needs to be restarted to load the updated code.

**Option A: Close and restart manually**
1. Find the terminal window running the backend server
2. Press `Ctrl+C` to stop it
3. Run: `python api_server.py`

**Option B: Kill and restart**
1. Open Command Prompt as Administrator
2. Run:
```cmd
cd "c:\Users\bhanukaranP\Desktop\DAD New\Backend"
for /f "tokens=5" %a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do taskkill /F /PID %a
python api_server.py
```

**You should see:**
```
============================================================
XFORIA DAD API Server
============================================================
Server running on: http://localhost:5001
...
============================================================
```

### Step 2: Test with Large Dataset

Open a **NEW** terminal and run:

```cmd
cd "c:\Users\bhanukaranP\Desktop\DAD New\Backend"
python test_large_dataset.py
```

**Expected Output:**
```
Testing Real-Time Analysis with Large Dataset (5000 rows)
======================================================================
[OK] Found dataset: ../dataset/staement_fraud_5000.csv
[OK] File size: 0.98 MB

[INFO] Uploading dataset to: http://localhost:5001/api/real-time/analyze
[INFO] This may take 10-30 seconds for model training...
[OK] Response received in 15-25 seconds
[OK] Response status: 200

======================================================================
[SUCCESS] LARGE DATASET ANALYSIS SUCCESSFUL!
======================================================================

Dataset Information:
  Total Transactions: 5000
  Columns: 31
  Date Range: 2024-01-01 to 2024-01-31

Fraud Detection Results:
  Model Type: ml_ensemble
  Fraudulent Transactions: XXX
  Legitimate Transactions: XXX
  Fraud Percentage: XX.XX%
  Total Amount: $XXX,XXX.XX
  Fraud Amount: $XX,XXX.XX

Model Training Metrics:
  Accuracy: 0.XXX
  Precision: 0.XXX
  Recall: 0.XXX
  F1 Score: 0.XXX
  AUC: 0.XXX

Insights Generated:
  Plots: 6
  Recommendations: X
  Fraud Patterns: X

Performance:
  Total Processing Time: 15-25 seconds
  Transactions/Second: 250-350

======================================================================

[INFO] The adaptive training parameters were successfully applied!
[INFO] With 5000 transactions, the model should have used:
       - 200 estimators (instead of 100)
       - Max depth: 15 for Random Forest, 8 for Gradient Boosting
       - Adaptive contamination rate for Isolation Forest
```

### Step 3: Monitor Backend Logs

In the backend terminal, you should see:

```
INFO:api_server:Received real-time transaction analysis request
INFO:api_server:CSV file saved: temp_uploads/staement_fraud_5000.csv
INFO:api_server:Step 1: Processing CSV file
INFO:real_time.csv_processor:Mapped column 'merchant_name' to 'merchant'
INFO:real_time.csv_processor:Mapped column 'transaction_date' to 'timestamp'
INFO:real_time.csv_processor:Mapped column 'balance_after' to 'account_balance'
INFO:real_time.csv_processor:Successfully processed 5000 transactions
INFO:api_server:Processed 5000 transactions
INFO:api_server:Step 2: Running ML fraud detection
INFO:real_time.fraud_detector:Analyzing 5000 transactions for fraud
INFO:real_time.model_trainer:Starting automatic model training with 5000 transactions
INFO:real_time.model_trainer:Using adaptive contamination rate: 0.XXX for 5000 transactions
INFO:real_time.model_trainer:Training with 200 estimators for 4000 samples
INFO:real_time.model_trainer:Model trained - Accuracy: 0.XXX, AUC: 0.XXX
INFO:api_server:Fraud detection complete: XXX/5000 fraudulent
INFO:api_server:Step 3: Generating insights and plots
INFO:real_time.insights_generator:Successfully generated insights with 6 plots
INFO:api_server:Real-time transaction analysis complete
127.0.0.1 - - [DATE] "POST /api/real-time/analyze HTTP/1.1" 200 -
```

**Key things to look for:**
- [OK] "Mapped column 'merchant_name' to 'merchant'" - Column mapping working
- [OK] "Training with 200 estimators for 4000 samples" - Adaptive training working
- [OK] "Using adaptive contamination rate" - Smart fraud detection
- [OK] "Successfully processed 5000 transactions" - All data loaded
- [OK] "Successfully generated insights with 6 plots" - Visualizations created

---

## Using in the Web Interface

Once the backend is updated and tested:

1. **Make sure backend is running** (see Step 1)
2. **Open frontend**: http://localhost:3000
3. **Navigate to**: Real Time Transactions page
4. **Upload your dataset**: `dataset/staement_fraud_5000.csv`
5. **Review preview**: Should show 5000 rows, 31 columns
6. **Click**: "▶ Proceed to Insights"
7. **Wait**: 15-25 seconds (model is training with 200 estimators)
8. **View results**: Fraud statistics with 6 cards
9. **Click**: "Show Insights & Plots"
10. **See visualizations**: 6 plots analyzing fraud patterns

---

## Performance Expectations

### Dataset Size vs Processing Time

| Rows   | Estimators | RF Depth | GB Depth | Expected Time |
|--------|------------|----------|----------|---------------|
| 10     | 100        | 10       | 5        | 1-2 seconds   |
| 100    | 100        | 10       | 5        | 2-3 seconds   |
| 1,000  | 150        | 12       | 6        | 5-8 seconds   |
| 5,000  | 200        | 15       | 8        | 15-25 seconds |
| 10,000 | 200        | 15       | 8        | 30-45 seconds |

### Model Quality

Larger datasets should see **better model performance**:
- More accurate fraud detection
- Better AUC scores (>0.85 for 5000+ rows)
- More reliable probability estimates
- Better feature importance analysis

---

## Troubleshooting

### Error: "Missing required column: 'merchant'"

**Cause**: Backend server not restarted after code update

**Fix**: Restart backend server (see Step 1)

### Error: "Insufficient data for training"

**Cause**: CSV has less than 10 rows

**Fix**: Use a dataset with at least 10 transactions

### Slow Performance (>60 seconds)

**Possible causes**:
- Very large dataset (>10,000 rows) - expected
- Low-powered computer - reduce estimators in [model_trainer.py](Backend/real_time/model_trainer.py:152-165)

**To speed up**:
Edit [model_trainer.py](Backend/real_time/model_trainer.py#L152-L165):
```python
# Reduce estimators for faster training
if n_samples > 5000:
    n_estimators = 100  # instead of 200
    max_depth_rf = 12   # instead of 15
    max_depth_gb = 6    # instead of 8
```

### No plots showing

**Cause**: Insights button not clicked

**Fix**: Click "Show Insights & Plots" button (it's a toggle)

---

## What the Adaptive Training Does

### Small Dataset (10 rows)
```python
n_estimators = 100
max_depth_rf = 10
max_depth_gb = 5
contamination ≈ 0.10 (fixed)
```
- Fast training (1-2 seconds)
- Basic model complexity
- Good for testing

### Your Dataset (5000 rows)
```python
n_estimators = 200
max_depth_rf = 15
max_depth_gb = 8
contamination ≈ 0.05-0.30 (adaptive based on outliers)
```
- Longer training (15-25 seconds)
- High model complexity
- Better accuracy and generalization
- Smart contamination rate based on data analysis

### Why This Matters

**Without adaptive training:**
- Small datasets → Overfitting with complex models
- Large datasets → Underfitting with simple models

**With adaptive training:**
- Small datasets → Simpler models that generalize better
- Large datasets → Complex models that capture patterns
- Contamination rate adapts to actual fraud prevalence in data

---

## Column Mapping Reference

Your dataset has these columns (and how they're mapped):

| Your Column              | Maps To          | Used For                    |
|--------------------------|------------------|-----------------------------|
| `amount`                 | `amount`         | [YES] Core feature             |
| `merchant_name`          | `merchant`       | [YES] Merchant analysis        |
| `transaction_date`       | `timestamp`      | [YES] Time-based features      |
| `account_number`         | `customer_id`    | [YES] Customer behavior        |
| `balance_after`          | `account_balance`| [YES] Balance ratio features   |
| `category`               | `category`       | [YES] Category risk analysis   |
| `transaction_id`         | `transaction_id` | [YES] Unique identifier        |
| `is_fraud`               | (ignored)        | Label (for evaluation only) |
| `customer_name`          | -                | Not used in ML              |
| `bank_name`              | -                | Not used in ML              |
| `opening_balance`        | -                | Not used in ML              |
| `ending_balance`         | -                | Not used in ML              |
| ... (other columns)      | -                | Not used in ML              |

**Note**: The `is_fraud` column in your dataset is the **ground truth label**. The ML model will generate its own predictions and we can compare them to see how well the unsupervised learning performed.

---

## Next Steps

1. [ ] Restart backend server
2. [ ] Run `python test_large_dataset.py`
3. [ ] Check that adaptive training is being used (200 estimators)
4. [ ] Verify 6 plots are generated
5. [ ] Try uploading in the web interface
6. [ ] Compare ML predictions with actual `is_fraud` labels

---

**Good luck! The system is now optimized for your large dataset!**
