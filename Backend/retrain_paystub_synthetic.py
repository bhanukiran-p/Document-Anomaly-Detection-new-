"""
Force paystub model retraining with 100% synthetic data
This ensures balanced 50/50 legitimate/fraudulent training set
"""

import sys
import os
import logging

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from training.paystub_model_retrainer import PaystubModelRetrainer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("=" * 80)
    print("PAYSTUB MODEL RETRAINING - USING 100% SYNTHETIC DATA")
    print("=" * 80)
    print()

    retrainer = PaystubModelRetrainer()

    # Generate synthetic data (50% legitimate, 50% fraudulent)
    print("Generating balanced synthetic data (50% legitimate, 50% fraud)...")
    synthetic_df = retrainer.generate_synthetic_data(n_samples=1000)

    # Show distribution
    print(f"\nGenerated {len(synthetic_df)} samples")
    print(f"Risk score distribution:")
    print(synthetic_df['risk_score'].describe())
    print(f"\nLegitimate samples (risk < 30): {len(synthetic_df[synthetic_df['risk_score'] < 30])}")
    print(f"Fraud samples (risk >= 70): {len(synthetic_df[synthetic_df['risk_score'] >= 70])}")

    # Force use synthetic data by passing empty real data
    print("\n" + "=" * 80)
    print("Starting retraining with synthetic data...")
    print("=" * 80)

    # Call the parent class retrain method directly
    from training.automated_retraining import DocumentModelRetrainer

    # Prepare data
    feature_cols = [col for col in synthetic_df.columns if col != 'risk_score']
    X = synthetic_df[feature_cols].values
    y = synthetic_df['risk_score'].values

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=(y > 50).astype(int)
    )

    # Train ensemble
    rf_model, xgb_model, scaler, metrics = retrainer.train_ensemble_model(
        X_train, y_train, X_test, y_test
    )

    # Save models to production directory
    import joblib
    import json
    from datetime import datetime

    prod_dir = retrainer.production_models_dir
    print(f"\nSaving models to: {prod_dir}")

    # Save models
    rf_path = os.path.join(prod_dir, 'paystub_random_forest.pkl')
    xgb_path = os.path.join(prod_dir, 'paystub_xgboost.pkl')
    scaler_path = os.path.join(prod_dir, 'paystub_feature_scaler.pkl')
    metadata_path = os.path.join(prod_dir, 'paystub_model_metadata_latest.json')

    joblib.dump(rf_model, rf_path)
    joblib.dump(xgb_model, xgb_path)
    joblib.dump(scaler, scaler_path)

    # Save metadata
    metadata = {
        "document_type": "paystub",
        "model_type": "ensemble_random_forest_xgboost",
        "ensemble_weights": {
            "random_forest": 0.4,
            "xgboost": 0.6
        },
        "feature_names": feature_cols,
        "feature_count": len(feature_cols),
        "model_paths": {
            "random_forest": "paystub_random_forest.pkl",
            "xgboost": "paystub_xgboost.pkl"
        },
        "scaler_path": "paystub_feature_scaler.pkl",
        "trained_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "training_data": "synthetic_balanced",
        "training_samples": len(synthetic_df),
        "metrics": metrics
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 80)
    print("RETRAINING COMPLETE!")
    print("=" * 80)
    print(f"\nModel Performance Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")

    print(f"\nModels saved to:")
    print(f"  - {rf_path}")
    print(f"  - {xgb_path}")
    print(f"  - {scaler_path}")
    print(f"  - {metadata_path}")
    print("\nThe model should now detect fraud patterns properly!")
