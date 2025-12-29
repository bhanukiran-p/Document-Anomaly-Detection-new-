"""
Bank Statement Model Retrainer
Implements automated retraining for bank statement fraud detection models
"""

import sys
import os
import logging
import numpy as np
import pandas as pd
import random
import json
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.automated_retraining import DocumentModelRetrainer
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class BankStatementModelRetrainer(DocumentModelRetrainer):
    """
    Bank Statement specific model retrainer
    Handles 35 feature extraction and synthetic data generation
    """

    def __init__(self, config_path: str = None):
        super().__init__(document_type='bank_statement', config_path=config_path)
        
        # Feature names matching standard extractor (35 features)
        self.feature_names = [
            'bank_validity', 'account_number_present', 'account_holder_present', 'account_type_present',
            'beginning_balance', 'ending_balance', 'total_credits', 'total_debits',
            'period_start_present', 'period_end_present', 'statement_date_present', 'future_period',
            'period_age_days', 'transaction_count', 'avg_transaction_amount', 'max_transaction_amount',
            'balance_change', 'negative_ending_balance', 'balance_consistency', 'currency_present',
            'suspicious_transaction_pattern', 'large_transaction_count', 'round_number_transactions',
            'date_format_valid', 'period_length_days', 'critical_missing_count', 'field_quality',
            'transaction_date_consistency', 'duplicate_transactions', 'unusual_timing',
            'account_number_format_valid', 'name_format_valid', 'balance_volatility',
            'credit_debit_ratio', 'text_quality'
        ]

    def fetch_real_data_from_database(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Fetch real bank statement data from database
        Returns: Tuple of (DataFrame, error_message)
        """
        try:
            supabase = get_supabase()
            
            # Get data quality config
            min_confidence = self.config['data_quality']['min_confidence_score']
            confidence_field = self.config['data_quality']['confidence_score_field']
            
            # Query high-confidence samples
            response = supabase.table('bank_statements')\
                .select('*')\
                .gte(confidence_field, min_confidence)\
                .in_('ai_recommendation', ['APPROVE', 'REJECT'])\
                .execute()
            
            if not response.data:
                logger.warning("No high-confidence bank statement data found")
                return None, "No high-confidence data available"
                
            features_list = []
            for row in response.data:
                try:
                    features = self._extract_features_from_row(row)
                    if features:
                        features_list.append(features)
                except Exception as e:
                    logger.warning(f"Error extracting features from row: {e}")
                    continue
                    
            if not features_list:
                return None, "Failed to extract features"
            
            # Ensure columns are in correct order
            df = pd.DataFrame(features_list)
            
            # Fill missing columns with defaults if any
            for col in self.feature_names:
                if col not in df.columns:
                    df[col] = 0.0
                    
            return df, None

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None, str(e)

    def _extract_features_from_row(self, row: Dict) -> Dict:
        """Extract 35 features from database row"""
        features = {}
        
        # 1. Basic Validity
        features['bank_validity'] = 1.0 if row.get('bank_name') else 0.0
        features['account_number_present'] = 1.0 if row.get('account_number') else 0.0
        features['account_holder_present'] = 1.0 if row.get('account_holder_name') else 0.0
        features['account_type_present'] = 1.0 # Assumed
        
        # 2. Financials (Safe parsing)
        def parse_float(val):
            try: return float(val or 0)
            except: return 0.0
            
        features['beginning_balance'] = parse_float(row.get('beginning_balance'))
        features['ending_balance'] = parse_float(row.get('ending_balance'))
        features['total_credits'] = parse_float(row.get('total_credits'))
        features['total_debits'] = parse_float(row.get('total_debits'))
        
        # 3. Dates
        features['period_start_present'] = 1.0 if row.get('period_start') else 0.0
        features['period_end_present'] = 1.0 if row.get('period_end') else 0.0
        features['statement_date_present'] = 1.0 if row.get('statement_date') else 0.0
        features['future_period'] = 0.0 # Logic would require date parsing
        features['period_age_days'] = 30.0 # Placeholder
        
        # 4. Transactions
        # In real scenario we'd query transactions table or parse JSON
        txn_count = 10.0 # Default/Average
        features['transaction_count'] = txn_count
        features['avg_transaction_amount'] = features['total_debits'] / txn_count if txn_count else 0
        features['max_transaction_amount'] = features['avg_transaction_amount'] * 2 # Estimation
        
        # 5. Analysis
        features['balance_change'] = features['ending_balance'] - features['beginning_balance']
        features['negative_ending_balance'] = 1.0 if features['ending_balance'] < 0 else 0.0
        
        consistency = 1.0
        calc_end = features['beginning_balance'] + features['total_credits'] - features['total_debits']
        if abs(calc_end - features['ending_balance']) > 1.0:
            consistency = 0.5
        features['balance_consistency'] = consistency
        
        features['currency_present'] = 1.0
        
        # 6. Advanced / Risk
        features['suspicious_transaction_pattern'] = 0.0  
        features['large_transaction_count'] = 0.0
        features['round_number_transactions'] = 0.0
        features['date_format_valid'] = 1.0
        features['period_length_days'] = 30.0
        
        # Missing count
        missing = 0
        if not row.get('bank_name'): missing += 1
        if not row.get('account_number'): missing += 1
        features['critical_missing_count'] = float(missing)
        
        features['field_quality'] = 0.9
        features['transaction_date_consistency'] = 1.0
        features['duplicate_transactions'] = 0.0
        features['unusual_timing'] = 0.0
        features['account_number_format_valid'] = 1.0
        features['name_format_valid'] = 1.0
        features['balance_volatility'] = 0.0 
        
        features['credit_debit_ratio'] = (features['total_credits']/features['total_debits']) if features['total_debits'] > 0 else 0
        features['text_quality'] = 0.95 

        # Target Risk Score
        rec = row.get('ai_recommendation', 'APPROVE')
        if rec == 'REJECT':
             features['risk_score'] = float(row.get('fraud_risk_score', 85.0))
        else:
             features['risk_score'] = float(row.get('fraud_risk_score', 10.0))
        
        return features

    def generate_synthetic_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic bank statement data (port from train_bank_statement_models.py)"""
        logger.info(f"Generating {n_samples} synthetic bank statement samples...")
        
        data = []
        for _ in range(n_samples):
            # 1. Determine Target Category (Balanced distribution)
            cat_rand = random.random()
            if cat_rand < 0.45: target_min, target_max = 0, 30
            elif cat_rand < 0.70: target_min, target_max = 31, 60
            elif cat_rand < 0.875: target_min, target_max = 61, 85
            else: target_min, target_max = 86, 100
            
            # 2. Set base params based on category
            if target_max <= 30:
                bank_valid = 1.0
                account_present = 1.0
                account_holder_present = 1.0
                future_period = 0.0
                negative_ending = 0.0
                consistency = 1.0
                critical_missing = random.randint(0, 1)
            elif target_max <= 60:
                bank_valid = random.choice([1.0, 0.0])
                account_present = random.choice([1.0, 0.0])
                account_holder_present = random.choice([1.0, 0.0])
                future_period = random.choice([0.0, 1.0])
                negative_ending = random.choice([0.0, 1.0])
                consistency = random.uniform(0.3, 0.7)
                critical_missing = random.randint(2, 4)
            elif target_max <= 85:
                bank_valid = random.choice([1.0, 0.0, 0.0])
                account_present = random.choice([1.0, 0.0, 0.0])
                account_holder_present = random.choice([1.0, 0.0, 0.0])
                future_period = random.choice([0.0, 1.0, 1.0])
                negative_ending = random.choice([0.0, 1.0, 1.0])
                consistency = random.uniform(0.0, 0.5)
                critical_missing = random.randint(4, 6)
            else: # Critical
                bank_valid = 0.0
                account_present = random.choice([1.0, 0.0, 0.0, 0.0])
                account_holder_present = 0.0
                future_period = 1.0
                negative_ending = random.choice([0.0, 1.0, 1.0, 1.0])
                consistency = random.uniform(0.0, 0.3)
                critical_missing = random.randint(5, 7)
            
            # Helper to generate numeric
            beg_bal = random.uniform(0, 100000) if account_present else 0
            end_bal = random.uniform(0, 100000) if account_present else 0
            cred = random.uniform(0, 50000) if account_present else 0
            deb = random.uniform(0, 50000) if account_present else 0
            
            # 3. Build Feature Vector
            features = {
                'bank_validity': bank_valid,
                'account_number_present': account_present,
                'account_holder_present': account_holder_present,
                'account_type_present': random.choice([1.0, 0.0]),
                'beginning_balance': beg_bal,
                'ending_balance': end_bal, 
                'total_credits': cred,
                'total_debits': deb,
                'period_start_present': random.choice([1.0, 0.0]),
                'period_end_present': random.choice([1.0, 0.0]),
                'statement_date_present': random.choice([1.0, 0.0]),
                'future_period': future_period,
                'period_age_days': random.uniform(0, 365),
                'transaction_count': random.randint(0, 500),
                'avg_transaction_amount': random.uniform(0, 5000),
                'max_transaction_amount': random.uniform(0, 10000),
                'balance_change': end_bal - beg_bal,
                'negative_ending_balance': negative_ending,
                'balance_consistency': consistency,
                'currency_present': 1.0,
                'suspicious_transaction_pattern': random.choice([0.0, 1.0]),
                'large_transaction_count': random.randint(0, 50),
                'round_number_transactions': random.uniform(0, 50),
                'date_format_valid': 1.0,
                'period_length_days': 30.0,
                'critical_missing_count': float(critical_missing),
                'field_quality': random.uniform(0.0, 1.0),
                'transaction_date_consistency': random.uniform(0.0, 1.0),
                'duplicate_transactions': random.choice([0.0, 0.5, 1.0]),
                'unusual_timing': random.uniform(0.0, 1.0),
                'account_number_format_valid': 1.0,
                'name_format_valid': 1.0,
                'balance_volatility': random.uniform(0.0, 10.0),
                'credit_debit_ratio': random.uniform(0.0, 10.0),
                'text_quality': random.uniform(0.0, 1.0),
            }
            
            # Simple scoring logic approx
            risk_score = (critical_missing / 7.0) * 40
            if bank_valid == 0: risk_score += 30
            if account_holder_present == 0: risk_score += 25
            
            # Noise + Clamping
            risk_score += random.uniform(-5, 5)
            
            # Force into category range
            if target_max <= 30: 
                risk_score = random.uniform(0, 30)
            elif target_max <= 60:
                risk_score = random.uniform(31, 60)
            elif target_max <= 85:
                risk_score = random.uniform(61, 85)
            else:
                risk_score = random.uniform(86, 100)
                
            features['risk_score'] = risk_score
            data.append(features)
            
        return pd.DataFrame(data)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    retrainer = BankStatementModelRetrainer()
    result = retrainer.retrain()
    print(result)
