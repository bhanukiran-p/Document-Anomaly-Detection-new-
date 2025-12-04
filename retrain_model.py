"""
Quick Script to Retrain Fraud Detection Model
Use this when your data has a different fraud distribution than the training data
"""

import requests
import sys

# Configuration
API_URL = "http://localhost:5001/api"

def retrain_model(csv_file_path):
    """
    Retrain the fraud detection model using your labeled dataset

    Requirements:
    - CSV file must have an 'is_fraud' column with 0/1 labels
    - CSV must have 'amount' column
    - Should have other transaction features (merchant, category, etc.)
    """
    print("=" * 80)
    print("FRAUD DETECTION MODEL RETRAINING")
    print("=" * 80)
    print()
    print(f"Uploading dataset: {csv_file_path}")
    print()

    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': (csv_file_path, f, 'text/csv')}

            print("Sending retraining request to API...")
            response = requests.post(f"{API_URL}/real-time/retrain-model", files=files, timeout=300)

        if response.status_code != 200:
            print(f"[FAIL] HTTP {response.status_code}")
            print(response.text)
            return False

        result = response.json()

        if not result.get('success'):
            print(f"[FAIL] {result.get('error')}")
            print(result.get('message'))
            return False

        print("[SUCCESS] Model retrained successfully!")
        print()
        print("=" * 80)
        print("TRAINING RESULTS")
        print("=" * 80)

        training_results = result.get('training_results', {})

        print(f"Total samples:       {training_results.get('samples')}")
        print(f"Fraud samples:       {training_results.get('fraud_samples')}")
        print(f"Legitimate samples:  {training_results.get('legitimate_samples')}")
        print(f"Fraud percentage:    {training_results.get('fraud_percentage')}%")
        print()

        metrics = training_results.get('metrics', {})
        if metrics:
            print("Model Performance:")
            print(f"  Accuracy:  {metrics.get('accuracy', 0):.3f}")
            print(f"  Precision: {metrics.get('precision', 0):.3f}")
            print(f"  Recall:    {metrics.get('recall', 0):.3f}")
            print(f"  F1-Score:  {metrics.get('f1_score', 0):.3f}")
            print(f"  AUC:       {metrics.get('auc', 0):.3f}")

        print()
        print(f"Trained at: {training_results.get('trained_at')}")
        print()
        print("=" * 80)
        print("[INFO] The model is now ready to use!")
        print("[INFO] Upload your test dataset in the Real-Time Analysis page to see improved results.")
        print("=" * 80)

        return True

    except FileNotFoundError:
        print(f"[FAIL] File not found: {csv_file_path}")
        return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Could not connect to API server")
        print("Make sure the backend server is running on http://localhost:5001")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python retrain_model.py <path_to_csv_file>")
        print()
        print("Example:")
        print('  python retrain_model.py "C:\\Users\\user\\Desktop\\my_fraud_data.csv"')
        print()
        print("Requirements:")
        print("  - CSV must have 'is_fraud' column (0 = legitimate, 1 = fraud)")
        print("  - CSV must have 'amount' column")
        print("  - Backend server must be running on http://localhost:5001")
        sys.exit(1)

    csv_file = sys.argv[1]
    success = retrain_model(csv_file)

    sys.exit(0 if success else 1)
