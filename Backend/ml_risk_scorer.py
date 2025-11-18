"""
ML-Based Risk Scoring Module for Document Fraud Detection
Provides risk scoring, risk factors, and recommendations for all document types
Supports both trained ML models and weighted scoring fallback
"""

import re
import os
import pickle
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class MLRiskScorer:
    """
    ML-based risk scoring system for document fraud detection
    Uses trained ML models for real-time inference, falls back to weighted scoring
    """
    
    def __init__(self, models_dir='models'):
        """
        Initialize the risk scorer
        
        Args:
            models_dir: Directory containing trained models
        """
        self.models_dir = models_dir
        self.trained_models = {}  # Cache loaded models
        self.model_metadata = {}  # Cache model metadata
        
        # Load trained models if available
        self._load_trained_models()
        
        # Known suspicious patterns
        self.suspicious_patterns = {
            'amount_manipulation': [
                r'\d+\.\d{3,}',  # More than 2 decimal places
                r'[0-9]{6,}',  # Very large numbers
            ],
            'date_anomalies': [
                r'20[0-9]{2}-[0-9]{2}-[0-9]{2}',  # Future dates
            ],
            'text_quality': [
                r'[A-Z]{10,}',  # All caps long strings
                r'[!@#$%^&*]{3,}',  # Excessive special chars
            ],
        }
        
        # Risk weights for different document types (fallback when no model)
        self.risk_weights = {
            'check': {
                'missing_critical_fields': 0.30,
                'amount_anomalies': 0.25,
                'date_anomalies': 0.15,
                'signature_issues': 0.10,
                'text_quality': 0.10,
                'pattern_anomalies': 0.10,
            },
            'paystub': {
                'missing_critical_fields': 0.25,
                'amount_anomalies': 0.20,
                'tax_calculation_errors': 0.20,
                'date_anomalies': 0.15,
                'text_quality': 0.10,
                'pattern_anomalies': 0.10,
            },
            'money_order': {
                'missing_critical_fields': 0.30,
                'amount_anomalies': 0.25,
                'issuer_verification': 0.15,
                'date_anomalies': 0.10,
                'text_quality': 0.10,
                'pattern_anomalies': 0.10,
            },
            'bank_statement': {
                'missing_critical_fields': 0.25,
                'transaction_anomalies': 0.25,
                'balance_inconsistencies': 0.20,
                'date_anomalies': 0.15,
                'text_quality': 0.10,
                'pattern_anomalies': 0.05,
            },
        }
    
    def _load_trained_models(self):
        """Load trained ML models from disk if available"""
        if not os.path.exists(self.models_dir):
            return
        
        document_types = ['check', 'paystub', 'money_order', 'bank_statement']
        
        for doc_type in document_types:
            model_path = os.path.join(self.models_dir, f"{doc_type}_risk_model_latest.pkl")
            scaler_path = os.path.join(self.models_dir, f"{doc_type}_scaler_latest.pkl")
            metadata_path = os.path.join(self.models_dir, f"{doc_type}_model_metadata_latest.json")
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                try:
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    with open(scaler_path, 'rb') as f:
                        scaler = pickle.load(f)
                    
                    metadata = {}
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    
                    self.trained_models[doc_type] = {
                        'model': model,
                        'scaler': scaler,
                        'metadata': metadata
                    }
                    print(f"Loaded trained {doc_type} risk model")
                except Exception as e:
                    print(f"Warning: Failed to load {doc_type} model: {e}")
    
    def calculate_risk_score(
        self, 
        document_type: str, 
        extracted_data: Dict, 
        raw_text: str = ""
    ) -> Dict:
        """
        Calculate ML-based risk score for a document
        Uses trained ML model if available, otherwise falls back to weighted scoring
        
        Args:
            document_type: Type of document ('check', 'paystub', 'money_order', 'bank_statement')
            extracted_data: Extracted data from the document
            raw_text: Raw OCR text (optional)
        
        Returns:
            Dictionary with risk_score, risk_factors, and recommendations
        """
        if document_type not in self.risk_weights:
            document_type = 'check'  # Default
        
        # Extract features
        features = self._extract_features(document_type, extracted_data, raw_text)
        
        # Try to use trained ML model first
        risk_score = None
        use_ml_model = False
        
        if document_type in self.trained_models:
            try:
                risk_score = self._predict_with_model(document_type, features, extracted_data)
                use_ml_model = True
            except Exception as e:
                print(f"Warning: ML model prediction failed, using fallback: {e}")
        
        # Fallback to weighted scoring if no model or model failed
        if risk_score is None:
            # Calculate risk components
            risk_components = self._calculate_risk_components(
                document_type, features, extracted_data
            )
            
            # Calculate overall risk score (0-100, higher = more risky)
            risk_score = self._calculate_overall_risk(
                document_type, risk_components
            )
            use_ml_model = False
        
        # Calculate risk components for risk factor identification
        risk_components = self._calculate_risk_components(
            document_type, features, extracted_data
        )
        
        # Calculate overall risk for context (if not already calculated)
        if not use_ml_model:
            calculated_risk = risk_score
        else:
            # Calculate weighted risk for factor severity determination
            calculated_risk = self._calculate_overall_risk(document_type, risk_components)
        
        # Identify risk factors (pass overall risk for context)
        risk_factors = self._identify_risk_factors(
            document_type, risk_components, extracted_data, calculated_risk
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            document_type, risk_score, risk_factors, extracted_data
        )
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': self._get_risk_level(risk_score),
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'risk_components': risk_components,
            'model_used': 'ml_model' if use_ml_model else 'weighted_scoring',
            'timestamp': datetime.now().isoformat(),
        }
    
    def _predict_with_model(
        self, 
        document_type: str, 
        features: Dict, 
        extracted_data: Dict
    ) -> float:
        """
        Predict risk score using trained ML model
        
        Args:
            document_type: Type of document
            features: Extracted features
            extracted_data: Original extracted data
            
        Returns:
            Risk score (0-100)
        """
        model_info = self.trained_models[document_type]
        model = model_info['model']
        scaler = model_info['scaler']
        metadata = model_info.get('metadata', {})
        feature_names = metadata.get('feature_names', [])
        
        # Extract features in the same format as training
        feature_vector = self._extract_model_features(
            document_type, features, extracted_data, feature_names
        )
        
        # Scale features
        feature_vector_scaled = scaler.transform([feature_vector])
        
        # Predict
        risk_score = model.predict(feature_vector_scaled)[0]
        
        # Ensure score is in valid range
        risk_score = max(0.0, min(100.0, float(risk_score)))
        
        return risk_score
    
    def _extract_model_features(
        self,
        document_type: str,
        features: Dict,
        extracted_data: Dict,
        feature_names: List[str]
    ) -> List[float]:
        """
        Extract features in the format expected by the trained model
        
        Returns:
            Feature vector as list of floats
        """
        feature_dict = {}
        
        if document_type == 'check':
            # Map to training feature format
            feature_dict['has_bank_name'] = 1 if extracted_data.get('bank_name') else 0
            feature_dict['has_payee'] = 1 if extracted_data.get('payee_name') else 0
            feature_dict['has_amount'] = 1 if extracted_data.get('amount_numeric') else 0
            feature_dict['has_date'] = 1 if extracted_data.get('date') else 0
            feature_dict['has_signature'] = 1 if extracted_data.get('signature_detected') else 0
            
            amount = extracted_data.get('amount_numeric', 0)
            try:
                amount_val = float(str(amount).replace(',', '').replace('$', ''))
            except:
                amount_val = 0.0
            
            feature_dict['amount_value'] = amount_val
            feature_dict['amount_suspicious'] = 1 if amount_val > 100000 or amount_val < 0 else 0
            
            date_anom = features.get('date_anomalies', {})
            feature_dict['date_valid'] = 0 if date_anom.get('invalid_date') else 1
            feature_dict['date_future'] = 1 if date_anom.get('future_date') else 0
            
            text_qual = features.get('text_quality', {})
            feature_dict['text_quality'] = min(1.0, max(0.0, 1.0 - (text_qual.get('suspicious_chars', 0) / 10.0)))
            feature_dict['suspicious_chars'] = text_qual.get('suspicious_chars', 0)
            
            completeness = features.get('field_completeness', {})
            missing_count = sum(1 for v in completeness.values() if v == 0)
            feature_dict['missing_fields_count'] = missing_count
        
        elif document_type == 'paystub':
            feature_dict['has_company'] = 1 if extracted_data.get('company_name') else 0
            feature_dict['has_employee'] = 1 if extracted_data.get('employee_name') else 0
            feature_dict['has_gross'] = 1 if extracted_data.get('gross_pay') else 0
            feature_dict['has_net'] = 1 if extracted_data.get('net_pay') else 0
            feature_dict['has_date'] = 1 if extracted_data.get('pay_date') else 0
            
            gross = extracted_data.get('gross_pay', 0)
            net = extracted_data.get('net_pay', 0)
            try:
                gross_val = float(str(gross).replace(',', '').replace('$', ''))
                net_val = float(str(net).replace(',', '').replace('$', ''))
            except:
                gross_val = 0.0
                net_val = 0.0
            
            feature_dict['gross_pay'] = gross_val
            feature_dict['net_pay'] = net_val
            feature_dict['tax_error'] = 1 if net_val >= gross_val else 0
            
            text_qual = features.get('text_quality', {})
            feature_dict['text_quality'] = min(1.0, max(0.0, 1.0 - (text_qual.get('suspicious_chars', 0) / 10.0)))
            
            completeness = features.get('field_completeness', {})
            missing_count = sum(1 for v in completeness.values() if v == 0)
            feature_dict['missing_fields_count'] = missing_count
        
        # Build feature vector in the order expected by the model
        feature_vector = []
        for name in feature_names:
            feature_vector.append(feature_dict.get(name, 0.0))
        
        return feature_vector
    
    def _extract_features(
        self, 
        document_type: str, 
        extracted_data: Dict, 
        raw_text: str
    ) -> Dict:
        """Extract features from document for ML analysis"""
        features = {
            'field_completeness': {},
            'numeric_anomalies': {},
            'date_anomalies': {},
            'text_quality': {},
            'pattern_matches': {},
        }
        
        # Field completeness
        if document_type == 'check':
            critical_fields = ['bank_name', 'payee_name', 'amount_numeric', 'date']
            for field in critical_fields:
                features['field_completeness'][field] = 1 if extracted_data.get(field) else 0
        
        elif document_type == 'paystub':
            critical_fields = ['company_name', 'employee_name', 'gross_pay', 'net_pay', 'pay_date']
            for field in critical_fields:
                features['field_completeness'][field] = 1 if extracted_data.get(field) else 0
        
        elif document_type == 'money_order':
            critical_fields = ['issuer', 'amount', 'payee', 'serial_number']
            for field in critical_fields:
                features['field_completeness'][field] = 1 if extracted_data.get(field) else 0
        
        elif document_type == 'bank_statement':
            critical_fields = ['bank_name', 'account_number', 'statement_period', 'balances']
            for field in critical_fields:
                features['field_completeness'][field] = 1 if extracted_data.get(field) else 0
        
        # Numeric anomalies
        if document_type == 'check':
            amount = extracted_data.get('amount_numeric')
            if amount:
                try:
                    amount_val = float(str(amount).replace(',', '').replace('$', ''))
                    features['numeric_anomalies']['amount'] = amount_val
                    features['numeric_anomalies']['amount_suspicious'] = 1 if amount_val > 100000 or amount_val < 0 else 0
                except:
                    features['numeric_anomalies']['amount_suspicious'] = 1
        
        # Date anomalies
        date_str = extracted_data.get('date') or extracted_data.get('pay_date')
        if date_str:
            try:
                # Check if date is in future
                date_obj = self._parse_date(date_str)
                if date_obj:
                    if date_obj > datetime.now():
                        features['date_anomalies']['future_date'] = 1
                    else:
                        features['date_anomalies']['future_date'] = 0
            except:
                features['date_anomalies']['invalid_date'] = 1
        
        # Text quality
        if raw_text:
            features['text_quality']['length'] = len(raw_text)
            features['text_quality']['suspicious_chars'] = len(re.findall(r'[!@#$%^&*]{2,}', raw_text))
        
        return features
    
    def _calculate_risk_components(
        self, 
        document_type: str, 
        features: Dict, 
        extracted_data: Dict
    ) -> Dict:
        """Calculate individual risk components"""
        components = {}
        weights = self.risk_weights.get(document_type, self.risk_weights['check'])
        
        # Missing critical fields
        completeness = features.get('field_completeness', {})
        missing_count = sum(1 for v in completeness.values() if v == 0)
        total_fields = len(completeness) if completeness else 1
        components['missing_critical_fields'] = (missing_count / total_fields) * 100 if total_fields > 0 else 0
        
        # Amount anomalies
        numeric = features.get('numeric_anomalies', {})
        if numeric.get('amount_suspicious'):
            components['amount_anomalies'] = 80.0
        else:
            components['amount_anomalies'] = 0.0
        
        # Date anomalies
        date_anom = features.get('date_anomalies', {})
        if date_anom.get('future_date'):
            components['date_anomalies'] = 70.0
        elif date_anom.get('invalid_date'):
            components['date_anomalies'] = 50.0
        else:
            components['date_anomalies'] = 0.0
        
        # Text quality
        text_qual = features.get('text_quality', {})
        if text_qual.get('suspicious_chars', 0) > 5:
            components['text_quality'] = 60.0
        else:
            components['text_quality'] = 0.0
        
        # Pattern anomalies
        components['pattern_anomalies'] = 0.0  # Can be enhanced with pattern matching
        
        # Document-specific components
        if document_type == 'check':
            components['signature_issues'] = 0.0 if extracted_data.get('signature_detected') else 40.0
        
        elif document_type == 'paystub':
            # Tax calculation errors
            gross = extracted_data.get('gross_pay')
            net = extracted_data.get('net_pay')
            if gross and net:
                try:
                    gross_val = float(str(gross).replace(',', '').replace('$', ''))
                    net_val = float(str(net).replace(',', '').replace('$', ''))
                    if net_val >= gross_val:
                        components['tax_calculation_errors'] = 90.0
                    else:
                        components['tax_calculation_errors'] = 0.0
                except:
                    components['tax_calculation_errors'] = 30.0
            else:
                components['tax_calculation_errors'] = 0.0
        
        elif document_type == 'money_order':
            # Issuer verification
            issuer = extracted_data.get('issuer', '').upper()
            known_issuers = ['WESTERN UNION', 'MONEYGRAM', 'USPS', 'POSTAL SERVICE']
            if issuer and not any(k in issuer for k in known_issuers):
                components['issuer_verification'] = 50.0
            else:
                components['issuer_verification'] = 0.0
        
        elif document_type == 'bank_statement':
            # Transaction anomalies
            transactions = extracted_data.get('transactions', [])
            if len(transactions) == 0:
                components['transaction_anomalies'] = 60.0
            else:
                components['transaction_anomalies'] = 0.0
            
            # Balance inconsistencies
            balances = extracted_data.get('balances', {})
            if not balances or not balances.get('current'):
                components['balance_inconsistencies'] = 50.0
            else:
                components['balance_inconsistencies'] = 0.0
        
        return components
    
    def _calculate_overall_risk(
        self, 
        document_type: str, 
        risk_components: Dict
    ) -> float:
        """Calculate overall risk score using weighted components"""
        weights = self.risk_weights.get(document_type, self.risk_weights['check'])
        
        total_risk = 0.0
        for component, weight in weights.items():
            component_risk = risk_components.get(component, 0.0)
            total_risk += component_risk * weight
        
        # Normalize to 0-100 scale
        return min(100.0, max(0.0, total_risk))
    
    def _identify_risk_factors(
        self, 
        document_type: str, 
        risk_components: Dict, 
        extracted_data: Dict,
        overall_risk_score: float = None
    ) -> List[Dict]:
        """Identify specific risk factors"""
        factors = []
        
        # Missing critical fields
        if risk_components.get('missing_critical_fields', 0) > 30:
            factors.append({
                'type': 'missing_fields',
                'severity': 'high',
                'message': 'Critical document fields are missing or incomplete',
                'impact': 'Unable to fully verify document authenticity'
            })
        
        # Amount anomalies
        if risk_components.get('amount_anomalies', 0) > 50:
            factors.append({
                'type': 'amount_anomaly',
                'severity': 'high',
                'message': 'Unusual or suspicious amount detected',
                'impact': 'Amount may be manipulated or incorrect'
            })
        
        # Date anomalies - calculate actual contribution to overall risk
        date_score = risk_components.get('date_anomalies', 0)
        if date_score > 0:
            # Get date weight for this document type
            weights = self.risk_weights.get(document_type, {})
            date_weight = weights.get('date_anomalies', 0.15)
            date_contribution = (date_score / 100) * date_weight * 100
            
            # Determine severity based on contribution
            # HIGH: contributes >10% to overall risk, MEDIUM: 5-10%, LOW: <5%
            if date_contribution > 10:
                severity = 'high'
            elif date_contribution > 5:
                severity = 'medium'
            else:
                severity = 'low'
            
            factors.append({
                'type': 'date_anomaly',
                'severity': severity,
                'message': 'Date appears to be invalid or in the future',
                'impact': f'Contributes {date_contribution:.1f}% to overall risk score'
            })
        
        # Document-specific factors
        if document_type == 'check':
            # Signature issues - only show as HIGH if it significantly impacts overall score
            signature_score = risk_components.get('signature_issues', 0)
            if signature_score > 30:
                # Calculate actual contribution to overall risk (signature has 10% weight)
                signature_contribution = (signature_score / 100) * 0.10 * 100  # Convert to percentage
                # Only show as HIGH if it contributes >5% to overall risk, otherwise MEDIUM
                severity = 'high' if signature_contribution > 5 else 'medium'
                factors.append({
                    'type': 'signature_missing',
                    'severity': severity,
                    'message': 'Signature not detected on check',
                    'impact': 'Check may be invalid without proper signature'
                })
            if not extracted_data.get('payee_name'):
                # Payee is critical (30% weight for missing fields), so this is HIGH
                factors.append({
                    'type': 'missing_payee',
                    'severity': 'high',
                    'message': 'Payee name is missing',
                    'impact': 'Cannot verify who the check is payable to'
                })
            if not extracted_data.get('bank_name'):
                # Bank name is part of missing fields (30% weight), but less critical alone
                factors.append({
                    'type': 'missing_bank',
                    'severity': 'medium',
                    'message': 'Bank name not identified',
                    'impact': 'Cannot verify issuing bank'
                })
            if not extracted_data.get('routing_number') and not extracted_data.get('micr_code'):
                # Routing number is optional (not in critical fields), so LOW severity
                # It doesn't directly contribute to risk score calculation
                factors.append({
                    'type': 'missing_routing',
                    'severity': 'low',
                    'message': 'Routing number or MICR code not found',
                    'impact': 'Cannot verify bank routing information (informational only)'
                })
        
        elif document_type == 'paystub':
            if risk_components.get('tax_calculation_errors', 0) > 50:
                factors.append({
                    'type': 'tax_calculation_error',
                    'severity': 'high',
                    'message': 'Net pay is greater than or equal to gross pay',
                    'impact': 'Tax calculations appear incorrect'
                })
            if not extracted_data.get('company_name'):
                factors.append({
                    'type': 'missing_company',
                    'severity': 'medium',
                    'message': 'Company name is missing',
                    'impact': 'Cannot verify employer information'
                })
            if not extracted_data.get('employee_name'):
                factors.append({
                    'type': 'missing_employee',
                    'severity': 'medium',
                    'message': 'Employee name is missing',
                    'impact': 'Cannot verify employee information'
                })
            if not extracted_data.get('gross_pay') or not extracted_data.get('net_pay'):
                factors.append({
                    'type': 'missing_pay_amounts',
                    'severity': 'high',
                    'message': 'Gross pay or net pay is missing',
                    'impact': 'Cannot verify payment amounts'
                })
            if not extracted_data.get('pay_date'):
                factors.append({
                    'type': 'missing_pay_date',
                    'severity': 'medium',
                    'message': 'Pay date is missing',
                    'impact': 'Cannot verify payment date'
                })
        
        elif document_type == 'money_order':
            if risk_components.get('issuer_verification', 0) > 30:
                factors.append({
                    'type': 'issuer_verification',
                    'severity': 'medium',
                    'message': 'Issuer not recognized or verified',
                    'impact': 'Money order may be from unverified source'
                })
            if not extracted_data.get('issuer'):
                factors.append({
                    'type': 'missing_issuer',
                    'severity': 'high',
                    'message': 'Money order issuer is missing',
                    'impact': 'Cannot verify money order source'
                })
            if not extracted_data.get('amount'):
                factors.append({
                    'type': 'missing_amount',
                    'severity': 'high',
                    'message': 'Money order amount is missing',
                    'impact': 'Cannot verify money order value'
                })
            if not extracted_data.get('serial_number') and not extracted_data.get('control_number'):
                factors.append({
                    'type': 'missing_serial',
                    'severity': 'medium',
                    'message': 'Serial number or control number not found',
                    'impact': 'Cannot track or verify money order'
                })
            if not extracted_data.get('purchaser_name'):
                factors.append({
                    'type': 'missing_purchaser',
                    'severity': 'medium',
                    'message': 'Purchaser name is missing',
                    'impact': 'Cannot verify who purchased the money order'
                })
        
        elif document_type == 'bank_statement':
            if risk_components.get('transaction_anomalies', 0) > 40:
                factors.append({
                    'type': 'transaction_anomaly',
                    'severity': 'medium',
                    'message': 'No transactions found or unusual transaction patterns',
                    'impact': 'Statement may be incomplete or altered'
                })
            if risk_components.get('balance_inconsistencies', 0) > 40:
                factors.append({
                    'type': 'balance_inconsistency',
                    'severity': 'high',
                    'message': 'Balance calculations appear inconsistent',
                    'impact': 'Statement may contain errors or be fraudulent'
                })
            if not extracted_data.get('bank_name'):
                factors.append({
                    'type': 'missing_bank',
                    'severity': 'medium',
                    'message': 'Bank name is missing',
                    'impact': 'Cannot verify issuing bank'
                })
            if not extracted_data.get('account_holder'):
                factors.append({
                    'type': 'missing_account_holder',
                    'severity': 'medium',
                    'message': 'Account holder name is missing',
                    'impact': 'Cannot verify account ownership'
                })
            transactions = extracted_data.get('transactions', [])
            if not transactions or len(transactions) == 0:
                factors.append({
                    'type': 'no_transactions',
                    'severity': 'high',
                    'message': 'No transactions found in statement',
                    'impact': 'Statement appears incomplete or invalid'
                })
            balances = extracted_data.get('balances', {})
            if not balances.get('ending_balance') and not balances.get('current_balance'):
                factors.append({
                    'type': 'missing_balance',
                    'severity': 'medium',
                    'message': 'Ending balance is missing',
                    'impact': 'Cannot verify account balance'
                })
        
        # Text quality
        if risk_components.get('text_quality', 0) > 40:
            factors.append({
                'type': 'text_quality',
                'severity': 'low',
                'message': 'Poor text quality or suspicious characters detected',
                'impact': 'Document may be altered or of poor quality'
            })
        
        return factors
    
    def _generate_recommendations(
        self, 
        document_type: str, 
        risk_score: float, 
        risk_factors: List[Dict], 
        extracted_data: Dict
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Base recommendations based on risk score
        if risk_score >= 70:
            recommendations.append("HIGH RISK: Request additional verification documents")
            recommendations.append("Contact the issuing institution to verify document authenticity")
            recommendations.append("Consider manual review by fraud detection specialist")
        elif risk_score >= 40:
            recommendations.append("MEDIUM RISK: Verify key information with source documents")
            recommendations.append("Cross-reference with known good documents if available")
        else:
            recommendations.append("LOW RISK: Document appears legitimate, proceed with standard verification")
        
        # Specific recommendations based on risk factors
        for factor in risk_factors:
            if factor['type'] == 'missing_fields':
                recommendations.append("ACTION: Request complete document with all required fields")
            elif factor['type'] == 'amount_anomaly':
                recommendations.append("ACTION: Verify amount with payee or issuing institution")
            elif factor['type'] == 'date_anomaly':
                recommendations.append("ACTION: Confirm document date is valid and current")
            elif factor['type'] == 'signature_missing':
                recommendations.append("ACTION: Ensure check has valid signature before processing")
            elif factor['type'] == 'tax_calculation_error':
                recommendations.append("ACTION: Verify tax calculations with payroll department")
            elif factor['type'] == 'issuer_verification':
                recommendations.append("ACTION: Verify money order issuer through official channels")
            elif factor['type'] == 'transaction_anomaly':
                recommendations.append("ACTION: Request complete bank statement with all transactions")
        
        # Document-specific recommendations
        if document_type == 'check':
            recommendations.append("NEXT STEP: Verify check with bank using routing and account numbers")
            recommendations.append("NEXT STEP: Check for duplicate check numbers in your records")
        
        elif document_type == 'paystub':
            recommendations.append("NEXT STEP: Verify employee information with HR department")
            recommendations.append("NEXT STEP: Cross-check YTD values with previous paystubs")
        
        elif document_type == 'money_order':
            recommendations.append("NEXT STEP: Verify money order serial number with issuer")
            recommendations.append("NEXT STEP: Confirm money order has not been cashed already")
        
        elif document_type == 'bank_statement':
            recommendations.append("NEXT STEP: Verify account balance with bank directly")
            recommendations.append("NEXT STEP: Review transaction history for unusual patterns")
        
        return recommendations
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level category"""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        return None

