"""
PDF Statement Validator - Rule-Based Tampering Detection

This module performs rule-based analysis on bank statement PDFs to detect
signs of modification, forgery, or editing.
"""

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from google.cloud import vision
except ImportError:
    vision = None

import hashlib
import re
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFStatementValidator:
    """Validates bank statement PDFs for signs of tampering."""

    # Rules for validation
    VALIDATION_RULES = {
        'metadata': {
            'weight': 0.15,
            'checks': [
                'creator_suspicious',
                'producer_suspicious',
                'creation_date_future',
                'modification_recent'
            ]
        },
        'structure': {
            'weight': 0.20,
            'checks': [
                'missing_pages',
                'page_order_suspicious',
                'corrupted_objects'
            ]
        },
        'content': {
            'weight': 0.35,
            'checks': [
                'inconsistent_formatting',
                'text_overlay_detected',
                'unusual_spacing',
                'broken_fonts'
            ]
        },
        'financial': {
            'weight': 0.30,
            'checks': [
                'balance_calculation_error',
                'transaction_date_inconsistency',
                'suspicious_amounts',
                'missing_transactions'
            ]
        }
    }

    def __init__(self, pdf_path: str, vision_client: Optional[object] = None):
        """
        Initialize validator with PDF file.

        Args:
            pdf_path: Path to PDF file
            vision_client: Optional Google Cloud Vision API client for OCR fallback
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.pdf_reader = None
        self.pdf_doc = None
        self.pdf_plumber = None
        self.num_pages = 0
        self.metadata = None
        self.text_content = {}
        self.vision_client = vision_client
        self.vision_used = False
        self.findings = {
            'suspicious_indicators': [],
            'warnings': [],
            'risk_score': 0.0,
            'verdict': 'CLEAN'
        }

    def load_pdf(self) -> bool:
        """Load and parse PDF file."""
        # Try PyMuPDF first (best for both text and image-based PDFs)
        if fitz:
            try:
                self.pdf_doc = fitz.open(str(self.pdf_path))
                self.num_pages = len(self.pdf_doc)
                logger.info(f"PDF loaded with PyMuPDF: {self.num_pages} pages")
                return True
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}, trying pdfplumber")
                self.pdf_doc = None

        # Try pdfplumber (better text extraction for some PDFs)
        if pdfplumber:
            try:
                self.pdf_plumber = pdfplumber.open(str(self.pdf_path))
                self.num_pages = len(self.pdf_plumber.pages)
                logger.info(f"PDF loaded with pdfplumber: {self.num_pages} pages")
                return True
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
                self.pdf_plumber = None

        # Try PyPDF2 as fallback
        if PyPDF2:
            try:
                with open(self.pdf_path, 'rb') as f:
                    self.pdf_reader = PyPDF2.PdfReader(f)
                    self.num_pages = len(self.pdf_reader.pages)
                    self.metadata = self.pdf_reader.metadata

                logger.info(f"PDF loaded with PyPDF2: {self.num_pages} pages")
                return True
            except Exception as e:
                logger.warning(f"PyPDF2 failed: {e}")

        # Fallback: Basic PDF reading using standard library
        try:
            with open(self.pdf_path, 'rb') as f:
                # Read raw PDF to count pages and extract text
                raw_content = f.read()
                # Count endobj markers as approximate page count
                self.num_pages = raw_content.count(b'endobj')
                if self.num_pages > 100:  # Likely not page count
                    self.num_pages = 1  # Default to at least 1 page

            logger.info(f"PDF loaded with fallback method: {self.num_pages} pages")
            return True
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            self.findings['suspicious_indicators'].append(f"Failed to load PDF: {e}")
            return False

    def extract_text(self) -> Dict[int, str]:
        """Extract text from all pages."""
        # TESTING MODE: Try Google Vision first for better accuracy
        if self.vision_client:
            logger.info("TESTING MODE: Attempting Google Vision API extraction as PRIMARY method")
            vision_result = self._extract_text_with_vision()
            if vision_result and sum(len(text) for text in vision_result.values()) > 100:
                logger.info("Vision API extraction successful, returning Vision results")
                return vision_result
            elif vision_result:
                logger.warning(f"Vision API extraction returned minimal text ({sum(len(text) for text in vision_result.values())} chars), trying PyMuPDF fallback")
            else:
                logger.warning("Vision API extraction returned no results, trying PyMuPDF fallback")

        # Fallback 1: Try PyMuPDF (best for native PDFs)
        if hasattr(self, 'pdf_doc') and self.pdf_doc:
            try:
                for page_num in range(len(self.pdf_doc)):
                    page = self.pdf_doc[page_num]
                    text = page.get_text()
                    self.text_content[page_num] = text if text else ""
                logger.info(f"Text extracted from {len(self.text_content)} pages using PyMuPDF")
                return self.text_content
            except Exception as e:
                logger.warning(f"PyMuPDF text extraction failed: {e}")
                self.text_content = {}

        # Fallback 2: Try pdfplumber
        if hasattr(self, 'pdf_plumber') and self.pdf_plumber:
            try:
                for page_num, page in enumerate(self.pdf_plumber.pages):
                    text = page.extract_text()
                    self.text_content[page_num] = text if text else ""
                logger.info(f"Text extracted from {len(self.text_content)} pages using pdfplumber")
                return self.text_content
            except Exception as e:
                logger.warning(f"pdfplumber text extraction failed: {e}")
                self.text_content = {}

        # Fallback 3: Try PyPDF2
        if hasattr(self, 'pdf_reader') and self.pdf_reader:
            try:
                for page_num, page in enumerate(self.pdf_reader.pages):
                    text = page.extract_text()
                    self.text_content[page_num] = text if text else ""
                logger.info(f"Text extracted from {len(self.text_content)} pages using PyPDF2")
                return self.text_content
            except Exception as e:
                logger.warning(f"PyPDF2 text extraction failed: {e}")

        # Fallback 4: Extract text from raw PDF content
        try:
            with open(self.pdf_path, 'rb') as f:
                raw_content = f.read()
                # Extract text between BT (begin text) and ET (end text) markers
                import re as regex_mod
                text_objects = regex_mod.findall(b'BT(.*?)ET', raw_content, regex_mod.DOTALL)

                combined_text = ""
                for obj in text_objects:
                    # Extract strings from text objects (enclosed in parentheses or angle brackets)
                    strings = regex_mod.findall(b'\\((.*?)\\)|<([0-9A-Fa-f]+)>', obj)
                    for match in strings:
                        if match[0]:
                            try:
                                combined_text += match[0].decode('latin-1', errors='ignore') + " "
                            except:
                                pass

                if combined_text.strip():
                    self.text_content[0] = combined_text
                    logger.info("Text extracted from raw PDF content")

            # Check if we got meaningful text
            total_text_length = sum(len(text) for text in self.text_content.values())

            return self.text_content
        except Exception as e:
            logger.warning(f"Fallback text extraction failed: {e}")
            return {}

    def _extract_text_with_vision(self) -> Dict[int, str]:
        """
        Extract text from PDF using Google Cloud Vision API OCR.
        This is used as a fallback for scanned PDFs or when standard extraction fails.
        NOW PROCESSES ALL PAGES (with reasonable limits for cost control).

        Returns:
            Dict[int, str]: Extracted text by page number
        """
        if not self.vision_client or not vision:
            logger.warning("Vision client not available for OCR fallback")
            return {}

        try:
            logger.info("Using Google Cloud Vision API for text extraction (OCR fallback)")
            self.vision_used = True

            # Try to convert PDF to images if we have PyMuPDF
            if hasattr(self, 'pdf_doc') and self.pdf_doc:
                try:
                    # Process ALL pages (max 100 for cost control)
                    page_limit = min(len(self.pdf_doc), 100)
                    logger.info(f"Processing {page_limit} pages with Vision API")

                    for page_num in range(page_limit):
                        try:
                            page = self.pdf_doc[page_num]
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                            image_bytes = pix.tobytes("png")

                            image = vision.Image(content=image_bytes)
                            response = self.vision_client.text_detection(image=image)

                            if response.text_annotations:
                                text = response.text_annotations[0].description
                                self.text_content[page_num] = text if text else ""
                                logger.info(f"Extracted text from page {page_num} using Vision API")

                        except Exception as e:
                            logger.warning(f"Vision API extraction failed for page {page_num}: {e}")
                            continue

                    if self.text_content:
                        logger.info(f"Vision API extracted text from {len(self.text_content)} pages")
                        return self.text_content

                except Exception as e:
                    logger.warning(f"Failed to extract pages for Vision API: {e}")

            # Fallback: Try to read the PDF file directly
            try:
                with open(self.pdf_path, 'rb') as f:
                    content = f.read()

                image = vision.Image(content=content)
                response = self.vision_client.text_detection(image=image)

                if response.text_annotations:
                    text = response.text_annotations[0].description
                    self.text_content[0] = text if text else ""
                    logger.info("Vision API extracted text from PDF (treating as single image)")
                    return self.text_content

            except Exception as e:
                logger.error(f"Vision API fallback extraction failed: {e}")

            if not self.text_content:
                logger.error("Vision API could not extract any text from the PDF")
                self.findings['warnings'].append(
                    "PDF appears to be a scanned image, but Vision API extraction produced no results"
                )

            return self.text_content

        except Exception as e:
            logger.error(f"Unexpected error during Vision API extraction: {e}")
            return {}

    def check_metadata(self) -> Dict[str, any]:
        """Check PDF metadata for suspicious indicators."""
        results = {
            'creator_suspicious': False,
            'producer_suspicious': False,
            'creation_date_future': False,
            'modification_recent': False
        }

        if not self.metadata:
            return results

        try:
            # Check creator
            creator = str(self.metadata.get('/Creator', ''))
            suspicious_creators = [
                'adobe', 'Microsoft', 'LibreOffice', 'Pages',
                'iTextSharp', 'wkhtmltopdf', 'Unknown'
            ]
            if any(s.lower() in creator.lower() for s in suspicious_creators):
                results['creator_suspicious'] = True
                self.findings['warnings'].append(
                    f"Creator field: {creator} (may indicate editing)"
                )

            # Check producer
            producer = str(self.metadata.get('/Producer', ''))
            if 'edited' in producer.lower() or 'modified' in producer.lower():
                results['producer_suspicious'] = True
                self.findings['suspicious_indicators'].append(
                    f"Producer indicates editing: {producer}"
                )

            # Check dates
            created_date = self.metadata.get('/CreationDate', '')
            modified_date = self.metadata.get('/ModDate', '')

            if created_date and modified_date:
                if self._parse_pdf_date(modified_date) > self._parse_pdf_date(created_date):
                    results['modification_recent'] = True
                    self.findings['warnings'].append(
                        "Document has been modified after creation"
                    )

            # Check for future dates
            if created_date:
                created = self._parse_pdf_date(created_date)
                if created > datetime.now():
                    results['creation_date_future'] = True
                    self.findings['suspicious_indicators'].append(
                        "Creation date is in the future"
                    )

        except Exception as e:
            logger.error(f"Error checking metadata: {e}")

        return results

    def check_structure(self) -> Dict[str, any]:
        """Check PDF structure for anomalies."""
        results = {
            'missing_pages': False,
            'page_order_suspicious': False,
            'corrupted_objects': False
        }

        try:
            # Check page count
            if self.num_pages < 1:
                results['missing_pages'] = True
                self.findings['suspicious_indicators'].append(
                    "PDF contains no pages"
                )
            elif self.num_pages > 100:
                self.findings['warnings'].append(
                    f"Unusually large document: {self.num_pages} pages"
                )

            # Check for suspicious page ordering
            page_dates = []
            if self.text_content:
                for page_num, text in self.text_content.items():
                    # Try multiple date formats
                    dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text)
                    if not dates:
                        dates = re.findall(r'\d{1,2}-\d{1,2}-\d{4}', text)
                    if not dates:
                        dates = re.findall(r'\d{4}/\d{1,2}/\d{1,2}', text)
                    if not dates:
                        dates = re.findall(r'\d{4}-\d{1,2}-\d{1,2}', text)
                    if dates:
                        page_dates.append((page_num, dates[0]))

            if len(page_dates) > 1:
                # Check if dates are in descending order (pages out of order)
                for i in range(len(page_dates) - 1):
                    date1 = datetime.strptime(page_dates[i][1], '%m/%d/%Y')
                    date2 = datetime.strptime(page_dates[i + 1][1], '%m/%d/%Y')
                    if date2 > date1:
                        results['page_order_suspicious'] = True
                        self.findings['warnings'].append(
                            f"Pages may be out of chronological order"
                        )
                        break

        except Exception as e:
            logger.error(f"Error checking structure: {e}")

        return results

    def check_content(self) -> Dict[str, any]:
        """Check content for editing artifacts."""
        results = {
            'inconsistent_formatting': False,
            'text_overlay_detected': False,
            'unusual_spacing': False,
            'broken_fonts': False
        }

        if not self.pdf_reader:
            return results

        try:
            # Analyze formatting consistency
            font_families = set()
            unusual_chars = 0

            for page_num, page in enumerate(self.pdf_reader.pages):
                if '/Font' in page['/Resources']:
                    fonts = page['/Resources']['/Font']
                    for font_ref in fonts:
                        font_families.add(str(fonts[font_ref]))

                # Check for unusual character spacing
                text = self.text_content.get(page_num, '')
                # Look for excessive spaces or unusual patterns
                if re.search(r'\s{5,}', text):
                    results['unusual_spacing'] = True

                # Count non-ASCII characters
                unusual_chars += sum(1 for c in text if ord(c) > 127)

            if unusual_chars > len(''.join(self.text_content.values())) * 0.05:
                results['broken_fonts'] = True
                self.findings['warnings'].append(
                    "Detected unusual characters (possible font corruption)"
                )

            if len(font_families) > 10:
                results['inconsistent_formatting'] = True
                self.findings['warnings'].append(
                    f"Document uses {len(font_families)} different fonts"
                )

            # Check for text overlay (same text appearing at different positions)
            all_text = ' '.join(self.text_content.values())
            words = all_text.split()
            word_freq = {}
            for word in words:
                if len(word) > 5:  # Only check meaningful words
                    word_freq[word] = word_freq.get(word, 0) + 1

            if any(freq > 3 for freq in word_freq.values()):
                results['text_overlay_detected'] = True
                self.findings['warnings'].append(
                    "Detected possible text overlay or duplication"
                )

        except Exception as e:
            logger.error(f"Error checking content: {e}")

        return results

    def check_financial_consistency(self) -> Dict[str, any]:
        """Check financial data for consistency and accuracy."""
        results = {
            'balance_calculation_error': False,
            'transaction_date_inconsistency': False,
            'suspicious_amounts': False,
            'missing_transactions': False
        }

        try:
            all_text = ' '.join(self.text_content.values())

            # Extract financial numbers
            amounts = re.findall(r'\$?\s*(\d+[.,]\d{2})', all_text)

            # Enhanced date detection - try multiple formats
            dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', all_text)  # MM/DD/YYYY
            if not dates:
                dates = re.findall(r'\d{1,2}-\d{1,2}-\d{4}', all_text)  # MM-DD-YYYY
            if not dates:
                dates = re.findall(r'\d{4}/\d{1,2}/\d{1,2}', all_text)  # YYYY/MM/DD
            if not dates:
                dates = re.findall(r'\d{4}-\d{1,2}-\d{1,2}', all_text)  # YYYY-MM-DD
            if not dates:
                # Try month name patterns (Jan, January, etc)
                dates = re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}', all_text, re.IGNORECASE)
            if not dates:
                dates = re.findall(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}', all_text, re.IGNORECASE)

            if not amounts:
                results['missing_transactions'] = True
                self.findings['warnings'].append(
                    "No transaction amounts found in document"
                )

            if not dates:
                results['transaction_date_inconsistency'] = True
                self.findings['suspicious_indicators'].append(
                    "No dates found in document"
                )

            # Check for suspicious amounts
            large_amounts = [
                float(a.replace('$', '').replace(',', ''))
                for a in amounts if '$' in str(a) or ',' in str(a)
            ]
            if large_amounts:
                avg_amount = sum(large_amounts) / len(large_amounts)
                suspicious = [a for a in large_amounts if a > avg_amount * 5]
                if suspicious:
                    results['suspicious_amounts'] = True
                    self.findings['warnings'].append(
                        f"Detected unusually large amounts: {suspicious[:3]}"
                    )

            # Check date ordering consistency
            if dates:
                try:
                    date_objects = [datetime.strptime(d, '%m/%d/%Y') for d in dates]
                    if date_objects != sorted(date_objects):
                        results['transaction_date_inconsistency'] = True
                        self.findings['warnings'].append(
                            "Transaction dates are not in chronological order"
                        )
                except:
                    pass

        except Exception as e:
            logger.error(f"Error checking financial consistency: {e}")

        return results

    def check_missing_data_and_dates(self) -> Dict[str, any]:
        """
        Check for missing critical data and impossible/invalid dates.
        Forged statements often have incomplete account info or invalid dates.
        """
        results = {
            'missing_fields': [],
            'invalid_dates': [],
            'fraud_score': 0.0
        }

        try:
            all_text = ' '.join(self.text_content.values())
            lines = all_text.split('\n')

            # Critical fields that should be present in a bank statement
            critical_fields = {
                'account_number': ['Account Number', 'Acct', 'account ending'],
                'account_holder': ['name', 'holder', 'customer'],
                'bank_name': ['bank', 'credit union', 'financial'],
                'statement_period': ['statement period', 'period:', 'through'],
                'beginning_balance': ['beginning balance', 'opening balance', 'starting balance'],
                'ending_balance': ['ending balance', 'closing balance', 'final balance'],
            }

            # Count missing critical fields
            text_lower = all_text.lower()
            missing_count = 0

            for field, keywords in critical_fields.items():
                found = any(keyword in text_lower for keyword in keywords)
                if not found:
                    missing_count += 1
                    results['missing_fields'].append(field)
                    results['fraud_score'] += 8
                    self.findings['suspicious_indicators'].append(
                        f"🚨 MISSING DATA: {field} not found in statement"
                    )

            # Check for incomplete account number (all **** or missing)
            if '****' in all_text and not any(char.isdigit() for char in all_text.split('****')[1].split('\n')[0] if char != '*'):
                results['fraud_score'] += 12
                results['missing_fields'].append('account_number_incomplete')
                self.findings['suspicious_indicators'].append(
                    "🚨 INCOMPLETE ACCOUNT DATA: Account number shows only ****"
                )

            # Check for sparse/incomplete last names (single name entries)
            account_holder_line = None
            for i, line in enumerate(lines):
                if 'account' in line.lower() and i > 0:
                    account_holder_line = lines[i-1].strip()
                    break

            # Detect impossible dates (day > 31)
            import re as regex_mod
            all_dates = regex_mod.findall(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', all_text)

            for month, day, year in all_dates:
                day_int = int(day)
                month_int = int(month)

                # Check for impossible days (32+)
                if day_int > 31:
                    results['invalid_dates'].append(f"{month}/{day}/{year}")
                    results['fraud_score'] += 15
                    self.findings['suspicious_indicators'].append(
                        f"🚨 IMPOSSIBLE DATE: {month}/{day}/{year} (day {day_int} doesn't exist)"
                    )

                # Check for impossible months
                if month_int > 12 and month_int <= 31:  # Could be swapped MM/DD
                    results['invalid_dates'].append(f"{month}/{day}/{year} (possible swap)")
                    results['fraud_score'] += 12
                    self.findings['suspicious_indicators'].append(
                        f"🚨 INVALID MONTH: {month}/{day}/{year} (month {month_int} invalid)"
                    )

            # Check for dates outside statement period
            statement_period_match = regex_mod.search(r'statement period[:\s]*(\d{1,2}/\d{1,2}/\d{4})[^\d]*(\d{1,2}/\d{1,2}/\d{4})', all_text, regex_mod.IGNORECASE)
            if statement_period_match and all_dates:
                try:
                    period_start = datetime.strptime(statement_period_match.group(1), '%m/%d/%Y')
                    period_end = datetime.strptime(statement_period_match.group(2), '%m/%d/%Y')

                    out_of_period = 0
                    for month, day, year in all_dates:
                        try:
                            trans_date = datetime.strptime(f"{month}/{day}/{year}", '%m/%d/%Y')
                            if trans_date < period_start or trans_date > period_end:
                                out_of_period += 1
                        except:
                            pass

                    if out_of_period > len(all_dates) * 0.1:  # More than 10% out of period
                        results['fraud_score'] += 10
                        results['invalid_dates'].append(f"{out_of_period} transactions outside period")
                        self.findings['suspicious_indicators'].append(
                            f"🚨 OUT OF PERIOD: {out_of_period} transactions outside statement period"
                        )
                except:
                    pass

            # Check for non-chronological transaction dates
            transaction_dates = []
            transaction_lines = []
            for line in lines:
                date_match = regex_mod.match(r'^(\d{1,2})[/-](\d{1,2})', line.strip())
                if date_match:
                    transaction_lines.append(line.strip())
                    try:
                        month, day = date_match.groups()
                        date_obj = datetime.strptime(f"{month}/{day}/2024", '%m/%d/%Y')  # Assume current year for sorting
                        transaction_dates.append(date_obj)
                    except:
                        pass

            if len(transaction_dates) > 2:
                is_sorted = all(transaction_dates[i] <= transaction_dates[i+1] for i in range(len(transaction_dates)-1))
                if not is_sorted:
                    # Count how many are out of order
                    out_of_order = sum(1 for i in range(len(transaction_dates)-1) if transaction_dates[i] > transaction_dates[i+1])
                    if out_of_order > 0:
                        results['fraud_score'] += 10
                        self.findings['suspicious_indicators'].append(
                            f"🚨 NON-CHRONOLOGICAL: {out_of_order} transactions out of order"
                        )

            # Normalize fraud score to 0-1 range
            results['fraud_score'] = min(results['fraud_score'] / 30.0, 1.0)

        except Exception as e:
            logger.error(f"Error checking missing data and dates: {e}")

        return results

    def check_spelling_and_formatting(self) -> Dict[str, any]:
        """
        Check for spelling errors and formatting inconsistencies that indicate forgery.
        Forged documents often have typos in bank names, field names, etc.
        """
        results = {
            'spelling_errors_found': [],
            'formatting_issues': [],
            'fraud_score': 0.0
        }

        try:
            all_text = ' '.join(self.text_content.values())

            # Bank name spelling errors (common forgery mistakes)
            bank_misspellings = {
                'CHAES': ('CHASE', 8),
                'CHASSE': ('CHASE', 8),
                'CITIBANK': ('CITIBANK', 5),  # Less common
                'WELLS FARGO': ('WELLS FARGO', 5),
                'CHASE BANK': ('CHASE', 3),
                'AMERICA BANK': ('BANK OF AMERICA', 6),
            }

            common_bank_names = ['chase', 'wellsfargo', 'citibank', 'bankofamerica', 'us bank', 'td bank', 'pnc', 'capitalone']
            text_lower = all_text.lower()

            # Check for misspelled bank names
            for misspelling, (correct_name, weight) in bank_misspellings.items():
                if misspelling.lower() in text_lower:
                    results['spelling_errors_found'].append({
                        'error': misspelling,
                        'correct': correct_name,
                        'weight': weight
                    })
                    results['fraud_score'] += weight

            # Field name spelling errors (FORGED documents often misspell these)
            field_errors = {
                'ACOUNT': ('ACCOUNT', 12),        # Common typo in forged statements - INCREASED WEIGHT
                'STATMENT': ('STATEMENT', 11),
                'BEGINING': ('BEGINNING', 12),
                'BALENCE': ('BALANCE', 12),
                'TRANSATION': ('TRANSACTION', 11),
                'DESCRITI0N': ('DESCRIPTION', 13),  # Using zeros instead of letter O - INCREASED
                'ВАLANCE': ('BALANCE', 18),  # Cyrillic characters mixed in (strong forgery indicator) - INCREASED
                'DAТЕ': ('DATE', 18),  # Cyrillic character instead of Latin - INCREASED
                'AM0UNT': ('AMOUNT', 13),  # Using zeros instead of letter O - INCREASED
                'STRAET': ('STREET', 11),
                'MICHEAL': ('MICHAEL', 10),
            }

            for error, (correct, weight) in field_errors.items():
                if error in all_text:
                    results['spelling_errors_found'].append({
                        'error': error,
                        'correct': correct,
                        'weight': weight
                    })
                    results['fraud_score'] += weight
                    # Log this as critical finding
                    self.findings['suspicious_indicators'].append(
                        f"🚨 FORGERY INDICATOR: Field name misspelling '{error}' (should be '{correct}')"
                    )

            # Check for mixed character sets (Latin vs Cyrillic) - strong forgery indicator
            if any(ord(c) > 1024 for c in all_text):  # Cyrillic range
                results['fraud_score'] += 25  # INCREASED from 15
                results['formatting_issues'].append("Mixed character sets detected (Cyrillic + Latin)")
                self.findings['suspicious_indicators'].append(
                    "🚨 CRITICAL: Mixed character encoding detected (potential copy-paste from non-English source)"
                )

            # Check for excessive spacing or alignment issues (editing artifacts)
            lines = all_text.split('\n')
            alignment_issues = 0
            for line in lines:
                if line.startswith('   ') or line.startswith('\t\t'):  # Excessive leading whitespace
                    alignment_issues += 1

            if alignment_issues > len(lines) * 0.2:  # More than 20% of lines have alignment issues
                results['fraud_score'] += 15  # INCREASED from 8
                results['formatting_issues'].append(f"Alignment issues in {alignment_issues} lines")

            # Normalize fraud score to 0-1 range - CHANGED DIVISOR from 50 to 30 for better sensitivity
            results['fraud_score'] = min(results['fraud_score'] / 30.0, 1.0)

        except Exception as e:
            logger.error(f"Error checking spelling and formatting: {e}")

        return results

    def check_transaction_behavior(self) -> Dict[str, any]:
        """Check for suspicious transaction patterns and behavioral fraud indicators."""
        results = {
            'suspicious_patterns': [],
            'fraud_score': 0.0,
            'risk_level': 'CLEAN'
        }

        try:
            all_text = ' '.join(self.text_content.values()).lower()

            # Define suspicious transaction patterns (higher weights = more suspicious)
            suspicious_keywords = {
                'wire transfer': 8,
                'international': 6,
                'offshore': 10,
                'crypto': 10,
                'bitcoin': 10,
                'western union': 8,
                'moneygram': 8,
                'cash advance': 6,
                'atm withdrawal': 2,
                'casino': 12,
                'gambling': 12,
                'poker': 10,
                'betting': 8,
                'coinbase': 10,
                'crypto.com': 10,
                'ripple': 8,
                'ethereum': 8,
                'dark web': 15,
                'tor': 12,
                'anonymous': 8,
                'shell company': 14,
                'money laundering': 18,
                'structured deposit': 12,
                'smurfing': 14
            }

            # Check for suspicious keywords
            keyword_score = 0
            found_keywords = []
            for keyword, weight in suspicious_keywords.items():
                count = all_text.count(keyword)
                if count > 0:
                    keyword_score += count * weight
                    found_keywords.append(f"{keyword} (x{count})")

            if found_keywords:
                results['suspicious_patterns'].append(f"Found {len(found_keywords)} suspicious transaction keywords: {', '.join(found_keywords[:5])}")

            # Check for rapid transaction patterns
            dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', all_text)
            if len(dates) > 50:  # Many transactions in short period (legitimate accounts can have 20-30)
                results['suspicious_patterns'].append(f"High transaction velocity: {len(dates)} transactions in statement period")
                keyword_score += 30

            # Check for multiple large withdrawals
            amounts = re.findall(r'\$?\s*(\d+[.,]\d{2})', all_text)
            large_amounts = [float(a.replace('$', '').replace(',', '')) for a in amounts if float(a.replace('$', '').replace(',', '')) > 5000]
            if len(large_amounts) >= 3:
                results['suspicious_patterns'].append(f"Multiple large transactions detected: {len(large_amounts)} transactions over $5,000")
                keyword_score += 40

            # Check for negative balance (overdraft)
            if '-$' in all_text or 'negative' in all_text.lower():
                negative_count = all_text.count('-$')
                if negative_count > 5:
                    results['suspicious_patterns'].append(f"Multiple withdrawals with possible overdraft conditions")
                    keyword_score += 25

            # Check for round amounts (exact $1000, $5000, etc - suspicious pattern)
            round_amounts = re.findall(r'\$\s*(\d{4,}\.00)', all_text)
            if len(round_amounts) >= 3:
                results['suspicious_patterns'].append(f"Detected {len(round_amounts)} round-number transactions (possible structuring)")
                keyword_score += 20

            # NOTE: Deposit-then-withdraw pattern is NORMAL banking behavior - removed to reduce false positives
            # Legitimate users often deposit paycheck then withdraw cash or make payments
            # This should only be flagged if combined with other HIGH-RISK indicators

            # Check for repeated identical transaction descriptions (copy-paste fraud)
            # Only flag this if there are MANY repetitions (5+ same phrases is abnormal)
            all_text_split = all_text.split()
            desc_phrases = []
            for i in range(len(all_text_split) - 2):
                phrase = ' '.join(all_text_split[i:i+3])
                if len(phrase) > 10:  # Only meaningful phrases
                    desc_phrases.append(phrase.lower())

            phrase_counts = {}
            for phrase in desc_phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

            # Only flag if same phrase appears 10+ times (legitimate banks repeat headers/footers)
            repeated_phrases = [p for p, c in phrase_counts.items() if c >= 10]
            if repeated_phrases:
                results['suspicious_patterns'].append(f"Detected {len(repeated_phrases)} highly repeated transaction descriptions (possible copy-paste fraud)")
                keyword_score += 18

            # Calculate fraud score (0-1 scale)
            # Normalize to 0-1 range
            # Using 45.0 as denominator to give proper weight to actual fraud keywords
            # This ensures: single high-risk keyword (crypto/casino: 10-12) = 0.22-0.27 fraud score
            # Multiple fraud keywords accumulate properly
            results['fraud_score'] = min(keyword_score / 45.0, 1.0)

            # Determine risk level
            if results['fraud_score'] >= 0.7:
                results['risk_level'] = 'HIGH FRAUD RISK'
            elif results['fraud_score'] >= 0.5:
                results['risk_level'] = 'MEDIUM FRAUD RISK'
            elif results['fraud_score'] >= 0.3:
                results['risk_level'] = 'LOW FRAUD RISK'
            else:
                results['risk_level'] = 'CLEAN'

            if results['suspicious_patterns']:
                logger.warning(f"Transaction behavior concerns detected: {results['risk_level']}")
                for pattern in results['suspicious_patterns']:
                    self.findings['suspicious_indicators'].append(f"[Behavioral] {pattern}")

        except Exception as e:
            logger.error(f"Error checking transaction behavior: {e}")

        return results

    def calculate_risk_score(self) -> float:
        """
        Calculate overall risk score (0.0 to 1.0).

        Returns:
            float: Risk score
        """
        score = 0.0
        rule_scores = {}

        # Run all checks
        metadata_results = self.check_metadata()
        structure_results = self.check_structure()
        content_results = self.check_content()
        financial_results = self.check_financial_consistency()
        behavior_results = self.check_transaction_behavior()
        spelling_results = self.check_spelling_and_formatting()
        missing_data_results = self.check_missing_data_and_dates()

        # Calculate score for metadata
        metadata_issues = sum(1 for v in metadata_results.values() if v)
        rule_scores['metadata'] = (metadata_issues / len(metadata_results)) * 0.05

        # Calculate score for structure
        structure_issues = sum(1 for v in structure_results.values() if v)
        rule_scores['structure'] = (structure_issues / len(structure_results)) * 0.08

        # Calculate score for content
        content_issues = sum(1 for v in content_results.values() if v)
        rule_scores['content'] = (content_issues / len(content_results)) * 0.12

        # Calculate score for financial
        financial_issues = sum(1 for v in financial_results.values() if v)
        rule_scores['financial'] = (financial_issues / len(financial_results)) * 0.10

        # Calculate score for behavioral fraud (HIGH PRIORITY)
        rule_scores['behavioral'] = behavior_results.get('fraud_score', 0.0) * 0.35

        # Calculate score for spelling/formatting (HIGH PRIORITY for forgery detection)
        # Spelling errors are STRONG indicators of forgery
        rule_scores['spelling'] = spelling_results.get('fraud_score', 0.0) * 0.25

        # Calculate score for missing data/invalid dates (HIGHEST PRIORITY for forgery detection)
        # Missing critical fields and impossible dates are definitive fraud indicators
        rule_scores['missing_data'] = missing_data_results.get('fraud_score', 0.0) * 0.35

        score = sum(rule_scores.values())

        # Determine verdict based on composite score
        if score >= 0.7:
            self.findings['verdict'] = 'HIGH RISK - FRAUD DETECTED'
        elif score >= 0.45:
            self.findings['verdict'] = 'MEDIUM RISK - SUSPICIOUS ACTIVITY'
        elif score >= 0.25:
            self.findings['verdict'] = 'LOW RISK - MINOR CONCERNS'
        else:
            self.findings['verdict'] = 'CLEAN'

        # Set is_suspicious flag
        self.findings['is_suspicious'] = score >= 0.25

        self.findings['risk_score'] = round(score, 3)

        return score

    def validate(self) -> Dict:
        """
        Run complete validation.

        Returns:
            dict: Validation results and findings
        """
        if not self.load_pdf():
            return self.findings

        self.extract_text()
        self.calculate_risk_score()

        logger.info(f"\n{'='*60}")
        logger.info("PDF VALIDATION REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"File: {self.pdf_path.name}")
        logger.info(f"Risk Score: {self.findings['risk_score']:.3f}")
        logger.info(f"Verdict: {self.findings['verdict']}")

        if self.findings['suspicious_indicators']:
            logger.info("\nSuspicious Indicators:")
            for indicator in self.findings['suspicious_indicators']:
                logger.info(f"  ✗ {indicator}")

        if self.findings['warnings']:
            logger.info("\nWarnings:")
            for warning in self.findings['warnings']:
                logger.info(f"  ⚠ {warning}")

        if not self.findings['suspicious_indicators'] and not self.findings['warnings']:
            logger.info("✓ No issues detected")

        return self.findings

    @staticmethod
    def _parse_pdf_date(date_string: str) -> datetime:
        """
        Parse PDF date format (D:YYYYMMDDHHmmSS).

        Args:
            date_string: PDF date string

        Returns:
            datetime: Parsed date
        """
        try:
            # Remove 'D:' prefix if present
            date_str = str(date_string).replace('D:', '')
            # Parse YYYYMMDDHHMMSS format
            if len(date_str) >= 14:
                return datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
            else:
                return datetime.now()
        except:
            return datetime.now()


def validate_statement_pdf(pdf_path: str) -> Dict:
    """
    Convenience function to validate a PDF statement.

    Args:
        pdf_path: Path to PDF file

    Returns:
        dict: Validation results
    """
    validator = PDFStatementValidator(pdf_path)
    return validator.validate()


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        results = validate_statement_pdf(pdf_file)
    else:
        print("Usage: python pdf_statement_validator.py <pdf_file>")
