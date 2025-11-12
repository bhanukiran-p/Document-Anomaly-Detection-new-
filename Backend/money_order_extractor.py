"""
Money Order Extractor using Google Vision API
Extracts key information from money order documents
"""

import os
import io
import re
from typing import Dict, Optional
from google.cloud import vision
from google.oauth2 import service_account


class MoneyOrderExtractor:
    """
    Extract information from money order documents using Google Vision API
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Vision API client

        Args:
            credentials_path: Path to Google Cloud service account JSON file
        """
        # Set up credentials
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            self.client = vision.ImageAnnotatorClient()
        else:
            self.client = vision.ImageAnnotatorClient()

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text using Google Vision API

        Returns:
            full_text: Complete text extracted from the image
        """
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)

        if response.error.message:
            raise Exception(f'Vision API Error: {response.error.message}')

        texts = response.text_annotations

        if not texts:
            return ""

        return texts[0].description

    def extract_money_order(self, image_path: str) -> Dict:
        """
        Extract money order details from image

        Returns:
            Dictionary containing extracted money order information
        """
        # Get OCR text
        text = self.extract_text_from_image(image_path)

        if not text:
            return {
                'status': 'error',
                'message': 'No text detected in image',
                'extracted_data': {}
            }

        # Extract money order fields
        extracted_data = {
            'issuer': self._extract_issuer(text),
            'serial_number': self._extract_serial_number(text),
            'amount': self._extract_amount(text),
            'payee': self._extract_payee(text),
            'purchaser': self._extract_purchaser(text),
            'date': self._extract_date(text),
            'location': self._extract_location(text),
            'receipt_number': self._extract_receipt_number(text),
        }

        # Perform anomaly detection
        anomalies = self._detect_anomalies(extracted_data, text)

        # Calculate confidence score
        confidence = self._calculate_confidence(extracted_data)

        return {
            'status': 'success',
            'extracted_data': extracted_data,
            'anomalies': anomalies,
            'confidence_score': confidence,
            'raw_text': text
        }

    def _extract_issuer(self, text: str) -> Optional[str]:
        """Extract money order issuer (Western Union, MoneyGram, USPS, etc.)"""
        issuers = [
            'Western Union', 'MoneyGram', 'USPS', 'U.S. Postal Service',
            '7-Eleven', 'Walmart', 'CVS', 'Moneygram', 'ACE Cash Express'
        ]

        text_upper = text.upper()
        for issuer in issuers:
            if issuer.upper() in text_upper:
                return issuer

        return None

    def _extract_serial_number(self, text: str) -> Optional[str]:
        """Extract serial/control number"""
        # Common patterns for serial numbers
        patterns = [
            r'SERIAL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})',
            r'CONTROL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})',
            r'(?:NO|NUMBER|#)?[:\s]*([A-Z0-9]{10,15})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_amount(self, text: str) -> Optional[str]:
        """Extract money order amount"""
        # Look for currency amounts
        patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'AMOUNT[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:USD|US\$)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"

        return None

    def _extract_payee(self, text: str) -> Optional[str]:
        """Extract payee (pay to the order of)"""
        patterns = [
            r'PAY\s+TO(?:\s+THE\s+ORDER\s+OF)?[:\s]*([A-Z\s\.]+?)(?:\n|$)',
            r'PAYEE[:\s]*([A-Z\s\.]+?)(?:\n|$)',
            r'TO[:\s]*([A-Z][A-Za-z\s\.]+?)(?:\n|AMOUNT)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                payee = match.group(1).strip()
                if len(payee) > 3 and not payee.isdigit():
                    return payee

        return None

    def _extract_purchaser(self, text: str) -> Optional[str]:
        """Extract purchaser/sender information"""
        patterns = [
            r'PURCHASER[:\s]*([A-Z][A-Za-z\s\.]+?)(?:\n|$)',
            r'FROM[:\s]*([A-Z][A-Za-z\s\.]+?)(?:\n|$)',
            r'SENDER[:\s]*([A-Z][A-Za-z\s\.]+?)(?:\n|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                purchaser = match.group(1).strip()
                if len(purchaser) > 3:
                    return purchaser

        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract transaction date"""
        patterns = [
            r'DATE[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location/office where money order was purchased"""
        patterns = [
            r'LOCATION[:\s]*([A-Z][A-Za-z\s,\.]+?)(?:\n|$)',
            r'OFFICE[:\s]*([A-Z][A-Za-z\s,\.]+?)(?:\n|$)',
            r'([A-Z][a-z]+,\s*[A-Z]{2}\s+\d{5})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 3:
                    return location

        return None

    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """Extract receipt/reference number"""
        patterns = [
            r'RECEIPT\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{6,20})',
            r'REF(?:ERENCE)?\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{6,20})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _detect_anomalies(self, data: Dict, text: str) -> list:
        """
        Detect potential anomalies or fraud indicators
        """
        anomalies = []

        # Check for missing critical fields
        if not data.get('amount'):
            anomalies.append({
                'type': 'missing_field',
                'field': 'amount',
                'severity': 'high',
                'message': 'Amount not detected'
            })

        if not data.get('serial_number'):
            anomalies.append({
                'type': 'missing_field',
                'field': 'serial_number',
                'severity': 'high',
                'message': 'Serial number not detected'
            })

        if not data.get('payee'):
            anomalies.append({
                'type': 'missing_field',
                'field': 'payee',
                'severity': 'medium',
                'message': 'Payee information not detected'
            })

        # Check for suspiciously high amounts
        if data.get('amount'):
            amount_str = data['amount'].replace('$', '').replace(',', '')
            try:
                amount_val = float(amount_str)
                if amount_val > 1000:
                    anomalies.append({
                        'type': 'high_amount',
                        'field': 'amount',
                        'severity': 'medium',
                        'message': f'High amount detected: {data["amount"]} (typical limit is $1,000)'
                    })
            except ValueError:
                pass

        # Check for alterations keywords
        alteration_keywords = ['VOID', 'ALTERED', 'COUNTERFEIT', 'COPY', 'SPECIMEN']
        text_upper = text.upper()
        for keyword in alteration_keywords:
            if keyword in text_upper:
                anomalies.append({
                    'type': 'alteration_indicator',
                    'field': 'document',
                    'severity': 'critical',
                    'message': f'Potential alteration keyword detected: {keyword}'
                })

        return anomalies

    def _calculate_confidence(self, data: Dict) -> float:
        """
        Calculate confidence score based on extracted fields
        """
        weights = {
            'issuer': 20,
            'serial_number': 25,
            'amount': 20,
            'payee': 15,
            'purchaser': 10,
            'date': 5,
            'location': 3,
            'receipt_number': 2
        }

        score = 0
        for field, weight in weights.items():
            if data.get(field):
                score += weight

        return round(score, 2)
