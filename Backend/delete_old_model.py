"""
Delete old trained model to force retraining with new features
"""
import os

MODEL_DIR = 'real_time/models'
files_to_delete = [
    os.path.join(MODEL_DIR, 'transaction_fraud_model.pkl'),
    os.path.join(MODEL_DIR, 'transaction_scaler.pkl'),
    os.path.join(MODEL_DIR, 'model_metadata.json')
]

for file_path in files_to_delete:
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"[OK] Deleted: {file_path}")
    else:
        print(f"[SKIP] Not found: {file_path}")

print("\n[OK] Old model files deleted. System will retrain with new features on next analysis.")
