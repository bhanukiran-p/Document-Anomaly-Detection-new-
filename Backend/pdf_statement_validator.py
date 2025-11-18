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

import hashlib
import re
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

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

    def __init__(self, pdf_path: str):
        """
        Initialize validator with PDF file.

        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.pdf_reader = None
        self.num_pages = 0
        self.metadata = None
        self.text_content = {}
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
        # Try PyMuPDF first (best for both text and image-based PDFs)
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

        # Try pdfplumber
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

        # Try PyPDF2
        if hasattr(self, 'pdf_reader') and self.pdf_reader:
            try:
                for page_num, page in enumerate(self.pdf_reader.pages):
                    text = page.extract_text()
                    self.text_content[page_num] = text if text else ""
                logger.info(f"Text extracted from {len(self.text_content)} pages using PyPDF2")
                return self.text_content
            except Exception as e:
                logger.warning(f"PyPDF2 text extraction failed: {e}")

        # Fallback: Extract text from raw PDF content
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

            return self.text_content
        except Exception as e:
            logger.warning(f"Fallback text extraction failed: {e}")
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

        # Calculate score for behavioral fraud (HIGHEST PRIORITY)
        # Behavioral fraud score gets 50% weight since it's the most reliable indicator
        rule_scores['behavioral'] = behavior_results.get('fraud_score', 0.0) * 0.50

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
