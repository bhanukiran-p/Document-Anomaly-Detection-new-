"""
Train Money Order Fraud Detection Models
Creates Random Forest + XGBoost ensemble for money order fraud detection
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    import xgboost as xgb
except ImportError as e:
    print(f"ERROR: {e}")
    print("Install with: pip install scikit-learn xgboost")
    sys.exit(1)


class MoneyOrderModelTrainer:
    """Train fraud detection models for money orders"""

    def __init__(self):
        self.output_dir = 'money_order/ml/models'
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_training_data(self, n_samples=2000):
        """Generate synthetic money order training data"""
        print(f"Generating {n_samples} money order samples...")

        data = []
        for i in range(n_samples):
            # Generate features (30 features for money orders)
            features = self._generate_sample()

            # Calculate risk score (0-100) based on features
            risk_score = self._calculate_risk_score(features)

            data.append(features + [risk_score])

        # Create DataFrame
        feature_names = [f'feature_{i}' for i in range(30)] + ['risk_score']
        df = pd.DataFrame(data, columns=feature_names)

        print(f"Generated {len(df)} samples")
        print(f"Risk distribution: min={df['risk_score'].min():.1f}, "
              f"max={df['risk_score'].max():.1f}, mean={df['risk_score'].mean():.1f}")

        return df

    def _generate_sample(self):
        """Generate one money order sample (30 features)"""
        # 70% legitimate, 30% fraudulent
        is_legit = random.random() < 0.7

        if is_legit:
            return self._generate_legitimate_mo()
        else:
            return self._generate_fraudulent_mo()

    def _generate_legitimate_mo(self):
        """Generate legitimate money order features"""
        return [
            1.0,  # issuer_valid
            1.0,  # serial_format_valid
            1.0,  # serial_pattern_match
            random.uniform(50, 2000),  # amount_numeric
            random.randint(1, 2),  # amount_category (low-medium)
            1.0,  # amount_is_round (30% round)
            1.0,  # recipient_present
            1.0,  # sender_present
            1.0,  # date_present
            0.0,  # date_is_future
            random.uniform(0, 60),  # date_age_days
            1.0,  # signature_present
            1.0,  # exact_amount_match
            random.uniform(0.85, 1.0),  # amount_parsing_confidence
            0.0,  # suspicious_amount_pattern
            1.0,  # date_format_consistency
            random.choice([0.0, 1.0]) if random.random() < 0.15 else 0.0,  # weekend_holiday (15%)
            0.0,  # date_amount_correlation
            0.0,  # critical_missing_score
            random.uniform(0.8, 1.0),  # field_quality_score
            1.0,  # issuer_specific_validation
            random.uniform(0.8, 1.0),  # check_number_pattern (reused for MO)
            1.0,  # address_validation
            random.uniform(0.85, 1.0),  # name_consistency
            1.0,  # signature_requirement
            random.uniform(0.0, 0.2),  # type_risk_factor
            random.uniform(0.85, 1.0),  # text_quality_score
            0.0,  # missing_fields_count
            1.0,  # endorsement_present (30%)
            random.uniform(0.8, 1.0),  # overall_confidence
        ]

    def _generate_fraudulent_mo(self):
        """Generate fraudulent money order features"""
        fraud_type = random.choice(['invalid_issuer', 'missing_fields', 'date_fraud', 'amount_fraud', 'combo'])

        features = [0.5] * 30  # Start with neutral

        if fraud_type in ['invalid_issuer', 'combo']:
            features[0] = 0.0  # invalid issuer
            features[1] = 0.0 if random.random() < 0.5 else 1.0  # invalid serial
            features[2] = random.uniform(0.2, 0.5)  # poor pattern match

        if fraud_type in ['missing_fields', 'combo']:
            features[6] = 0.0 if random.random() < 0.4 else 1.0  # missing recipient
            features[7] = 0.0 if random.random() < 0.4 else 1.0  # missing sender
            features[11] = 0.0 if random.random() < 0.6 else 1.0  # missing signature
            features[27] = random.randint(2, 5)  # missing fields count

        if fraud_type in ['date_fraud', 'combo']:
            features[9] = 1.0  # future date
            features[10] = random.uniform(180, 500)  # very old or weird age

        if fraud_type in ['amount_fraud', 'combo']:
            features[3] = random.uniform(5000, 25000)  # high amount
            features[4] = random.randint(3, 4)  # high category
            features[12] = 0.0  # amount mismatch
            features[14] = 1.0  # suspicious pattern

        # Common fraud indicators
        features[18] = random.uniform(0.3, 0.8)  # poor critical score
        features[19] = random.uniform(0.3, 0.6)  # low field quality
        features[26] = random.uniform(0.3, 0.6)  # low text quality
        features[29] = random.uniform(0.4, 0.7)  # low confidence

        return features

    def _calculate_risk_score(self, features):
        """Calculate ground truth risk score (0-100)"""
        risk = 0.0

        # Invalid issuer/serial
        if features[0] < 0.5:  # invalid issuer
            risk += 25
        if features[1] < 0.5:  # invalid serial
            risk += 20

        # Date issues
        if features[9] > 0.5:  # future date
            risk += 40
        if features[10] > 180:  # very old
            risk += 10

        # Missing fields
        risk += min(30, features[27] * 10)

        # Amount issues
        if features[3] > 5000:  # high amount
            risk += 10
        if features[12] < 0.5:  # amount mismatch
            risk += 15
        if features[14] > 0.5:  # suspicious pattern
            risk += 10

        # Missing signature
        if features[11] < 0.5:
            risk += 50

        # Poor quality
        if features[19] < 0.5:  # low field quality
            risk += 15
        if features[26] < 0.5:  # low text quality
            risk += 15

        return min(100.0, risk)

    def train_models(self, df):
        """Train RF and XGBoost models"""
        # Separate features and target
        X = df.drop('risk_score', axis=1).values
        y = df['risk_score'].values

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale
        print("\nScaling features...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train Random Forest
        print("\n" + "="*60)
        print("Training Random Forest Regressor...")
        print("="*60)
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)

        rf_pred_test = rf_model.predict(X_test_scaled)
        rf_mse = mean_squared_error(y_test, rf_pred_test)
        rf_r2 = r2_score(y_test, rf_pred_test)
        print(f"Test MSE: {rf_mse:.4f}")
        print(f"Test R²:  {rf_r2:.4f}")

        # Train XGBoost
        print("\n" + "="*60)
        print("Training XGBoost Regressor...")
        print("="*60)
        xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train_scaled, y_train)

        xgb_pred_test = xgb_model.predict(X_test_scaled)
        xgb_mse = mean_squared_error(y_test, xgb_pred_test)
        xgb_r2 = r2_score(y_test, xgb_pred_test)
        print(f"Test MSE: {xgb_mse:.4f}")
        print(f"Test R²:  {xgb_r2:.4f}")

        # Ensemble evaluation
        print("\n" + "="*60)
        print("Ensemble Performance (40% RF + 60% XGB)")
        print("="*60)
        ensemble_pred = 0.4 * rf_pred_test + 0.6 * xgb_pred_test
        ensemble_mse = mean_squared_error(y_test, ensemble_pred)
        ensemble_r2 = r2_score(y_test, ensemble_pred)
        print(f"Test MSE: {ensemble_mse:.4f}")
        print(f"Test R²:  {ensemble_r2:.4f}")

        return rf_model, xgb_model, scaler

    def save_models(self, rf_model, xgb_model, scaler):
        """Save models with correct filenames"""
        print("\n" + "="*60)
        print("Saving Models")
        print("="*60)

        rf_path = os.path.join(self.output_dir, 'money_order_random_forest.pkl')
        xgb_path = os.path.join(self.output_dir, 'money_order_xgboost.pkl')
        scaler_path = os.path.join(self.output_dir, 'money_order_feature_scaler.pkl')

        joblib.dump(rf_model, rf_path)
        print(f"✓ Saved: {rf_path}")

        joblib.dump(xgb_model, xgb_path)
        print(f"✓ Saved: {xgb_path}")

        joblib.dump(scaler, scaler_path)
        print(f"✓ Saved: {scaler_path}")

        # Save metadata
        metadata = {
            'trained_at': datetime.now().isoformat(),
            'n_features': 30,
            'model_types': {
                'random_forest': 'RandomForestRegressor',
                'xgboost': 'XGBRegressor'
            }
        }

        import json
        metadata_path = os.path.join(self.output_dir, 'money_order_model_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Saved: {metadata_path}")

        print("\n" + "="*60)
        print("Training Complete!")
        print("="*60)
        print("\nMoney order fraud detector now has:")
        print("  ✓ money_order_random_forest.pkl")
        print("  ✓ money_order_xgboost.pkl")
        print("  ✓ money_order_feature_scaler.pkl")
        print("\nEnsemble ready: 40% RF + 60% XGBoost")


def main():
    print("="*60)
    print("Money Order Fraud Detection Model Training")
    print("="*60)

    trainer = MoneyOrderModelTrainer()

    # Generate data
    df = trainer.generate_training_data(n_samples=2000)

    # Train models
    rf_model, xgb_model, scaler = trainer.train_models(df)

    # Save models
    trainer.save_models(rf_model, xgb_model, scaler)


if __name__ == '__main__':
    main()
