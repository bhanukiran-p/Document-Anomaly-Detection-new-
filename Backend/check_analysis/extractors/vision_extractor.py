"""
Check Vision Extractor
Uses Google Vision API and Regex to extract data from checks
"""

import os
import io
import re
from typing import Dict, Optional, Any
from google.cloud import vision
from google.oauth2 import service_account

class CheckVisionExtractor:
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

    def extract(self, image_path: str) -> Dict[str, Any]:
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
            'signature_detected': True # Placeholder
        }
        return data

    def _extract_bank_name(self, text: str) -> str:
        banks = ['Bank of America', 'Chase', 'Wells Fargo', 'Citi', 'US Bank', 'PNC', 'JPMorgan Chase']
        text_lower = text.lower()
        for bank in banks:
            if bank.lower() in text_lower:
                if bank.lower() == 'jpmorgan chase': return 'Chase'
                return bank
        return "Unknown Bank"

    def _extract_check_number(self, text: str) -> Optional[str]:
        # Look for 4-6 digit number in top right or bottom line
        # Priority 1: Top right corner (often near date)
        lines = text.split('\n')
        for line in lines[:5]: # Check first few lines
            match = re.search(r'\b(\d{3,6})\b', line)
            if match:
                # Filter out dates
                if not re.search(r'\d{1,2}[/-]\d{1,2}', line):
                    return match.group(1)
        
        # Priority 2: Aux on MICR line
        match = re.search(r'\|?(\d{3,6})\|?', text)
        return match.group(1) if match else None

    def _extract_date(self, text: str) -> Optional[str]:
        # MM/DD/YYYY or similar
        match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', text)
        if match: return match.group(1)
        
        # Month DD, YYYY
        match = re.search(r'([A-Z][a-z]+ \d{1,2},? \d{4})', text)
        return match.group(1) if match else None

    def _extract_amount(self, text: str) -> Optional[str]:
        # Look for $ followed by number
        match = re.search(r'\$\s?([\d,]+\.\d{2})', text)
        return match.group(1) if match else None

    def _extract_amount_words(self, text: str) -> Optional[str]:
        # Look for lines ending in "Dollars"
        lines = text.split('\n')
        for line in lines:
            if 'dollars' in line.lower():
                return line.strip()
        return None

    def _extract_payee(self, text: str) -> Optional[str]:
        # Look for "Pay to the order of"
        # Handle case where name is on same line or next line
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'pay to the order of' in line.lower():
                # Check if name is on same line
                parts = re.split(r'pay to the order of', line, flags=re.IGNORECASE)
                if len(parts) > 1 and parts[1].strip():
                    # Remove dots/lines
                    return re.sub(r'[._]', '', parts[1]).strip()
                # Else check next line
                if i + 1 < len(lines):
                    return lines[i+1].strip()
        return None

    def _extract_payer(self, text: str) -> Optional[str]:
        # Usually top left
        lines = text.split('\n')
        if lines:
            # Filter out bank names if they appear first
            first_line = lines[0].strip()
            if "bank" not in first_line.lower() and "chase" not in first_line.lower():
                return first_line
            if len(lines) > 1:
                return lines[1].strip()
        return None

    def _extract_routing_number(self, text: str) -> Optional[str]:
        # 9 digits between |: symbols (transit symbol)
        # OCR often reads |: as A, C, or just :
        match = re.search(r'[A|C:]([0-9]{9})[A|C:]', text)
        if match: return match.group(1)
        
        # Fallback: just 9 digits at start of a line near bottom
        lines = text.split('\n')
        for line in lines[-3:]: # Check last 3 lines
            match = re.search(r'\b(\d{9})\b', line)
            if match: return match.group(1)
        return None

    def _extract_account_number(self, text: str) -> Optional[str]:
        # Usually follows routing number
        # Look for sequence of digits 8-12 long
        lines = text.split('\n')
        for line in lines[-3:]:
            # Find routing first to exclude it
            routing = re.search(r'\b\d{9}\b', line)
            if routing:
                # Look for other numbers in same line
                parts = re.split(r'\b\d{9}\b', line)
                for part in parts:
                    match = re.search(r'\b(\d{8,14})\b', part)
                    if match: return match.group(1)
        return None
