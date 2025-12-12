"""
Train Bank Statement Fraud Detection Models
Creates Random Forest + XGBoost ensemble for bank statement fraud detection
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import random
import json

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


class BankStatementModelTrainer:
    """Train fraud detection models for bank statements"""

    def __init__(self):
        self.output_dir = 'bank_statement/ml/models'
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_training_data(self, n_samples=2000):
        """Generate synthetic bank statement training data (35 features)"""
        print(f"Generating {n_samples} bank statement samples...")

        supported_banks = [
            'Bank of America', 'Chase', 'Wells Fargo', 'Citibank',
            'U.S. Bank', 'PNC Bank', 'TD Bank', 'Capital One'
        ]

        data = []

        for i in range(n_samples):
            # Determine target risk range (0-100) with BALANCED distribution
            # More legitimate samples (45%), fewer critical samples (12.5%)
            category_rand = random.random()
            if category_rand < 0.45:  # 45% legitimate (0-30%)
                target_min, target_max = 0, 30
            elif category_rand < 0.70:  # 25% medium risk (31-60%)
                target_min, target_max = 31, 60
            elif category_rand < 0.875:  # 17.5% high risk (61-85%)
                target_min, target_max = 61, 85
            else:  # 12.5% critical risk (86-100%)
                target_min, target_max = 86, 100

            # Generate features based on risk level
            if target_max <= 30:
                # Legitimate: All fields present, good quality
                bank_valid = 1.0  # Supported bank
                account_present = 1.0
                account_holder_present = 1.0
                account_type_present = 1.0
                period_start_present = 1.0
                period_end_present = 1.0
                statement_date_present = 1.0
                future_period = 0.0
                negative_ending_balance = 0.0
                balance_consistency = 1.0
                currency_present = 1.0
                suspicious_transaction_pattern = 0.0
                duplicate_transactions = 0.0
                unusual_timing = random.uniform(0.0, 0.1)  # Low weekend transactions
                critical_missing_count = random.randint(0, 1)
                field_quality = random.uniform(0.8, 1.0)
                text_quality = random.uniform(0.8, 1.0)
            elif target_max <= 60:
                # Medium risk: Some fields missing, some issues
                bank_valid = random.choice([1.0, 0.0])  # 50% unsupported
                account_present = random.choice([1.0, 0.0])  # 50% missing
                account_holder_present = random.choice([1.0, 0.0])  # 50% missing
                account_type_present = random.choice([1.0, 0.0])
                period_start_present = random.choice([1.0, 0.0])
                period_end_present = random.choice([1.0, 0.0])
                statement_date_present = random.choice([1.0, 0.0])
                future_period = random.choice([0.0, 1.0])  # 50% future
                negative_ending_balance = random.choice([0.0, 1.0])  # 50% negative
                balance_consistency = random.uniform(0.3, 0.7)
                currency_present = random.choice([1.0, 0.0])
                suspicious_transaction_pattern = random.choice([0.0, 1.0])
                # Duplicate transactions - MEDIUM IMPACT: Three levels (0.0, 0.5, 1.0)
                # 0.0 = no duplicates, 0.5 = single duplicate, 1.0 = multiple duplicates
                duplicate_choice = random.choice([0.0, 0.5, 1.0])
                duplicate_transactions = duplicate_choice
                unusual_timing = random.uniform(0.1, 0.3)
                critical_missing_count = random.randint(2, 4)
                field_quality = random.uniform(0.5, 0.8)
                text_quality = random.uniform(0.5, 0.8)
            elif target_max <= 85:
                # High risk: Many fields missing, many issues
                bank_valid = random.choice([1.0, 0.0, 0.0])  # 67% unsupported
                account_present = random.choice([1.0, 0.0, 0.0])  # 67% missing
                account_holder_present = random.choice([1.0, 0.0, 0.0])  # 67% missing
                account_type_present = random.choice([1.0, 0.0, 0.0])
                period_start_present = random.choice([1.0, 0.0, 0.0])
                period_end_present = random.choice([1.0, 0.0, 0.0])
                statement_date_present = random.choice([1.0, 0.0, 0.0])
                future_period = random.choice([0.0, 1.0, 1.0])  # 67% future
                negative_ending_balance = random.choice([0.0, 1.0, 1.0])  # 67% negative
                balance_consistency = random.uniform(0.0, 0.5)
                currency_present = random.choice([1.0, 0.0, 0.0])
                suspicious_transaction_pattern = random.choice([0.0, 1.0, 1.0])
                # Duplicate transactions - MEDIUM IMPACT: Three levels (0.0, 0.5, 1.0)
                duplicate_choice = random.choice([0.0, 0.5, 0.5, 1.0, 1.0])  # More likely to have duplicates
                duplicate_transactions = duplicate_choice
                unusual_timing = random.uniform(0.3, 0.6)
                critical_missing_count = random.randint(4, 6)
                field_quality = random.uniform(0.3, 0.6)
                text_quality = random.uniform(0.3, 0.6)
            else:
                # Critical risk: Most fields missing, severe issues
                bank_valid = 0.0  # Unsupported
                account_present = random.choice([1.0, 0.0, 0.0, 0.0])  # 75% missing
                account_holder_present = 0.0  # Missing
                account_type_present = random.choice([1.0, 0.0, 0.0, 0.0])
                period_start_present = random.choice([1.0, 0.0, 0.0, 0.0])
                period_end_present = random.choice([1.0, 0.0, 0.0, 0.0])
                statement_date_present = random.choice([1.0, 0.0, 0.0, 0.0])
                future_period = 1.0  # Future
                negative_ending_balance = random.choice([0.0, 1.0, 1.0, 1.0])  # 75% negative
                balance_consistency = random.uniform(0.0, 0.3)
                currency_present = random.choice([1.0, 0.0, 0.0, 0.0])
                suspicious_transaction_pattern = 1.0
                # Duplicate transactions - MEDIUM IMPACT: Three levels (0.0, 0.5, 1.0)
                duplicate_choice = random.choice([0.5, 1.0, 1.0, 1.0])  # Critical risk likely has duplicates
                duplicate_transactions = duplicate_choice
                unusual_timing = random.uniform(0.5, 1.0)
                critical_missing_count = random.randint(5, 7)
                field_quality = random.uniform(0.0, 0.4)
                text_quality = random.uniform(0.0, 0.4)

            # Generate numeric features
            beginning_balance = random.uniform(0, 1000000) if account_present else 0.0
            ending_balance = random.uniform(-5000, 1000000) if account_present else 0.0
            if negative_ending_balance == 1.0:
                ending_balance = random.uniform(-10000, -100)

            total_credits = random.uniform(0, 500000) if account_present else 0.0
            total_debits = random.uniform(0, 500000) if account_present else 0.0

            # Balance consistency calculation
            if balance_consistency < 0.5:
                # Make balance inconsistent
                expected_ending = beginning_balance + total_credits - total_debits
                ending_balance = expected_ending + random.uniform(-1000, 1000) * (1 - balance_consistency)

            period_age_days = random.uniform(0, 365) if period_end_present else 0.0
            transaction_count = random.randint(0, 1000) if account_present else 0
            avg_transaction_amount = random.uniform(0, 50000) if transaction_count > 0 else 0.0
            max_transaction_amount = random.uniform(0, 100000) if transaction_count > 0 else 0.0
            balance_change = ending_balance - beginning_balance

            # Transaction pattern features
            large_transaction_count = random.randint(0, 50) if transaction_count > 0 else 0
            if suspicious_transaction_pattern == 1.0:
                large_transaction_count = random.randint(10, 50)

            # Round number transactions - MEDIUM IMPACT: Generate raw count, will be normalized/2 in feature extractor
            # Generate raw count (0-100), but training will use normalized values (0-50)
            round_number_transactions_raw = random.randint(0, 100) if transaction_count > 0 else 0
            # Normalize by dividing by 2 to match updated feature extractor logic
            round_number_transactions = round_number_transactions_raw / 2.0
            date_format_valid = 1.0 if period_start_present else 0.0
            period_length_days = random.uniform(0, 365) if (period_start_present and period_end_present) else 0.0
            transaction_date_consistency = random.uniform(0.5, 1.0) if transaction_count > 0 else 0.5
            account_number_format_valid = 1.0 if account_present else 0.0
            name_format_valid = 1.0 if account_holder_present else 0.0
            balance_volatility = random.uniform(0.0, 10.0) if beginning_balance > 0 else 0.0
            credit_debit_ratio = (total_credits / total_debits) if total_debits > 0 else (total_credits if total_credits > 0 else 0.0)
            credit_debit_ratio = min(credit_debit_ratio, 100.0)

            # Calculate risk score based on features
            risk_score = 0.0

            # Balance volatility: REDUCED IMPACT - up to 12 points (10-12% of total)
            # Normalize volatility (0-10 range) to contribution (0-12 points)
            if balance_volatility > 0:
                # Scale volatility to 0-12 points: volatility of 5.0+ contributes max 12 points
                volatility_contribution = min((balance_volatility / 5.0) * 12, 12)
                risk_score += volatility_contribution

            # Missing critical fields: up to 40 points
            risk_score += (critical_missing_count / 7) * 40

            # Unsupported bank: +30 points
            if bank_valid == 0.0:
                risk_score += 30

            # Missing account holder: +25 points
            if account_holder_present == 0.0:
                risk_score += 25

            # Missing account number: +20 points
            if account_present == 0.0:
                risk_score += 20

            # Future period: +25 points
            if future_period == 1.0:
                risk_score += 25

            # Negative balance: +20 points
            if negative_ending_balance == 1.0:
                risk_score += 20

            # Balance inconsistency: REDUCED IMPACT - up to 12 points (10-12% of total)
            if balance_consistency < 0.5:
                risk_score += (1 - balance_consistency) * 12

            # Suspicious transaction patterns: up to 20 points
            if suspicious_transaction_pattern == 1.0:
                risk_score += 20

            # Duplicate transactions - MEDIUM IMPACT: Reduced scoring
            # Single duplicate (0.5): +8 points, Multiple duplicates (1.0): +12 points
            if duplicate_transactions >= 1.0:
                risk_score += 12  # Multiple duplicates
            elif duplicate_transactions >= 0.5:
                risk_score += 8   # Single duplicate (reduced impact)

            # Round number transactions - REDUCED IMPACT: ~5% of total score
            # Only add points if there are many round numbers (20+ in raw count, 10+ normalized)
            if round_number_transactions >= 10.0:  # Normalized threshold (20+ raw)
                risk_score += min((round_number_transactions - 10.0) / 10.0 * 5, 5)  # Up to 5 points (reduced from 10)

            # Low field quality: up to 15 points
            if field_quality < 0.5:
                risk_score += (1 - field_quality) * 15

            # Low text quality: up to 10 points
            if text_quality < 0.5:
                risk_score += (1 - text_quality) * 10

            # Unusual timing: up to 10 points
            if unusual_timing > 0.3:
                risk_score += unusual_timing * 10

            # No transactions: +10 points
            if transaction_count == 0:
                risk_score += 10

            # Add noise
            risk_score += random.uniform(-5, 5)
            risk_score = max(0, min(100, risk_score))

            # CRITICAL: Force risk score to match target category to ensure balanced distribution
            # This ensures the training data has the distribution we want (45% legitimate, 12.5% critical)
            if target_max <= 30:
                # Legitimate: Force to 0-30% range
                if risk_score > 30:
                    risk_score = random.uniform(0, 30)
            elif target_min >= 31 and target_max <= 60:
                # Medium risk: Force to 31-60% range
                if risk_score < 31 or risk_score > 60:
                    risk_score = random.uniform(31, 60)
            elif target_min >= 61 and target_max <= 85:
                # High risk: Force to 61-85% range
                if risk_score < 61 or risk_score > 85:
                    risk_score = random.uniform(61, 85)
            else:  # target_min >= 86
                # Critical risk: Force to 86-100% range
                if risk_score < 86:
                    risk_score = random.uniform(86, 100)

            # Build features dictionary with all 35 features (matching bank_statement_feature_extractor.py)
            features = {
                # Basic features (1-20)
                'bank_validity': bank_valid,
                'account_number_present': account_present,
                'account_holder_present': account_holder_present,
                'account_type_present': account_type_present,
                'beginning_balance': min(abs(beginning_balance), 1000000.0),
                'ending_balance': min(abs(ending_balance), 1000000.0),
                'total_credits': min(abs(total_credits), 1000000.0),
                'total_debits': min(abs(total_debits), 1000000.0),
                'period_start_present': period_start_present,
                'period_end_present': period_end_present,
                'statement_date_present': statement_date_present,
                'future_period': future_period,
                'period_age_days': min(period_age_days, 365.0),
                'transaction_count': min(transaction_count, 1000.0),
                'avg_transaction_amount': min(abs(avg_transaction_amount), 50000.0),
                'max_transaction_amount': min(abs(max_transaction_amount), 100000.0),
                'balance_change': min(abs(balance_change), 1000000.0),
                'negative_ending_balance': negative_ending_balance,
                'balance_consistency': balance_consistency,
                'currency_present': currency_present,
                # Advanced features (21-35)
                'suspicious_transaction_pattern': suspicious_transaction_pattern,
                'large_transaction_count': min(large_transaction_count, 50.0),
                'round_number_transactions': min(round_number_transactions, 50.0),  # Normalized (0-50 range)
                'date_format_valid': date_format_valid,
                'period_length_days': min(period_length_days, 365.0),
                'critical_missing_count': float(critical_missing_count),
                'field_quality': field_quality,
                'transaction_date_consistency': transaction_date_consistency,
                'duplicate_transactions': duplicate_transactions,
                'unusual_timing': unusual_timing,
                'account_number_format_valid': account_number_format_valid,
                'name_format_valid': name_format_valid,
                'balance_volatility': min(balance_volatility, 10.0),
                'credit_debit_ratio': min(credit_debit_ratio, 100.0),
                'text_quality': text_quality,
                # Target
                'risk_score': risk_score
            }

            data.append(features)

        df = pd.DataFrame(data)
        print(f"Generated {len(df)} samples")
        print(f"Risk score distribution: min={df['risk_score'].min():.1f}, max={df['risk_score'].max():.1f}, mean={df['risk_score'].mean():.1f}")

        # Print detailed distribution
        legitimate = len(df[(df['risk_score'] >= 0) & (df['risk_score'] <= 30)])
        slightly_suspicious = len(df[(df['risk_score'] > 30) & (df['risk_score'] <= 60)])
        highly_suspicious = len(df[(df['risk_score'] > 60) & (df['risk_score'] <= 85)])
        critical = len(df[df['risk_score'] > 85])

        print(f"\nRisk Score Distribution:")
        print(f"  Legitimate (0-30%): {legitimate} samples ({legitimate/len(df)*100:.1f}%)")
        print(f"  Slightly Suspicious (31-60%): {slightly_suspicious} samples ({slightly_suspicious/len(df)*100:.1f}%)")
        print(f"  Highly Suspicious (61-85%): {highly_suspicious} samples ({highly_suspicious/len(df)*100:.1f}%)")
        print(f"  Critical (86-100%): {critical} samples ({critical/len(df)*100:.1f}%)")

        return df

    def train_models(self, df):
        """Train RF and XGBoost models"""
        # Feature names matching bank_statement_feature_extractor.py
        feature_cols = [
            # Basic features (1-20)
            'bank_validity', 'account_number_present', 'account_holder_present', 'account_type_present',
            'beginning_balance', 'ending_balance', 'total_credits', 'total_debits',
            'period_start_present', 'period_end_present', 'statement_date_present', 'future_period',
            'period_age_days', 'transaction_count', 'avg_transaction_amount', 'max_transaction_amount',
            'balance_change', 'negative_ending_balance', 'balance_consistency', 'currency_present',
            # Advanced features (21-35)
            'suspicious_transaction_pattern', 'large_transaction_count', 'round_number_transactions',
            'date_format_valid', 'period_length_days', 'critical_missing_count', 'field_quality',
            'transaction_date_consistency', 'duplicate_transactions', 'unusual_timing',
            'account_number_format_valid', 'name_format_valid', 'balance_volatility',
            'credit_debit_ratio', 'text_quality'
        ]

        # Separate features and target
        X = df[feature_cols].values
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
            n_estimators=100,
            max_depth=10,
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
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
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

        return rf_model, xgb_model, scaler, feature_cols

    def save_models(self, rf_model, xgb_model, scaler, feature_names):
        """Save models with correct filenames"""
        print("\n" + "="*60)
        print("Saving Models")
        print("="*60)

        rf_path = os.path.join(self.output_dir, 'bank_statement_random_forest.pkl')
        xgb_path = os.path.join(self.output_dir, 'bank_statement_xgboost.pkl')
        scaler_path = os.path.join(self.output_dir, 'bank_statement_feature_scaler.pkl')

        joblib.dump(rf_model, rf_path)
        print(f"✓ Saved: {rf_path}")

        joblib.dump(xgb_model, xgb_path)
        print(f"✓ Saved: {xgb_path}")

        joblib.dump(scaler, scaler_path)
        print(f"✓ Saved: {scaler_path}")

        # Save metadata with ensemble info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata = {
            'document_type': 'bank_statement',
            'model_type': 'ensemble_random_forest_xgboost',
            'ensemble_weights': {
                'random_forest': 0.4,
                'xgboost': 0.6
            },
            'feature_names': feature_names,
            'feature_count': 35,
            'model_paths': {
                'random_forest': 'bank_statement_random_forest.pkl',
                'xgboost': 'bank_statement_xgboost.pkl'
            },
            'scaler_path': 'bank_statement_feature_scaler.pkl',
            'trained_at': timestamp
        }

        metadata_path = os.path.join(self.output_dir, 'bank_statement_model_metadata_latest.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Saved: {metadata_path}")

        print("\n" + "="*60)
        print("Training Complete!")
        print("="*60)
        print("\nBank statement fraud detector now has:")
        print("  ✓ bank_statement_random_forest.pkl")
        print("  ✓ bank_statement_xgboost.pkl")
        print("  ✓ bank_statement_feature_scaler.pkl")
        print("\nEnsemble ready: 40% RF + 60% XGBoost")


def main():
    print("="*60)
    print("Bank Statement Fraud Detection Model Training")
    print("="*60)

    trainer = BankStatementModelTrainer()

    # Generate data
    df = trainer.generate_training_data(n_samples=2000)

    # Train models
    rf_model, xgb_model, scaler, feature_names = trainer.train_models(df)

    # Save models
    trainer.save_models(rf_model, xgb_model, scaler, feature_names)


if __name__ == '__main__':
    main()
