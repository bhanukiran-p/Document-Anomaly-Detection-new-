"""
Check Model Retrainer
Implements automated retraining for check fraud detection models
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.automated_retraining import DocumentModelRetrainer
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class CheckModelRetrainer(DocumentModelRetrainer):
    """
    Check-specific model retrainer
    Handles 30 check fraud detection features
    """

    def __init__(self, config_path: str = None):
        """Initialize check model retrainer"""
        super().__init__(document_type='check', config_path=config_path)
        
        # 30 feature names from CheckFeatureExtractor
        self.feature_names = [
            'bank_validity', 'routing_validity', 'account_present', 'check_number_valid',
            'amount_value', 'amount_category', 'round_amount', 'payer_present',
            'payee_present', 'payer_address_present', 'date_present', 'future_date',
            'date_age_days', 'signature_detected', 'memo_present',
            'amount_matching', 'amount_parsing_confidence', 'suspicious_amount',
            'date_format_valid', 'weekend_holiday', 'critical_missing_count',
            'field_quality', 'bank_routing_match', 'check_number_pattern',
            'address_valid', 'name_consistency', 'signature_requirement',
            'endorsement_present', 'check_type_risk', 'text_quality'
        ]

    def fetch_real_data_from_database(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Fetch real check data from database
        
        Returns:
            Tuple of (DataFrame with features and risk_score, error message)
        """
        try:
            logger.info("Fetching real check data from database...")
            supabase = get_supabase()
            
            # Get data quality config
            min_confidence = self.config['data_quality']['min_confidence_score']
            confidence_field = self.config['data_quality']['confidence_score_field']
            
            # Query high-confidence samples
            # Note: Using .gte() for greater-than-or-equal
            response = supabase.table('checks')\
                .select('*')\
                .gte(confidence_field, min_confidence)\
                .in_('ai_recommendation', ['APPROVE', 'REJECT'])\
                .execute()
            
            if not response.data or len(response.data) == 0:
                logger.warning("No high-confidence check data found in database")
                return None, "No high-confidence data available"
            
            logger.info(f"Fetched {len(response.data)} high-confidence check samples")
            
            # Extract features from each row
            features_list = []
            for row in response.data:
                try:
                    features = self._extract_features_from_row(row)
                    risk_score = self._map_recommendation_to_risk(row['ai_recommendation'], row.get('fraud_risk_score'))
                    features['risk_score'] = risk_score
                    features_list.append(features)
                except Exception as e:
                    logger.warning(f"Error extracting features from row: {e}")
                    continue
            
            if not features_list:
                return None, "Failed to extract features from database rows"
            
            df = pd.DataFrame(features_list)
            logger.info(f"Successfully extracted features for {len(df)} samples")
            
            return df, None
            
        except Exception as e:
            logger.error(f"Error fetching data from database: {e}", exc_info=True)
            return None, str(e)

    def _extract_features_from_row(self, row: Dict) -> Dict[str, float]:
        """
        Extract 30 features from a database row
        
        Args:
            row: Database row with check data
            
        Returns:
            Dictionary mapping feature names to values
        """
        features = {}
        
        # Feature 1-4: Bank and account validation
        features['bank_validity'] = 1.0 if row.get('bank_name') else 0.0
        features['routing_validity'] = 1.0 if row.get('routing_number') and len(str(row.get('routing_number', ''))) == 9 else 0.0
        features['account_present'] = 1.0 if row.get('account_number') else 0.0
        features['check_number_valid'] = 1.0 if row.get('check_number') else 0.0
        
        # Feature 5-7: Amount features
        amount = float(row.get('amount', 0) or 0)
        features['amount_value'] = min(amount / 10000.0, 1.0)  # Normalize to 0-1
        features['amount_category'] = self._categorize_amount(amount)
        features['round_amount'] = 1.0 if amount > 0 and amount % 100 == 0 else 0.0
        
        # Feature 8-10: Payer/Payee information
        features['payer_present'] = 1.0 if row.get('payer_name') else 0.0
        features['payee_present'] = 1.0 if row.get('payee_name') else 0.0
        features['payer_address_present'] = 1.0 if row.get('payer_address') else 0.0
        
        # Feature 11-13: Date features
        features['date_present'] = 1.0 if row.get('date') else 0.0
        features['future_date'] = 0.0  # Would need date parsing
        features['date_age_days'] = 0.0  # Would need date parsing
        
        # Feature 14-15: Signature and memo
        features['signature_detected'] = 1.0 if row.get('signature_present') else 0.0
        features['memo_present'] = 1.0 if row.get('memo') else 0.0
        
        # Feature 16-18: Amount validation
        features['amount_matching'] = 1.0  # Assume matching if in DB
        features['amount_parsing_confidence'] = 0.9  # High confidence for DB data
        features['suspicious_amount'] = 1.0 if amount > 9000 and amount < 10000 else 0.0
        
        # Feature 19-20: Date validation
        features['date_format_valid'] = 1.0 if row.get('date') else 0.0
        features['weekend_holiday'] = 0.0  # Would need date parsing
        
        # Feature 21-22: Data quality
        critical_fields = ['bank_name', 'amount', 'payer_name', 'payee_name', 'date']
        missing_count = sum(1 for field in critical_fields if not row.get(field))
        features['critical_missing_count'] = float(missing_count) / len(critical_fields)
        features['field_quality'] = 1.0 - features['critical_missing_count']
        
        # Feature 23-24: Bank validation
        features['bank_routing_match'] = 1.0 if row.get('bank_name') and row.get('routing_number') else 0.0
        features['check_number_pattern'] = 1.0 if row.get('check_number') else 0.0
        
        # Feature 25-27: Additional validation
        features['address_valid'] = 1.0 if row.get('payer_address') else 0.0
        features['name_consistency'] = 1.0  # Assume consistent if in DB
        features['signature_requirement'] = 1.0 if row.get('signature_present') else 0.0
        
        # Feature 28-30: Advanced features
        features['endorsement_present'] = 0.0  # Not typically in DB
        features['check_type_risk'] = 0.3  # Default medium-low risk
        features['text_quality'] = 0.8  # Assume good quality for DB data
        
        return features

    def _categorize_amount(self, amount: float) -> float:
        """Categorize amount into risk brackets (0.0-1.0)"""
        if amount < 100:
            return 0.1
        elif amount < 500:
            return 0.3
        elif amount < 1000:
            return 0.5
        elif amount < 5000:
            return 0.7
        else:
            return 0.9

    def _map_recommendation_to_risk(self, recommendation: str, fraud_risk_score: Optional[float] = None) -> float:
        """
        Map AI recommendation to risk score
        
        Args:
            recommendation: 'APPROVE' or 'REJECT'
            fraud_risk_score: Optional fraud risk score from database
            
        Returns:
            Risk score (0-100)
        """
        if fraud_risk_score is not None:
            # Use existing fraud risk score if available
            return float(fraud_risk_score)
        
        # Map recommendation to risk score
        if recommendation == 'APPROVE':
            # Legitimate checks: low risk (0-30)
            return np.random.uniform(0, 30)
        elif recommendation == 'REJECT':
            # Fraudulent checks: high risk (70-100)
            return np.random.uniform(70, 100)
        else:
            # Should not happen (ESCALATE filtered out)
            return 50.0

    def generate_synthetic_data(self, n_samples: int) -> pd.DataFrame:
        """
        Generate synthetic check data for training
        
        Args:
            n_samples: Number of synthetic samples to generate
            
        Returns:
            DataFrame with 30 features and risk_score column
        """
        logger.info(f"Generating {n_samples} synthetic check samples...")
        
        data = []
        for i in range(n_samples):
            # 50% legitimate, 50% fraudulent
            is_fraud = np.random.random() < 0.5
            
            if is_fraud:
                # Fraudulent check characteristics
                features = self._generate_fraudulent_check()
            else:
                # Legitimate check characteristics
                features = self._generate_legitimate_check()
            
            data.append(features)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} synthetic samples ({len(df[df['risk_score'] >= 70])} fraud, {len(df[df['risk_score'] <= 30])} legitimate)")
        
        return df

    def _generate_legitimate_check(self) -> Dict[str, float]:
        """Generate features for a legitimate check"""
        features = {}
        
        # High validity scores
        features['bank_validity'] = 1.0
        features['routing_validity'] = 1.0
        features['account_present'] = 1.0
        features['check_number_valid'] = 1.0
        
        # Reasonable amount (mostly under $1000)
        amount = np.random.lognormal(mean=5.0, sigma=1.5)  # Log-normal distribution
        amount = min(amount, 5000)  # Cap at $5000
        features['amount_value'] = min(amount / 10000.0, 1.0)
        features['amount_category'] = self._categorize_amount(amount)
        features['round_amount'] = 1.0 if np.random.random() < 0.3 else 0.0  # 30% round amounts
        
        # Complete information
        features['payer_present'] = 1.0
        features['payee_present'] = 1.0
        features['payer_address_present'] = 1.0 if np.random.random() < 0.9 else 0.0
        
        # Valid dates
        features['date_present'] = 1.0
        features['future_date'] = 0.0
        features['date_age_days'] = np.random.uniform(0, 180) / 365.0  # 0-6 months old
        
        # Signature and memo
        features['signature_detected'] = 1.0 if np.random.random() < 0.95 else 0.0
        features['memo_present'] = 1.0 if np.random.random() < 0.7 else 0.0
        
        # High matching and parsing confidence
        features['amount_matching'] = 1.0
        features['amount_parsing_confidence'] = np.random.uniform(0.85, 1.0)
        features['suspicious_amount'] = 0.0
        
        # Valid date format
        features['date_format_valid'] = 1.0
        features['weekend_holiday'] = 1.0 if np.random.random() < 0.1 else 0.0  # 10% on weekends
        
        # Low missing fields
        features['critical_missing_count'] = 0.0
        features['field_quality'] = np.random.uniform(0.9, 1.0)
        
        # Good validation
        features['bank_routing_match'] = 1.0
        features['check_number_pattern'] = 1.0
        features['address_valid'] = 1.0
        features['name_consistency'] = 1.0
        features['signature_requirement'] = 1.0
        
        # Additional features
        features['endorsement_present'] = 1.0 if np.random.random() < 0.5 else 0.0
        features['check_type_risk'] = np.random.uniform(0.0, 0.3)  # Low risk
        features['text_quality'] = np.random.uniform(0.8, 1.0)
        
        # Low risk score
        features['risk_score'] = np.random.uniform(0, 30)
        
        return features

    def _generate_fraudulent_check(self) -> Dict[str, float]:
        """Generate features for a fraudulent check"""
        features = {}
        
        # Lower validity scores (some missing/invalid)
        features['bank_validity'] = 1.0 if np.random.random() < 0.7 else 0.0
        features['routing_validity'] = 1.0 if np.random.random() < 0.6 else 0.0
        features['account_present'] = 1.0 if np.random.random() < 0.8 else 0.0
        features['check_number_valid'] = 1.0 if np.random.random() < 0.7 else 0.0
        
        # Higher amounts, often suspicious
        amount = np.random.uniform(500, 15000)
        features['amount_value'] = min(amount / 10000.0, 1.0)
        features['amount_category'] = self._categorize_amount(amount)
        features['round_amount'] = 1.0 if np.random.random() < 0.6 else 0.0  # 60% round amounts (suspicious)
        
        # Some missing information
        features['payer_present'] = 1.0 if np.random.random() < 0.9 else 0.0
        features['payee_present'] = 1.0 if np.random.random() < 0.9 else 0.0
        features['payer_address_present'] = 1.0 if np.random.random() < 0.5 else 0.0  # Often missing
        
        # Date issues
        features['date_present'] = 1.0 if np.random.random() < 0.9 else 0.0
        features['future_date'] = 1.0 if np.random.random() < 0.2 else 0.0  # 20% future dated
        features['date_age_days'] = np.random.uniform(0, 365) / 365.0  # Can be old
        
        # Signature issues
        features['signature_detected'] = 1.0 if np.random.random() < 0.6 else 0.0  # Often missing
        features['memo_present'] = 1.0 if np.random.random() < 0.4 else 0.0
        
        # Lower matching confidence
        features['amount_matching'] = 1.0 if np.random.random() < 0.7 else 0.0  # 30% mismatch
        features['amount_parsing_confidence'] = np.random.uniform(0.4, 0.8)
        features['suspicious_amount'] = 1.0 if amount > 9000 and amount < 10000 else 0.0
        
        # Date validation issues
        features['date_format_valid'] = 1.0 if np.random.random() < 0.8 else 0.0
        features['weekend_holiday'] = 1.0 if np.random.random() < 0.3 else 0.0  # 30% on weekends
        
        # More missing fields
        features['critical_missing_count'] = np.random.uniform(0.1, 0.4)
        features['field_quality'] = np.random.uniform(0.5, 0.8)
        
        # Validation issues
        features['bank_routing_match'] = 1.0 if np.random.random() < 0.6 else 0.0
        features['check_number_pattern'] = 1.0 if np.random.random() < 0.7 else 0.0
        features['address_valid'] = 1.0 if np.random.random() < 0.6 else 0.0
        features['name_consistency'] = 1.0 if np.random.random() < 0.7 else 0.0
        features['signature_requirement'] = 1.0 if np.random.random() < 0.5 else 0.0
        
        # Additional features
        features['endorsement_present'] = 1.0 if np.random.random() < 0.2 else 0.0  # Rarely endorsed
        features['check_type_risk'] = np.random.uniform(0.6, 1.0)  # High risk
        features['text_quality'] = np.random.uniform(0.3, 0.7)  # Lower quality
        
        # High risk score
        features['risk_score'] = np.random.uniform(70, 100)
        
        return features


