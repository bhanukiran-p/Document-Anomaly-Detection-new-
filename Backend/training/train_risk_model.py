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
        # Default to global models directory (for backward compatibility)
        # Individual document types will override this
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
    
    def generate_dummy_paystub_data(self, n_samples=2000, document_type='paystub') -> pd.DataFrame:
        """Generate dummy paystub data for training with proper risk distribution"""
        print(f"Generating {n_samples} dummy paystub samples with improved risk distribution...")
        
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
            
            # ===== GENERATE NEW FEATURES (TAXES, PROPORTIONS) =====
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
            
            # ===== ENHANCED RISK SCORE FORMULA (incorporates all 18 features) =====
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
            
            # Zero withholding (ZERO_WITHHOLDING_SUSPICIOUS): up to 25 points
            if gross > 1000:  # Only check if gross is meaningful
                if not has_federal_tax and not has_state_tax and not has_social_security and not has_medicare:
                    risk_score += 25  # No taxes at all (very suspicious)
                elif total_tax_amount < gross * 0.02:  # Less than 2% taxes
                    risk_score += 15
                elif not has_social_security or not has_medicare:  # Missing mandatory taxes
                    risk_score += 10
            
            # Unrealistic proportions (UNREALISTIC_PROPORTIONS): up to 20 points
            if gross > 0:
                if net_to_gross_ratio > 0.95:  # Net > 95% of gross
                    risk_score += 20
                elif net_to_gross_ratio > 0.90:  # Net > 90% of gross
                    risk_score += 10
                if tax_to_gross_ratio < 0.02 and gross > 1000:  # Tax < 2% of gross
                    risk_score += 15
                if deduction_percentage > 0.50:  # Deductions > 50% (unusual)
                    risk_score += 10
            
            # Suspicious amount patterns: up to 15 points
            if gross > 0:
                if gross > 50000:  # Very high salary
                    risk_score += 8
                if gross == net:  # No deductions at all
                    risk_score += 15
                elif (gross - net) < gross * 0.1:  # Very low deductions
                    risk_score += 5
            
            # Missing critical fields individually: up to 10 points
            if not has_company:
                risk_score += 5
            if not has_employee:
                risk_score += 5
            
            # Random variation
            risk_score += random.uniform(-5, 5)
            
            # Cap at 100
            risk_score = max(0, min(100, risk_score))
            
            # REMOVED: Score forcing logic that was artificially lowering legitimate sample scores
            # This was causing the model to learn that even suspicious-looking legitimate samples
            # should have low scores, leading to poor fraud detection on real paystubs.
            # The risk score calculation above should be sufficient to generate appropriate scores.
            
            # Build features dictionary with all 22 features
            features = {
                # Basic presence flags (1-5)
                'has_company': 1 if has_company else 0,
                'has_employee': 1 if has_employee else 0,
                'has_gross': 1 if has_gross else 0,
                'has_net': 1 if has_net else 0,
                'has_date': 1 if has_date else 0,
                # Amounts (6-7)
                'gross_pay': gross,
                'net_pay': net,
                # Errors and quality (8-10)
                'tax_error': tax_error,
                'text_quality': text_quality,
                'missing_fields_count': missing_fields,
                # Tax features (11-16)
                'has_federal_tax': 1 if has_federal_tax else 0,
                'has_state_tax': 1 if has_state_tax else 0,
                'has_social_security': 1 if has_social_security else 0,
                'has_medicare': 1 if has_medicare else 0,
                'total_tax_amount': total_tax_amount,
                'tax_to_gross_ratio': tax_to_gross_ratio,
                # Proportion features (17-18)
                'net_to_gross_ratio': net_to_gross_ratio,
                'deduction_percentage': deduction_percentage,
                # Target
                'risk_score': risk_score
            }
            
            data.append(features)
        
        df = pd.DataFrame(data)
        print(f"Generated {len(df)} samples")
        print(f"Risk score distribution: min={df['risk_score'].min():.1f}, max={df['risk_score'].max():.1f}, mean={df['risk_score'].mean():.1f}")
        
        # Print detailed distribution
        legitimate = len(df[(df['risk_score'] >= 0) & (df['risk_score'] <= 30)])
        slightly_suspicious = len(df[(df['risk_score'] > 30) & (df['risk_score'] <= 70)])
        highly_suspicious = len(df[df['risk_score'] > 70])
        
        print(f"\nRisk Score Distribution:")
        print(f"  Legitimate (0-30%): {legitimate} samples ({legitimate/len(df)*100:.1f}%)")
        print(f"  Slightly Suspicious (31-70%): {slightly_suspicious} samples ({slightly_suspicious/len(df)*100:.1f}%)")
        print(f"  Highly Suspicious (71-100%): {highly_suspicious} samples ({highly_suspicious/len(df)*100:.1f}%)")
        
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
    
    def generate_dummy_bank_statement_data(self, n_samples=2000, document_type='bank_statement') -> pd.DataFrame:
        """
        Generate dummy bank statement data for training with 35 features
        
        Args:
            n_samples: Number of training samples to generate
            document_type: Document type identifier
            
        Returns:
            DataFrame with 35 features and risk scores
        """
        print(f"Generating {n_samples} dummy bank statement samples...")
        
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
        
        # Optionally save to CSV/Excel for review
        save_training_data = os.getenv('SAVE_TRAINING_DATA', 'true').lower() == 'true'
        if save_training_data:
            csv_path = os.path.join(self.model_dir, f'{document_type}_training_data.csv')
            df.to_csv(csv_path, index=False)
            print(f"  Saved training data to: {csv_path}")
        
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
                # Basic presence flags (1-5)
                'has_company', 'has_employee', 'has_gross', 'has_net', 'has_date',
                # Amounts (6-7)
                'gross_pay', 'net_pay',
                # Errors and quality (8-10)
                'tax_error', 'text_quality', 'missing_fields_count',
                # Tax features (11-16)
                'has_federal_tax', 'has_state_tax', 'has_social_security', 'has_medicare',
                'total_tax_amount', 'tax_to_gross_ratio',
                # Proportion features (17-18)
                'net_to_gross_ratio', 'deduction_percentage'
            ]
        elif document_type == 'bank_statement':
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
        
        # Also save as latest in document-specific folder
        # Map document types to their specific model directories
        doc_specific_dirs = {
            'check': 'check/ml/models',
            'paystub': 'paystub/ml/models',
            'money_order': 'money_order/ml/models',
            'bank_statement': 'bank_statement/ml/models'
        }
        
        # Save to document-specific folder if it exists
        if document_type in doc_specific_dirs:
            doc_dir = doc_specific_dirs[document_type]
            os.makedirs(doc_dir, exist_ok=True)
            
            doc_latest_model = os.path.join(doc_dir, f"{document_type}_risk_model_latest.pkl")
            doc_latest_scaler = os.path.join(doc_dir, f"{document_type}_scaler_latest.pkl")
            doc_latest_metadata = os.path.join(doc_dir, f"{document_type}_model_metadata_latest.json")
            
            import shutil
            shutil.copy(model_path, doc_latest_model)
            shutil.copy(scaler_path, doc_latest_scaler)
            shutil.copy(metadata_path, doc_latest_metadata)
            print(f"  Also saved to document-specific folder: {doc_dir}")
        
        # Also save as latest in global models directory (for backward compatibility)
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
        print(f"  Latest versions also saved to global models directory")
        
        return model_path, scaler_path, metadata_path


