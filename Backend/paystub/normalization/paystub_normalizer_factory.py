"""
Paystub Normalizer Factory
Creates appropriate normalizer based on employer
"""

class PaystubNormalizer:
    """Base paystub normalizer"""

    def normalize(self, extracted_data: dict) -> dict:
        """Normalize paystub data"""
        return extracted_data

class PaystubNormalizerFactory:
    """Factory to create paystub normalizers"""

    @staticmethod
    def get_normalizer(employer_name: str = None):
        """
        Get appropriate normalizer for the employer

        Args:
            employer_name: Name of the employer (optional)

        Returns:
            PaystubNormalizer instance
        """
        return PaystubNormalizer()
