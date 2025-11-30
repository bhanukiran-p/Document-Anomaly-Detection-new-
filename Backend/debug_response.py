"""Quick debug to see actual response structure"""
import requests
import json

csv_file = '../dataset/staement_fraud_5000.csv'
API_URL = 'http://localhost:5001/api/real-time/analyze'

with open(csv_file, 'rb') as f:
    files = {'file': ('staement_fraud_5000.csv', f, 'text/csv')}
    response = requests.post(API_URL, files=files, timeout=120)

result = response.json()
print("Full Response Structure:")
print("=" * 70)
print(json.dumps(result, indent=2, default=str))
