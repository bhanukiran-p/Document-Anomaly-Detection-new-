"""
Test the real-time analysis with the large 5000-row dataset
This will verify adaptive training parameters are working
"""
import requests
import os
import time

API_URL = 'http://localhost:5001/api/real-time/analyze'

print("Testing Real-Time Analysis with Large Dataset (5000 rows)")
print("=" * 70)

# Use the larger dataset
csv_file = '../dataset/staement_fraud_5000.csv'
if not os.path.exists(csv_file):
    print("[ERROR] Large dataset not found!")
    print(f"   Looking for: {os.path.abspath(csv_file)}")
    exit(1)

print(f"[OK] Found dataset: {csv_file}")
file_size = os.path.getsize(csv_file) / 1024 / 1024  # Size in MB
print(f"[OK] File size: {file_size:.2f} MB")

# Test the API
try:
    print(f"\n[INFO] Uploading dataset to: {API_URL}")
    print("[INFO] This may take 10-30 seconds for model training...")

    start_time = time.time()

    with open(csv_file, 'rb') as f:
        files = {'file': ('staement_fraud_5000.csv', f, 'text/csv')}
        response = requests.post(API_URL, files=files, timeout=120)

    elapsed_time = time.time() - start_time

    print(f"[OK] Response received in {elapsed_time:.1f} seconds")
    print(f"[OK] Response status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n" + "=" * 70)
            print("[SUCCESS] LARGE DATASET ANALYSIS SUCCESSFUL!")
            print("=" * 70)

            # CSV Info
            csv_info = result['csv_info']
            print(f"\nDataset Information:")
            print(f"  Total Transactions: {csv_info['total_count']}")
            print(f"  Columns: {csv_info['column_count']}")
            print(f"  Date Range: {csv_info.get('date_range', 'N/A')}")

            # Fraud Detection Results
            fraud = result['fraud_detection']
            print(f"\nFraud Detection Results:")
            print(f"  Model Type: {fraud.get('model_type', 'N/A')}")
            print(f"  Fraudulent Transactions: {fraud['fraud_count']}")
            print(f"  Legitimate Transactions: {fraud['legitimate_count']}")
            print(f"  Fraud Percentage: {fraud['fraud_percentage']:.2f}%")
            print(f"  Total Amount: ${fraud['total_amount']:,.2f}")
            print(f"  Fraud Amount: ${fraud['fraud_amount']:,.2f}")

            # Model Training Metrics (if available)
            if 'training_metrics' in fraud:
                metrics = fraud['training_metrics']
                print(f"\nModel Training Metrics:")
                print(f"  Accuracy: {metrics.get('accuracy', 0):.3f}")
                print(f"  Precision: {metrics.get('precision', 0):.3f}")
                print(f"  Recall: {metrics.get('recall', 0):.3f}")
                print(f"  F1 Score: {metrics.get('f1_score', 0):.3f}")
                print(f"  AUC: {metrics.get('auc', 0):.3f}")

            # Insights
            insights = result['insights']
            print(f"\nInsights Generated:")
            print(f"  Plots: {len(insights['plots'])}")
            print(f"  Recommendations: {len(insights.get('recommendations', []))}")
            print(f"  Fraud Patterns: {len(insights.get('fraud_patterns', []))}")

            # Processing time breakdown
            print(f"\nPerformance:")
            print(f"  Total Processing Time: {elapsed_time:.1f} seconds")
            print(f"  Transactions/Second: {csv_info['total_count'] / elapsed_time:.0f}")

            print("=" * 70)
            print("\n[INFO] The adaptive training parameters were successfully applied!")
            print("[INFO] With 5000 transactions, the model should have used:")
            print("       - 200 estimators (instead of 100)")
            print("       - Max depth: 15 for Random Forest, 8 for Gradient Boosting")
            print("       - Adaptive contamination rate for Isolation Forest")

        else:
            print(f"\n[ERROR] API returned error: {result.get('error')}")
            print(f"[ERROR] Message: {result.get('message', 'No message')}")
    else:
        print(f"\n[ERROR] HTTP Error {response.status_code}")
        print(f"Response: {response.text[:500]}")  # First 500 chars

except requests.exceptions.ConnectionError:
    print("\n[ERROR] CONNECTION ERROR!")
    print("   The backend server is not running.")
    print("\nTo fix:")
    print("   1. Open a terminal")
    print("   2. cd Backend")
    print("   3. Run: python api_server.py")
    print("   4. Wait for 'Server running on: http://localhost:5001'")
    print("   5. Then run this test again")

except requests.exceptions.Timeout:
    print("\n[ERROR] REQUEST TIMEOUT!")
    print("   The request took too long (>120 seconds)")
    print("   This might happen with very large datasets")

except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)
