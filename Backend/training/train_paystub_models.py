"""
Train Paystub Fraud Detection Models
Creates Random Forest + XGBoost ensemble for paystub fraud detection
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


class PaystubModelTrainer:
    """Train fraud detection models for paystubs"""

    def __init__(self):
        self.output_dir = 'paystub/ml/models'
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_training_data(self, n_samples=2000):
        """Generate synthetic paystub training data (18 features)"""
        print(f"Generating {n_samples} paystub samples...")

        data = []
        
        # Target distribution:
        # - Legitimate (0-30%): 40% of samples
        # - Slightly suspicious (31-70%): 40% of samples
        # - Highly suspicious (71-100%): 20% of samples
        
        for i in range(n_samples):
            # Determine target risk category
            category_rand = random.random()
            if category_rand < 0.4:
                # Legitimate paystubs (0-30%)
                target_min, target_max = 0, 30
            elif category_rand < 0.8:
                # Slightly suspicious (31-70%)
                target_min, target_max = 31, 70
            else:
                # Highly suspicious (71-100%)
                target_min, target_max = 71, 100
            
            # Generate features based on target risk level
            if target_max <= 30:
                # Legitimate: Most fields present, no errors
                has_company = random.random() > 0.05  # 95% have company
                has_employee = random.random() > 0.03  # 97% have employee
                has_gross = random.random() > 0.02     # 98% have gross
                has_net = random.random() > 0.02      # 98% have net
                has_date = random.random() > 0.05      # 95% have date
                tax_error_prob = 0.05  # 5% have tax errors
                text_quality_min = 0.7
            elif target_max <= 70:
                # Slightly suspicious: Some fields missing, some errors
                has_company = random.random() > 0.15   # 85% have company
                has_employee = random.random() > 0.20  # 80% have employee
                has_gross = random.random() > 0.10     # 90% have gross
                has_net = random.random() > 0.10       # 90% have net
                has_date = random.random() > 0.25      # 75% have date
                tax_error_prob = 0.20  # 20% have tax errors
                text_quality_min = 0.4
            else:
                # Highly suspicious: Many fields missing, many errors
                has_company = random.random() > 0.40    # 60% have company
                has_employee = random.random() > 0.50  # 50% have employee
                has_gross = random.random() > 0.30     # 70% have gross
                has_net = random.random() > 0.30       # 70% have net
                has_date = random.random() > 0.50      # 50% have date
                tax_error_prob = 0.60  # 60% have tax errors
                text_quality_min = 0.2
            
            # Generate amounts
            if has_gross and has_net:
                gross = random.uniform(1000, 10000)
                # For high-risk, sometimes make net >= gross (tax error)
                if random.random() < tax_error_prob:
                    net = random.uniform(gross, gross * 1.2)  # Net >= gross (impossible!)
                    tax_error = 1
                else:
                    net = random.uniform(500, gross * 0.9)  # Normal: net < gross
                    tax_error = 0
            else:
                gross = 0
                net = 0
                tax_error = 1 if random.random() < tax_error_prob else 0
            
            missing_fields = sum([not has_company, not has_employee, not has_gross, not has_net, not has_date])
            text_quality = random.uniform(text_quality_min, 1.0)
            
            # Tax features - legitimate paystubs should have taxes
            if target_max <= 30:
                # Legitimate: Should have taxes (90% have federal, 80% state, 100% SS/Medicare)
                has_federal_tax = random.random() > 0.10
                has_state_tax = random.random() > 0.20
                has_social_security = True  # Always present for W-2
                has_medicare = True  # Always present for W-2
                # Tax amounts: typically 15-30% of gross
                tax_percentage = random.uniform(0.15, 0.30)
            elif target_max <= 70:
                # Suspicious: Some missing taxes
                has_federal_tax = random.random() > 0.30  # 70% have federal
                has_state_tax = random.random() > 0.40  # 60% have state
                has_social_security = random.random() > 0.20  # 80% have SS
                has_medicare = random.random() > 0.20  # 80% have Medicare
                tax_percentage = random.uniform(0.05, 0.25)  # Lower tax percentage
            else:
                # Highly suspicious: Many missing taxes
                has_federal_tax = random.random() > 0.60  # 40% have federal
                has_state_tax = random.random() > 0.70  # 30% have state
                has_social_security = random.random() > 0.50  # 50% have SS
                has_medicare = random.random() > 0.50  # 50% have Medicare
                tax_percentage = random.uniform(0.0, 0.15)  # Very low or zero taxes
            
            # Calculate tax amounts
            total_tax_amount = gross * tax_percentage if gross > 0 else 0.0
            if not has_federal_tax:
                total_tax_amount *= 0.7  # Reduce if no federal
            if not has_state_tax:
                total_tax_amount *= 0.9  # Slight reduction
            if not has_social_security:
                total_tax_amount *= 0.85  # SS is ~6.2%
            if not has_medicare:
                total_tax_amount *= 0.985  # Medicare is ~1.45%
            
            total_tax_amount = min(total_tax_amount, 50000.0)  # Cap at $50k
            tax_to_gross_ratio = (total_tax_amount / gross) if gross > 0 else 0.0
            tax_to_gross_ratio = min(tax_to_gross_ratio, 1.0)
            
            # Proportion features
            net_to_gross_ratio = (net / gross) if gross > 0 else 0.0
            net_to_gross_ratio = min(net_to_gross_ratio, 1.0)
            
            deduction_amount = gross - net
            deduction_percentage = (deduction_amount / gross) if gross > 0 else 0.0
            deduction_percentage = min(deduction_percentage, 1.0)
            
            # Calculate risk score (0-100)
            risk_score = 0.0
            
            # Missing fields: up to 35 points
            risk_score += (missing_fields / 5) * 35
            
            # Tax error: +30 points (critical issue)
            if tax_error:
                risk_score += 30
            
            # Low text quality: up to 20 points
            if text_quality < 0.5:
                risk_score += 20
            elif text_quality < 0.7:
                risk_score += 10
            elif text_quality < 0.8:
                risk_score += 5
            
            # Zero withholding: up to 25 points
            if gross > 1000:
                if not has_federal_tax and not has_state_tax and not has_social_security and not has_medicare:
                    risk_score += 25
                elif total_tax_amount < gross * 0.02:
                    risk_score += 15
                elif not has_social_security or not has_medicare:
                    risk_score += 10
            
            # Unrealistic proportions: up to 20 points
            if gross > 0:
                if net_to_gross_ratio > 0.95:
                    risk_score += 20
                elif net_to_gross_ratio > 0.90:
                    risk_score += 10
                if tax_to_gross_ratio < 0.02 and gross > 1000:
                    risk_score += 15
                if deduction_percentage > 0.50:
                    risk_score += 10
            
            # Missing critical fields: up to 10 points
            if not has_company:
                risk_score += 5
            if not has_employee:
                risk_score += 5
            
            # Random variation
            risk_score += random.uniform(-5, 5)
            
            # Cap at 100
            risk_score = max(0, min(100, risk_score))
            
            # Build features list (18 features matching PaystubFeatureExtractor)
            features = [
                1 if has_company else 0,  # has_company
                1 if has_employee else 0,  # has_employee
                1 if has_gross else 0,  # has_gross
                1 if has_net else 0,  # has_net
                1 if has_date else 0,  # has_date
                gross,  # gross_pay
                net,  # net_pay
                tax_error,  # tax_error
                text_quality,  # text_quality
                missing_fields,  # missing_fields_count
                1 if has_federal_tax else 0,  # has_federal_tax
                1 if has_state_tax else 0,  # has_state_tax
                1 if has_social_security else 0,  # has_social_security
                1 if has_medicare else 0,  # has_medicare
                total_tax_amount,  # total_tax_amount
                tax_to_gross_ratio,  # tax_to_gross_ratio
                net_to_gross_ratio,  # net_to_gross_ratio
                deduction_percentage,  # deduction_percentage
                risk_score  # risk_score (target)
            ]
            
            data.append(features)
        
        # Create DataFrame with proper feature names (matching PaystubFeatureExtractor)
        feature_names = [
            'has_company', 'has_employee', 'has_gross', 'has_net', 'has_date',
            'gross_pay', 'net_pay', 'tax_error', 'text_quality', 'missing_fields_count',
            'has_federal_tax', 'has_state_tax', 'has_social_security', 'has_medicare',
            'total_tax_amount', 'tax_to_gross_ratio', 'net_to_gross_ratio', 'deduction_percentage',
            'risk_score'
        ]
        
        df = pd.DataFrame(data, columns=feature_names)
        
        print(f"Generated {len(df)} samples")
        print(f"Risk distribution: min={df['risk_score'].min():.1f}, "
              f"max={df['risk_score'].max():.1f}, mean={df['risk_score'].mean():.1f}")
        
        # Print detailed distribution
        legitimate = len(df[(df['risk_score'] >= 0) & (df['risk_score'] <= 30)])
        slightly_suspicious = len(df[(df['risk_score'] > 30) & (df['risk_score'] <= 70)])
        highly_suspicious = len(df[df['risk_score'] > 70])
        
        print(f"\nRisk Score Distribution:")
        print(f"  Legitimate (0-30%): {legitimate} samples ({legitimate/len(df)*100:.1f}%)")
        print(f"  Slightly Suspicious (31-70%): {slightly_suspicious} samples ({slightly_suspicious/len(df)*100:.1f}%)")
        print(f"  Highly Suspicious (71-100%): {highly_suspicious} samples ({highly_suspicious/len(df)*100:.1f}%)")
        
        return df

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

        return rf_model, xgb_model, scaler

    def save_models(self, rf_model, xgb_model, scaler):
        """Save models with correct filenames"""
        print("\n" + "="*60)
        print("Saving Models")
        print("="*60)

        rf_path = os.path.join(self.output_dir, 'paystub_random_forest.pkl')
        xgb_path = os.path.join(self.output_dir, 'paystub_xgboost.pkl')
        scaler_path = os.path.join(self.output_dir, 'paystub_feature_scaler.pkl')

        joblib.dump(rf_model, rf_path)
        print(f"✓ Saved: {rf_path}")

        joblib.dump(xgb_model, xgb_path)
        print(f"✓ Saved: {xgb_path}")

        joblib.dump(scaler, scaler_path)
        print(f"✓ Saved: {scaler_path}")

        # Save metadata with ensemble info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata = {
            'document_type': 'paystub',
            'model_type': 'ensemble_random_forest_xgboost',
            'ensemble_weights': {
                'random_forest': 0.4,
                'xgboost': 0.6
            },
            'feature_names': [
                'has_company', 'has_employee', 'has_gross', 'has_net', 'has_date',
                'gross_pay', 'net_pay', 'tax_error', 'text_quality', 'missing_fields_count',
                'has_federal_tax', 'has_state_tax', 'has_social_security', 'has_medicare',
                'total_tax_amount', 'tax_to_gross_ratio', 'net_to_gross_ratio', 'deduction_percentage'
            ],
            'feature_count': 18,
            'model_paths': {
                'random_forest': 'paystub_random_forest.pkl',
                'xgboost': 'paystub_xgboost.pkl'
            },
            'scaler_path': 'paystub_feature_scaler.pkl',
            'trained_at': timestamp
        }

        metadata_path = os.path.join(self.output_dir, 'paystub_model_metadata_latest.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Saved: {metadata_path}")

        print("\n" + "="*60)
        print("Training Complete!")
        print("="*60)
        print("\nPaystub fraud detector now has:")
        print("  ✓ paystub_random_forest.pkl")
        print("  ✓ paystub_xgboost.pkl")
        print("  ✓ paystub_feature_scaler.pkl")
        print("\nEnsemble ready: 40% RF + 60% XGBoost")


def main():
    print("="*60)
    print("Paystub Fraud Detection Model Training")
    print("="*60)

    trainer = PaystubModelTrainer()

    # Generate data
    df = trainer.generate_training_data(n_samples=2000)

    # Train models
    rf_model, xgb_model, scaler = trainer.train_models(df)

    # Save models
    trainer.save_models(rf_model, xgb_model, scaler)


if __name__ == '__main__':
    main()
