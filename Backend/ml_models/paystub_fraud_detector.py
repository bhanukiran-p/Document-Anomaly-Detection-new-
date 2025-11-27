"""
Paystub Fraud Detector
ML-based fraud detection for paystubs
"""

import numpy as np
from typing import Dict, List

class PaystubFraudDetector:
    """
    Fraud detection for Paystubs
    Currently uses heuristic rules as we don't have a trained model yet.
    """

    def __init__(self):
        self.feature_names = [
            'net_pay_vs_gross_pay',
            'taxes_present',
            'round_numbers',
            'future_date',
            'missing_critical_fields',
            'ytd_consistency'
        ]

    def predict_fraud(self, extracted_data: Dict, raw_text: str = "") -> Dict:
        """
        Predict fraud probability for a paystub
        """
        # Extract features
        features = self._extract_features(extracted_data)
        
        # Generate prediction (Mock/Heuristic for now)
        return self._heuristic_predict(features, extracted_data)

    def _extract_features(self, data: Dict) -> List[float]:
        """
        Extract numerical features from paystub data
        """
        features = []
        
        # 1. Net Pay vs Gross Pay Ratio (Should be < 1)
        try:
            gross = float(str(data.get('gross_pay', '0')).replace(',', ''))
            net = float(str(data.get('net_pay', '0')).replace(',', ''))
            if gross > 0:
                features.append(net / gross)
            else:
                features.append(0.0)
        except:
            features.append(0.0)
            
        # 2. Taxes Present (1 if yes, 0 if no)
        has_taxes = 1.0 if (data.get('federal_tax') or data.get('state_tax') or 
                           data.get('social_security') or data.get('medicare')) else 0.0
        features.append(has_taxes)
        
        # 3. Round Numbers (1 if Net Pay is exactly round, e.g., 5000.00)
        try:
            net = float(str(data.get('net_pay', '0')).replace(',', ''))
            if net > 0 and net % 100 == 0:
                features.append(1.0)
            else:
                features.append(0.0)
        except:
            features.append(0.0)
            
        # 4. Future Date (1 if yes)
        # (Skipping complex date parsing for this snippet, assuming 0 for now)
        features.append(0.0)
        
        # 5. Missing Critical Fields
        critical = ['company_name', 'employee_name', 'gross_pay', 'net_pay', 'pay_date']
        missing = sum(1 for f in critical if not data.get(f))
        features.append(float(missing))
        
        # 6. YTD Consistency (1 if YTD >= Current)
        try:
            gross = float(str(data.get('gross_pay', '0')).replace(',', ''))
            ytd_gross = float(str(data.get('ytd_gross', '0')).replace(',', ''))
            if ytd_gross >= gross:
                features.append(1.0)
            else:
                features.append(0.0) # Inconsistent
        except:
            features.append(1.0) # Assume consistent if missing
            
        return features

    def _heuristic_predict(self, features: List[float], data: Dict) -> Dict:
        """
        Generate risk score based on features
        """
        risk_score = 0.0
        indicators = []
        
        # Unpack features
        net_gross_ratio = features[0]
        has_taxes = features[1]
        is_round_number = features[2]
        is_future_date = features[3]
        missing_fields = features[4]
        ytd_consistent = features[5]
        
        # Rule 1: Net Pay > Gross Pay (Impossible)
        if net_gross_ratio > 1.0:
            risk_score += 0.5
            indicators.append("CRITICAL: Net Pay is greater than Gross Pay")
            
        # Rule 2: No Taxes (Suspicious for standard employment)
        if has_taxes == 0.0:
            risk_score += 0.3
            indicators.append("No tax withholdings detected")
            
        # Rule 3: Round Numbers (Often fake)
        if is_round_number == 1.0:
            risk_score += 0.2
            indicators.append("Net Pay is a perfect round number (suspicious)")
            
        # Rule 4: Missing Fields
        if missing_fields > 0:
            risk_score += (missing_fields * 0.1)
            indicators.append(f"Missing {int(missing_fields)} critical fields")
            
        # Rule 5: YTD Inconsistency
        if ytd_consistent == 0.0:
            risk_score += 0.3
            indicators.append("YTD Gross is less than Current Gross")
            
        # Cap score
        risk_score = min(1.0, risk_score)
        
        # Determine level
        if risk_score < 0.3:
            risk_level = 'LOW'
        elif risk_score < 0.7:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
            
        return {
            'fraud_risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'model_confidence': 0.85, # Static confidence for heuristic
            'model_scores': {
                'heuristic': round(risk_score, 2)
            },
            'feature_importance': indicators
        }
