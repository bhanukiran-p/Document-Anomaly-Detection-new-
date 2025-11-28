# Fix for "Network Error" Issue

## Problem
You're seeing this error:
```
[ERROR] save_uploaded_file() takes 1 positional argument but 2 were given
```

## [FIXED]
I've updated the `save_uploaded_file()` function to accept CSV files and the correct parameters.

## How to Start the System

### Step 1: Start Backend Server

**Option A: Using the batch file**
```
Double-click: start_backend.bat
```

**Option B: Using terminal**
```bash
cd "c:\Users\bhanukaranP\Desktop\DAD New\Backend"
python api_server.py
```

**You should see:**
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
 * Running on http://127.0.0.1:5001
```

**IMPORTANT: Keep this window OPEN!**

### Step 2: Test the API (Optional but Recommended)

Open a NEW terminal:
```bash
cd "c:\Users\bhanukaranP\Desktop\DAD New\Backend"
python test_api_endpoint.py
```

You should see:
```
[SUCCESS] API TEST SUCCESSFUL!
Total Transactions: 10
Fraud Detected: 1
Fraud Percentage: 10.0%
Plots Generated: 6
```

### Step 3: Start Frontend

**Option A: Using the batch file**
```
Double-click: start_frontend.bat
```

**Option B: Using terminal**
```bash
cd "c:\Users\bhanukaranP\Desktop\DAD New\Frontend"
npm start
```

Browser will open automatically at `http://localhost:3000`

## How to Use Real-Time Transaction Analysis

1. Navigate to **Real Time Transactions** page
2. **Upload CSV file** (use `sample_transactions.csv` provided)
3. **Review Preview:**
   - Total Rows
   - Total Columns
   - Estimated Fraud Transactions
   - Column Information table
   - First 10 rows of data
4. Click **"▶ Proceed to Insights"** button
5. Wait for analysis (ML model will train automatically)
6. View results with fraud statistics
7. Click **"Show Insights & Plots"** to see:
   - 6 visualization plots
   - Recommendations
   - Fraud patterns
   - Top fraud cases

## What Was Fixed

### 1. File Handler Update
**File:** `Backend/utils/file_handler.py`

**Before:**
```python
def save_uploaded_file(file):  # Only 1 parameter
    # Didn't support CSV files
```

**After:**
```python
def save_uploaded_file(file, file_type=None):  # 2 parameters
    # Now supports CSV files
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'csv'}
```

### 2. Better Error Messages
**File:** `Frontend/src/pages/RealTimeAnalysis.jsx`

Now shows helpful error when server isn't running:
```
Cannot connect to server. Please make sure the backend API
server is running on http://localhost:5001
```

## Troubleshooting

### Still Getting Network Error?
1. **Check if backend is running:**
   - Look for terminal with "Server running on: http://localhost:5001"
   - If not running, use Step 1 above

2. **Test the API directly:**
   ```bash
   cd Backend
   python test_api_endpoint.py
   ```

3. **Check port 5001:**
   ```bash
   netstat -ano | findstr :5001
   ```
   Should show something is listening on port 5001

### Different Error?
- Check Backend terminal for error messages
- Check Browser console (F12) for details
- Make sure both servers are running

### Plots Not Showing?
1. Click the **"Show Insights & Plots"** button (it toggles visibility)
2. Plots are generated as base64 images by matplotlib
3. Check browser console for any errors

## Expected Behavior

### After Upload:
1. File preview appears immediately (client-side parsing)
2. Shows statistics and data table

### After "Proceed to Insights":
1. Loading indicator appears
2. Backend processes CSV (2-5 seconds)
3. ML model trains automatically
4. Results appear with 6 stat cards

### After "Show Insights & Plots":
1. Recommendations section expands
2. Fraud patterns displayed
3. 6 plots rendered:
   - Pie chart (Fraud vs Legitimate)
   - Box plot (Amount distribution)
   - Histogram (Fraud probability)
   - Bar chart (Hourly patterns)
   - Horizontal bar (Category fraud rates)
   - Scatter plot (Amount vs Probability)

## Success Indicators

[OK] Backend shows: "Server running on: http://localhost:5001"
[OK] Frontend shows: "Compiled successfully!"
[OK] CSV upload shows preview with statistics
[OK] Analysis completes without errors
[OK] 6 plots appear when clicking "Show Insights & Plots"

---

**Need more help?**
- Run `python test_api_endpoint.py` to diagnose API issues
- Check both terminal windows for error messages
