# 🧪 API Endpoint Tester - Like FastAPI Swagger!

## ✅ Created Interactive Test Page

**Access it at:** `http://localhost:5001/api/docs/test`

## Features

✅ **Visual Interface** - Like FastAPI's Swagger UI  
✅ **Test All Endpoints** - Click buttons to test  
✅ **Edit Requests** - Modify JSON payloads  
✅ **See Responses** - Formatted JSON responses  
✅ **Color-Coded** - Success (green) vs Error (red)  

## How to Use

### **Step 1: Start the server**
```bash
cd Backend
python api_server.py
```

### **Step 2: Open in browser**
```
http://localhost:5001/api/docs/test
```

### **Step 3: Test endpoints**
Click the "Test" buttons to try each endpoint!

---

## Available Endpoints in Tester

### 1. **GET /webhook/bank/customers**
- Lists all 100 customers
- No input needed
- Click "Test" → See results

### 2. **POST /webhook/bank/accounts**
- Gets accounts for a customer
- Edit the JSON: `{"customer_id": "CUST_0001"}`
- Click "Test" → See account info

### 3. **POST /webhook/bank/transactions**
- Gets transactions with date filtering
- Edit JSON to change account IDs and dates
- Click "Test" → See transactions (NO fraud labels!)

---

## Screenshot of What You'll See

```
🏦 Mock Bank API Tester
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────┐
│ GET  /webhook/bank/customers        │
│ List all available customers        │
│                                     │
│ [Test] ←── Click here!             │
│                                     │
│ Response (200 OK)                   │
│ {                                   │
│   "count": 100,                     │
│   "customers": [...]                │
│ }                                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ POST /webhook/bank/accounts         │
│ Get accounts for a customer         │
│                                     │
│ {"customer_id": "CUST_0001"}        │
│ ↑ Edit this!                        │
│                                     │
│ [Test] ←── Click here!             │
└─────────────────────────────────────┘
```

---

## Alternative: Use curl (Command Line)

If you prefer terminal testing:

```bash
# Test customers
curl http://localhost:5001/webhook/bank/customers | python3 -m json.tool

# Test accounts
curl -X POST http://localhost:5001/webhook/bank/accounts \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST_0001"}' | python3 -m json.tool

# Test transactions
curl -X POST http://localhost:5001/webhook/bank/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "account_ids": ["ACC_0001_1"],
    "start_date": "2025-11-01",
    "end_date": "2025-12-23"
  }' | python3 -m json.tool
```

---

## Bonus: Install Postman (Optional)

For advanced testing, use Postman:
1. Download: https://www.postman.com/downloads/
2. Import endpoints from the HTML page
3. Save as collection

---

**The interactive tester is faster than curl and more convenient than Postman for quick testing!** 🚀