def train_bank_statement_models():
    """Train both Random Forest and XGBoost models for bank statements (ensemble)"""
    if not SKLEARN_AVAILABLE:
        print("ERROR: scikit-learn is required for training. Install with: pip install scikit-learn")
        return
    
    if not XGBOOST_AVAILABLE:
        print("ERROR: xgboost is required for bank statement training. Install with: pip install xgboost")
        return
    
    print("=" * 60)
    print("Training BANK STATEMENT Models (RF + XGBoost Ensemble)")
    print("=" * 60)
    
    # Generate dummy data
    trainer = RiskModelTrainer(model_type='random_forest')
    df = trainer.generate_dummy_bank_statement_data(n_samples=2000, document_type='bank_statement')
    
    # Prepare features
    X, y = trainer.prepare_features(df, 'bank_statement')
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("\n" + "=" * 60)
    print("Training Random Forest Model")
    print("=" * 60)
    rf_trainer = RiskModelTrainer(model_type='random_forest')
    rf_trainer.scaler = scaler
    rf_trainer.feature_names = trainer.feature_names
    rf_trainer.train_model(X_train_scaled, y_train, X_test_scaled, y_test)
    rf_model = rf_trainer.model
    
    # Train XGBoost
    print("\n" + "=" * 60)
    print("Training XGBoost Model")
    print("=" * 60)
    xgb_model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_train_scaled, y_train)
    
    # Evaluate XGBoost
    xgb_pred = xgb_model.predict(X_test_scaled)
    xgb_mse = mean_squared_error(y_test, xgb_pred)
    xgb_r2 = r2_score(y_test, xgb_pred)
    print(f"\nXGBoost Test Results:")
    print(f"  MSE: {xgb_mse:.4f}")
    print(f"  R²: {xgb_r2:.4f}")
    
    # Save models to bank_statement/ml/models directory
    model_dir = 'bank_statement/ml/models'
    os.makedirs(model_dir, exist_ok=True)
    
    import joblib
    
    # Save Random Forest
    rf_path = os.path.join(model_dir, 'bank_statement_random_forest.pkl')
    joblib.dump(rf_model, rf_path)
    print(f"\nSaved Random Forest model to: {rf_path}")
    
    # Save XGBoost
    xgb_path = os.path.join(model_dir, 'bank_statement_xgboost.pkl')
    joblib.dump(xgb_model, xgb_path)
    print(f"Saved XGBoost model to: {xgb_path}")
    
    # Save scaler
    scaler_path = os.path.join(model_dir, 'bank_statement_feature_scaler.pkl')
    joblib.dump(scaler, scaler_path)
    print(f"Saved feature scaler to: {scaler_path}")
    
    # Save metadata
    metadata = {
        'document_type': 'bank_statement',
        'model_type': 'ensemble',
        'models': ['random_forest', 'xgboost'],
        'feature_names': trainer.feature_names,
        'feature_count': len(trainer.feature_names),
        'trained_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'rf_mse': float(rf_trainer.mse) if hasattr(rf_trainer, 'mse') else None,
        'rf_r2': float(rf_trainer.r2) if hasattr(rf_trainer, 'r2') else None,
        'xgb_mse': float(xgb_mse),
        'xgb_r2': float(xgb_r2)
    }
    
    metadata_path = os.path.join(model_dir, 'bank_statement_model_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to: {metadata_path}")
    
    print("\n" + "=" * 60)
    print("Bank Statement Model Training Complete!")
    print("=" * 60)


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
    
    # Train bank statement models separately (requires ensemble)
    train_bank_statement_models()
    
    print(f"\n{'=' * 60}")
    print("Training Complete!")
    print(f"{'=' * 60}")
    print("\nModels are saved in the 'models' directory")
    print("The MLRiskScorer will automatically use these models for real-time inference")


if __name__ == '__main__':
    train_all_models()

