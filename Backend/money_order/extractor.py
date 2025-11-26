"""
Money Order extraction using Mindee API with ML Fraud Detection, Normalization, and AI Analysis
"""
import os
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from mindee import ClientV2, InferenceParameters, PathInput
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

logger = logging.getLogger(__name__)


def convert_to_json_serializable(obj: Any) -> Any:
    """
    Recursively convert NumPy types and other non-JSON-serializable types to native Python types
    
    Args:
        obj: Object to convert (can be dict, list, or primitive type)
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, (np.integer, np.int_)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_json_serializable(item) for item in obj)
    else:
        return obj

# Import ML models and AI agent
try:
    from ml_models.fraud_detector import MoneyOrderFraudDetector
    ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML fraud detector not available: {e}")
    ML_AVAILABLE = False
    MoneyOrderFraudDetector = None

# Import normalization module
try:
    from normalization import NormalizerFactory
    NORMALIZATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Normalization module not available: {e}")
    NORMALIZATION_AVAILABLE = False
    NormalizerFactory = None

# Import AI analysis agent
try:
    from langchain_agent.fraud_analysis_agent import FraudAnalysisAgent
    from langchain_agent.tools import DataAccessTools
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI fraud analysis agent not available: {e}")
    AI_AVAILABLE = False
    FraudAnalysisAgent = None
    DataAccessTools = None

# Load configuration from environment
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_MONEY_ORDER = os.getenv("MINDEE_MODEL_ID_MONEY_ORDER", "7ecd4b47-c7a0-430c-ac68-a68b04960a39").strip()

# Initialize Mindee client lazily to avoid import-time errors
mindee_client = None

def get_mindee_client():
    """Get or create Mindee client"""
    global mindee_client
    if mindee_client is None:
        if not MINDEE_API_KEY:
            raise RuntimeError("MINDEE_API_KEY is not set in environment variables")
        mindee_client = ClientV2(MINDEE_API_KEY)
    return mindee_client


def _run_model(file_path: str, model_id: str) -> Dict[str, Any]:
    """Run Mindee model inference on a document"""
    try:
        client = get_mindee_client()
        params = InferenceParameters(model_id=model_id, raw_text=True)
        input_source = PathInput(file_path)
        response = client.enqueue_and_get_inference(input_source, params)
        
        if not response or not hasattr(response, 'inference'):
            raise ValueError("Invalid response from Mindee API: missing inference object")
        
        if not response.inference or not hasattr(response.inference, 'result'):
            raise ValueError("Invalid response from Mindee API: missing result object")
            
        result = response.inference.result
        if not result:
            raise ValueError("Invalid response from Mindee API: result is None")
            
        fields = result.fields or {}

        logger.info(f"=== MINDEE RAW RESPONSE DEBUG ===")
        logger.info(f"Available field names: {list(fields.keys())}")

        simple_fields: Dict[str, Any] = {}
        for name, field in fields.items():
            if hasattr(field, "value"):
                simple_fields[name] = field.value
                logger.info(f"  {name}: {field.value}")
            elif hasattr(field, "items"):
                values = []
                for item in field.items:
                    if hasattr(item, "value"):
                        values.append(item.value)
                    elif hasattr(item, "fields"):
                        values.append({k: v.value for k, v in item.fields.items()})
                simple_fields[name] = values
                logger.info(f"  {name} (list): {values}")
            elif hasattr(field, "fields"):
                simple_fields[name] = {k: v.value for k, v in field.fields.items()}
                logger.info(f"  {name} (dict): {simple_fields[name]}")

        logger.info(f"=== END DEBUG ===")
        logger.info(f"Extracted fields summary: {simple_fields}")

        raw_text = getattr(result, "raw_text", "") or ""
        # Convert RawText object to string if it's not already a string
        if raw_text and not isinstance(raw_text, str):
            raw_text = str(raw_text)
        return {"fields": simple_fields, "raw_text": raw_text}
    except Exception as e:
        logger.error(f"Mindee API error: {e}", exc_info=True)
        raise RuntimeError(f"Failed to process document with Mindee API: {str(e)}")


def _extract_from_raw_text(raw_text: str, field_name: str) -> Optional[str]:
    """
    Fallback extraction from raw text using regex patterns for money order fields
    
    Args:
        raw_text: Raw OCR text from the document
        field_name: Name of the field to extract
        
    Returns:
        Extracted value or None
    """
    if not raw_text:
        return None
    
    patterns = {
        'issuer': [
            r'western\s+union',
            r'moneygram',
            r'usps|u\.s\.\s+postal\s+service|united\s+states\s+postal\s+service',
            r'american\s+express',
            r'postal\s+service',
            r'walmart\s+money\s+order|walmart',
            r'kroger\s+money\s+order|kroger',
            r'7-eleven|7eleven|seven\s+eleven',
            r'cvs\s+pharmacy|cvs',
            r'walgreens',
            r'rite\s+aid',
            r'giant\s+eagle',
            r'publix',
            r'safeway',
            r'k\s+mart|kmart',
        ],
        'date': [
            r'date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'issue\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'purchase\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'issued[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Generic date pattern
        ],
        'location': [
            r'location[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'purchased\s+at[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'issued\s+at[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'agent\s+location[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'agent[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
            r'store[:\s]+([A-Z][A-Za-z0-9\s,\.]+)',
        ],
        'amount_in_words': [
            r'amount\s+in\s+words[:\s]+([A-Z][A-Za-z\s-]+)',
            r'pay\s+the\s+sum\s+of[:\s]+([A-Z][A-Za-z\s-]+)',
            r'([A-Z][A-Za-z\s-]+\s+dollars?\s+and\s+[A-Z][A-Za-z\s-]+\s+cents?)',
            r'([A-Z][A-Za-z\s-]+\s+dollars?)',
            r'([A-Z\s-]+DOLLARS?\s*(?:AND\s+[A-Z0-9/ ]+)?)(?:\n|$)',
        ],
        'receipt_number': [
            r'receipt\s+number[:\s]+([A-Z0-9-]+)',
            r'receipt\s+no[:\s]+([A-Z0-9-]+)',
            r'receipt[:\s]+([A-Z0-9-]+)',
        ],
        'signature': [
            r'signature[:\s]+([A-Z][A-Za-z\s]+)',
            r'signed[:\s]+([A-Z][A-Za-z\s]+)',
            r'purchaser\s+signature[:\s]+([A-Z][A-Za-z\s]+)',
        ],
    }
    
    if field_name not in patterns:
        return None
    
    # Special handling for issuer (case-insensitive brand name matching)
    if field_name == 'issuer':
        text_lower = raw_text.lower()
        for pattern in patterns[field_name]:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Capitalize the issuer name properly
                issuer_name = match.group(0).strip()
                # Format common issuers
                if 'western union' in issuer_name:
                    return 'Western Union'
                elif 'moneygram' in issuer_name:
                    return 'MoneyGram'
                elif 'usps' in issuer_name or 'u.s. postal service' in issuer_name or 'postal service' in issuer_name:
                    return 'USPS'
                elif 'american express' in issuer_name:
                    return 'American Express'
                elif 'walmart' in issuer_name:
                    return 'Walmart'
                elif 'kroger' in issuer_name:
                    return 'Kroger'
                elif '7-eleven' in issuer_name or '7eleven' in issuer_name:
                    return '7-Eleven'
                elif 'cvs' in issuer_name:
                    return 'CVS'
                elif 'walgreens' in issuer_name:
                    return 'Walgreens'
                elif 'rite aid' in issuer_name:
                    return 'Rite Aid'
                elif 'giant eagle' in issuer_name:
                    return 'Giant Eagle'
                elif 'publix' in issuer_name:
                    return 'Publix'
                elif 'safeway' in issuer_name:
                    return 'Safeway'
                elif 'k mart' in issuer_name or 'kmart' in issuer_name:
                    return 'Kmart'
                return issuer_name.title()
        return None
    
    # For other fields, use standard pattern matching
    for pattern in patterns[field_name]:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip() if match.lastindex else match.group(0).strip()
            logger.info(f"Extracted {field_name} from raw text: {value}")
            return value
    
    return None


def extract_money_order(file_path: str) -> Dict[str, Any]:
    """
    Extract money order data using Mindee API with ML Fraud Detection, Normalization, and AI Analysis

    Args:
        file_path: Path to the money order image/PDF file

    Returns:
        Dictionary containing extracted money order data with ML and AI analysis
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        out = _run_model(file_path, MINDEE_MODEL_ID_MONEY_ORDER)
        fields = out.get("fields", {})
        raw_text = out.get("raw_text", "")
    except Exception as e:
        logger.error(f"Money order extraction error: {e}", exc_info=True)
        raise
    
    # Extract fields with fallback to raw text extraction
    issuer = fields.get("issuer")
    if not issuer:
        issuer = _extract_from_raw_text(raw_text, "issuer")
    
    date = fields.get("issue_date") or fields.get("date")
    if not date:
        date = _extract_from_raw_text(raw_text, "date")
    
    location = fields.get("location") or fields.get("address")
    if not location:
        location = _extract_from_raw_text(raw_text, "location")
        # If location extraction failed, try to construct from city/state
        if not location:
            city = fields.get("city")
            state = fields.get("state")
            if city or state:
                location = ", ".join(filter(None, [city, state]))
    
    amount_in_words = fields.get("amount_in_words") or fields.get("word_amount")
    if not amount_in_words:
        amount_in_words = _extract_from_raw_text(raw_text, "amount_in_words")
    
    receipt_number = fields.get("receipt_number")
    if not receipt_number:
        receipt_number = _extract_from_raw_text(raw_text, "receipt_number")
    
    signature = fields.get("signature")
    if not signature:
        signature = _extract_from_raw_text(raw_text, "signature")
    if not signature and raw_text:
        if re.search(r'(authorized\s+signature|signature)', raw_text, re.IGNORECASE):
            signature = "PRESENT"
    
    # Format amount as currency string
    amount_value = fields.get("amount")
    amount_numeric = None
    if amount_value:
        if isinstance(amount_value, (int, float)):
            amount_numeric = float(amount_value)
        elif isinstance(amount_value, str):
            # Extract numeric value from string
            amount_str = re.sub(r'[^\d.]', '', amount_value)
            if amount_str:
                try:
                    amount_numeric = float(amount_str)
                except ValueError:
                    pass
        amount_formatted = f"${amount_numeric:,.2f}" if amount_numeric else str(amount_value)
    else:
        amount_formatted = None
    
    extracted = {
        "issuer": issuer or "",
        # Mindee uses 'payer' instead of 'purchaser'
        "purchaser": fields.get("payer") or fields.get("purchaser"),
        "payee": fields.get("payee"),
        "amount": amount_formatted,
        "amount_numeric": amount_numeric,  # Keep numeric value for ML
        "date": date,
        # Mindee uses 'money_order_number' instead of 'serial_number'
        "serial_number": fields.get("money_order_number") or fields.get("serial_number"),
        "location": location,
        "amount_in_words": amount_in_words,
        "receipt_number": receipt_number,
        "signature": signature,
        # Additional Mindee fields
        "money_order_number": fields.get("money_order_number"),
        "address": fields.get("address"),
        "city": fields.get("city"),
        "state": fields.get("state"),
        "zip_code": fields.get("zip_code"),
        "raw_ocr_text": raw_text,
    }
    
    # Normalize data to standardized schema
    normalized_data = None
    if NORMALIZATION_AVAILABLE and extracted.get('issuer'):
        try:
            normalizer = NormalizerFactory.get_normalizer(extracted['issuer'])
            if normalizer:
                normalized_data = normalizer.normalize(extracted)
                logger.info(f"Data normalized using {normalizer.__class__.__name__}")
        except Exception as e:
            logger.warning(f"Normalization failed: {e}")
    
    # Perform ML fraud detection
    ml_analysis = None
    if ML_AVAILABLE and MoneyOrderFraudDetector:
        try:
            logger.info("Starting ML fraud detection...")
            model_dir = os.getenv('ML_MODEL_DIR', 'ml_models')
            fraud_detector = MoneyOrderFraudDetector(model_dir=model_dir)
            logger.info(f"Fraud detector initialized, models loaded: {fraud_detector.models_loaded}")
            
            # Ensure extracted data has required fields for ML
            if not extracted or not isinstance(extracted, dict):
                logger.warning("Extracted data is empty or invalid for ML analysis")
                ml_analysis = {
                    "fraud_risk_score": 0.0,
                    "risk_level": "UNKNOWN",
                    "model_confidence": 0.0,
                    "error": "Invalid extracted data"
                }
            else:
                ml_analysis = fraud_detector.predict_fraud(extracted, raw_text)
                logger.info(f"ML fraud detection completed: risk_score={ml_analysis.get('fraud_risk_score', 'N/A')}, risk_level={ml_analysis.get('risk_level', 'N/A')}")
                if ml_analysis:
                    logger.info(f"ML analysis keys: {list(ml_analysis.keys())}")
        except Exception as e:
            logger.error(f"ML fraud detection failed: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            ml_analysis = {
                "error": str(e),
                "fraud_risk_score": 0.0,
                "risk_level": "UNKNOWN",
                "model_confidence": 0.0
            }
    else:
        logger.warning(f"ML fraud detection not available - ML_AVAILABLE: {ML_AVAILABLE}, MoneyOrderFraudDetector: {MoneyOrderFraudDetector}")
        ml_analysis = {
            "fraud_risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "model_confidence": 0.0,
            "error": "ML detection not available"
        }
    
    # Perform AI fraud analysis
    ai_analysis = None
    if AI_AVAILABLE and FraudAnalysisAgent and DataAccessTools:
        try:
            # Initialize data access tools for LangChain agent
            ml_scores_path = os.getenv('ML_SCORES_CSV', 'ml_models/mock_data/ml_scores.csv')
            customer_history_path = os.getenv('CUSTOMER_HISTORY_CSV', 'ml_models/mock_data/customer_history.csv')
            fraud_cases_path = os.getenv('FRAUD_CASES_CSV', 'ml_models/mock_data/fraud_cases.csv')
            
            data_tools = DataAccessTools(
                ml_scores_path=ml_scores_path,
                customer_history_path=customer_history_path,
                fraud_cases_path=fraud_cases_path
            )
            
            # Initialize AI fraud analysis agent
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                ai_agent = FraudAnalysisAgent(
                    api_key=openai_key,
                    model=os.getenv('AI_MODEL', 'gpt-4'),
                    data_tools=data_tools
                )
                
                # Prepare analysis context
                analysis_context = {
                    'extracted_data': extracted,
                    'ml_results': ml_analysis,
                    'normalized_data': normalized_data.to_dict() if normalized_data else None
                }
                
                ai_analysis = ai_agent.analyze_fraud(ml_analysis, extracted, customer_id=None)
                logger.info(f"AI fraud analysis completed: recommendation={ai_analysis.get('recommendation', 'N/A')}")
        except Exception as e:
            logger.error(f"AI fraud analysis failed: {e}", exc_info=True)
    
    # Generate anomalies list
    anomalies = _generate_anomalies(extracted, ml_analysis, ai_analysis)
    
    # Calculate overall confidence score
    confidence_score = _calculate_confidence_score(extracted, ml_analysis)
    
    # Convert numeric values to native Python types for JSON serialization
    confidence_score = float(confidence_score) if confidence_score is not None else 0.0
    
    # Build complete response
    result = {
        "status": "success",
        "extracted_data": extracted,
        "raw_fields": fields,
        "raw_text": raw_text,
        "timestamp": datetime.now().isoformat(),
        "anomalies": anomalies,
        "confidence_score": confidence_score
    }
    
    # Add normalized data if available
    if normalized_data:
        result["normalized_data"] = normalized_data.to_dict()
        logger.info("Normalized data added to response")
    
    # Always add ML analysis to response (even if None or has error)
    if ml_analysis:
        # Convert NumPy types to JSON-serializable types
        ml_analysis_serializable = convert_to_json_serializable(ml_analysis)
        result["ml_analysis"] = ml_analysis_serializable
        result["ml_fraud_analysis"] = ml_analysis_serializable  # For backward compatibility
        # Safely get keys if ml_analysis is a dict
        if isinstance(ml_analysis_serializable, dict):
            logger.info(f"ML analysis added to response: {list(ml_analysis_serializable.keys())}")
        else:
            logger.info(f"ML analysis added to response (type: {type(ml_analysis_serializable).__name__})")
    else:
        logger.warning("ML analysis is None - adding default structure")
        result["ml_analysis"] = {
            "fraud_risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "model_confidence": 0.0,
            "error": "ML analysis returned None"
        }
        result["ml_fraud_analysis"] = result["ml_analysis"]
    
    # Add AI analysis if available
    if ai_analysis:
        # Convert NumPy types to JSON-serializable types
        ai_analysis_serializable = convert_to_json_serializable(ai_analysis)
        result["ai_analysis"] = ai_analysis_serializable
        logger.info("AI analysis added to response")
    else:
        logger.info("AI analysis not available (LangChain not installed or OpenAI key not set)")
    
    # Also convert normalized_data if present
    if result.get("normalized_data"):
        result["normalized_data"] = convert_to_json_serializable(result["normalized_data"])
    
    logger.info(f"Final result keys: {list(result.keys())}")
    return result


