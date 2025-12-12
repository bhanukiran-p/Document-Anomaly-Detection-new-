"""
Retrain Check Models with 30 Features
Matches the current CheckFeatureExtractor which produces 30 features
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
    sys.exit(1)


class CheckModelTrainer30:
    """Train check models with 30 features to match CheckFeatureExtractor"""

    def __init__(self):
        self.output_dir = 'check/ml/models'
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_training_data(self, n_samples=2000):
        """Generate synthetic check data with 30 features"""
        print(f"Generating {n_samples} check samples with 30 features...")

        data = []
        for i in range(n_samples):
            features = self._generate_sample()
            risk_score = self._calculate_risk_score(features)
            data.append(features + [risk_score])

        feature_names = [f'feature_{i}' for i in range(30)] + ['risk_score']
        df = pd.DataFrame(data, columns=feature_names)

        print(f"Generated {len(df)} samples")
        print(f"Risk: min={df['risk_score'].min():.1f}, max={df['risk_score'].max():.1f}, mean={df['risk_score'].mean():.1f}")

        return df

    def _generate_sample(self):
        """Generate one check sample (30 features)"""
        is_legit = random.random() < 0.7

        if is_legit:
            return self._generate_legitimate_check()
        else:
            return self._generate_fraudulent_check()

    def _generate_legitimate_check(self):
        """30-feature legitimate check"""
        return [
            1.0,  # bank_validity
            1.0,  # routing_validity
            1.0,  # account_present
            1.0,  # check_number_valid
            random.uniform(50, 5000),  # amount_numeric
            random.randint(1, 2),  # amount_category
            1.0 if random.random() < 0.3 else 0.0,  # amount_is_round
            1.0,  # payer_present
            1.0,  # payee_present
            1.0 if random.random() < 0.85 else 0.0,  # payee_address
            1.0,  # date_present
            0.0,  # future_date
            random.uniform(0, 90),  # date_age_days
            1.0 if random.random() < 0.9 else 0.0,  # signature
            1.0 if random.random() < 0.5 else 0.0,  # memo
            1.0,  # exact_amount_match
            random.uniform(0.85, 1.0),  # amount_parsing_confidence
            0.0,  # suspicious_amount
            1.0,  # date_format_consistency
            1.0 if random.random() < 0.15 else 0.0,  # weekend_holiday
            random.randint(0, 1),  # critical_missing_count
            random.uniform(0.8, 1.0),  # field_quality_score
            1.0,  # bank_routing_match
            random.uniform(0.7, 1.0),  # check_number_pattern
            1.0,  # address_valid
            random.uniform(0.8, 1.0),  # name_consistency
            1.0,  # signature_required
            random.uniform(0.0, 0.3),  # check_type_risk
            random.uniform(0.8, 1.0),  # text_quality_score
            1.0 if random.random() < 0.3 else 0.0,  # endorsement
        ]

    def _generate_fraudulent_check(self):
        """30-feature fraudulent check"""
        fraud_type = random.choice(['invalid_bank', 'missing_fields', 'date_fraud', 'amount_fraud', 'combo'])

        features = [0.5] * 30

        if fraud_type in ['invalid_bank', 'combo']:
            features[0] = 0.0  # invalid bank
            features[1] = 0.0 if random.random() < 0.5 else 1.0
            features[22] = 0.0  # bank_routing mismatch

        if fraud_type in ['missing_fields', 'combo']:
            features[7] = 0.0 if random.random() < 0.4 else 1.0  # missing payer
            features[8] = 0.0 if random.random() < 0.4 else 1.0  # missing payee
            features[13] = 0.0 if random.random() < 0.6 else 1.0  # missing signature
            features[20] = random.randint(3, 6)  # critical missing

        if fraud_type in ['date_fraud', 'combo']:
            features[11] = 1.0  # future date
            features[12] = random.uniform(180, 500)  # very old

        if fraud_type in ['amount_fraud', 'combo']:
            features[4] = random.uniform(10000, 50000)  # high amount
            features[5] = random.randint(3, 4)
            features[15] = 0.0  # amount mismatch
            features[17] = 1.0  # suspicious

        # Common fraud indicators
        features[21] = random.uniform(0.3, 0.6)  # low field quality
        features[28] = random.uniform(0.3, 0.6)  # low text quality

        return features

    def _calculate_risk_score(self, features):
        """Calculate ground truth risk (0-100)"""
        risk = 0.0

        if features[0] < 0.5:  # invalid bank
            risk += 25
        if features[1] < 0.5:  # invalid routing
            risk += 20
        if features[11] > 0.5:  # future date
            risk += 40
        if features[13] < 0.5:  # missing signature
            risk += 50
        if features[15] < 0.5:  # amount mismatch
            risk += 15
        if features[17] > 0.5:  # suspicious amount
            risk += 15

        # Missing fields
        risk += min(30, features[20] * 10)

        # Old check
        if features[12] > 180:
            risk += 10

        # High amount
        if features[4] > 10000:
            risk += 10

        return min(100.0, risk)

    def train_models(self, df):
        """Train RF and XGBoost"""
        X = df.drop('risk_score', axis=1).values
        y = df['risk_score'].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print("\nScaling features...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train RF
        print("\n" + "="*60)
        print("Training Random Forest (30 features)...")
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

        rf_pred = rf_model.predict(X_test_scaled)
        print(f"Test MSE: {mean_squared_error(y_test, rf_pred):.4f}")
        print(f"Test R²:  {r2_score(y_test, rf_pred):.4f}")

        # Train XGBoost
        print("\n" + "="*60)
        print("Training XGBoost (30 features)...")
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

        xgb_pred = xgb_model.predict(X_test_scaled)
        print(f"Test MSE: {mean_squared_error(y_test, xgb_pred):.4f}")
        print(f"Test R²:  {r2_score(y_test, xgb_pred):.4f}")

        # Ensemble
        ensemble_pred = 0.4 * rf_pred + 0.6 * xgb_pred
        print("\n" + "="*60)
        print("Ensemble (40% RF + 60% XGB)...")
        print("="*60)
        print(f"Test MSE: {mean_squared_error(y_test, ensemble_pred):.4f}")
        print(f"Test R²:  {r2_score(y_test, ensemble_pred):.4f}")

        return rf_model, xgb_model, scaler

    def save_models(self, rf_model, xgb_model, scaler):
        """Save with correct filenames"""
        print("\n" + "="*60)
        print("Saving Models (30 features)")
        print("="*60)

        joblib.dump(rf_model, os.path.join(self.output_dir, 'check_random_forest.pkl'))
        print(f"✓ check_random_forest.pkl")

        joblib.dump(xgb_model, os.path.join(self.output_dir, 'check_xgboost.pkl'))
        print(f"✓ check_xgboost.pkl")

        joblib.dump(scaler, os.path.join(self.output_dir, 'check_feature_scaler.pkl'))
        print(f"✓ check_feature_scaler.pkl")

        print("\n" + "="*60)
        print("SUCCESS! Check models ready (30 features)")
        print("="*60)


def main():
    trainer = CheckModelTrainer30()
    df = trainer.generate_training_data(n_samples=2000)
    rf, xgb, scaler = trainer.train_models(df)
    trainer.save_models(rf, xgb, scaler)


if __name__ == '__main__':
    main()
