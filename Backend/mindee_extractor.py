"""
Mindee-based document extraction for XFORIA DAD
Extracts structured information from bank statements, invoices, and other documents using Mindee SDK
"""

import logging
import os
import json
from typing import Dict, Optional
from pathlib import Path

import mindee
from mindee.parsing.common import Inference

logger = logging.getLogger(__name__)


class MindeeExtractor:
    """
    Extract structured information from documents using Mindee SDK.
    Uses Mindee SDK for reliable document processing with AI models.
    """

    def __init__(self, api_key: str, bank_statement_model_id: Optional[str] = None):
        """
        Initialize Mindee extractor.

        Args:
            api_key: Mindee API key
            bank_statement_model_id: Custom trained bank statement model ID
        """
        self.api_key = api_key
        self.bank_statement_model_id = bank_statement_model_id
        self.client = mindee.Client(api_key=api_key)

        # Initialize custom endpoint if model ID provided
        self.custom_bank_statement_endpoint = None
        if self.bank_statement_model_id:
            try:
                # Create endpoint for custom bank statement model
                # Format: account_name/endpoint_name
                parts = self.bank_statement_model_id.split('/')
                if len(parts) == 2:
                    account_name, endpoint_name = parts
                else:
                    # Assume it's just the endpoint name
                    account_name = 'mindee'
                    endpoint_name = self.bank_statement_model_id

                self.custom_bank_statement_endpoint = self.client.create_endpoint(
                    endpoint_name=endpoint_name,
                    account_name=account_name
                )
                logger.info(f"Custom bank statement endpoint created: {account_name}/{endpoint_name}")
            except Exception as e:
                logger.warning(f"Could not create custom endpoint: {e}. Will use fallback.")
                self.custom_bank_statement_endpoint = None

        logger.info("Mindee extractor initialized successfully")
        if self.bank_statement_model_id:
            logger.info(f"Custom bank statement model configured: {self.bank_statement_model_id}")

    def extract_bank_statement(self, file_path: str) -> Dict:
        """
        Extract bank statement information using Mindee.

        Args:
            file_path: Path to the document (PDF, JPG, PNG)

        Returns:
            Dictionary with extracted bank statement details
        """
        try:
            logger.info(f"Extracting bank statement from: {file_path}")

            # Try custom model if available
            if self.custom_bank_statement_endpoint:
                try:
                    input_source = mindee.Client.source_from_path(file_path)
                    result = self.client.enqueue_and_parse(
                        mindee.parsing.common.Inference,
                        input_source,
                        endpoint=self.custom_bank_statement_endpoint
                    )
                    logger.info("Successfully extracted using custom bank statement model")
                    extracted_data = self._process_result(result)
                except Exception as e:
                    logger.warning(f"Custom model failed: {e}, trying fallback")
                    extracted_data = self._extract_with_financial_api(file_path)
            else:
                # Use standard Financial Document API
                logger.info("Using Mindee Financial Document API")
                extracted_data = self._extract_with_financial_api(file_path)

            return {
                'success': True,
                'data': extracted_data,
                'extraction_method': 'mindee_financial_api'
            }

        except Exception as e:
            logger.error(f"Mindee bank statement extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_method': 'mindee_financial_api'
            }

    def extract_invoice(self, file_path: str) -> Dict:
        """
        Extract invoice information using Mindee Invoice API.

        Args:
            file_path: Path to the invoice document

        Returns:
            Dictionary with extracted invoice details
        """
        try:
            logger.info(f"Extracting invoice from: {file_path}")

            input_source = mindee.Client.source_from_path(file_path)
            result = self.client.parse(
                mindee.product.InvoiceV4,
                input_source
            )

            extracted_data = self._process_result(result)

            return {
                'success': True,
                'data': extracted_data,
                'extraction_method': 'mindee_invoice_api'
            }

        except Exception as e:
            logger.error(f"Mindee invoice extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_method': 'mindee_invoice_api'
            }

    def extract_receipt(self, file_path: str) -> Dict:
        """
        Extract receipt information using Mindee Receipt API.

        Args:
            file_path: Path to the receipt document

        Returns:
            Dictionary with extracted receipt details
        """
        try:
            logger.info(f"Extracting receipt from: {file_path}")

            input_source = mindee.Client.source_from_path(file_path)
            result = self.client.parse(
                mindee.product.ReceiptV5,
                input_source
            )

            extracted_data = self._process_result(result)

            return {
                'success': True,
                'data': extracted_data,
                'extraction_method': 'mindee_receipt_api'
            }

        except Exception as e:
            logger.error(f"Mindee receipt extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_method': 'mindee_receipt_api'
            }

    def extract_raw_text(self, file_path: str) -> Dict:
        """
        Extract raw text from document using Mindee.

        Args:
            file_path: Path to the document

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            logger.info(f"Extracting raw text from: {file_path}")

            # Use Financial Document API which includes text extraction
            extracted_data = self._extract_with_financial_api(file_path, include_words=True)
            full_text = self._extract_full_text(extracted_data)

            return {
                'success': True,
                'raw_text': full_text,
                'extraction_method': 'mindee_text_extraction'
            }

        except Exception as e:
            logger.error(f"Mindee text extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_method': 'mindee_text_extraction'
            }

    def _extract_with_financial_api(self, file_path: str, include_words: bool = False) -> Dict:
        """
        Extract using Mindee Financial Document API.

        Args:
            file_path: Path to document
            include_words: Whether to include full text

        Returns:
            Extracted data dictionary
        """
        try:
            input_source = mindee.Client.source_from_path(file_path)
            result = self.client.parse(
                mindee.product.FinancialDocumentV1,
                input_source,
                include_words=include_words
            )
            logger.info("Successfully extracted using Financial Document API")
            return self._process_result(result)
        except Exception as e:
            logger.error(f"Financial API extraction failed: {e}")
            # Fallback to text extraction
            return self._extract_text_from_file(file_path)

    def _process_result(self, result) -> Dict:
        """
        Process Mindee API result into standardized format.

        Args:
            result: Mindee API result object

        Returns:
            Standardized dictionary
        """
        try:
            # Convert result to dictionary
            return {
                'raw_response': str(result),
                'status': 'success' if hasattr(result, 'document') else 'partial',
                'document': result.document if hasattr(result, 'document') else None
            }
        except Exception as e:
            logger.warning(f"Could not process result: {e}")
            return {'raw_response': str(result)}

    def _extract_text_from_file(self, file_path: str) -> Dict:
        """
        Extract text and structured data from file using pdfplumber for PDFs.
        Fallback method when Mindee API fails or is unreachable.

        Args:
            file_path: Path to document file

        Returns:
            Dictionary with extracted data
        """
        data = {
            'raw_text': '',
            'account_holder': None,
            'account_number': None,
            'iban': None,
            'swift_code': None,
            'invoice_number': None,
            'invoice_date': None,
            'total_amount': None,
        }

        try:
            # Check file type
            if file_path.lower().endswith('.pdf'):
                data['raw_text'] = self._extract_pdf_text(file_path)
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                data['raw_text'] = self._extract_image_text(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                data['raw_text'] = ""

            logger.info(f"Extracted {len(data['raw_text'])} characters from {file_path}")

        except Exception as e:
            logger.warning(f"Error extracting text: {e}")

        return data

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    text += "\n"
            return text
        except ImportError:
            logger.warning("pdfplumber not installed, trying PyPDF2")
            try:
                from PyPDF2 import PdfReader
                text = ""
                with open(pdf_path, 'rb') as f:
                    reader = PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ""
                        text += "\n"
                return text
            except ImportError:
                logger.error("No PDF extraction library available")
                return ""

    def _extract_image_text(self, image_path: str) -> str:
        """
        Extract text from image file using OCR.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text
        """
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text
        except ImportError:
            logger.warning("pytesseract not installed")
            return ""

    def _extract_full_text(self, data: Dict) -> str:
        """
        Extract full text from Mindee response data.

        Args:
            data: Dictionary with extracted data

        Returns:
            Full text string
        """
        try:
            # If raw_text exists, return it
            if isinstance(data, dict) and 'raw_text' in data:
                return data['raw_text']

            # Otherwise return JSON representation
            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Error extracting full text: {e}")
            return json.dumps(data, indent=2, default=str)
