"""
Money Order Model Retrainer
Implements automated retraining for money order fraud detection models
"""

import sys
import os
import logging
import numpy as np
import pandas as pd
import random
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.automated_retraining import DocumentModelRetrainer
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class MoneyOrderModelRetrainer(DocumentModelRetrainer):
    """
    Money Order specific model retrainer
    Handles 30 feature extraction and synthetic data generation
    """

    def __init__(self, config_path: str = None):
        super().__init__(document_type='money_order', config_path=config_path)

    def fetch_real_data_from_database(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Fetch real money order data from database
        Returns: Tuple of (DataFrame, error_message)
        """
        try:
            supabase = get_supabase()
            
            # Get data quality config
            min_confidence = self.config['data_quality']['min_confidence_score']
            confidence_field = self.config['data_quality']['confidence_score_field']
            
            # Query high-confidence samples
            response = supabase.table('money_orders')\
                .select('*')\
                .gte(confidence_field, min_confidence)\
                .in_('ai_recommendation', ['APPROVE', 'REJECT'])\
                .execute()
            
            if not response.data:
                logger.warning("No high-confidence money order data found")
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
                
            return pd.DataFrame(features_list), None

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None, str(e)

    def _extract_features_from_row(self, row: Dict) -> Dict:
        """Extract 30 features from database row"""
        # Map DB fields to 30 features used in training
        # Note: This is an approximation since we don't store 30 raw features in DB
        # We reconstruct them from stored metadata where possible
        
        features = {} 
        
        # 1. Issuer Validation
        features['feature_0'] = 1.0 if row.get('issuer_name') else 0.0
        features['feature_1'] = 1.0 if row.get('serial_number') else 0.0
        features['feature_2'] = 1.0 # Serial pattern match (assumed valid if in DB)
        
        # 2. Amount Features
        amount = float(row.get('amount', 0) or 0)
        features['feature_3'] = amount
        features['feature_4'] = 1.0 if amount < 500 else (2.0 if amount < 1000 else 3.0)
        features['feature_5'] = 1.0 if amount > 0 and amount % 100 == 0 else 0.0
        
        # 3. Field Presence
        features['feature_6'] = 1.0 if row.get('payee_name') else 0.0
        features['feature_7'] = 1.0 if row.get('payer_name') else 0.0
        features['feature_8'] = 1.0 # Date present (assumed)
        
        # 4. Date Logic
        features['feature_9'] = 0.0 # Future date
        features['feature_10'] = 30.0 # Day age (avg)
        
        # 5. Signatures & consistency
        features['feature_11'] = 1.0 # Signature present
        features['feature_12'] = 1.0 # Amount match
        features['feature_13'] = 0.95 # Parsing confidence
        features['feature_14'] = 0.0 # Suspicious pattern
        
        # 6. Formatting
        features['feature_15'] = 1.0
        features['feature_16'] = 0.0 # Weekend
        features['feature_17'] = 0.0 # Correlation
        
        # 7. Quality
        features['feature_18'] = 0.0 # Missing critical
        features['feature_19'] = 0.9 # Field quality
        features['feature_20'] = 1.0 # specific val
        features['feature_21'] = 1.0 # check num pattern
        features['feature_22'] = 1.0 # address val
        features['feature_23'] = 1.0 # name consist
        features['feature_24'] = 1.0 # sig req
        
        # 8. Risk & Text
        features['feature_25'] = 0.1 # Type risk
        features['feature_26'] = 0.9 # Text quality
        features['feature_27'] = 0.0 # Missing count
        features['feature_28'] = 0.0 # Endorsement
        features['feature_29'] = float(row.get('model_confidence', 0.9))
        
        # Target
        rec = row.get('ai_recommendation', 'APPROVE')
        if rec == 'REJECT':
             features['risk_score'] = float(row.get('fraud_risk_score', 85.0))
        else:
             features['risk_score'] = float(row.get('fraud_risk_score', 10.0))
             
        # Rename keys to feature_0..29 to match training logic if needed, 
        # but better to use descriptive names if possible. 
        # However, the original training script used feature_0..29.
        # Let's keep strict parity for now.
        
        return features

    def generate_synthetic_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic money order data (port from train_money_order_models.py)"""
        logger.info(f"Generating {n_samples} synthetic money order samples...")
        
        data = []
        for _ in range(n_samples):
            features_list = self._generate_sample()
            risk_score = self._calculate_risk_score(features_list)
            
            # Convert list to dict with feature_N keys
            row_dict = {f'feature_{i}': val for i, val in enumerate(features_list)}
            row_dict['risk_score'] = risk_score
            data.append(row_dict)
            
        return pd.DataFrame(data)

    def _generate_sample(self):
        """Generate one money order sample (30 features)"""
        is_legit = random.random() < 0.7
        if is_legit:
            return self._generate_legitimate_mo()
        else:
            return self._generate_fraudulent_mo()

    def _generate_legitimate_mo(self):
        return [
            1.0, 1.0, 1.0, random.uniform(50, 2000), random.randint(1, 2),
            1.0, 1.0, 1.0, 1.0, 0.0, random.uniform(0, 60),
            1.0, 1.0, random.uniform(0.85, 1.0), 0.0, 1.0,
            random.choice([0.0, 1.0]) if random.random() < 0.15 else 0.0,
            0.0, 0.0, random.uniform(0.8, 1.0), 1.0, random.uniform(0.8, 1.0),
            1.0, random.uniform(0.85, 1.0), 1.0, random.uniform(0.0, 0.2),
            random.uniform(0.85, 1.0), 0.0, 1.0, random.uniform(0.8, 1.0)
        ]

    def _generate_fraudulent_mo(self):
        fraud_type = random.choice(['invalid_issuer', 'missing_fields', 'date_fraud', 'amount_fraud', 'combo'])
        features = [0.5] * 30
        
        if fraud_type in ['invalid_issuer', 'combo']:
            features[0] = 0.0
            features[1] = 0.0 if random.random() < 0.5 else 1.0
            features[2] = random.uniform(0.2, 0.5)

        if fraud_type in ['missing_fields', 'combo']:
            features[6] = 0.0 if random.random() < 0.4 else 1.0
            features[7] = 0.0 if random.random() < 0.4 else 1.0
            features[11] = 0.0 if random.random() < 0.6 else 1.0
            features[27] = random.randint(2, 5)

        if fraud_type in ['date_fraud', 'combo']:
            features[9] = 1.0
            features[10] = random.uniform(180, 500)

        if fraud_type in ['amount_fraud', 'combo']:
            features[3] = random.uniform(5000, 25000)
            features[4] = random.randint(3, 4)
            features[12] = 0.0
            features[14] = 1.0

        features[18] = random.uniform(0.3, 0.8)
        features[19] = random.uniform(0.3, 0.6)
        features[26] = random.uniform(0.3, 0.6)
        features[29] = random.uniform(0.4, 0.7)
        return features

    def _calculate_risk_score(self, features):
        risk = 0.0
        if features[0] < 0.5: risk += 25
        if features[1] < 0.5: risk += 20
        if features[9] > 0.5: risk += 40
        if features[10] > 180: risk += 10
        risk += min(30, features[27] * 10)
        if features[3] > 5000: risk += 10
        if features[12] < 0.5: risk += 15
        if features[14] > 0.5: risk += 10
        if features[11] < 0.5: risk += 50
        if features[19] < 0.5: risk += 15
        if features[26] < 0.5: risk += 15
        return min(100.0, risk)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    retrainer = MoneyOrderModelRetrainer()
    result = retrainer.retrain()
    print(result)
