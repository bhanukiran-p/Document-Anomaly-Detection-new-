"""
Production Check Extractor using Google Vision API
"""

import os
import io
import re
from typing import Dict, Optional, Any
from google.cloud import vision
from google.oauth2 import service_account

class ProductionCheckExtractor:
    """
    Extract information from checks using Google Vision API
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Vision API client
        """
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            self.client = vision.ImageAnnotatorClient()
        else:
            self.client = vision.ImageAnnotatorClient()

    def extract_check_details(self, image_path: str) -> Dict[str, Any]:
        """
        Extract details from check image
        """
        text = self._extract_text(image_path)
        return self._parse_text(text)

    def _extract_text(self, image_path: str) -> str:
        """
        Extract raw text from image
        """
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f'{response.error.message}')

        return response.text_annotations[0].description if response.text_annotations else ""

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """
        Parse extracted text using Regex
        """
        data = {
            'raw_text': text,
            'bank_name': self._extract_bank_name(text),
            'check_number': self._extract_check_number(text),
            'date': self._extract_date(text),
            'amount_numeric': self._extract_amount(text),
            'amount_words': self._extract_amount_words(text),
            'payee_name': self._extract_payee(text),
            'payer_name': self._extract_payer(text),
            'routing_number': self._extract_routing_number(text),
            'account_number': self._extract_account_number(text),
            'signature_detected': True # Placeholder, requires object detection
        }
        return data

    def _extract_bank_name(self, text: str) -> str:
        # Simple heuristic: Look for common bank names
        banks = ['Bank of America', 'Chase', 'Wells Fargo', 'Citi', 'US Bank', 'PNC']
        for bank in banks:
            if bank.lower() in text.lower():
                return bank
        return "Unknown Bank"

    def _extract_check_number(self, text: str) -> Optional[str]:
        # Top right corner usually
        match = re.search(r'\b\d{3,6}\b', text) # Simplified
        return match.group(0) if match else None

    def _extract_date(self, text: str) -> Optional[str]:
        match = re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
        return match.group(0) if match else None

    def _extract_amount(self, text: str) -> Optional[str]:
        match = re.search(r'\$\s?([\d,]+\.\d{2})', text)
        return match.group(1) if match else None

    def _extract_amount_words(self, text: str) -> Optional[str]:
        # Hard to extract reliably without NLP
        return None

    def _extract_payee(self, text: str) -> Optional[str]:
        match = re.search(r'Pay to the order of\s+([^\n]+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_payer(self, text: str) -> Optional[str]:
        # Top left usually
        lines = text.split('\n')
        if lines:
            return lines[0]
        return None

    def _extract_routing_number(self, text: str) -> Optional[str]:
        match = re.search(r'\|:(\d{9})\|:', text)
        return match.group(1) if match else None

    def _extract_account_number(self, text: str) -> Optional[str]:
        match = re.search(r'\|:(\d{9})\|:\s*(\d+)', text)
        return match.group(2) if match else None
