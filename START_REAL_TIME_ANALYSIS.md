# Real-Time Transaction Analysis - Quick Start Guide

## Prerequisites
- Python 3.13+ installed
- Node.js and npm installed
- All dependencies installed

## Step 1: Start the Backend API Server

Open a terminal in the `Backend` folder and run:

```bash
cd "c:\Users\bhanukaranP\Desktop\DAD New\Backend"
python api_server.py
```

You should see:
```
============================================================
XFORIA DAD API Server
============================================================
Server running on: http://localhost:5001
API Endpoints:
  - GET  /api/health
  - POST /api/check/analyze
  - POST /api/paystub/analyze
  - POST /api/money-order/analyze
  - POST /api/bank-statement/analyze
  - POST /api/real-time/analyze
============================================================
```

**Keep this terminal window open** - the server must remain running.

## Step 2: Start the Frontend React App

Open a **NEW** terminal in the `Frontend` folder and run:

```bash
cd "c:\Users\bhanukaranP\Desktop\DAD New\Frontend"
npm start
```

The React app will open in your browser at `http://localhost:3000`

## Step 3: Use the Real-Time Transaction Analysis

1. Click on **"Real Time Transactions"** button on the transaction type page
2. Upload a CSV file (drag & drop or browse)
3. **Review the preview** showing:
   - Total Rows, Columns, Fraud Transactions, Date Range
   - Column Information table
   - First 10 rows of data
4. Click **"Proceed to Insights"** button to analyze
5. View the analysis results with fraud statistics
6. Click **"Show Insights & Plots"** to see:
   - Fraud vs Legitimate pie chart
   - Amount distribution box plots
   - Fraud probability histogram
   - Hourly transaction patterns
   - Category-based fraud analysis
   - Scatter plots
   - Recommendations
   - Fraud patterns detected

## Test CSV File

Create a file called `sample_transactions.csv` with this content:

```csv
transaction_id,customer_id,amount,merchant,category,timestamp,location,account_balance,card_type
TXN001,CUST12345,45.99,Amazon,retail,2024-01-15 14:30:00,New York,2500.00,credit
TXN002,CUST67890,1250.00,Crypto Exchange,cryptocurrency,2024-01-15 23:45:00,London,5000.00,debit
TXN003,CUST12345,12.50,Starbucks,food,2024-01-16 08:15:00,New York,2450.00,credit
TXN004,CUST54321,850.00,Best Buy,retail,2024-01-16 11:20:00,Los Angeles,3200.00,credit
TXN005,CUST67890,5000.00,Wire Transfer,wire_transfer,2024-01-16 02:30:00,London,4500.00,debit
TXN006,CUST12345,35.75,Uber,travel,2024-01-16 18:45:00,New York,2415.00,credit
TXN007,CUST99999,2500.00,Casino Royal,gambling,2024-01-17 03:15:00,Las Vegas,1000.00,credit
TXN008,CUST54321,67.89,Whole Foods,food,2024-01-17 09:30:00,Los Angeles,3100.00,credit
TXN009,CUST12345,150.00,Shell Gas Station,utilities,2024-01-17 16:00:00,New York,2265.00,debit
TXN010,CUST88888,9999.99,Unknown Merchant 123,retail,2024-01-17 04:20:00,Unknown,500.00,credit
```

## Troubleshooting

### Network Error
**Problem**: "Network Error" when clicking "Analyze Transactions"

**Solution**:
1. Make sure the backend server is running (Step 1)
2. Check that it's running on `http://localhost:5001`
3. Verify the frontend is configured to use `http://localhost:5001/api`

### Port Already in Use
**Problem**: Port 5001 or 3000 already in use

**Solution**:
- Backend: Change port in `api_server.py` (last line: `app.run(port=5001)`)
- Frontend: Will automatically use next available port

### Module Not Found Error
**Problem**: Python modules not found

**Solution**:
```bash
cd Backend
pip install flask flask-cors pandas numpy scikit-learn matplotlib seaborn joblib
```

## Features

### Pure ML Fraud Detection
- Uses **genuine machine learning** models only (no rule-based fallbacks)
- Ensemble of Random Forest (60%) + Gradient Boosting (40%)
- Automatic training using Isolation Forest for unsupervised learning
- Minimum 10 transactions required for training

### Automatic Model Training
- Trains automatically on uploaded CSV data
- Saves model to `Backend/real_time/models/`
- Keeps training history (last 10,000 records)
- Incrementally learns from new data

### Comprehensive Insights
- 6 different visualization plots
- Fraud pattern detection
- Actionable recommendations
- Top fraud cases with reasons
- Statistical analysis

## Data Storage

Training data and models are saved in:
```
Backend/real_time/models/
  ├── transaction_fraud_model.pkl    (ML model)
  ├── transaction_scaler.pkl          (Feature scaler)
  ├── training_data.csv               (Historical data)
  └── model_metadata.json             (Training metrics)
```

## System Requirements

- **Minimum**: 10 transactions in CSV file
- **Recommended**: 50+ transactions for better accuracy
- **CSV Format**: Must include at least `amount` and `merchant` columns
- **Optional columns**: customer_id, timestamp, category, location, account_balance

---

**Need Help?** Check the console logs in both terminal windows for error details.
