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
    Extracts 18 features matching the trained model schema:
    - Basic fields: has_company, has_employee, has_gross, has_net, has_date
    - Amounts: gross_pay, net_pay
    - Errors: tax_error, text_quality, missing_fields_count
    - Taxes: has_federal_tax, has_state_tax, has_social_security, has_medicare, total_tax_amount, tax_to_gross_ratio
    - Proportions: net_to_gross_ratio, deduction_percentage
    """

    def __init__(self):
        self.feature_names = [
            # Basic presence flags (1-5)
            'has_company',
            'has_employee',
            'has_gross',
            'has_net',
            'has_date',
            # Amounts (6-7)
            'gross_pay',
            'net_pay',
            # Errors and quality (8-10)
            'tax_error',
            'text_quality',
            'missing_fields_count',
            # Tax presence and amounts (11-16)
            'has_federal_tax',
            'has_state_tax',
            'has_social_security',
            'has_medicare',
            'total_tax_amount',
            'tax_to_gross_ratio',
            # Proportion features (17-18)
            'net_to_gross_ratio',
            'deduction_percentage'
        ]

    def extract_features(self, paystub_data: Dict, raw_text: str = "") -> List[float]:
        """
        Extract 18 features from paystub data matching trained model schema
        NO FALLBACKS - All features must be extracted, missing values become 0.0

        Args:
            paystub_data: Extracted/normalized paystub data
            raw_text: Raw OCR text (optional, for text quality calculation)

        Returns:
            List of 18 float values representing features
        """
        features = []

        # ===== BASIC PRESENCE FLAGS (Features 1-5) =====
        # Feature 1: has_company
        features.append(1.0 if paystub_data.get('company_name') else 0.0)

        # Feature 2: has_employee
        features.append(1.0 if paystub_data.get('employee_name') else 0.0)

        # Feature 3: has_gross
        features.append(1.0 if paystub_data.get('gross_pay') else 0.0)

        # Feature 4: has_net
        features.append(1.0 if paystub_data.get('net_pay') else 0.0)

        # Feature 5: has_date
        has_date = 1.0 if (paystub_data.get('pay_period_start') or paystub_data.get('pay_period_end')) else 0.0
        features.append(has_date)

        # ===== AMOUNTS (Features 6-7) =====
        # Feature 6: gross_pay (capped at $100k)
        gross = self._extract_numeric_value(paystub_data.get('gross_pay', 0))
        features.append(min(gross, 100000.0))

        # Feature 7: net_pay (capped at $100k)
        net = self._extract_numeric_value(paystub_data.get('net_pay', 0))
        features.append(min(net, 100000.0))

        # ===== ERRORS AND QUALITY (Features 8-10) =====
        # Feature 8: tax_error (1 if net >= gross, 0 otherwise)
        tax_error = 1.0 if (gross > 0 and net >= gross) else 0.0
        features.append(tax_error)

        # Feature 9: text_quality (0.5-1.0 based on field completeness)
        critical_fields = ['company_name', 'employee_name', 'gross_pay', 'net_pay']
        present_fields = sum(1 for field in critical_fields if paystub_data.get(field))
        has_date_field = 1 if (paystub_data.get('pay_period_start') or paystub_data.get('pay_period_end')) else 0
        present_fields += has_date_field
        text_quality = 0.5 + (present_fields / 5.0) * 0.5  # Range: 0.5-1.0
        features.append(text_quality)

        # Feature 10: missing_fields_count (0-5)
        critical_fields = ['company_name', 'employee_name', 'gross_pay', 'net_pay']
        missing_count = sum(1 for field in critical_fields if not paystub_data.get(field))
        if not (paystub_data.get('pay_period_start') or paystub_data.get('pay_period_end')):
            missing_count += 1
        features.append(float(missing_count))

        # ===== TAX FEATURES (Features 11-16) =====
        # Extract tax amounts
        federal_tax = self._extract_numeric_value(paystub_data.get('federal_tax', 0))
        state_tax = self._extract_numeric_value(paystub_data.get('state_tax', 0))
        social_security = self._extract_numeric_value(paystub_data.get('social_security', 0))
        medicare = self._extract_numeric_value(paystub_data.get('medicare', 0))

        # Feature 11: has_federal_tax
        features.append(1.0 if federal_tax > 0 else 0.0)

        # Feature 12: has_state_tax
        features.append(1.0 if state_tax > 0 else 0.0)

        # Feature 13: has_social_security
        features.append(1.0 if social_security > 0 else 0.0)

        # Feature 14: has_medicare
        features.append(1.0 if medicare > 0 else 0.0)

        # Feature 15: total_tax_amount (sum of all taxes, capped at $50k)
        total_tax = federal_tax + state_tax + social_security + medicare
        features.append(min(total_tax, 50000.0))

        # Feature 16: tax_to_gross_ratio (total_tax / gross_pay, capped at 1.0)
        tax_to_gross_ratio = (total_tax / gross) if gross > 0 else 0.0
        features.append(min(tax_to_gross_ratio, 1.0))

        # ===== PROPORTION FEATURES (Features 17-18) =====
        # Feature 17: net_to_gross_ratio (net_pay / gross_pay, capped at 1.0)
        net_to_gross_ratio = (net / gross) if gross > 0 else 0.0
        features.append(min(net_to_gross_ratio, 1.0))

        # Feature 18: deduction_percentage ((gross - net) / gross, capped at 1.0)
        deduction_amount = gross - net
        deduction_percentage = (deduction_amount / gross) if gross > 0 else 0.0
        features.append(min(deduction_percentage, 1.0))

        # Validate we have exactly 18 features
        if len(features) != 18:
            raise RuntimeError(
                f"Feature extraction failed: Expected 18 features, got {len(features)}. "
                f"This is a critical error - no fallback available."
            )

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

