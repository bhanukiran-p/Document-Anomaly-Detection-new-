#!/bin/bash
# Test Mock Bank Webhook Endpoints

echo "🧪 Testing Mock Bank Webhook Endpoints"
echo "========================================"
echo ""

# Base URL
BASE_URL="http://localhost:5001"

echo "1️⃣ Testing GET /webhook/bank/customers (List all customers)"
echo "-----------------------------------------------------------"
curl -X GET "${BASE_URL}/webhook/bank/customers" \
  -H "Content-Type: application/json" \
  2>/dev/null | python3 -m json.tool | head -30
echo ""
echo ""

echo "2️⃣ Testing POST /webhook/bank/accounts (Get accounts for CUST_0001)"
echo "---------------------------------------------------------------------"
curl -X POST "${BASE_URL}/webhook/bank/accounts" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST_0001"}' \
  2>/dev/null | python3 -m json.tool
echo ""
echo ""

echo "3️⃣ Testing POST /webhook/bank/transactions (Get transactions)"
echo "---------------------------------------------------------------"
curl -X POST "${BASE_URL}/webhook/bank/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "account_ids": ["ACC_0001_1"],
    "start_date": "2025-11-01",
    "end_date": "2025-12-22"
  }' \
  2>/dev/null | python3 -m json.tool | head -50
echo ""
echo ""

echo "✅ Testing complete!"
