"""
Paystub Model Retrainer
Implements automated retraining for paystub fraud detection models
"""

import sys
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.automated_retraining import DocumentModelRetrainer
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)



class PaystubModelRetrainer(DocumentModelRetrainer):
    """Paystub-specific model retrainer"""
    
    def __init__(self):
        super().__init__(document_type='paystub')
        self.supabase = get_supabase()

    
    def fetch_real_data_from_database(self) -> tuple:
        """
        Fetch high-quality paystub data from database
        Returns tuple of (DataFrame with 18 features + fraud_risk_score, error_message)
        """
        try:
            # Query paystubs with high confidence (>= 0.8) and valid recommendations
            response = self.supabase.table('paystubs').select('*').gte(
                'model_confidence', 0.8
            ).in_('ai_recommendation', ['APPROVE', 'REJECT']).execute()
            
            if not response.data:
                logger.warning("No high-confidence paystub data found in database")
                return None, "No high-confidence data available"
            
            logger.info(f"Fetched {len(response.data)} high-confidence paystubs from database")
            
            # Convert to features
            features_list = []
            for record in response.data:
                features = self._extract_features_from_record(record)
                if features is not None:
                    features_list.append(features)
            
            if not features_list:
                return None, "Failed to extract features from database rows"
            
            df = pd.DataFrame(features_list)
            logger.info(f"Extracted {len(df)} paystub samples with {len(df.columns)} features")
            return df, None
            
        except Exception as e:
            logger.error(f"Error fetching paystub data: {e}", exc_info=True)
            return None, str(e)
    
    def _extract_features_from_record(self, record: Dict) -> Dict:
        """Extract 18 features from database record"""
        try:
            # Extract amounts
            gross_pay = float(record.get('gross_pay') or 0)
            net_pay = float(record.get('net_pay') or 0)
            
            # Parse deductions JSON
            import json
            deductions = record.get('deductions')
            if isinstance(deductions, str):
                try:
                    deductions = json.loads(deductions)
                except:
                    deductions = []
            elif not isinstance(deductions, list):
                deductions = []
            
            # Extract tax amounts from deductions
            federal_tax = 0.0
            state_tax = 0.0
            social_security = 0.0
            medicare = 0.0
            
            for deduction in deductions:
                if isinstance(deduction, dict):
                    name = str(deduction.get('name', '')).lower()
                    amount = float(deduction.get('amount', 0) or 0)
                    
                    if 'federal' in name or 'fed' in name:
                        federal_tax += amount
                    elif 'state' in name:
                        state_tax += amount
                    elif 'social security' in name or 'fica' in name:
                        social_security += amount
                    elif 'medicare' in name:
                        medicare += amount
            
            # Calculate derived features
            total_tax = federal_tax + state_tax + social_security + medicare
            tax_to_gross_ratio = (total_tax / gross_pay) if gross_pay > 0 else 0.0
            net_to_gross_ratio = (net_pay / gross_pay) if gross_pay > 0 else 0.0
            deduction_percentage = ((gross_pay - net_pay) / gross_pay) if gross_pay > 0 else 0.0
            
            # Count missing fields
            critical_fields = [
                record.get('employer_name'),
                record.get('employee_name'),
                gross_pay if gross_pay > 0 else None,
                net_pay if net_pay > 0 else None
            ]
            missing_count = sum(1 for field in critical_fields if not field)
            
            # Text quality based on completeness
            present_count = len(critical_fields) - missing_count
            text_quality = 0.5 + (present_count / 4.0) * 0.5
            
            # Map recommendation to fraud score (0-100)
            recommendation = record.get('ai_recommendation', 'APPROVE').upper()
            fraud_risk_score = record.get('fraud_risk_score', None)  # Correct column name

            # Convert from 0-1 range to 0-100 range if needed
            if fraud_risk_score is not None and fraud_risk_score <= 1.0:
                fraud_risk_score = fraud_risk_score * 100.0

            if fraud_risk_score is None:
                # Fallback: REJECT=80, ESCALATE=50, APPROVE=10
                if recommendation == 'REJECT':
                    fraud_risk_score = 80.0
                elif recommendation == 'ESCALATE':
                    fraud_risk_score = 50.0
                else:
                    fraud_risk_score = 10.0
            
            # Build feature dict (18 features + target)
            features = {
                # Basic presence flags (1-5)
                'has_company': 1.0 if record.get('employer_name') else 0.0,
                'has_employee': 1.0 if record.get('employee_name') else 0.0,
                'has_gross': 1.0 if gross_pay > 0 else 0.0,
                'has_net': 1.0 if net_pay > 0 else 0.0,
                'has_date': 1.0,  # Assume date is present if record exists
                
                # Amounts (6-7)
                'gross_pay': min(gross_pay, 100000.0),
                'net_pay': min(net_pay, 100000.0),
                
                # Errors and quality (8-10)
                'tax_error': 1.0 if (gross_pay > 0 and net_pay >= gross_pay) else 0.0,
                'text_quality': text_quality,
                'missing_fields_count': float(missing_count),
                
                # Tax features (11-16)
                'has_federal_tax': 1.0 if federal_tax > 0 else 0.0,
                'has_state_tax': 1.0 if state_tax > 0 else 0.0,
                'has_social_security': 1.0 if social_security > 0 else 0.0,
                'has_medicare': 1.0 if medicare > 0 else 0.0,
                'total_tax_amount': min(total_tax, 50000.0),
                'tax_to_gross_ratio': min(tax_to_gross_ratio, 1.0),
                
                # Proportion features (17-18)
                'net_to_gross_ratio': min(net_to_gross_ratio, 1.0),
                'deduction_percentage': min(deduction_percentage, 1.0),
                
                # Target variable
                'risk_score': float(fraud_risk_score)
            }
            
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting features from record: {e}")
            return None
    
    def generate_synthetic_data(self, n_samples: int) -> pd.DataFrame:
        """
        Generate realistic synthetic paystub data
        Creates 50% legitimate, 50% fraudulent samples
        """
        np.random.seed(42)
        synthetic_data = []
        
        legitimate_count = n_samples // 2
        fraudulent_count = n_samples - legitimate_count
        
        # Generate legitimate paystubs
        for _ in range(legitimate_count):
            gross = np.random.uniform(2000, 15000)
            
            # Realistic tax rates
            federal_tax_rate = np.random.uniform(0.10, 0.25)
            state_tax_rate = np.random.uniform(0.03, 0.08)
            ss_rate = 0.062
            medicare_rate = 0.0145
            
            federal_tax = gross * federal_tax_rate
            state_tax = gross * state_tax_rate
            social_security = gross * ss_rate
            medicare = gross * medicare_rate
            total_tax = federal_tax + state_tax + social_security + medicare
            
            net = gross - total_tax
            
            features = {
                'has_company': 1.0,
                'has_employee': 1.0,
                'has_gross': 1.0,
                'has_net': 1.0,
                'has_date': 1.0,
                'gross_pay': gross,
                'net_pay': net,
                'tax_error': 0.0,
                'text_quality': np.random.uniform(0.85, 1.0),
                'missing_fields_count': 0.0,
                'has_federal_tax': 1.0,
                'has_state_tax': 1.0,
                'has_social_security': 1.0,
                'has_medicare': 1.0,
                'total_tax_amount': total_tax,
                'tax_to_gross_ratio': total_tax / gross,
                'net_to_gross_ratio': net / gross,
                'deduction_percentage': total_tax / gross,
                'risk_score': np.random.uniform(5, 25)  # Low fraud score
            }
            synthetic_data.append(features)
        
        # Generate fraudulent paystubs
        for _ in range(fraudulent_count):
            fraud_type = np.random.choice(['zero_withholding', 'inflated_income', 'missing_fields'])
            
            if fraud_type == 'zero_withholding':
                # Zero or very low taxes (fraud indicator)
                gross = np.random.uniform(3000, 20000)
                total_tax = np.random.uniform(0, gross * 0.02)  # 0-2% tax (suspicious)
                net = gross - total_tax
                
                features = {
                    'has_company': 1.0,
                    'has_employee': 1.0,
                    'has_gross': 1.0,
                    'has_net': 1.0,
                    'has_date': 1.0,
                    'gross_pay': gross,
                    'net_pay': net,
                    'tax_error': 0.0,
                    'text_quality': np.random.uniform(0.7, 0.9),
                    'missing_fields_count': 0.0,
                    'has_federal_tax': 0.0,  # Missing taxes
                    'has_state_tax': 0.0,
                    'has_social_security': 0.0,
                    'has_medicare': 0.0,
                    'total_tax_amount': total_tax,
                    'tax_to_gross_ratio': total_tax / gross,
                    'net_to_gross_ratio': net / gross,
                    'deduction_percentage': total_tax / gross,
                    'risk_score': np.random.uniform(85, 99)
                }
            
            elif fraud_type == 'inflated_income':
                # Unrealistically high income
                gross = np.random.uniform(50000, 100000)
                total_tax = gross * np.random.uniform(0.25, 0.35)
                net = gross - total_tax
                
                features = {
                    'has_company': 1.0,
                    'has_employee': 1.0,
                    'has_gross': 1.0,
                    'has_net': 1.0,
                    'has_date': 1.0,
                    'gross_pay': min(gross, 100000.0),
                    'net_pay': min(net, 100000.0),
                    'tax_error': 0.0,
                    'text_quality': np.random.uniform(0.6, 0.85),
                    'missing_fields_count': 0.0,
                    'has_federal_tax': 1.0,
                    'has_state_tax': 1.0,
                    'has_social_security': 1.0,
                    'has_medicare': 1.0,
                    'total_tax_amount': min(total_tax, 50000.0),
                    'tax_to_gross_ratio': min(total_tax / gross, 1.0),
                    'net_to_gross_ratio': min(net / gross, 1.0),
                    'deduction_percentage': min(total_tax / gross, 1.0),
                    'risk_score': np.random.uniform(75, 95)
                }
            
            else:  # missing_fields
                # Missing critical information
                gross = np.random.uniform(2000, 10000)
                net = gross * np.random.uniform(0.7, 0.9)
                
                features = {
                    'has_company': np.random.choice([0.0, 1.0]),
                    'has_employee': np.random.choice([0.0, 1.0]),
                    'has_gross': 1.0,
                    'has_net': 1.0,
                    'has_date': np.random.choice([0.0, 1.0]),
                    'gross_pay': gross,
                    'net_pay': net,
                    'tax_error': 0.0,
                    'text_quality': np.random.uniform(0.5, 0.7),
                    'missing_fields_count': float(np.random.randint(2, 4)),
                    'has_federal_tax': 0.0,
                    'has_state_tax': 0.0,
                    'has_social_security': 0.0,
                    'has_medicare': 0.0,
                    'total_tax_amount': 0.0,
                    'tax_to_gross_ratio': 0.0,
                    'net_to_gross_ratio': net / gross,
                    'deduction_percentage': (gross - net) / gross,
                    'risk_score': np.random.uniform(70, 90)
                }
            
            synthetic_data.append(features)
        
        df = pd.DataFrame(synthetic_data)
        logger.info(f"Generated {len(df)} synthetic paystub samples (50% legitimate, 50% fraudulent)")
        return df


if __name__ == "__main__":
    print("=" * 60)
    print("Paystub Model Retrainer")
    print("=" * 60)
    
    retrainer = PaystubModelRetrainer()
    retrainer.retrain()
