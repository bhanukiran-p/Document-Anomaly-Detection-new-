"""
Money Order Extractor using Google Vision API + ML Fraud Detection + AI Analysis
Extracts key information from money order documents and provides fraud risk assessment
"""

import os
import sys
import io
import re
from typing import Dict, Optional
from datetime import datetime
from google.cloud import vision
from google.oauth2 import service_account

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import centralized config and logging
from config import Config
logger = Config.get_logger(__name__)

# Import ML models and AI agent
try:
    from .ml.money_order_fraud_detector import MoneyOrderFraudDetector
    from .ai.fraud_analysis_agent import FraudAnalysisAgent
    from .ai.tools import DataAccessTools
    from .ai.result_storage import save_analysis_result
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML models or AI agent not available: {e}")
    ML_AVAILABLE = False

# Import normalization module (local to money_order)
try:
    from .normalization import MoneyOrderNormalizerFactory
    NORMALIZATION_AVAILABLE = True
except ImportError as e:
    # Fallback to global normalization if local not available
    try:
        from normalization import NormalizerFactory as MoneyOrderNormalizerFactory
        NORMALIZATION_AVAILABLE = True
    except ImportError:
        print(f"Warning: Normalization module not available: {e}")
        NORMALIZATION_AVAILABLE = False


