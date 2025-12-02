"""
Feature Extractor for Paystub Fraud Detection
Converts extracted paystub data into ML features matching the trained model schema
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PaystubFeatureExtractor:
    """
    Extract ML features from paystub data for fraud detection
    Extracts 10 features matching the trained model schema:
    - has_company, has_employee, has_gross, has_net, has_date
    - gross_pay, net_pay, tax_error, text_quality, missing_fields_count
    """

    def __init__(self):
        self.feature_names = [
            'has_company',
            'has_employee',
            'has_gross',
            'has_net',
            'has_date',
            'gross_pay',
            'net_pay',
            'tax_error',
            'text_quality',
            'missing_fields_count'
        ]

    def extract_features(self, paystub_data: Dict, raw_text: str = "") -> List[float]:
        """
        Extract 10 features from paystub data matching trained model schema

        Args:
            paystub_data: Extracted/normalized paystub data
            raw_text: Raw OCR text (optional, for text quality calculation)

        Returns:
            List of 10 float values representing features
        """
        features = []

        # Feature 1: has_company (1 if company_name exists, 0 otherwise)
        features.append(1.0 if paystub_data.get('company_name') else 0.0)

        # Feature 2: has_employee (1 if employee_name exists, 0 otherwise)
        features.append(1.0 if paystub_data.get('employee_name') else 0.0)

        # Feature 3: has_gross (1 if gross_pay exists, 0 otherwise)
        features.append(1.0 if paystub_data.get('gross_pay') else 0.0)

        # Feature 4: has_net (1 if net_pay exists, 0 otherwise)
        features.append(1.0 if paystub_data.get('net_pay') else 0.0)

        # Feature 5: has_date (1 if pay_period_start or pay_period_end exists, 0 otherwise)
        # Use pay_period_start or pay_period_end instead of pay_date
        has_date = 1.0 if (paystub_data.get('pay_period_start') or paystub_data.get('pay_period_end')) else 0.0
        features.append(has_date)

        # Feature 6: gross_pay (numeric value, capped at reasonable max)
        try:
            gross = self._extract_numeric_value(paystub_data.get('gross_pay', 0))
            features.append(min(gross, 100000.0))  # Cap at $100k
        except:
            features.append(0.0)

        # Feature 7: net_pay (numeric value, capped at reasonable max)
        try:
            net = self._extract_numeric_value(paystub_data.get('net_pay', 0))
            features.append(min(net, 100000.0))  # Cap at $100k
        except:
            features.append(0.0)

        # Feature 8: tax_error (1 if net >= gross, 0 otherwise)
        try:
            gross = self._extract_numeric_value(paystub_data.get('gross_pay', 0))
            net = self._extract_numeric_value(paystub_data.get('net_pay', 0))
            tax_error = 1.0 if (gross > 0 and net >= gross) else 0.0
            features.append(tax_error)
        except:
            features.append(0.0)

        # Feature 9: text_quality (0.5-1.0 based on field completeness)
        # Calculate based on how many critical fields are present
        # Use pay_period_start or pay_period_end instead of pay_date
        critical_fields = ['company_name', 'employee_name', 'gross_pay', 'net_pay']
        present_fields = sum(1 for field in critical_fields if paystub_data.get(field))
        # Check for date fields (pay_period_start or pay_period_end)
        has_date_field = 1 if (paystub_data.get('pay_period_start') or paystub_data.get('pay_period_end')) else 0
        present_fields += has_date_field
        text_quality = 0.5 + (present_fields / 5.0) * 0.5  # Range: 0.5-1.0 (5 fields total)
        features.append(text_quality)

        # Feature 10: missing_fields_count (0-5)
        # Use pay_period_start or pay_period_end instead of pay_date
        critical_fields = ['company_name', 'employee_name', 'gross_pay', 'net_pay']
        missing_count = sum(1 for field in critical_fields if not paystub_data.get(field))
        # Check for date fields
        if not (paystub_data.get('pay_period_start') or paystub_data.get('pay_period_end')):
            missing_count += 1
        features.append(float(missing_count))

        logger.debug(f"Extracted {len(features)} features: {features}")
        return features

    def _extract_numeric_value(self, value) -> float:
        """Extract numeric value from various formats"""
        if value is None:
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove commas, dollar signs, and whitespace
            cleaned = value.replace(',', '').replace('$', '').replace(' ', '').strip()
            try:
                return float(cleaned)
            except:
                return 0.0
        
        return 0.0

    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.feature_names.copy()

