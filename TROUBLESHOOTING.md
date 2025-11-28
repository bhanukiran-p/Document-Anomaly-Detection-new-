# Real-Time Transaction Analysis - Troubleshooting Guide

## Issue: "Not getting any insights"

### Quick Diagnosis

**Run this first:**
```
Double-click: DIAGNOSE.bat
```

This will tell you what's wrong!

---

## Most Common Issue: Backend Server Not Running

### Symptoms:
- [OK] CSV preview works (showing Total Rows, Columns, etc.)
- [ERROR] Nothing happens when clicking "Analyze Transactions"
- [ERROR] OR shows "Network Error" / "Cannot connect to server"

### Why This Happens:
The CSV preview works **client-side** (in your browser), but the ML analysis requires the **backend server** to be running.

### Solution:

#### Step 1: Start Backend Server

**Terminal 1:**
```bash
cd "c:\Users\bhanukaranP\Desktop\DAD New\Backend"
python api_server.py
```

**You MUST see this output:**
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
 * Serving Flask app 'api_server'
 * Debug mode: off
WARNING: This is a development server.
 * Running on http://127.0.0.1:5001
Press CTRL+C to quit
```

**IMPORTANT:** Keep this window OPEN while using the system!

#### Step 2: Verify Backend is Working

**Terminal 2 (NEW terminal):**
```bash
cd "c:\Users\bhanukaranP\Desktop\DAD New\Backend"
python test_api_endpoint.py
```

**Expected output:**
```
Testing Real-Time Analysis API Endpoint
============================================================
✓ Found sample CSV: ../sample_transactions.csv

Testing connection to: http://localhost:5001/api/real-time/analyze
✓ Response status: 200

============================================================
✓ API TEST SUCCESSFUL!
============================================================
Total Transactions: 10
Fraud Detected: 1
Fraud Percentage: 10.0%
Plots Generated: 6
============================================================
```

If you see this, your backend is working! [SUCCESS]

#### Step 3: Try Again in Browser

1. Refresh the Real-Time Analysis page
2. Upload CSV file
3. Review preview
4. Click **"▶ Proceed to Insights"**
5. Wait 2-5 seconds (model is training)
6. Should see Analysis Results with 6 stat cards
7. Click **"Show Insights & Plots"**
8. Should see 6 visualization plots

---

## What You Should See (Step by Step)

### 1. After Uploading CSV:
```
[OK] Data Preview section appears
[OK] Shows: Total Rows, Total Columns, Fraud Transactions, Date Range
[OK] Shows: Column Information table
[OK] Shows: First 10 Rows table
[OK] Shows: Two buttons (Proceed to Insights | Upload Different File)
```

### 2. After Clicking "Proceed to Insights":
```
[WAIT] Button shows "Analyzing..." (2-5 seconds)
```

Then:
```
[OK] Analysis Results section appears
[OK] Shows 6 stat cards:
   - Total Transactions
   - Fraudulent (red number)
   - Legitimate (green number)
   - Total Amount
   - Fraud Amount (red)
   - Model Type (ml_ensemble)
[OK] Shows "Top Fraud Cases" list
[OK] Shows "Show Insights & Plots" button (blue, pill-shaped)
```

### 3. After Clicking "Show Insights & Plots":
```
[OK] Detailed Insights section expands
[OK] Shows Recommendations (bullet list)
[OK] Shows Fraud Patterns Detected (orange cards)
[OK] Shows Visual Analytics with 6 plots:
   1. Fraud vs Legitimate Distribution (pie chart)
   2. Amount Distribution by Status (box plot)
   3. Fraud Probability Distribution (histogram)
   4. Hourly Transaction Patterns (bar chart)
   5. Fraud Rate by Category (horizontal bar)
   6. Amount vs Fraud Probability (scatter plot)
