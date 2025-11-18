"""
Production Google Vision API Integration for Check Extraction
Ready for deployment with actual API credentials
"""

import os
import io
import re
import json
from typing import Dict, List, Optional
from datetime import datetime

# Google Cloud Vision imports
try:
    from google.cloud import vision
    from google.oauth2 import service_account
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print("Warning: google-cloud-vision not installed. Run: pip install google-cloud-vision")


class ProductionCheckExtractor:
    """
    Production-ready Google Vision API check extractor
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Vision API client
        
        Args:
            credentials_path: Path to Google Cloud service account JSON file
        """
        if not VISION_AVAILABLE:
            raise ImportError("google-cloud-vision package not installed")
        
        # Set up credentials
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            # Use environment variable (set by api_server.py)
            self.client = vision.ImageAnnotatorClient()
        else:
            # Try to find credentials in the same directory as this file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            default_creds = os.path.join(script_dir, 'google-credentials.json')
            if os.path.exists(default_creds):
                credentials = service_account.Credentials.from_service_account_file(
                    default_creds
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
            else:
                # Try default credentials
                self.client = vision.ImageAnnotatorClient()
    
    def extract_text_from_image(self, image_path: str) -> tuple:
        """
        Extract text using Google Vision API
        
        Returns:
            (full_text, annotations_list)
        """
        # Read image
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Perform text detection
        response = self.client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f'Vision API Error: {response.error.message}')
        
        texts = response.text_annotations
        
        if not texts:
            return "", []
        
        # First annotation contains full text
        full_text = texts[0].description
        
        # Create word-level annotations with bounding boxes
        word_annotations = []
        for text in texts[1:]:  # Skip first (full text)
            word_annotations.append({
                'text': text.description,
                'confidence': text.confidence if hasattr(text, 'confidence') else None,
                'bounds': {
                    'vertices': [
                        {'x': vertex.x, 'y': vertex.y}
                        for vertex in text.bounding_poly.vertices
                    ]
                }
            })
        
        return full_text, word_annotations
    
    def extract_check_details(self, image_path: str) -> Dict:
        """
        Main extraction method
        """
        # Get OCR results
        full_text, annotations = self.extract_text_from_image(image_path)
        
        # Detect bank
        bank_type = self._detect_bank_type(full_text)
        
        # Extract based on bank type
        if bank_type == "AXIS":
            details = self._extract_axis_check(full_text, annotations)
        elif bank_type == "BANK_OF_AMERICA":
            details = self._extract_boa_check(full_text, annotations)
        elif bank_type == "ICICI":
            details = self._extract_icici_check(full_text, annotations)
        elif bank_type == "HDFC":
            details = self._extract_hdfc_check(full_text, annotations)
        elif bank_type == "CHASE":
            details = self._extract_chase_check(full_text, annotations)
        elif bank_type == "WELLS_FARGO":
            details = self._extract_wells_fargo_check(full_text, annotations)
        elif bank_type == "CITIBANK":
            details = self._extract_citibank_check(full_text, annotations)
        else:
            details = self._extract_generic_check(full_text, annotations)
        
        # Add metadata
        details.update({
            'bank_type': bank_type,
            'raw_ocr_text': full_text,
            'word_count': len(annotations),
            'extraction_timestamp': datetime.now().isoformat(),
            'confidence_score': self._calculate_confidence(details),
            'api_used': 'Google Cloud Vision API'
        })
        
        return details
    
    def _detect_bank_type(self, text: str) -> str:
        """Detect bank from OCR text"""
        text_upper = text.upper()
        
        bank_patterns = {
            'AXIS': ['AXIS BANK', 'AXIS'],
            'BANK_OF_AMERICA': ['BANK OF AMERICA', 'BANKOFAMERICA', 'BOA', 'B OF A'],
            'ICICI': ['ICICI BANK', 'ICICI'],
            'HDFC': ['HDFC BANK', 'HDFC'],
            'CHASE': ['CHASE BANK', 'JPMORGAN CHASE', 'CHASE', 'JPMORGAN'],
            'WELLS_FARGO': ['WELLS FARGO', 'WELLS'],
            'CITIBANK': ['CITIBANK', 'CITI']
        }
        
        # Check patterns in order of specificity (most specific first)
        for bank, patterns in bank_patterns.items():
            for pattern in patterns:
                if pattern in text_upper:
                    return bank
        
        return "UNKNOWN"
    
    def _extract_axis_check(self, text: str, annotations: List) -> Dict:
        """Extract Axis Bank check (Indian format)"""
        return {
            'bank_name': 'AXIS BANK LTD',
            'country': 'India',
            'payee_name': self._extract_payee_axis(text),
            'amount_numeric': self._extract_amount_numeric_inr(text),
            'amount_words': self._extract_amount_words(text, 'RUPEES'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number(text),
            'account_number': self._extract_account_number(text),
            'micr_code': self._extract_micr_code(text),
            'ifsc_code': self._extract_ifsc_code(text),
            'signature_detected': self._has_signature(annotations),
            'currency': 'INR'
        }
    
    def _extract_boa_check(self, text: str, annotations: List) -> Dict:
        """Extract Bank of America check (US format)"""
        is_cashier = 'CASHIER' in text.upper()
        
        return {
            'bank_name': 'Bank of America, N.A.',
            'country': 'USA',
            'check_type': "Cashier's Check" if is_cashier else "Personal/Business Check",
            'payee_name': self._extract_payee_us(text),
            'amount_numeric': self._extract_amount_numeric_usd(text),
            'amount_words': self._extract_amount_words(text, 'DOLLARS'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number_us(text),
            'routing_number': self._extract_routing_number(text),
            'account_number': self._extract_account_number_us(text),
            'memo': self._extract_memo(text),
            'signature_detected': self._has_signature(annotations),
            'currency': 'USD'
        }
    
    def _extract_icici_check(self, text: str, annotations: List) -> Dict:
        """Extract ICICI Bank check"""
        return {
            'bank_name': 'ICICI BANK LIMITED',
            'country': 'India',
            'payee_name': self._extract_payee_axis(text),
            'amount_numeric': self._extract_amount_numeric_inr(text),
            'amount_words': self._extract_amount_words(text, 'RUPEES'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number(text),
            'account_number': self._extract_account_number(text),
            'micr_code': self._extract_micr_code(text),
            'ifsc_code': self._extract_ifsc_code(text),
            'signature_detected': self._has_signature(annotations),
            'currency': 'INR'
        }
    
    def _extract_hdfc_check(self, text: str, annotations: List) -> Dict:
        """Extract HDFC Bank check"""
        return {
            'bank_name': 'HDFC BANK LTD',
            'country': 'India',
            'payee_name': self._extract_payee_axis(text),
            'amount_numeric': self._extract_amount_numeric_inr(text),
            'amount_words': self._extract_amount_words(text, 'RUPEES'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number(text),
            'account_number': self._extract_account_number(text),
            'micr_code': self._extract_micr_code(text),
            'ifsc_code': self._extract_ifsc_code(text),
            'signature_detected': self._has_signature(annotations),
            'currency': 'INR'
        }
    
    def _extract_chase_check(self, text: str, annotations: List) -> Dict:
        """Extract Chase Bank check (US format)"""
        return {
            'bank_name': 'JPMorgan Chase Bank, N.A.',
            'country': 'USA',
            'payee_name': self._extract_payee_us(text),
            'amount_numeric': self._extract_amount_numeric_usd(text),
            'amount_words': self._extract_amount_words(text, 'DOLLARS'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number_us(text),
            'routing_number': self._extract_routing_number(text),
            'account_number': self._extract_account_number_us(text),
            'memo': self._extract_memo(text),
            'signature_detected': self._has_signature(annotations),
            'currency': 'USD'
        }
    
    def _extract_wells_fargo_check(self, text: str, annotations: List) -> Dict:
        """Extract Wells Fargo check (US format)"""
        return {
            'bank_name': 'Wells Fargo Bank, N.A.',
            'country': 'USA',
            'payee_name': self._extract_payee_us(text),
            'amount_numeric': self._extract_amount_numeric_usd(text),
            'amount_words': self._extract_amount_words(text, 'DOLLARS'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number_us(text),
            'routing_number': self._extract_routing_number(text),
            'account_number': self._extract_account_number_us(text),
            'memo': self._extract_memo(text),
            'signature_detected': self._has_signature(annotations),
            'currency': 'USD'
        }
    
    def _extract_citibank_check(self, text: str, annotations: List) -> Dict:
        """Extract Citibank check (US format)"""
        return {
            'bank_name': 'Citibank, N.A.',
            'country': 'USA',
            'payee_name': self._extract_payee_us(text),
            'amount_numeric': self._extract_amount_numeric_usd(text),
            'amount_words': self._extract_amount_words(text, 'DOLLARS'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number_us(text),
            'routing_number': self._extract_routing_number(text),
            'account_number': self._extract_account_number_us(text),
            'memo': self._extract_memo(text),
            'signature_detected': self._has_signature(annotations),
            'currency': 'USD'
        }
    
    def _extract_generic_check(self, text: str, annotations: List) -> Dict:
        """Generic extraction for unknown banks"""
        bank_name = self._extract_bank_name(text)
        # If we couldn't extract bank name, try to detect from text
        if not bank_name:
            detected_type = self._detect_bank_type(text)
            if detected_type != "UNKNOWN":
                # Map detected type to bank name
                bank_name_map = {
                    'CHASE': 'JPMorgan Chase Bank',
                    'BANK_OF_AMERICA': 'Bank of America',
                    'WELLS_FARGO': 'Wells Fargo Bank',
                    'CITIBANK': 'Citibank',
                }
                bank_name = bank_name_map.get(detected_type, None)
        
        return {
            'bank_name': bank_name,
            'payee_name': self._extract_payee_generic(text),
            'amount_numeric': self._extract_amount_generic(text),
            'amount_words': self._extract_amount_words(text, 'DOLLARS|RUPEES'),
            'date': self._extract_date(text),
            'check_number': self._extract_check_number(text),
            'signature_detected': self._has_signature(annotations)
        }
    
    # Extraction helper methods
    
    def _extract_payee_axis(self, text: str) -> Optional[str]:
        """Extract payee for Indian banks"""
        patterns = [
            r'PAY\s+([A-Za-z\s]+?)(?:\s+OR\s+BEARER|RUPEES)',
            r'PAY\s+([A-Za-z\s\.]+?)(?:\s+OR|\n|₹)',
            r'PAY\s+TO\s+([A-Za-z\s\.]+?)(?:\n|OR|RUPEES)',
            r'PAY\s+([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+OR)',
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_payee_us(self, text: str) -> Optional[str]:
        """Extract payee for US banks"""
        patterns = [
            r'TO\s+THE\s+ORDER\s+OF\s+([A-Za-z\s&,\.]+?)(?:\s+\$|\n)',
            r'PAY\s+TO\s+THE\s+ORDER\s+OF\s+([A-Za-z\s&,\.]+?)(?:\s+\$|\n)',
            r'ORDER\s+OF\s+([A-Za-z\s&,\.]+?)(?:\$|\n)',
            r'PAY\s+TO[:\s]+([A-Za-z\s&,\.]+?)(?:\s+\$|\n)',
            r'THE\s+ORDER\s+OF[:\s]+([A-Za-z\s&,\.]+?)(?:\s+\$)',
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_payee_generic(self, text: str) -> Optional[str]:
        """Generic payee extraction"""
        patterns = [
            r'PAY\s+(?:TO\s+)?(?:THE\s+ORDER\s+OF\s+)?([A-Za-z\s&,\.]+?)(?:\s+[$₹]|\n)',
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_amount_numeric_inr(self, text: str) -> Optional[str]:
        """Extract INR amount"""
        patterns = [
            r'₹\s*([\d,]+\.?\d*)',
            r'Rs\.?\s*([\d,]+\.?\d*)',
            r'INR\s*([\d,]+\.?\d*)',
            r'RUPEES.*?₹\s*([\d,]+)',
            r'(?:AMOUNT|TOTAL)[:\s]*₹\s*([\d,]+\.?\d*)',
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_amount_numeric_usd(self, text: str) -> Optional[str]:
        """Extract USD amount"""
        patterns = [
            r'\$\s*\*?\*?\s*([\d,]+\.?\d{0,2})\s*\*?\*?',
            r'USD\s*([\d,]+\.?\d{0,2})',
            r'AMOUNT[:\s]*\$\s*([\d,]+\.?\d{0,2})',
            r'DOLLARS.*?\$\s*([\d,]+\.?\d{0,2})',
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_amount_generic(self, text: str) -> Optional[str]:
        """Generic amount extraction"""
        patterns = [
            r'[$₹]\s*([\d,]+\.?\d*)',
            r'\b([\d,]+\.\d{2})\b'
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_amount_words(self, text: str, currency_word: str) -> Optional[str]:
        """Extract amount in words"""
        pattern = f'{currency_word}\\s+(.+?)(?:\\s+ONLY|\\s+[$₹]|\\n|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1):
            return match.group(1).strip()
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date in various formats"""
        patterns = [
            r'DATE[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b',
            r'\b([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\b',
            r'(\d{2}\s+\d{2}\s+\d{2,4})',  # Format: DD MM YYYY
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_check_number(self, text: str) -> Optional[str]:
        """Extract check number"""
        patterns = [
            r'CHECK\s+NO\.?\s*[:\s]*(\d+)',
            r'CHEQUE\s+NO\.?\s*[:\s]*(\d+)',
            r'CHECK\s+NUMBER[:\s]*(\d+)',
            r'NO\.?\s*[:\s]*(\d{6,10})',
            r'(?:^|\n)(\d{6})(?:\n|$)',  # Standalone 6-digit number
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_check_number_us(self, text: str) -> Optional[str]:
        """Extract US check number"""
        patterns = [
            r'CHECK\s+NO\.?\s*(\d+)',
            r'NO\.?\s*(\d{4,10})',
            r'\b(\d{4})\b'  # Often 4 digits in corner
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_account_number(self, text: str) -> Optional[str]:
        """Extract account number (Indian format)"""
        patterns = [
            r'A/?C\s*NO\.?\s*[:\s]*(\d{10,18})',
            r'ACCOUNT\s+NO\.?\s*[:\s]*(\d{10,18})',
            r'ACCOUNT\s+NUMBER[:\s]*(\d{10,18})',
            r'A/?C[:\s]+(\d{14,18})',
            r'\b(\d{14,18})\b'
        ]
        return self._try_patterns(text, patterns)
    
    def _extract_account_number_us(self, text: str) -> Optional[str]:
        """Extract US account number from MICR"""
        pattern = r'⑆\d{9}⑆\s*(\d{8,12})⑆'
        match = re.search(pattern, text)
        if match and match.group(1):
            return match.group(1)
        return None
    
    def _extract_routing_number(self, text: str) -> Optional[str]:
        """Extract routing number (US)"""
        pattern = r'⑆(\d{9})⑆'
        match = re.search(pattern, text)
        if match and match.group(1):
            return match.group(1)
        return None
    
    def _extract_micr_code(self, text: str) -> Optional[str]:
        """Extract MICR code (Indian banks)"""
        pattern = r'\b(\d{9})\b'
        matches = re.findall(pattern, text)
        return matches[0] if matches else None
    
    def _extract_ifsc_code(self, text: str) -> Optional[str]:
        """Extract IFSC code (Indian banks)"""
        pattern = r'\b([A-Z]{4}0[A-Z0-9]{6})\b'
        match = re.search(pattern, text)
        if match and match.group(1):
            return match.group(1)
        return None
    
    def _extract_memo(self, text: str) -> Optional[str]:
        """Extract memo field"""
        pattern = r'MEMO\s+([A-Za-z0-9\s]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1):
            return match.group(1).strip()
        return None
    
    def _extract_bank_name(self, text: str) -> Optional[str]:
        """Extract bank name"""
        text_upper = text.upper()
        
        # First, try to detect known banks and return proper name
        detected_type = self._detect_bank_type(text)
        bank_name_map = {
            'CHASE': 'JPMorgan Chase Bank, N.A.',
            'BANK_OF_AMERICA': 'Bank of America, N.A.',
            'WELLS_FARGO': 'Wells Fargo Bank, N.A.',
            'CITIBANK': 'Citibank, N.A.',
            'AXIS': 'AXIS BANK LTD',
            'ICICI': 'ICICI BANK LIMITED',
            'HDFC': 'HDFC BANK LTD',
        }
        
        if detected_type in bank_name_map:
            return bank_name_map[detected_type]
        
        # Fallback: Look for bank name in first few lines
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line:
                line_upper = line.upper().strip()
                # Skip common non-bank words
                skip_words = ['EMPLOYEE', 'PAY', 'SSN', 'DATE', 'CHECK', 'NUMBER', 
                             'ROUTING', 'ACCOUNT', 'MEMO', 'SIGNATURE', 'PAYEE', 'PAY TO']
                if any(word in line_upper for word in skip_words):
                    continue
                
                # Look for bank indicators
                if ('BANK' in line_upper or 'CHASE' in line_upper or 
                    'WELLS' in line_upper or 'CITI' in line_upper or
                    'JPMORGAN' in line_upper):
                    stripped = line.strip()
                    if stripped and len(stripped) > 3:
                        return stripped
        
        return None
    
    def _has_signature(self, annotations: List) -> bool:
        """Detect if signature is present (simple heuristic)"""
        # Check for signature-like patterns or specific keywords
        if not annotations:
            return False
        
        # Count annotations in lower portion of image
        lower_annotations = [a for a in annotations 
                           if a.get('bounds', {}).get('vertices', [{}])[0].get('y', 0) > 200]
        
        # If there are sparse annotations in lower portion, likely signature
        return len(lower_annotations) > 3
    
    def _try_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """Try multiple regex patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1):
                result = match.group(1).strip()
                if result:  # Only return non-empty strings
                    return result
        return None
    
    def _calculate_confidence(self, details: Dict) -> float:
        """Calculate extraction confidence with weighted scoring"""
        # Critical fields - must have for valid check
        critical_fields = ['bank_name', 'payee_name', 'amount_numeric']
        
        # Important fields - should have for complete check
        important_fields = ['date', 'check_number', 'account_number']
        
        # Optional fields - nice to have
        optional_fields = ['routing_number', 'micr_code', 'ifsc_code', 'signature_detected']
        
        critical_filled = sum(1 for k in critical_fields if details.get(k))
        important_filled = sum(1 for k in important_fields if details.get(k))
        optional_filled = sum(1 for k in optional_fields if details.get(k))
        
        # Weighted confidence score
        confidence = (
            (critical_filled / len(critical_fields)) * 50 +   # 50% weight for critical
            (important_filled / len(important_fields)) * 35 +  # 35% weight for important
            (optional_filled / len(optional_fields)) * 15      # 15% weight for optional
        )
        
        return round(confidence, 2)


def batch_process_checks(image_paths: List[str], credentials_path: str = None) -> List[Dict]:
    """
    Process multiple checks in batch
    """
    extractor = ProductionCheckExtractor(credentials_path)
    results = []
    
    for image_path in image_paths:
        try:
            details = extractor.extract_check_details(image_path)
            results.append({
                'image_path': image_path,
                'success': True,
                'details': details
            })
        except Exception as e:
            results.append({
                'image_path': image_path,
                'success': False,
                'error': str(e)
            })
    
    return results


def save_results(results: List[Dict], output_path: str = 'extraction_results.json'):
    """Save extraction results to JSON"""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    # Example usage
    print("Google Vision API Check Extractor - Production Version")
    print("=" * 60)

    # Set your credentials path
    credentials_path = "google-credentials.json"
    
    # Or use environment variable
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"\nError: Credentials file not found: {credentials_path}")
        print("Please ensure the Google Cloud credentials JSON file is in the current directory.")
        exit(1)
    
    print(f"\n[OK] Credentials file found: {credentials_path}")
    
    try:
        # Test API connection
        print("\n[INFO] Testing Google Vision API connection...")
        extractor = ProductionCheckExtractor(credentials_path)
        print("[OK] Successfully initialized Google Vision API client")
        print("\n" + "=" * 60)
        print("Application is ready to process check images!")
        print("=" * 60)
        print("\nUsage:")
        print("1. Place check images in the current directory")
        print("2. Update test_images list with your image paths")
        print("3. Run the script to extract check details")
        print("\nExample:")
        print("  test_images = ['check1.jpg', 'check2.png']")
        print("  results = batch_process_checks(test_images, credentials_path)")
        
        # Look for sample images in current directory
        print("\n" + "=" * 60)
        print("Looking for check images in current directory...")
        image_extensions = ['.jpg', '.jpeg', '.png']
        found_images = []
        for file in os.listdir('.'):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                found_images.append(file)
        
        if found_images:
            print(f"\n[INFO] Found {len(found_images)} image(s):")
            for img in found_images:
                print(f"  - {img}")
            
            process = input("\nWould you like to process these images? (y/n): ").strip().lower()
            if process == 'y':
                print("\nProcessing images...\n")
                results = batch_process_checks(found_images, credentials_path)
                
                # Display results
                for result in results:
                    if result['success']:
                        details = result['details']
                        print(f"\n[OK] {os.path.basename(result['image_path'])}")
                        print(f"  Bank: {details.get('bank_name')}")
                        print(f"  Payee: {details.get('payee_name')}")
                        print(f"  Amount: {details.get('amount_numeric')}")
                        print(f"  Confidence: {details.get('confidence_score')}%")
                    else:
                        print(f"\n[ERROR] {os.path.basename(result['image_path'])}")
                        print(f"  Error: {result['error']}")
                
                # Save results
                save_results(results)
        else:
            print("\n[INFO] No image files found in current directory")
            print("Please add check images (.jpg, .jpeg, .png) to process them")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nMake sure:")
        print("1. pip install google-cloud-vision")
        print("2. Set up Google Cloud credentials")
        print("3. Enable Vision API in Google Cloud Console")