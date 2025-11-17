"""
Paystub Extractor Module for API
Standalone paystub extraction with Google Vision API
"""

import re
from typing import Dict
from datetime import datetime
from google.cloud import vision
from google.oauth2 import service_account
import fitz  # PyMuPDF

class PaystubExtractor:
    """Extract paystub details using Google Vision API"""
    
    def __init__(self, credentials_path='google-credentials.json'):
        """Initialize with credentials"""
        import os
        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            self.client = vision.ImageAnnotatorClient()
    
    def extract_text(self, file_bytes, file_type='image'):
        """Extract text from image or PDF using Vision API"""
        
        # If it's a PDF, convert first page to image
        if file_type == 'application/pdf':
            try:
                pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
                page = pdf_document[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes("png")
                pdf_document.close()
                
                image = vision.Image(content=img_bytes)
                response = self.client.text_detection(image=image)
            except Exception as e:
                raise Exception(f'PDF Processing Error: {str(e)}')
        else:
            image = vision.Image(content=file_bytes)
            response = self.client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f'Vision API Error: {response.error.message}')
        
        texts = response.text_annotations
        return texts[0].description if texts else ""
    
    def extract_paystub(self, text: str) -> Dict:
        """Extract paystub details from text"""
        details = {
            'document_type': 'PAYSTUB',
            'company_name': None,
            'employee_name': None,
            'employee_id': None,
            'pay_period_start': None,
            'pay_period_end': None,
            'pay_date': None,
            'gross_pay': None,
            'net_pay': None,
            'ytd_gross': None,
            'ytd_net': None,
            'federal_tax': None,
            'state_tax': None,
            'social_security': None,
            'medicare': None,
            'deductions': {},
            'earnings': {},
            'raw_text_preview': text[:500]
        }
        
        lines = text.split('\n')
        
        # Extract company name
        for line in lines[:15]:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            skip_words = ['EMPLOYEE', 'PAY', 'SSN', 'DESCRIPTION', 'EARNINGS', 'DEDUCTIONS', 
                         'DATE', 'HOURS', 'RATE', 'CURRENT', 'YTD', 'FEDERAL', 'STATE']
            if any(word in line.upper() for word in skip_words):
                continue
            
            if any(keyword in line.upper() for keyword in ['INC', 'CORP', 'LLC', 'SYSTEMS', 
                                                            'COMPANY', 'GROUP', 'CORPORATION', 
                                                            'LIMITED', 'LTD', 'CO.']):
                details['company_name'] = line
                break
            
            if len(line) > 5 and not line.isupper() and any(c.isupper() for c in line):
                details['company_name'] = line
                break
        
        # Extract employee name
        employee_patterns = [
            r'(?:EMPLOYEE\s+NAME|NAME)[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
            r'(?:^|\n)([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*\n|\s+(?:EMPLOYEE|ID|SSN))',
        ]
        
        for pattern in employee_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name.split()) >= 2 and not any(word in name.upper() for word in 
                    ['EMPLOYEE', 'COMPANY', 'ADDRESS', 'DEPARTMENT', 'POSITION']):
                    details['employee_name'] = name
                    break
        
        # Extract employee ID
        empid_patterns = [
            r'EMPLOYEE\s*(?:ID|NUMBER)[:\s]*\n?\s*([A-Z0-9\-]{3,})',
            r'(?:EMP\s*)?ID[:\s]*([A-Z]{2,}-[A-Z0-9\-]{3,})',
            r'(?:^|\n)([A-Z]{2,3}-\d{4,})(?:\n|$)',
        ]
        for pattern in empid_patterns:
            empid_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if empid_match:
                emp_id = empid_match.group(1).strip()
                if (len(emp_id) >= 4 and 
                    not any(word in emp_id.upper() for word in ['EMPLOYEE', 'NAME', 'SSN', 'FEDERAL']) and
                    (any(c.isdigit() for c in emp_id) or '-' in emp_id)):
                    details['employee_id'] = emp_id
                    break
        
        # Extract pay period
        period_patterns = [
            r'(?:PAY\s+PERIOD|Period)[:\s]*\n?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*[-–to\s]+\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{2}/\d{2}/\d{4})\s*[-–]\s*(\d{2}/\d{2}/\d{4})',
        ]
        for pattern in period_patterns:
            period_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if period_match:
                details['pay_period_start'] = period_match.group(1)
                details['pay_period_end'] = period_match.group(2)
                break
        
        # Extract pay date
        date_patterns = [
            r'PAY\s+DATE[:\s]*\n?\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'CHECK\s+DATE[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(?:^|\n)DATE[:\s]*\n?\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if date_match:
                details['pay_date'] = date_match.group(1)
                break
        
        # Extract gross pay
        gross_patterns = [
            r'GROSS\s+(?:PAY|EARNINGS)[:\s]*\n?\s*\$?\s*([\d,]+\.?\d{0,2})',
            r'TOTAL\s+GROSS[:\s]*\n?\s*\$?\s*([\d,]+\.?\d{0,2})',
        ]
        for pattern in gross_patterns:
            gross_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if gross_match:
                details['gross_pay'] = gross_match.group(1)
                break
        
        # Extract net pay
        net_patterns = [
            r'NET\s+PAY[:\s]*\n?\s*\$?\s*([\d,]+\.?\d{0,2})',
            r'TAKE\s+HOME[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
        ]
        for pattern in net_patterns:
            net_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if net_match:
                details['net_pay'] = net_match.group(1)
                break
        
        # Extract taxes
        tax_patterns = {
            'federal_tax': r'FEDERAL\s+(?:INCOME\s+)?TAX[:\s]*\n?\s*\$?\s*([\d,]+\.\d{2})',
            'state_tax': r'(?:STATE|CA\s+SDI)\s+(?:INCOME\s+)?(?:TAX)?[:\s]*\n?\s*\$?\s*([\d,]+\.\d{2})',
            'social_security': r'SOCIAL\s+SECURITY\s+TAX[:\s]*\n?\s*\$?\s*([\d,]+\.\d{2})',
            'medicare': r'MEDICARE\s+TAX[:\s]*\n?\s*\$?\s*([\d,]+\.\d{2})'
        }
        
        for field, pattern in tax_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details[field] = match.group(1)
        
        # Calculate confidence
        critical_fields = ['company_name', 'employee_name', 'pay_date']
        important_fields = ['gross_pay', 'net_pay', 'employee_id']
        optional_fields = ['federal_tax', 'state_tax', 'social_security', 'medicare']
        
        critical_filled = sum(1 for k in critical_fields if details.get(k))
        important_filled = sum(1 for k in important_fields if details.get(k))
        optional_filled = sum(1 for k in optional_fields if details.get(k))
        
        confidence = (
            (critical_filled / len(critical_fields)) * 50 +
            (important_filled / len(important_fields)) * 30 +
            (optional_filled / len(optional_fields)) * 20
        )
        
        details['confidence_score'] = round(confidence, 2)
        details['extraction_timestamp'] = datetime.now().isoformat()
        
        return details

