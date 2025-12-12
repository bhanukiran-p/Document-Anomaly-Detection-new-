"""Money Order Normalization Module"""

class MoneyOrderNormalizerFactory:
    """Factory to create money order normalizers"""

    @staticmethod
    def get_normalizer(provider_name: str = None):
        """Get appropriate normalizer for the provider"""
        return MoneyOrderNormalizer()

class MoneyOrderNormalizer:
    """Base money order normalizer"""

    def normalize(self, extracted_data: dict) -> dict:
        """Normalize money order data"""
        return extracted_data

__all__ = ['MoneyOrderNormalizerFactory', 'MoneyOrderNormalizer']
