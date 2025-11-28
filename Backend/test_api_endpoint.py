"""
Quick test for real-time analysis API endpoint
"""
import requests
import os

# Test if server is running
API_URL = 'http://localhost:5001/api/real-time/analyze'

print("Testing Real-Time Analysis API Endpoint")
print("=" * 60)

# Check if sample CSV exists
csv_file = '../sample_transactions.csv'
if not os.path.exists(csv_file):
    print("[ERROR] Sample CSV file not found!")
    print(f"   Looking for: {os.path.abspath(csv_file)}")
    exit(1)

print(f"[OK] Found sample CSV: {csv_file}")

# Try to connect
try:
    print(f"\nTesting connection to: {API_URL}")

    with open(csv_file, 'rb') as f:
        files = {'file': ('sample_transactions.csv', f, 'text/csv')}
        response = requests.post(API_URL, files=files, timeout=60)

    print(f"[OK] Response status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n" + "=" * 60)
            print("[SUCCESS] API TEST SUCCESSFUL!")
            print("=" * 60)
            print(f"Total Transactions: {result['csv_info']['total_count']}")
            print(f"Fraud Detected: {result['fraud_detection']['fraud_count']}")
            print(f"Fraud Percentage: {result['fraud_detection']['fraud_percentage']}%")
            print(f"Plots Generated: {len(result['insights']['plots'])}")
            print("=" * 60)
        else:
            print(f"\n[ERROR] API returned error: {result.get('error')}")
    else:
        print(f"\n[ERROR] HTTP Error {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.ConnectionError:
    print("\n[ERROR] CONNECTION ERROR!")
    print("   The backend server is not running.")
    print("\nTo fix:")
    print("   1. Open a terminal")
    print("   2. Run: python api_server.py")
    print("   3. Wait for 'Server running on: http://localhost:5001'")
    print("   4. Then run this test again")

except Exception as e:
    print(f"\n[ERROR] Error: {e}")