```

---

## Common Errors and Fixes

### Error: "Network Error"
**Cause:** Backend server not running
**Fix:** Start backend (see Step 1 above)

### Error: "save_uploaded_file() takes 1 positional argument but 2 were given"
**Cause:** Old version of file_handler.py
**Fix:** Already fixed in your code! If you still see this, restart the backend server.

### Error: "Insufficient data for training"
**Cause:** CSV has less than 10 transactions
**Fix:** Use a CSV with at least 10 transactions (sample_transactions.csv has 10)

### Error: "Failed to analyze transactions"
**Cause:** Various - check backend terminal for details
**Fix:** Look at the backend terminal window for the actual error

### No error, but nothing happens
**Cause:** Backend server crashed or not responding
**Fix:**
1. Check backend terminal for errors
2. Restart backend server (Ctrl+C, then python api_server.py)
3. Check browser console (F12) for JavaScript errors

### Plots not showing
**Cause:**
- matplotlib not installed
- OR insights button not clicked

**Fix:**
1. Click the "Show Insights & Plots" button (it toggles)
2. If still not showing, check backend terminal
3. Install matplotlib: `pip install matplotlib seaborn`

---

## Backend Terminal Checklist

When backend is running correctly, you should see:

**On Startup:**
```
[OK] Server running on: http://localhost:5001
[OK] Shows list of API endpoints
[OK] Running on http://127.0.0.1:5001
```

**When you upload CSV:**
```
[OK] INFO:api_server:Received real-time transaction analysis request
[OK] INFO:api_server:CSV file saved: temp_uploads/sample_transactions.csv
[OK] INFO:api_server:Step 1: Processing CSV file
[OK] INFO:real_time.csv_processor:Processing CSV file: temp_uploads/...
[OK] INFO:real_time.csv_processor:Successfully processed 10 transactions
[OK] INFO:api_server:Processed 10 transactions
[OK] INFO:api_server:Step 2: Running ML fraud detection
[OK] INFO:real_time.fraud_detector:Analyzing 10 transactions for fraud
[OK] INFO:real_time.model_trainer:Starting automatic model training...
[OK] INFO:real_time.model_trainer:Model trained - Accuracy: 0.XXX, AUC: 0.XXX
[OK] INFO:api_server:Fraud detection complete: X/10 fraudulent
[OK] INFO:api_server:Step 3: Generating insights and plots
[OK] INFO:real_time.insights_generator:Successfully generated insights with 6 plots
[OK] INFO:api_server:Real-time transaction analysis complete
```

**HTTP Request:**
```
127.0.0.1 - - [DATE] "POST /api/real-time/analyze HTTP/1.1" 200 -
```

If you see any errors here, that's your problem!

---

## Quick Start Checklist

- [ ] Backend server running (see "Server running on: http://localhost:5001")
- [ ] Backend terminal stays open
- [ ] Test API successful (run test_api_endpoint.py)
- [ ] Frontend running (npm start)
- [ ] Browser open to http://localhost:3000
- [ ] Navigate to Real-Time Transaction page
- [ ] Upload sample_transactions.csv
- [ ] See preview with stats
- [ ] Click "Proceed to Insights"
- [ ] See analysis results
- [ ] Click "Show Insights & Plots"
- [ ] See 6 plots

---

## Still Having Issues?

1. **Run DIAGNOSE.bat** - tells you what's wrong
2. **Check both terminals** - backend and frontend
3. **Check browser console** (F12 → Console tab)
4. **Try test_api_endpoint.py** - verifies backend works
5. **Restart everything:**
   - Close all terminals
   - Start backend fresh
   - Start frontend fresh
   - Clear browser cache (Ctrl+Shift+Delete)

---

## Expected File Structure

```
DAD New/
├── Backend/
│   ├── api_server.py          ← Run this!
│   ├── test_api_endpoint.py   ← Test with this
│   ├── real_time/
│   │   ├── __init__.py
│   │   ├── csv_processor.py
│   │   ├── fraud_detector.py
│   │   ├── model_trainer.py
│   │   └── insights_generator.py
│   └── utils/
│       └── file_handler.py    ← Fixed version with CSV support
├── Frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── RealTimeAnalysis.jsx
│   │   └── services/
│   │       └── api.js
│   └── package.json
├── sample_transactions.csv    ← Test data
├── start_backend.bat          ← Quick starter
├── start_frontend.bat         ← Quick starter
├── DIAGNOSE.bat              ← Diagnostic tool
└── TROUBLESHOOTING.md        ← This file
```

---

**Good luck! The system works - you just need both servers running! 🚀**
