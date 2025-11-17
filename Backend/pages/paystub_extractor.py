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
        # Strategy: Find NET PAY that appears AFTER DEDUCTIONS but BEFORE any YTD section
        best_net_match = None
        
        # First, find where YTD section starts (if it exists)
        ytd_section_start = None
        ytd_markers = [
            r'YTD\s+GROSS',
            r'YTD\s+DEDCTIONS',
            r'YTD\s+DEDUCTIONS',
            r'YEAR\s+TO\s+DATE',
        ]
        for marker in ytd_markers:
            ytd_match = re.search(marker, text, re.IGNORECASE | re.MULTILINE)
            if ytd_match:
                ytd_section_start = ytd_match.start()
                break
        
        # Find NET PAY that comes before YTD section
        net_patterns = [
            r'NET\s+PAY[:\s]+([\d,]+\.\d{2})',
            r'NET\s+PAY\s*:\s*([\d,]+\.\d{2})',
            r'NET\s+PAY\s+([\d,]+\.\d{2})',
            r'DEDUCTIONS[:\s]+[\d,]+\.?\d{0,2}.*?NET\s+PAY[:\s]*([\d,]+\.\d{2})',
            r'TOTAL[:\s]+DEDUCTIONS.*?NET\s+PAY[:\s]*([\d,]+\.\d{2})',
        ]
        
        all_matches = []
        for pattern in net_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE):
                if match and match.group(1):
                    # Must be before YTD section if YTD section exists
                    if ytd_section_start is None or match.start() < ytd_section_start:
                        # Check context to ensure it's not YTD
                        before_text = text[max(0, match.start() - 15):match.start()].upper()
                        if 'YTD' not in before_text and 'YEAR TO DATE' not in before_text:
                            all_matches.append(match)
        
        # Sort by position (earlier = more likely current period)
        all_matches.sort(key=lambda m: m.start())
        
        # Take the last match before YTD section (most likely to be current period NET PAY)
        if all_matches:
            # Get the match closest to YTD section but before it
            if ytd_section_start:
                valid_matches = [m for m in all_matches if m.start() < ytd_section_start]
                if valid_matches:
                    best_net_match = valid_matches[-1]  # Last one before YTD
                else:
                    best_net_match = all_matches[0]  # Fallback to first
            else:
                best_net_match = all_matches[-1]  # Last match if no YTD section
        
        if best_net_match:
            details['net_pay'] = best_net_match.group(1).replace(',', '').strip()
        else:
            # Final fallback: Look for NET PAY that's clearly not YTD
            net_label_match = re.search(r'NET\s+PAY(?!\s+YTD)', text, re.IGNORECASE | re.MULTILINE)
            if net_label_match:
                after_text = text[net_label_match.end():net_label_match.end() + 30]
                number_match = re.search(r'([\d,]+\.\d{2})', after_text)
                if number_match:
                    before_num = after_text[:number_match.start()].upper()
                    if 'YTD' not in before_num:
                        details['net_pay'] = number_match.group(1).replace(',', '').strip()
        
        # Extract taxes - CURRENT period only (exclude YTD)
        tax_patterns = {
            'federal_tax': [
                r'FED\s+TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'FEDERAL\s+(?:INCOME\s+)?TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'FEDERAL\s+WITHHOLDING[:\s]*CURRENT\s+TOTAL[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'FED\s+TAX[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
            ],
            'state_tax': [
                r'(?:[A-Z]{2}\s+)?ST\s+TAX[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'STATE\s+(?:INCOME\s+)?(?:TAX|WITHHOLDING)?[:\s]*(?:CURRENT\s+TOTAL)?[:\s]*\$?\s*([\d,]+\.?\d{0,2})(?!\s*YTD)',
                r'STATE\s+TAX[:\s]*CURRENT\s+TOTAL[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'STATE\s+WITHHOLDING[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'CA\s+SDI[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
                r'NY\s+ST\s+TAX[:\s]*CURRENT[:\s]*\$?\s*([\d,]+\.?\d{0,2})',
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
        # Use very flexible patterns to handle OCR variations
        ytd_patterns = {
            'ytd_gross': [
                # Most common formats first - be very flexible
                r'YTD\s+GROSS[:\s]*([\d,]+\.\d{2})',
                r'YTD\s+GROSS\s*:\s*([\d,]+\.\d{2})',
                r'YTD\s+GROSS\s+([\d,]+\.\d{2})',
                r'YTD\s+GROSS[:\s]*([\d,]+\.?\d{0,2})',
                r'YTD\s+GROSS[:\s]*\$?\s*([\d,]+\.\d{2})',
                r'YEAR\s+TO\s+DATE\s+GROSS[:\s]*\$?\s*([\d,]+\.\d{2})',
                r'YTD\s+GROSS\s+WAGES[:\s]*\$?\s*([\d,]+\.\d{2})',
                r'YTD\s+EARNINGS[:\s]*\$?\s*([\d,]+\.\d{2})',
            ],
            'ytd_net': [
                # Most common formats first - MUST have NET PAY, not just NET
                r'YTD\s+NET\s+PAY[:\s]+([\d,]+\.\d{2})',
                r'YTD\s+NET\s+PAY\s*:\s*([\d,]+\.\d{2})',
                r'YTD\s+NET\s+PAY\s+([\d,]+\.\d{2})',
                r'YTD\s+NET\s+PAY[:\s]*\$?\s*([\d,]+\.\d{2})',
                r'YEAR\s+TO\s+DATE\s+NET\s+PAY[:\s]*\$?\s*([\d,]+\.\d{2})',
                r'YTD\s+NET\s+AMOUNT[:\s]*\$?\s*([\d,]+\.\d{2})',
                # Only use YTD NET (without PAY) if we're sure it's not GROSS
                r'YTD\s+NET[:\s]+([\d,]+\.\d{2})(?!.*GROSS)',
            ]
        }
        
        for field, patterns in ytd_patterns.items():
            found = False
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match and match.group(1):
                    value = match.group(1).replace(',', '').strip()
                    if value and value != '0' and len(value) > 0:
                        details[field] = value
                        found = True
                        break
            
            # Enhanced Fallback: Look for YTD label and find number nearby with multiple strategies
            if not found:
                ytd_label = None
                if field == 'ytd_gross':
                    # Try multiple label patterns
                    label_patterns = [
                        r'YTD\s+GROSS',
                        r'YTD\s+GROSS\s+WAGES',
                        r'YTD\s+EARNINGS',
                    ]
                    for lp in label_patterns:
                        ytd_label = re.search(lp, text, re.IGNORECASE | re.MULTILINE)
                        if ytd_label:
                            break
                elif field == 'ytd_net':
                    # Try multiple label patterns - MUST have NET PAY, not just NET
                    label_patterns = [
                        r'YTD\s+NET\s+PAY',
                        r'YTD\s+NET\s+PAY\s*:',
                        r'YTD\s+NET\s+PAY\s+',
                    ]
                    for lp in label_patterns:
                        ytd_label = re.search(lp, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        if ytd_label:
                            break
                    
                    # If still not found, look for YTD NET PAY that appears after YTD GROSS or YTD DEDCTIONS
                    if not ytd_label:
                        # Find the summary section and search after it
                        summary_match = re.search(r'YTD\s+(?:GROSS|DEDCTIONS|DEDUCTIONS)', text, re.IGNORECASE | re.MULTILINE)
                        if summary_match:
                            # Look for YTD NET PAY in the text after summary (within 200 chars)
                            after_summary_text = text[summary_match.end():summary_match.end() + 200]
                            net_match = re.search(r'YTD\s+NET\s+PAY', after_summary_text, re.IGNORECASE | re.MULTILINE)
                            if net_match:
                                # Create a match object with adjusted positions
                                class AdjustedMatch:
                                    def __init__(self, original_match, offset):
                                        self._original = original_match
                                        self._offset = offset
                                    def start(self):
                                        return self._original.start() + self._offset
                                    def end(self):
                                        return self._original.end() + self._offset
                                    def group(self, n=0):
                                        return self._original.group(n)
                                
                                ytd_label = AdjustedMatch(net_match, summary_match.end())
                
                if ytd_label:
                    # Get the line containing the YTD label
                    line_start = text.rfind('\n', 0, ytd_label.start()) + 1
                    line_end = text.find('\n', ytd_label.end())
                    if line_end == -1:
                        line_end = len(text)
                    line_text = text[line_start:line_end]
                    
                    # Look for number on the same line, after the label
                    after_label = line_text[ytd_label.end() - line_start:]
                    # Try multiple number patterns - prefer exact decimal format
                    number_patterns = [
                        r'([\d,]+\.\d{2})',  # Standard format: 5,000.00
                        r'([\d,]+\.\d{1,2})',  # Allow 1-2 decimals
                        r'([\d,]+)',  # Just numbers with commas
                    ]
                    for np in number_patterns:
                        number_match = re.search(np, after_label)
                        if number_match:
                            value = number_match.group(1).replace(',', '').strip()
                            # Validate it's a reasonable amount (not too small, has digits)
                            if value and value != '0' and len(value) > 0 and value.replace('.', '').isdigit():
                                value_float = float(value)
                                # Make sure it's not part of a date or other number
                                if value_float > 10:  # Reasonable minimum for YTD values
                                    # For YTD Net, validate it's less than YTD Gross (if we have it)
                                    if field == 'ytd_net' and details.get('ytd_gross'):
                                        try:
                                            ytd_gross_val = float(details['ytd_gross'].replace(',', ''))
                                            if value_float > ytd_gross_val:
                                                # This might be wrong - skip it
                                                continue
                                        except:
                                            pass
                                    details[field] = value
                                    found = True
                                    break
                    if found:
                        break
            
            # Final fallback: Search line by line for YTD values
            if not found:
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    line_upper = line.upper().strip()
                    if field == 'ytd_gross':
                        # Must have YTD and GROSS, but NOT NET
                        if 'YTD' in line_upper and 'GROSS' in line_upper and 'NET' not in line_upper:
                            # Extract number from this line
                            numbers = re.findall(r'([\d,]+\.\d{2})', line)
                            if numbers:
                                value = numbers[0].replace(',', '').strip()
                                if value and float(value) > 10:
                                    details[field] = value
                                    found = True
                                    break
                    elif field == 'ytd_net':
                        # Must have YTD and NET PAY (or NET), but NOT GROSS
                        if ('YTD' in line_upper and 'NET' in line_upper and 
                            'GROSS' not in line_upper and 
                            ('PAY' in line_upper or 'NET PAY' in line_upper)):
                            # Extract number from this line
                            numbers = re.findall(r'([\d,]+\.\d{2})', line)
                            if numbers:
                                value = numbers[0].replace(',', '').strip()
                                value_float = float(value)
                                if value_float > 10:
                                    # Validate it's less than YTD Gross if we have it
                                    if details.get('ytd_gross'):
                                        try:
                                            ytd_gross_val = float(details['ytd_gross'].replace(',', ''))
                                            if value_float <= ytd_gross_val:
                                                details[field] = value
                                                found = True
                                                break
                                        except:
                                            details[field] = value
                                            found = True
                                            break
                                    else:
                                        details[field] = value
                                        found = True
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

