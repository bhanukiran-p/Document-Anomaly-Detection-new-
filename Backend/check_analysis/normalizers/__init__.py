from .chase import ChaseNormalizer
from .boa import BankOfAmericaNormalizer

class CheckNormalizerFactory:
    @staticmethod
    def get_normalizer(bank_name: str):
        name = bank_name.lower()
        if 'chase' in name:
            return ChaseNormalizer()
        if 'bank of america' in name:
            return BankOfAmericaNormalizer()
        return None