def _generate_anomalies(extracted: Dict, ml_analysis: Optional[Dict], ai_analysis: Optional[Dict]) -> List[str]:
    """Generate list of anomalies based on ML and AI analysis"""
    anomalies = []
    
    if ml_analysis:
        risk_level = ml_analysis.get('risk_level', 'LOW')
        fraud_score = ml_analysis.get('fraud_risk_score', 0)
        
        if risk_level in ['HIGH', 'CRITICAL']:
            anomalies.append(f"High fraud risk detected: {risk_level} (score: {fraud_score:.2%})")
        
        # Check for specific fraud indicators
        feature_importance = ml_analysis.get('feature_importance', {})
        # Handle both dict and list formats for feature_importance
        if isinstance(feature_importance, dict):
            for feature, importance in list(feature_importance.items())[:5]:  # Top 5 features
                if isinstance(importance, (int, float)) and importance > 0.1:  # Significant importance
                    anomalies.append(f"Fraud indicator: {feature} (importance: {importance:.2%})")
        elif isinstance(feature_importance, list):
            # If it's a list, iterate directly
            for item in feature_importance[:5]:
                if isinstance(item, dict) and 'feature' in item and 'importance' in item:
                    importance = item.get('importance', 0)
                    if importance > 0.1:
                        feature = item.get('feature', 'Unknown')
                        anomalies.append(f"Fraud indicator: {feature} (importance: {importance:.2%})")
                elif isinstance(item, (tuple, list)) and len(item) >= 2:
                    # If it's a list of tuples (feature, importance)
                    feature, importance = item[0], item[1]
                    if isinstance(importance, (int, float)) and importance > 0.1:
                        anomalies.append(f"Fraud indicator: {feature} (importance: {importance:.2%})")
    
    if ai_analysis:
        recommendation = ai_analysis.get('recommendation', '')
        if recommendation and recommendation != 'APPROVE':
            anomalies.append(f"AI recommendation: {recommendation}")
        
        risk_factors = ai_analysis.get('risk_factors', [])
        anomalies.extend(risk_factors)
    
    # Basic validation checks
    if extracted.get('amount_numeric'):
        amount = extracted['amount_numeric']
        if amount > 10000:
            anomalies.append("Amount exceeds $10,000 - requires additional verification")
        if amount < 1:
            anomalies.append("Amount is suspiciously low")
    
    if not extracted.get('signature'):
        anomalies.append("Missing signature")
    
    if not extracted.get('serial_number'):
        anomalies.append("Missing serial number")
    
    return anomalies


def _calculate_confidence_score(extracted: Dict, ml_analysis: Optional[Dict]) -> float:
    """Calculate overall confidence score based on extraction and ML analysis"""
    confidence = 0.5  # Base confidence
    
    # Check field completeness
    required_fields = ['issuer', 'payee', 'amount_numeric', 'date', 'serial_number']
    present_fields = sum(1 for field in required_fields if extracted.get(field))
    field_completeness = present_fields / len(required_fields)
    confidence += field_completeness * 0.3
    
    # ML confidence if available
    if ml_analysis:
        ml_confidence = ml_analysis.get('model_confidence', 0.5)
        confidence += ml_confidence * 0.2
    else:
        confidence += 0.2  # Default if ML not available
    
    # Ensure score is between 0 and 1
    return min(1.0, max(0.0, confidence))
