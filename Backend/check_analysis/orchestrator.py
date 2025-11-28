"""
Check Analysis Orchestrator
Coordinates Extraction -> Normalization -> ML -> AI
"""

import os
from typing import Dict, Any, Optional
from .extractors import CheckVisionExtractor
from .normalizers import CheckNormalizerFactory
from .ml_models import CheckFraudDetector
from .ai_agent import CheckFraudAnalysisAgent

class CheckAnalysisOrchestrator:
    """
    Main orchestrator for check analysis
    """

    def __init__(self, credentials_path: Optional[str] = None):
        # 1. Initialize Extractor
        self.extractor = CheckVisionExtractor(credentials_path)
        
        # 2. Initialize ML Model
        self.ml_detector = CheckFraudDetector()
        
        # 3. Initialize AI Agent
        openai_key = os.getenv('OPENAI_API_KEY')
        self.ai_agent = CheckFraudAnalysisAgent(api_key=openai_key)

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """
        Process a check image
        """
        # 1. Extraction
        print(f"Extracting check: {image_path}")
        extracted_data = self.extractor.extract(image_path)
        
        # 2. Normalization
        bank_name = extracted_data.get('bank_name', '')
        print(f"Normalizing for bank: {bank_name}")
        
        normalizer = CheckNormalizerFactory.get_normalizer(bank_name)
        normalized_data = None
        
        if normalizer:
            normalized_data = normalizer.normalize(extracted_data)
            print("Normalization successful")
        else:
            print(f"No normalizer found for {bank_name}")
            # Basic fallback normalization
            normalized_data = {
                'issuer_name': bank_name,
                'amount_numeric': {'value': self._parse_amount(extracted_data.get('amount_numeric')), 'currency': 'USD'},
                'amount_written': extracted_data.get('amount_words'),
                'date': extracted_data.get('date'),
                'serial_primary': extracted_data.get('check_number'),
                'recipient': extracted_data.get('payee_name'),
                'sender_name': extracted_data.get('payer_name'),
                'signature': extracted_data.get('signature_detected')
            }

        # 3. ML Analysis
        print("Running ML analysis...")
        analysis_input = normalized_data if normalized_data else extracted_data
        ml_analysis = self.ml_detector.predict(analysis_input)

        # 4. AI Analysis
        print("Running AI analysis...")
        ai_analysis = self.ai_agent.analyze(
            extracted_data=analysis_input,
            ml_analysis=ml_analysis
        )

        # 5. Construct Response
        return {
            'extracted_data': extracted_data,
            'normalized_data': normalized_data,
            'ml_analysis': ml_analysis,
            'ai_analysis': ai_analysis,
            'anomalies': ml_analysis['anomalies'] + ai_analysis.get('risk_factors', [])
        }

    def _parse_amount(self, amount_str):
        if not amount_str: return 0.0
        try:
            return float(str(amount_str).replace(',', '').replace('$', ''))
        except:
            return 0.0
