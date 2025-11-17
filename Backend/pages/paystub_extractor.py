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
        
        # Extract company name - improved logic
        company_patterns = [
            r'^([A-Z][a-zA-Z\s&,\.]+(?:INC|CORP|LLC|SYSTEMS|COMPANY|GROUP|CORPORATION|LIMITED|LTD|CO\.?))',
            r'^([A-Z][a-zA-Z\s&,\.]+(?:INC|CORP|LLC|SYSTEMS|COMPANY|GROUP|CORPORATION|LIMITED|LTD|CO\.?))',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 3:
                    details['company_name'] = company
                    break
        
        # Fallback: check first few lines
        if not details['company_name']:
            for line in lines[:20]:
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                skip_words = ['EMPLOYEE', 'PAY', 'SSN', 'DESCRIPTION', 'EARNINGS', 'DEDUCTIONS', 
                             'DATE', 'HOURS', 'RATE', 'CURRENT', 'YTD', 'FEDERAL', 'STATE', 'PERIOD',
                             'PAYSTUB', 'PAYCHECK', 'STATEMENT']
                if any(word in line.upper() for word in skip_words):
                    continue
                
                if any(keyword in line.upper() for keyword in ['INC', 'CORP', 'LLC', 'SYSTEMS', 
                                                                'COMPANY', 'GROUP', 'CORPORATION', 
                                                                'LIMITED', 'LTD', 'CO.', 'ENTERPRISES']):
                    details['company_name'] = line
                    break
                
                # If line looks like a company name (has proper case, length > 5)
                if (len(line) > 5 and not line.isupper() and 
                    any(c.isupper() for c in line) and 
                    not any(char.isdigit() for char in line[:5])):
                    details['company_name'] = line
                    break
        
        # Extract employee name - more flexible patterns, stop at SOCIAL SEC or ID
        employee_patterns = [
            r'(?:EMPLOYEE\s+NAME|NAME)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+?)(?:\s+(?:SOCIAL|SEC|ID|EMPLOYEE|SSN))',
            r'(?:EMPLOYEE\s+NAME|NAME)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'EMPLOYEE\s+NAME[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?:^|\n)NAME[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+(?:SOCIAL|SEC|ID|EMPLOYEE|SSN))',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+(?:SOCIAL\s+SEC|EMPLOYEE\s+ID|SSN))',
        ]
        
        for pattern in employee_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up name - remove any trailing words that shouldn't be there
                name = re.sub(r'\s+(SOCIAL|SEC|ID|EMPLOYEE|SSN).*$', '', name, flags=re.IGNORECASE)
                name_parts = name.split()
                if (len(name_parts) >= 2 and 
                    not any(word in name.upper() for word in 
                    ['EMPLOYEE', 'COMPANY', 'ADDRESS', 'DEPARTMENT', 'POSITION', 'PAY', 'PERIOD', 'DATE', 'SOCIAL']) and
                    all(part[0].isupper() for part in name_parts if part and len(part) > 0)):
                    details['employee_name'] = name
                    break
        
        # Extract employee ID - more flexible patterns
        empid_patterns = [
            r'EMPLOYEE\s*(?:ID|NUMBER|#)[:\s]*\n?\s*([A-Z0-9\-]{3,})',
            r'(?:EMP\s*)?ID[:\s]*([A-Z]{2,}-[A-Z0-9\-]{3,})',
            r'(?:^|\n)([A-Z]{2,3}-\d{4,})(?:\n|$)',
            r'EMP\s*ID[:\s]*([A-Z0-9\-]{4,})',
            r'EMPLOYEE\s+#[:\s]*([A-Z0-9\-]{3,})',
            r'ID[:\s]+([A-Z0-9\-]{4,})',
        ]
        for pattern in empid_patterns:
            empid_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if empid_match and empid_match.group(1):
                emp_id = empid_match.group(1).strip()
                if (len(emp_id) >= 3 and 
                    not any(word in emp_id.upper() for word in ['EMPLOYEE', 'NAME', 'SSN', 'FEDERAL', 'STATE', 'PAY']) and
                    (any(c.isdigit() for c in emp_id) or '-' in emp_id or any(c.isalpha() for c in emp_id))):
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
        
        # Extract pay date - more flexible patterns
        date_patterns = [
            r'PAY\s+DATE[:\s]*\n?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'CHECK\s+DATE[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'PAID\s+DATE[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'PAY\s+DATE[:\s]+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'(?:^|\n)PAY\s+DATE[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if date_match and date_match.group(1):
                details['pay_date'] = date_match.group(1)
                break
        
        # Extract gross pay - CURRENT period only (exclude YTD)
        # Look for GROSS WAGES followed by CURRENT TOTAL value
        gross_patterns = [
            r'GROSS\s+WAGES[:\s]*CURRENT\s+TOTAL[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            r'GROSS\s+(?:PAY|EARNINGS|WAGES)[:\s]*CURRENT\s+TOTAL[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            r'CURRENT\s+TOTAL[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?=\s*(?:YTD|DEDUCTIONS|NET|YEAR))',
            r'GROSS\s+(?:PAY|EARNINGS|WAGES)[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
        ]
        for pattern in gross_patterns:
            gross_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if gross_match and gross_match.group(1):
                # Make sure it's not a YTD value by checking context
                match_text = gross_match.group(0)
                # Get surrounding context to verify
                start_pos = max(0, gross_match.start() - 50)
                end_pos = min(len(text), gross_match.end() + 50)
                context = text[start_pos:end_pos].upper()
                if 'YTD' not in context and 'YEAR TO DATE' not in context:
                    details['gross_pay'] = gross_match.group(1).replace(',', '')
                    break
        
        # Extract net pay - CURRENT period only (exclude YTD)
        # Try to find NET PAY that comes before YTD NET PAY
        net_patterns = [
            r'NET\s+PAY[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            r'NET\s+PAY[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            r'TAKE\s+HOME[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
        ]
        
        # Find all NET PAY matches and pick the one that's not YTD
        best_net_match = None
        for pattern in net_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE):
                if match and match.group(1):
                    # Get surrounding context to verify
                    start_pos = max(0, match.start() - 100)
                    end_pos = min(len(text), match.end() + 100)
                    context = text[start_pos:end_pos].upper()
                    
                    # Check if this is a YTD value
                    before_context = text[max(0, match.start() - 20):match.start()].upper()
                    after_context = text[match.end():min(len(text), match.end() + 20)].upper()
                    
                    # Skip if it's clearly YTD
                    if ('YTD' in before_context or 'YEAR TO DATE' in before_context or 
                        'YTD NET' in context or re.search(r'YTD\s+NET', context)):
                        continue
                    
                    # This looks like a current period NET PAY
                    best_net_match = match
                    break
            
            if best_net_match:
                break
        
        if best_net_match:
            details['net_pay'] = best_net_match.group(1).replace(',', '')
        
        # Extract taxes - CURRENT period only (exclude YTD)
        tax_patterns = {
            'federal_tax': [
                r'FED\s+TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'FEDERAL\s+(?:INCOME\s+)?TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'FEDERAL\s+WITHHOLDING[:\s]*CURRENT\s+TOTAL[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'FED\s+TAX[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ],
            'state_tax': [
                r'STATE\s+(?:INCOME\s+)?(?:TAX|WITHHOLDING)?[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'STATE\s+TAX[:\s]*CURRENT\s+TOTAL[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'STATE\s+WITHHOLDING[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'CA\s+SDI[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ],
            'social_security': [
                r'FICA\s+SS\s+TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'SOCIAL\s+SECURITY\s+TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'SS\s+TAX[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'OASDI[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ],
            'medicare': [
                r'FICA\s+MED\s+TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'MEDICARE\s+TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'MED\s+TAX[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'MEDICARE[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ]
        }
        
        for field, patterns in tax_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match and match.group(1):
                    # Make sure it's not a YTD value
                    match_text = match.group(0)
                    if 'YTD' not in match_text.upper() and 'YEAR TO DATE' not in match_text.upper():
                        details[field] = match.group(1).replace(',', '')
                        break
        
        # Extract YTD values if available - must explicitly be YTD
        ytd_patterns = {
            'ytd_gross': [
                r'YTD\s+GROSS[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'YEAR\s+TO\s+DATE\s+GROSS[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'YTD\s+GROSS\s+WAGES[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'YTD\s+EARNINGS[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ],
            'ytd_net': [
                r'YTD\s+NET\s+PAY[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'YTD\s+NET[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'YEAR\s+TO\s+DATE\s+NET\s+PAY[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'YTD\s+NET\s+AMOUNT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ]
        }
        
        for field, patterns in ytd_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match and match.group(1):
                    details[field] = match.group(1).replace(',', '')
                    break
        
        # Calculate confidence - improved scoring
        critical_fields = ['company_name', 'employee_name', 'pay_date']
        important_fields = ['gross_pay', 'net_pay', 'employee_id']
        optional_fields = ['federal_tax', 'state_tax', 'social_security', 'medicare', 'ytd_gross', 'ytd_net']
        
        critical_filled = sum(1 for k in critical_fields if details.get(k))
        important_filled = sum(1 for k in important_fields if details.get(k))
        optional_filled = sum(1 for k in optional_fields if details.get(k))
        
        # More lenient scoring - if we have at least 2 critical fields, boost score
        critical_bonus = 10 if critical_filled >= 2 else 0
        
        # Base confidence calculation
        base_confidence = (
            (critical_filled / len(critical_fields)) * 45 +
            (important_filled / len(important_fields)) * 35 +
            (optional_filled / len(optional_fields)) * 20
        )
        
        # Add bonus for having key fields
        if details.get('gross_pay') and details.get('net_pay'):
            base_confidence += 5
        
        confidence = min(base_confidence + critical_bonus, 100.0)
        
        details['confidence_score'] = round(confidence, 2)
        details['extraction_timestamp'] = datetime.now().isoformat()
        
        return details