if __name__ == '__main__':
    # Test the retrainer
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("Testing Check Model Retrainer")
    print("="*70)
    
    retrainer = CheckModelRetrainer()
    
    print("\n1. Testing synthetic data generation...")
    synthetic_df = retrainer.generate_synthetic_data(n_samples=100)
    print(f"Generated {len(synthetic_df)} samples")
    print(f"Features: {list(synthetic_df.columns)}")
    print(f"Fraud ratio: {len(synthetic_df[synthetic_df['risk_score'] >= 70]) / len(synthetic_df):.2%}")
    
    print("\n2. Testing database fetch...")
    real_df, error = retrainer.fetch_real_data_from_database()
    if error:
        print(f"Database fetch error: {error}")
    else:
        print(f"Fetched {len(real_df)} real samples")
        print(f"Fraud ratio: {len(real_df[real_df['risk_score'] >= 70]) / len(real_df):.2%}")
    
    print("\n3. Running full retraining...")
    result = retrainer.retrain()
    
    if result['success']:
        print(f"\n✅ Retraining successful!")
        print(f"Version: {result['version_id']}")
        print(f"Data source: {result['data_source']}")
        print(f"R² Score: {result['metrics']['r2_score']:.4f}")
        print(f"MSE: {result['metrics']['mse']:.4f}")
        print(f"Activated: {result['activated']}")
    else:
        print(f"\n❌ Retraining failed: {result.get('error')}")
