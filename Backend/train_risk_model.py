"""
ML Model Training Script for Document Risk Scoring
Trains models using dummy/example data for real-time risk assessment
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import random

# ML Libraries
try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed. Run: pip install scikit-learn")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: xgboost not installed. Run: pip install xgboost")


class RiskModelTrainer:
    """Train ML models for document risk scoring"""
    
    def __init__(self, model_type='random_forest'):
        """
        Initialize trainer
        
        Args:
            model_type: 'random_forest' or 'xgboost'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_dir = 'models'
        os.makedirs(self.model_dir, exist_ok=True)
    
    def generate_dummy_check_data(self, n_samples=1000, document_type='check') -> pd.DataFrame:
        """
        Generate dummy check data for training
        
        Args:
            n_samples: Number of training samples to generate
            
        Returns:
            DataFrame with features and risk scores
        """
        print(f"Generating {n_samples} dummy check samples...")
        
        data = []
        
        for i in range(n_samples):
            # Generate realistic check features
            has_bank_name = random.random() > 0.1  # 90% have bank name
            has_payee = random.random() > 0.05  # 95% have payee
            has_amount = random.random() > 0.02  # 98% have amount
            has_date = random.random() > 0.08  # 92% have date
            has_signature = random.random() > 0.15  # 85% have signature
            
            # Amount features
            if has_amount:
                amount = random.uniform(10, 50000)
                amount_suspicious = 1 if amount > 100000 or amount < 0 else 0
            else:
                amount = 0
                amount_suspicious = 1
            
            # Date features
            days_ago = random.randint(-30, 365)  # Some future dates
            date_valid = 1 if days_ago >= 0 else 0
            date_future = 1 if days_ago < 0 else 0
            
            # Text quality (simulated OCR confidence)
            text_quality_score = random.uniform(0.5, 1.0)
            suspicious_chars = random.randint(0, 10) if text_quality_score < 0.7 else 0
            
            # Calculate ground truth risk score (0-100)
            # This simulates what we want the model to learn
            risk_score = 0.0
            
            # Missing fields contribute to risk
            missing_fields = sum([not has_bank_name, not has_payee, not has_amount, not has_date])
            risk_score += (missing_fields / 4) * 30  # Up to 30 points
            
            # Amount anomalies
            if amount_suspicious:
                risk_score += 25
            
            # Date issues
            if date_future:
                risk_score += 15
            elif not date_valid:
                risk_score += 10
            
            # Signature missing
            if not has_signature:
                risk_score += 10
            
            # Text quality
            if text_quality_score < 0.7:
                risk_score += 10
            if suspicious_chars > 5:
                risk_score += 10
            
            # Add some noise
            risk_score += random.uniform(-5, 5)
            risk_score = max(0, min(100, risk_score))
            
            # Create feature vector
            features = {
                'has_bank_name': 1 if has_bank_name else 0,
                'has_payee': 1 if has_payee else 0,
                'has_amount': 1 if has_amount else 0,
                'has_date': 1 if has_date else 0,
                'has_signature': 1 if has_signature else 0,
                'amount_value': amount,
                'amount_suspicious': amount_suspicious,
                'date_valid': date_valid,
                'date_future': date_future,
                'text_quality': text_quality_score,
                'suspicious_chars': suspicious_chars,
                'missing_fields_count': missing_fields,
                'risk_score': risk_score
            }
            
            data.append(features)
        
        df = pd.DataFrame(data)
        print(f"Generated {len(df)} samples")
        print(f"Risk score distribution: min={df['risk_score'].min():.1f}, max={df['risk_score'].max():.1f}, mean={df['risk_score'].mean():.1f}")
        
        # Optionally save to CSV/Excel for review
        save_training_data = os.getenv('SAVE_TRAINING_DATA', 'true').lower() == 'true'  # Default to True
        if save_training_data:
            csv_path = os.path.join(self.model_dir, f'{document_type}_training_data.csv')
            df.to_csv(csv_path, index=False)
            print(f"Training data saved to CSV: {csv_path}")
            
            # Try to save Excel if openpyxl is available
            try:
                excel_path = os.path.join(self.model_dir, f'{document_type}_training_data.xlsx')
                df.to_excel(excel_path, index=False, engine='openpyxl')
                print(f"Training data saved to Excel: {excel_path}")
            except ImportError:
                print("Note: Excel export requires 'openpyxl'. Install with: pip install openpyxl")
            except Exception as e:
                print(f"Note: Could not save Excel file: {e}")
        
        return df
    
    def generate_dummy_paystub_data(self, n_samples=1000, document_type='paystub') -> pd.DataFrame:
        """Generate dummy paystub data for training"""
        print(f"Generating {n_samples} dummy paystub samples...")
        
        data = []
        
        for i in range(n_samples):
            has_company = random.random() > 0.08
            has_employee = random.random() > 0.05
            has_gross = random.random() > 0.03
            has_net = random.random() > 0.03
            has_date = random.random() > 0.08
            
            if has_gross and has_net:
                gross = random.uniform(1000, 10000)
                net = random.uniform(500, gross * 0.9)  # Net should be less than gross
                tax_error = 1 if net >= gross else 0
            else:
                gross = 0
                net = 0
                tax_error = 1
            
            missing_fields = sum([not has_company, not has_employee, not has_gross, not has_net, not has_date])
            text_quality = random.uniform(0.5, 1.0)
            
            risk_score = (missing_fields / 5) * 25
            if tax_error:
                risk_score += 20
            risk_score += random.uniform(-3, 3)
            risk_score = max(0, min(100, risk_score))
            
            features = {
                'has_company': 1 if has_company else 0,
                'has_employee': 1 if has_employee else 0,
                'has_gross': 1 if has_gross else 0,
                'has_net': 1 if has_net else 0,
                'has_date': 1 if has_date else 0,
                'gross_pay': gross,
                'net_pay': net,
                'tax_error': tax_error,
                'text_quality': text_quality,
                'missing_fields_count': missing_fields,
                'risk_score': risk_score
            }
            
            data.append(features)
        
        df = pd.DataFrame(data)
        print(f"Generated {len(df)} samples")
        print(f"Risk score distribution: min={df['risk_score'].min():.1f}, max={df['risk_score'].max():.1f}, mean={df['risk_score'].mean():.1f}")
        
        # Optionally save to CSV/Excel for review
        save_training_data = os.getenv('SAVE_TRAINING_DATA', 'true').lower() == 'true'  # Default to True
        if save_training_data:
            csv_path = os.path.join(self.model_dir, f'{document_type}_training_data.csv')
            df.to_csv(csv_path, index=False)
            print(f"Training data saved to CSV: {csv_path}")
            
            # Try to save Excel if openpyxl is available
            try:
                excel_path = os.path.join(self.model_dir, f'{document_type}_training_data.xlsx')
                df.to_excel(excel_path, index=False, engine='openpyxl')
                print(f"Training data saved to Excel: {excel_path}")
            except ImportError:
                print("Note: Excel export requires 'openpyxl'. Install with: pip install openpyxl")
            except Exception as e:
                print(f"Note: Could not save Excel file: {e}")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame, document_type: str) -> tuple:
        """
        Prepare features for training
        
        Returns:
            (X, y) where X is features and y is target risk scores
        """
        if document_type == 'check':
            feature_cols = [
                'has_bank_name', 'has_payee', 'has_amount', 'has_date', 'has_signature',
                'amount_value', 'amount_suspicious', 'date_valid', 'date_future',
                'text_quality', 'suspicious_chars', 'missing_fields_count'
            ]
        elif document_type == 'paystub':
            feature_cols = [
                'has_company', 'has_employee', 'has_gross', 'has_net', 'has_date',
                'gross_pay', 'net_pay', 'tax_error', 'text_quality', 'missing_fields_count'
            ]
        else:
            feature_cols = [col for col in df.columns if col != 'risk_score']
        
        X = df[feature_cols].values
        y = df['risk_score'].values
        
        self.feature_names = feature_cols
        
        return X, y
    
    def train_model(self, X_train, y_train, X_val=None, y_val=None):
        """Train the risk scoring model"""
        print(f"\nTraining {self.model_type} model...")
        print(f"Training samples: {len(X_train)}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        if self.model_type == 'random_forest':
            # Use RandomForestRegressor for continuous risk scores
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_train_scaled, y_train)
            
        elif self.model_type == 'xgboost':
            if not XGBOOST_AVAILABLE:
                raise ImportError("XGBoost not available")
            
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
        
        # Evaluate on validation set if provided
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            y_pred = self.model.predict(X_val_scaled)
            
            mse = mean_squared_error(y_val, y_pred)
            r2 = r2_score(y_val, y_pred)
            
            print(f"\nValidation Results:")
            print(f"  MSE: {mse:.2f}")
            print(f"  R² Score: {r2:.4f}")
            print(f"  RMSE: {np.sqrt(mse):.2f}")
            
            # Show some predictions
            print(f"\nSample Predictions (first 10):")
            for i in range(min(10, len(y_val))):
                print(f"  Actual: {y_val[i]:.1f}, Predicted: {y_pred[i]:.1f}, Error: {abs(y_val[i] - y_pred[i]):.1f}")
    
    def save_model(self, document_type: str):
        """Save trained model to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"{document_type}_risk_model_{timestamp}.pkl"
        scaler_filename = f"{document_type}_scaler_{timestamp}.pkl"
        metadata_filename = f"{document_type}_model_metadata_{timestamp}.json"
        
        model_path = os.path.join(self.model_dir, model_filename)
        scaler_path = os.path.join(self.model_dir, scaler_filename)
        metadata_path = os.path.join(self.model_dir, metadata_filename)
        
        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save scaler
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save metadata
        metadata = {
            'document_type': document_type,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'model_path': model_filename,
            'scaler_path': scaler_filename,
            'trained_at': timestamp,
            'feature_count': len(self.feature_names)
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Also save as latest
        latest_model_path = os.path.join(self.model_dir, f"{document_type}_risk_model_latest.pkl")
        latest_scaler_path = os.path.join(self.model_dir, f"{document_type}_scaler_latest.pkl")
        latest_metadata_path = os.path.join(self.model_dir, f"{document_type}_model_metadata_latest.json")
        
        import shutil
        shutil.copy(model_path, latest_model_path)
        shutil.copy(scaler_path, latest_scaler_path)
        shutil.copy(metadata_path, latest_metadata_path)
        
        print(f"\nModel saved:")
        print(f"  Model: {model_path}")
        print(f"  Scaler: {scaler_path}")
        print(f"  Metadata: {metadata_path}")
        print(f"  Latest versions also saved")
        
        return model_path, scaler_path, metadata_path


def train_all_models():
    """Train models for all document types"""
    if not SKLEARN_AVAILABLE:
        print("ERROR: scikit-learn is required for training. Install with: pip install scikit-learn")
        return
    
    print("=" * 60)
    print("ML Risk Model Training")
    print("=" * 60)
    
    document_types = ['check', 'paystub']
    
    for doc_type in document_types:
        print(f"\n{'=' * 60}")
        print(f"Training {doc_type.upper()} Risk Model")
        print(f"{'=' * 60}")
        
        trainer = RiskModelTrainer(model_type='random_forest')
        
        # Generate dummy data
        if doc_type == 'check':
            df = trainer.generate_dummy_check_data(n_samples=2000, document_type='check')
        elif doc_type == 'paystub':
            df = trainer.generate_dummy_paystub_data(n_samples=2000, document_type='paystub')
        
        # Prepare features
        X, y = trainer.prepare_features(df, doc_type)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        trainer.train_model(X_train, y_train, X_test, y_test)
        
        # Save model
        trainer.save_model(doc_type)
    
    print(f"\n{'=' * 60}")
    print("Training Complete!")
    print(f"{'=' * 60}")
    print("\nModels are saved in the 'models' directory")
    print("The MLRiskScorer will automatically use these models for real-time inference")


if __name__ == '__main__':
    train_all_models()