class MoneyOrderExtractor:
    """
    Extract information from money order documents using Google Vision API
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Vision API client, ML fraud detector, and AI analysis agent

        Args:
            credentials_path: Path to Google Cloud service account JSON file
        """
        # Set up Google Vision API credentials
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            self.client = vision.ImageAnnotatorClient()
        else:
            self.client = vision.ImageAnnotatorClient()

        # Initialize ML fraud detector and AI agent
        if ML_AVAILABLE:
            # Initialize ML fraud detector (self-contained, no model_dir needed)
            self.fraud_detector = MoneyOrderFraudDetector()

            # Initialize data access tools for LangChain agent
            ml_scores_path = os.getenv('ML_SCORES_CSV', 'money_order/mock_data/ml_scores.csv')
            customer_history_path = os.getenv('CUSTOMER_HISTORY_CSV', 'money_order/mock_data/customer_history.csv')
            fraud_cases_path = os.getenv('FRAUD_CASES_CSV', 'money_order/mock_data/fraud_cases.csv')

            self.data_tools = DataAccessTools(
                ml_scores_path=ml_scores_path,
                customer_history_path=customer_history_path,
                fraud_cases_path=fraud_cases_path
            )

            # Initialize AI fraud analysis agent
            openai_key = os.getenv('OPENAI_API_KEY')
            self.ai_agent = FraudAnalysisAgent(
                api_key=openai_key,
                model=os.getenv('AI_MODEL', 'o4-mini'),
                data_tools=self.data_tools
            )

            print("ML fraud detector and AI analysis agent initialized successfully")
        else:
            self.fraud_detector = None
            self.ai_agent = None
            self.data_tools = None
            print("ML and AI components not available - using basic extraction only")

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

        # Extract money order fields (OCR - issuer-specific)
        extracted_data = {
            'issuer': self._extract_issuer(text),
            'serial_number': self._extract_serial_number(text),
            'serial_secondary': self._extract_secondary_serial(text),
            'amount': self._extract_amount(text),
            'amount_in_words': self._extract_amount_in_words(text),
            'payee': self._extract_payee(text),
            'purchaser': self._extract_purchaser(text),
            'sender_address': self._extract_sender_address(text),
            'date': self._extract_date(text),
            'location': self._extract_location(text),
            'signature': self._extract_signature(text),
        }

        # Normalize data to standardized schema
        normalized_data = None
        if NORMALIZATION_AVAILABLE and extracted_data.get('issuer'):
            normalizer = MoneyOrderNormalizerFactory.get_normalizer(extracted_data['issuer'])
            if normalizer:
                normalized_data = normalizer.normalize(extracted_data)
                print(f"Data normalized using {normalizer}")
            else:
                print(f"No normalizer found for issuer: {extracted_data['issuer']}")
                # Fall back to raw extracted_data for unsupported issuers

        # Use normalized data for ML if available, otherwise use raw extracted_data
        data_for_ml = normalized_data.to_dict() if normalized_data else extracted_data

        # Perform anomaly detection with ML and AI
        anomalies, ml_analysis, ai_analysis = self._detect_anomalies(data_for_ml, text)

        # Calculate confidence score (OCR extraction confidence)
        confidence = self._calculate_confidence(extracted_data)

        # Build complete response with all analysis data
        response = {
            'status': 'success',
            'extracted_data': extracted_data,      # Raw OCR extraction (issuer-specific)
            'anomalies': anomalies,
            'confidence_score': confidence,
            'raw_text': text,
            'timestamp': datetime.now().isoformat()
        }

        # Add normalized data if available
        if normalized_data:
            response['normalized_data'] = normalized_data.to_dict()  # Standardized schema
            response['normalization_completeness'] = normalized_data.get_completeness_score()

        # Add ML analysis if available
        if ml_analysis:
            response['ml_analysis'] = ml_analysis

        # Add AI analysis if available
        if ai_analysis:
            response['ai_analysis'] = ai_analysis

        # Save complete analysis to JSON file (if ML/AI available)
        analysis_id = None
        if ML_AVAILABLE and (ml_analysis or ai_analysis):
            try:
                serial_number = extracted_data.get('serial_number', 'unknown')
                # Use relative path for analysis results
                storage_dir = os.path.join(os.path.dirname(__file__), 'analysis_results')
                analysis_id = save_analysis_result(
                    response,
                    serial_number=serial_number,
                    storage_dir=storage_dir
                )
                if analysis_id:
                    response['analysis_id'] = analysis_id
                    print(f"✅ Complete analysis saved with ID: {analysis_id}")
            except Exception as e:
                print(f"⚠️  Error saving analysis result: {e}")

        return response

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
            r'SERIAL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})',
            r'CONTROL\s*(?:NO|NUMBER|#)?[:\s]*([A-Z0-9\-]{8,20})',
            r'(?:NO|NUMBER|#)?[:\s]*([A-Z0-9]{10,15})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_secondary_serial(self, text: str) -> Optional[str]:
        """Extract secondary serial number (often at bottom left)"""
        # Look for long numeric strings that are NOT the primary serial
        # This is a heuristic: usually 10-12 digits at the bottom
        lines = text.split('\n')
        
        # Check bottom 3 lines
        for line in lines[-3:]:
            # Look for 10+ digit number
            match = re.search(r'\b(\d{10,12})\b', line)
            if match:
                return match.group(1)
                
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
        patterns = [
            r'([A-Z][A-Za-z\s]+(?:HUNDRED|THOUSAND|MILLION)\s+[A-Za-z\s]+AND\s+\d{1,2}/\d{2,3}\s+DOLLARS)',
            r'([A-Z][A-Z\s]+AND\s+\d{1,2}/\d{2,3}\s+DOLLARS)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                written_amount = match.group(1).strip()
                # Clean up extra spaces
                written_amount = ' '.join(written_amount.split())
                return written_amount

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

    def _extract_sender_address(self, text: str) -> Optional[str]:
        """Extract sender address (often below purchaser name)"""
        # Look for address-like patterns (Number Street, City, State Zip)
        # This is tricky without NER, but we can look for lines containing Zip codes
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Check if line looks like an address line (contains 5 digit zip)
            if re.search(r'\b\d{5}\b', line) and re.search(r'[A-Z]{2}', line):
                # If we found a city/state/zip line, the street address is likely the line before
                if i > 0:
                    street_line = lines[i-1]
                    # Simple heuristic: starts with number
                    if re.match(r'^\d+', street_line.strip()):
                        return f"{street_line.strip()}, {line.strip()}"
                return line.strip()
                
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract transaction date"""
        patterns = [
            r'DATE[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            # Add full month name formats
            r'DATE[:\s]*((?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2},?\s+\d{4})',
            r'((?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2},?\s+\d{4})',
            # Keep abbreviated month names
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                # Normalize month names to standard format for consistency
                date_str = self._normalize_date_format(date_str)
                return date_str

        return None

    def _normalize_date_format(self, date_str: str) -> str:
        """Normalize date string to MM/DD/YYYY format"""
        if not date_str:
            return date_str
        
        # Month name mapping
        month_map = {
            'JANUARY': '01', 'FEBRUARY': '02', 'MARCH': '03', 'APRIL': '04',
            'MAY': '05', 'JUNE': '06', 'JULY': '07', 'AUGUST': '08',
            'SEPTEMBER': '09', 'OCTOBER': '10', 'NOVEMBER': '11', 'DECEMBER': '12',
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        # Try to parse month name format
        for month_name, month_num in month_map.items():
            pattern = rf'({month_name})\s+(\d{{1,2}}),?\s+(\d{{4}})'
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                day = match.group(2).zfill(2)
                year = match.group(3)
                return f'{month_num}/{day}/{year}'
        
        # If already in numeric format, return as is
        return date_str

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

    def _detect_anomalies(self, data: Dict, text: str) -> tuple:
        """
        Detect potential anomalies or fraud indicators using ML models and AI analysis

        Returns:
            Tuple of (anomalies list, ml_analysis dict, ai_analysis dict)
        """
        if not ML_AVAILABLE or not self.fraud_detector or not self.ai_agent:
            # Fallback to empty anomalies if ML not available
            return ([], None, None)

        # Run ML fraud detection
        ml_analysis = self.fraud_detector.predict_fraud(data, text)

        # Look up customer by name and address to get fraud history context for AI analysis
        customer_id = None
        is_repeat_customer = False
        customer_fraud_history = None
        try:
            from database.supabase_client import get_supabase
            import logging

            supabase = get_supabase()
            logger = logging.getLogger(__name__)

            # Check both normalized field name (sender_name) and raw field name (purchaser)
            purchaser_name = data.get('sender_name') or data.get('purchaser')

            if purchaser_name:
                # Query for existing customer records by name (payer-based fraud tracking)
                # Fetch ALL records to get MAX escalate_count from all previous uploads
                # NOTE: Query by NAME ONLY, not by address - we track by payer name, payee doesn't matter
                query = supabase.table('money_order_customers').select('*').eq('name', purchaser_name).order('escalate_count', desc=True)

                response = query.execute()

                if response.data:
                    # Customer has previous records - this is a repeat customer
                    # Get the record with HIGHEST escalate_count to check if payer was escalated before
                    customer_record_with_max_escalate = response.data[0]
                    customer_record = response.data[0]  # For other fields, use latest

                    # But also get the latest record by creation date for customer_id consistency
                    latest_query = supabase.table('money_order_customers').select('customer_id').eq('name', purchaser_name).order('created_at', desc=True).limit(1)
                    latest_response = latest_query.execute()
                    if latest_response.data:
                        customer_id = latest_response.data[0].get('customer_id')
                    else:
                        customer_id = customer_record_with_max_escalate.get('customer_id')

                    is_repeat_customer = True
                    logger.info(f"[CUSTOMER_LOOKUP] Found existing customer records: {purchaser_name} ({customer_id})")
                    # Get fraud history from record with HIGHEST escalate_count for AI analysis
                    # Use the max escalate_count across all uploads by this payer
                    customer_fraud_history = {
                        'has_fraud_history': customer_record_with_max_escalate.get('has_fraud_history', False),
                        'fraud_count': customer_record_with_max_escalate.get('fraud_count', 0),
                        'escalate_count': customer_record_with_max_escalate.get('escalate_count', 0),
                        'last_recommendation': customer_record_with_max_escalate.get('last_recommendation'),
                        'last_analysis_date': customer_record_with_max_escalate.get('last_analysis_date')
                    }
                    logger.info(f"[CUSTOMER_LOOKUP] Using fraud history from record with escalate_count={customer_fraud_history.get('escalate_count')}")
                else:
                    # Customer doesn't have any records yet - will be created in storage layer
                    logger.info(f"[CUSTOMER_LOOKUP] No customer records found, will be created during storage: {purchaser_name}")
                    is_repeat_customer = False

        except Exception as e:
            # If database lookup fails, treat as new customer
            import logging
            logging.warning(f"[CUSTOMER_LOOKUP] Error in customer lookup: {e}")
            is_repeat_customer = False

        # Pass customer info to AI analysis
        # CRITICAL: Add raw_text to data so AI can detect spelling errors in amount field
        data_with_raw_text = {**data, 'raw_text': text}
        ai_analysis = self.ai_agent.analyze_fraud(ml_analysis, data_with_raw_text, customer_id, is_repeat_customer, customer_fraud_history)

        # Convert ML fraud indicators into anomalies format for frontend
        anomalies = self._convert_to_anomalies(ml_analysis, ai_analysis)

        return (anomalies, ml_analysis, ai_analysis)

    def _convert_to_anomalies(self, ml_analysis: Dict, ai_analysis: Dict) -> list:
        """
        Convert ML and AI analysis into anomalies format for frontend display

        Returns:
            List of anomaly dictionaries with severity, type, and message
        """
        anomalies = []

        # Determine overall severity based on ML risk level
        risk_level = ml_analysis.get('risk_level', 'LOW')
        fraud_score = ml_analysis.get('fraud_risk_score', 0)

        # Map risk level to severity
        severity_map = {
            'LOW': 'low',
            'MEDIUM': 'medium',
            'HIGH': 'high',
            'CRITICAL': 'critical'
        }
        base_severity = severity_map.get(risk_level, 'medium')

        # Add ML-identified fraud indicators as anomalies
        for indicator in ml_analysis.get('feature_importance', []):
            # Determine severity based on the indicator content
            if any(keyword in indicator.lower() for keyword in ['invalid', 'mismatch', 'future', 'missing']):
                severity = 'high' if fraud_score > 0.6 else 'medium'
            else:
                severity = 'medium' if fraud_score > 0.4 else 'low'

            anomalies.append({
                'severity': severity,
                'type': 'ml_indicator',
                'message': indicator
            })

        # Add AI-identified key indicators
        if ai_analysis:
            for indicator in ai_analysis.get('key_indicators', []):
                # AI indicators are usually more specific and actionable
                anomalies.append({
                    'severity': base_severity,
                    'type': 'ai_indicator',
                    'message': indicator
                })

        # Add overall fraud risk summary as top anomaly
        if fraud_score > 0.3:  # Only show if moderate risk or higher
            recommendation = ai_analysis.get('recommendation', 'ESCALATE') if ai_analysis else 'ESCALATE'
            summary = ai_analysis.get('summary', f'Fraud risk: {fraud_score:.1%}') if ai_analysis else f'Fraud risk: {fraud_score:.1%}'

            anomalies.insert(0, {
                'severity': base_severity,
                'type': f'fraud_risk_{risk_level.lower()}',
                'message': f'[{recommendation}] {summary}'
            })

        return anomalies

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
        }

        score = 0
        for field, weight in weights.items():
            if data.get(field):
                score += weight

        return round(score, 2)

