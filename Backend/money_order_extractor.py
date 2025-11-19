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
            'amount_in_words': self._extract_amount_in_words(text),
            'payee': self._extract_payee(text),
            'purchaser': self._extract_purchaser(text),
            'date': self._extract_date(text),
            'location': self._extract_location(text),
            'receipt_number': self._extract_receipt_number(text),
            'signature': self._extract_signature(text),
        }
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Money Order Extraction Results:")
        logger.info(f"  Issuer: {extracted_data.get('issuer')}")
        logger.info(f"  Serial Number: {extracted_data.get('serial_number')}")
        logger.info(f"  Amount: {extracted_data.get('amount')}")
        logger.info(f"  Amount in Words: {extracted_data.get('amount_in_words')}")
        logger.info(f"  Payee: {extracted_data.get('payee')}")
        logger.info(f"  Purchaser: {extracted_data.get('purchaser')}")
        logger.info(f"  Date: {extracted_data.get('date')}")
        logger.info(f"  Location: {extracted_data.get('location')}")

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
        text_upper = text.upper()

        # Check for USPS patterns (most common)
        if 'UNITED STATES POSTAL' in text_upper or 'U.S. POSTAL' in text_upper or 'USPS' in text_upper:
            if 'MONEY ORDER' in text_upper:
                return 'USPS'

        # Check for other issuers
        issuers = {
            'WESTERN UNION': 'Western Union',
            'MONEYGRAM': 'MoneyGram',
            '7-ELEVEN': '7-Eleven',
            'WALMART': 'Walmart',
            'CVS': 'CVS',
            'ACE CASH EXPRESS': 'ACE Cash Express',
            'MONEY MART': 'Money Mart',
            'CHECK INTO CASH': 'Check Into Cash'
        }

        for key, value in issuers.items():
            if key in text_upper:
                return value

        return None

    def _extract_serial_number(self, text: str) -> Optional[str]:
        """Extract serial/control number"""
        # Common patterns for serial numbers
        patterns = [
            # Explicit "SERIAL NUMBER:" or "CONTROL NUMBER:" labels
            r'SERIAL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})',
            r'CONTROL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})',
            # Money order number patterns (e.g., "14-473651041" or "9875647821")
            r'MONEY\s+ORDER\s+(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})',
            r'(?:^|\n)\s*([0-9]{2}-[0-9]{9,12})\s*(?:\n|$)',  # Format: XX-XXXXXXXXX
            r'(?:^|\n)\s*([0-9]{10,15})\s*(?:\n|$)',  # Format: XXXXXXXXXX (10-15 digits)
            # Generic number patterns (less specific, use as fallback)
            r'(?:NO|NUMBER|#)?[:\s]*([A-Z0-9]{10,15})',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                serial = match.group(1).strip()
                # Filter out dates, amounts, and other numbers
                # Serial numbers are typically 10-15 digits or alphanumeric
                if len(serial) >= 8 and not serial.startswith('$'):
                    # Check if it's not a date (MM/DD/YYYY or similar)
                    if not re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$', serial):
                        return serial

        return None

    def _extract_amount(self, text: str) -> Optional[str]:
        """Extract money order amount (numeric)"""
        # Look for currency amounts - prioritize amounts near "AMOUNT" label
        patterns = [
            r'AMOUNT[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))',
            r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'(?:USD|US\$)\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"

        return None

    def _extract_amount_in_words(self, text: str) -> Optional[str]:
        """Extract written amount (e.g., 'SEVEN HUNDRED FIFTY AND 00/100 DOLLARS')"""
        # Pattern for written amounts like on checks/money orders
        # Handle variations like "FISTY" (typo) and "00//100" (double slash)
        patterns = [
            r'([A-Z][A-Za-z\s]+(?:HUNDRED|THOUSAND|MILLION)\s+[A-Za-z\s]+AND\s+\d{1,2}/+/?\d{2,3}\s+DOLLARS)',
            r'([A-Z][A-Z\s]+AND\s+\d{1,2}/+/?\d{2,3}\s+DOLLARS)',
            r'([A-Z][A-Za-z\s]+(?:HUNDRED|THOUSAND|MILLION)\s+[A-Za-z\s]+AND\s+\d{1,2}/\d{2,3}\s+DOLLARS)',
            r'([A-Z][A-Z\s]+AND\s+\d{1,2}/\d{2,3}\s+DOLLARS)',
            # More flexible pattern for amounts with typos or variations
            r'([A-Z][A-Za-z\s]{10,}?\s+AND\s+\d{1,2}/+/?\d{2,3}\s+DOLLARS)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                written_amount = match.group(1).strip()
                # Clean up extra spaces and normalize double slashes
                written_amount = ' '.join(written_amount.split())
                written_amount = re.sub(r'/+', '/', written_amount)  # Normalize // to /
                # Filter out false positives
                false_positives = ['PAY', 'TO', 'THE', 'ORDER', 'OF', 'FROM', 'PURCHASER', 'SENDER']
                if not any(fp in written_amount.upper() for fp in false_positives):
                    return written_amount

        return None

    def _extract_payee(self, text: str) -> Optional[str]:
        """Extract payee (pay to the order of)"""
        patterns = [
            # Full "PAY TO THE ORDER OF" pattern
            r'PAY\s+TO\s+THE\s+ORDER\s+OF[:\s]+([A-Z][A-Za-z\s\.]+?)(?:\n|AMOUNT|DATE|FROM|$)',
            # "PAY TO:" format (common in USPS and Western Union)
            r'PAY\s+TO[:\s]+([A-Z][A-Za-z\s\.]+?)(?:\n|AMOUNT|DATE|FROM|$)',
            # "PAYEE:" format
            r'PAYEE[:\s]+([A-Z][A-Za-z\s\.]+?)(?:\n|AMOUNT|DATE|FROM|$)',
            # "TO:" format
            r'TO[:\s]+([A-Z][A-Za-z\s\.]+?)(?:\n|AMOUNT|DATE|FROM|$)',
            # More flexible pattern
            r'(?:PAY\s+TO|PAYEE|TO)[:\s]+([A-Z][A-Z][A-Za-z\s\.]{2,}?)(?:\n|AMOUNT|DATE|FROM|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                payee = match.group(1).strip()
                # Clean up - remove trailing dots, extra spaces
                payee = payee.rstrip('.').strip()
                # Filter out common false positives
                false_positives = ['AMOUNT', 'DATE', 'FROM', 'PURCHASER', 'SENDER', 'THE', 'ORDER', 'OF']
                if len(payee) > 3 and not payee.isdigit() and not any(fp in payee.upper() for fp in false_positives):
                    return payee

        return None

    def _extract_purchaser(self, text: str) -> Optional[str]:
        """Extract purchaser/sender information"""
        patterns = [
            # "FROM:" format (common in Western Union and USPS) - most common, check first
            r'FROM[:\s]+([A-Z][A-Za-z\s]+?)(?:\n|AMOUNT|DATE|PAY|TO|$)',
            # "PURCHASER:" format
            r'PURCHASER[:\s]+([A-Z][A-Za-z\s]+?)(?:\n|AMOUNT|DATE|PAY|TO|$)',
            # "SENDER:" format
            r'SENDER[:\s]+([A-Z][A-Za-z\s]+?)(?:\n|AMOUNT|DATE|PAY|TO|$)',
            # "PURCHASER'S ADDRESS" or "CHASER'S ADDRESS" (typo handling)
            r'(?:PURCHASER|CHASER)\'?S?\s+(?:ADDRESS|NAME)[:\s]*([A-Z][A-Za-z\s]+?)(?:\n|AMOUNT|DATE|PAY|TO|$)',
            # More flexible pattern that captures until next field (without requiring capital letters)
            r'(?:PURCHASER|FROM|SENDER)[:\s]+([A-Za-z][A-Za-z\s]{2,}?)(?:\n|AMOUNT|DATE|PAY|TO|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                purchaser = match.group(1).strip()
                # Clean up - remove trailing dots, extra spaces
                purchaser = purchaser.rstrip('.').strip()
                # Remove address-like patterns if they're part of the name (e.g., "P.O. BOX 248" should be separate)
                # But keep the name part
                purchaser_lines = purchaser.split('\n')
                if purchaser_lines:
                    # Take the first line as the name (before address)
                    purchaser = purchaser_lines[0].strip()
                # Split by common address separators and take first part (the name)
                if ',' in purchaser:
                    purchaser = purchaser.split(',')[0].strip()
                # Filter out common false positives and address indicators
                false_positives = ['AMOUNT', 'DATE', 'PAY', 'TO', 'THE', 'ORDER', 'OF', 'BOX', 'P.O.', 'PO BOX', 'ADDRESS']
                if len(purchaser) > 2 and not any(fp in purchaser.upper() for fp in false_positives):
                    # Ensure it looks like a name (has at least one letter)
                    if re.search(r'[A-Za-z]', purchaser):
                        return purchaser
        
        # Line-by-line fallback: look for "FROM:" on a line and get the name from same or next line
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_upper = line.upper()
            if 'FROM:' in line_upper or 'FROM' in line_upper:
                # Try to extract from current line
                match = re.search(r'FROM[:\s]+([A-Za-z][A-Za-z\s]{2,})', line, re.IGNORECASE)
                if match:
                    purchaser = match.group(1).strip()
                    # Clean up
                    if ',' in purchaser:
                        purchaser = purchaser.split(',')[0].strip()
                    false_positives = ['AMOUNT', 'DATE', 'PAY', 'TO', 'THE', 'ORDER', 'OF', 'BOX', 'P.O.', 'PO BOX', 'ADDRESS']
                    if len(purchaser) > 2 and not any(fp in purchaser.upper() for fp in false_positives):
                        if re.search(r'[A-Za-z]', purchaser):
                            return purchaser
                # Try next line if current line only has "FROM:"
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Check if next line looks like a name (not empty, has letters, not a field label)
                    if next_line and re.search(r'^[A-Za-z][A-Za-z\s]{2,}', next_line):
                        if not any(fp in next_line.upper() for fp in ['AMOUNT', 'DATE', 'PAY', 'TO', 'FROM', 'PURCHASER', 'SENDER']):
                            # Split by comma if it contains address
                            if ',' in next_line:
                                purchaser = next_line.split(',')[0].strip()
                            else:
                                purchaser = next_line.strip()
                            if len(purchaser) > 2:
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

    def _extract_signature(self, text: str) -> Optional[str]:
        """Extract signature information or detect signature field presence"""
        text_upper = text.upper()

        # Common signature-related terms that indicate a signature is present
        signature_indicators = [
            'POSTAL CLERK',
            'CLERK',
            'AGENT',
            'AUTHORIZED',
            'SIGNATURE',
            'SIGNED',
            'SIGN HERE',
        ]

        # Check for signature field labels with values
        signature_patterns = [
            r'(?:AGENT\s+)?AUTHORIZED\s+SIGNATURE[:\s]*([A-Z][A-Za-z\s\.\,\-]+?)(?:\n|\s{3,}|$)',
            r'SIGNATURE[:\s]*([A-Z][A-Za-z\s\.\,\-]+?)(?:\n|\s{3,}|$)',
            r'PURCHASER\s+SIGNATURE[:\s]*([A-Z][A-Za-z\s\.\,\-]+?)(?:\n|\s{3,}|$)',
            r'POSTAL\s+CLERK[:\s]*([A-Z][A-Za-z\s\.\,\-]+?)(?:\n|\s{3,}|$)',
        ]

        # Try to extract signature with label
        for pattern in signature_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                signature_value = match.group(1).strip()
                # Clean up and validate
                if len(signature_value) > 2 and signature_value.upper() not in ['N/A', 'NA', 'NONE']:
                    return signature_value

        # Look for standalone signature indicators (like "POSTAL CLERK" appearing as signature)
        for indicator in signature_indicators:
            if indicator in text_upper:
                # Check if it appears near the end of the document (common for signatures)
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if indicator in line.upper():
                        # Check if this might be a signature (not part of header/title)
                        if i > len(lines) / 2:  # In bottom half of document
                            # Try to extract the text on that line
                            signature_match = re.search(r'\b([A-Z][A-Za-z\s]+(?:CLERK|AGENT))\b', line, re.IGNORECASE)
                            if signature_match:
                                return signature_match.group(1).strip()

                # If we found the indicator but couldn't extract a specific value
                if indicator == 'SIGNATURE' or 'SIGNATURE' in indicator:
                    return "Signature field present"

        return None

    def _detect_anomalies(self, data: Dict, text: str) -> list:
        """
        Detect potential anomalies or fraud indicators
        (Disabled - returns empty list for clean data extraction)
        """
        # Return empty list - no anomaly detection
        return []

    def _calculate_confidence(self, data: Dict) -> float:
        """
        Calculate confidence score based on extracted fields
        """
        weights = {
            'issuer': 18,
            'serial_number': 20,
            'amount': 17,
            'amount_in_words': 14,
            'payee': 12,
            'purchaser': 8,
            'signature': 6,
            'date': 3,
            'location': 1,
            'receipt_number': 1
        }

        score = 0
        for field, weight in weights.items():
            if data.get(field):
                score += weight

        return round(score, 2)
