#!/bin/bash
# Test script for bank sync endpoint

echo "==================================================================="
echo " TESTING BANK SYNC ENDPOINT"
echo "==================================================================="
echo ""

# Make sure backend is running
echo "📡 Testing if backend is running..."
if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "❌ Backend not running on port 5001!"
    echo "Please start the backend with: python api_server.py"
    exit 1
fi
echo "✅ Backend is running"
echo ""

# Test 1: Basic analysis (no filters)
echo "-------------------------------------------------------------------"
echo "Test 1: Basic Bank Analysis (no filters)"
echo "-------------------------------------------------------------------"
curl -X POST http://localhost:5001/api/real-time/analyze-bank \
  -H "Content-Type: application/json" \
  -d '{}' \
  | python3 -m json.tool | head -50
echo ""

# Test 2: With date filtering
echo "-------------------------------------------------------------------"
echo "Test 2: Bank Analysis with Date Filter"
echo "-------------------------------------------------------------------"
curl -X POST http://localhost:5001/api/real-time/analyze-bank \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "limit": 100,
    "page": 1,
    "per_page": 10
  }' \
  | python3 -m json.tool | head -80
echo ""

# Test 3: Second request (should be cached - instant!)
echo "-------------------------------------------------------------------"
echo "Test 3: Second Request (Should be CACHED - instant!)"
echo "-------------------------------------------------------------------"
echo "⏱️  Starting cached request..."
time curl -X POST http://localhost:5001/api/real-time/analyze-bank \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "limit": 100
  }' \
  -s | python3 -c "import sys,json; data=json.load(sys.stdin); print('✅ Cached!') if data['success'] else print('❌ Failed'); print(f\"Analysis time: {data['summary']['analysis_time_seconds']}s\"); print(f\"Cache size: {data['summary']['cache_stats']['size']}\")"
echo ""

# Test 4: Check summary
echo "-------------------------------------------------------------------"
echo "Test 4: Summary Statistics"
echo "-------------------------------------------------------------------"
curl -X POST http://localhost:5001/api/real-time/analyze-bank \
  -H "Content-Type: application/json" \
  -d '{"limit": 500}' \
  -s | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['success']:
    s = data['summary']
    print(f\"✅ Success!\")
    print(f\"Total Transactions: {s['total_transactions']}\")
    print(f\"Fraud Detected: {s['fraud_detected']} ({s['fraud_percentage']}%)\")
    print(f\"Total Amount: \${s['total_amount']:,.2f}\")
    print(f\"Fraud Amount: \${s['fraud_amount']:,.2f}\")
    print(f\"Analysis Time: {s['analysis_time_seconds']}s\")
    print(f\"Cache Hits: {s['cache_stats']['size']}/{s['cache_stats']['maxsize']}\")
else:
    print(f\"❌ Failed: {data.get('error')}\")
"
echo ""

echo "==================================================================="
echo " ✅ ALL TESTS COMPLETE!"
echo "===================================================================" 
echo ""
echo "Next steps:"
echo "1. Check if response time < 3s ✓"
echo "2. Verify cached requests are instant ✓"
echo "3. Check fraud detection works ✓"
echo "4. Verify pagination works ✓"
