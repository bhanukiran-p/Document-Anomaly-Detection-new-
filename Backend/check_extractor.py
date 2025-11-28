"""
Check Extractor
Orchestrates extraction, normalization, and AI analysis for checks
"""

import os
from typing import Dict, Tuple, List, Optional
import importlib.util

# Dynamic import for module with hyphen
spec = importlib.util.spec_from_file_location(
    "production_extractor", 
    "production_google_vision-extractor.py"
)
production_extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(production_extractor)
ProductionCheckExtractor = production_extractor.ProductionCheckExtractor

from normalization.normalizer_factory import NormalizerFactory
from langchain_agent.fraud_analysis_agent import FraudAnalysisAgent
from langchain_agent.tools import DataAccessTools

class CheckExtractor:
    """
    Main extractor class for checks
    Combines OCR, Normalization, and AI Analysis
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize components
        """
        # 1. Initialize OCR Extractor
        self.ocr_extractor = ProductionCheckExtractor(credentials_path)
        
        # 2. Initialize AI Agent
        openai_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize data tools (reuse existing mock data paths)
        ml_scores_path = os.getenv('ML_SCORES_CSV', 'ml_models/mock_data/ml_scores.csv')
        customer_history_path = os.getenv('CUSTOMER_HISTORY_CSV', 'ml_models/mock_data/customer_history.csv')
        fraud_cases_path = os.getenv('FRAUD_CASES_CSV', 'ml_models/mock_data/fraud_cases.csv')
        
        self.data_tools = DataAccessTools(
            ml_scores_path=ml_scores_path,
            customer_history_path=customer_history_path,
            fraud_cases_path=fraud_cases_path
        )
        
        self.ai_agent = FraudAnalysisAgent(
            api_key=openai_key,
            model=os.getenv('AI_MODEL', 'gpt-4'),
            data_tools=self.data_tools
        )

    def extract_check(self, image_path: str) -> Dict:
        """
        Process a check image: Extract -> Normalize -> Analyze
        """
        # 1. Extract Raw Data (OCR)
        print(f"Extracting data from {image_path}...")
        extracted_data = self.ocr_extractor.extract_check_details(image_path)
        
        # 2. Normalize Data
        bank_name = extracted_data.get('bank_name', '')
        print(f"Normalizing data for bank: {bank_name}...")
        
        normalized_data = None
        normalizer = NormalizerFactory.get_normalizer(bank_name)
        
        if normalizer:
            normalized_object = normalizer.normalize(extracted_data)
            normalized_data = normalized_object.to_dict()
            print("Normalization successful")
        else:
            print(f"No normalizer found for {bank_name}, using raw data")
            # Create a basic normalized structure from raw data if no normalizer exists
            normalized_data = {
                'issuer_name': bank_name,
                'amount_numeric': {'value': self._parse_amount(extracted_data.get('amount_numeric')), 'currency': 'USD'},
                'amount_written': extracted_data.get('amount_words'),
                'date': extracted_data.get('date'),
                'serial_primary': extracted_data.get('check_number'),
                'recipient': extracted_data.get('payee_name'),
                'sender_name': extracted_data.get('payer_name'), # Note: Payer name might be missing in raw extraction
                'signature': extracted_data.get('signature_detected')
            }

        # 3. AI Analysis
        print("Running AI analysis...")
        # Prepare data for AI (similar to Money Order)
        # We simulate ML analysis for now since we don't have a trained ML model for checks yet
        ml_analysis = {
            'fraud_score': 0.1, # Default low risk
            'risk_level': 'LOW',
            'anomalies': [],
            'confidence_score': extracted_data.get('confidence_score', 0.8)
        }
        
        # If we have normalized data, use it for AI, otherwise use raw
        analysis_input = normalized_data if normalized_data else extracted_data
        
        ai_analysis = self.ai_agent.analyze_fraud(
            extracted_data=analysis_input,
            ml_analysis=ml_analysis,
            customer_id="CUST_CHECK_001" # Placeholder
        )

        # 4. Construct Final Response
        return {
            'extracted_data': extracted_data,
            'normalized_data': normalized_data,
            'ml_analysis': ml_analysis,
            'ai_analysis': ai_analysis,
            'anomalies': ml_analysis['anomalies']
        }

    def _parse_amount(self, amount_str):
        """Helper to parse amount string to float"""
        if not amount_str: return 0.0
        try:
            return float(str(amount_str).replace(',', '').replace('$', ''))
        except:
            return 0.0
