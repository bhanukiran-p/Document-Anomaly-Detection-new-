"""
Response formatting utilities for API endpoints.
"""
import logging

logger = logging.getLogger(__name__)


def safe_float(value):
    """
    Convert value to Python float, handling NumPy types and None.

    Args:
        value: Value to convert

    Returns:
        float: Converted value or 0.0 if conversion fails
    """
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def extract_ml_analysis_fields(ml_analysis):
    """
    Extract ML analysis fields with safe defaults.

    Args:
        ml_analysis: ML analysis dictionary

    Returns:
        dict: Extracted fields with safe defaults
    """
    if not isinstance(ml_analysis, dict):
        ml_analysis = {}

    return {
        'fraud_risk_score': safe_float(ml_analysis.get('fraud_risk_score', 0.0)),
        'model_confidence': safe_float(ml_analysis.get('model_confidence', 0.0)),
        'risk_level': str(ml_analysis.get('risk_level', 'UNKNOWN'))
    }


def extract_ai_analysis_fields(ai_analysis):
    """
    Extract AI analysis fields with safe defaults.

    Args:
        ai_analysis: AI analysis dictionary

    Returns:
        dict: Extracted fields with safe defaults
    """
    if not isinstance(ai_analysis, dict):
        ai_analysis = {}

    return {
        'ai_recommendation': str(ai_analysis.get('recommendation', 'UNKNOWN')),
        'ai_confidence': safe_float(ai_analysis.get('confidence', 0.0))
    }


def format_analysis_response(result, document_type='document'):
    """
    Format analysis result into standardized API response.

    Args:
        result: Raw analysis result from extractor
        document_type: Type of document being analyzed

    Returns:
        dict: Formatted response ready for JSON serialization
    """
    if not result or not isinstance(result, dict):
        logger.error(f"Invalid result for {document_type}: not a dictionary")
        raise ValueError(f"Invalid analysis result for {document_type}")

    # Extract components
    extracted_data = result.get('extracted_data', {})
    if not isinstance(extracted_data, dict):
        extracted_data = {}

    ml_analysis = result.get('ml_analysis', {}) or {}
    if not isinstance(ml_analysis, dict):
        ml_analysis = {}

    ai_analysis = result.get('ai_analysis', {}) or {}
    if not isinstance(ai_analysis, dict):
        ai_analysis = {}

    # Extract ML and AI fields
    ml_fields = extract_ml_analysis_fields(ml_analysis)
    ai_fields = extract_ai_analysis_fields(ai_analysis)

    # Build formatted response
    formatted_data = {
        **extracted_data,
        **ml_fields,
        **ai_fields,
        'ml_analysis': ml_analysis,
        'ai_analysis': ai_analysis,
        'anomalies': result.get('anomalies', []),
        'confidence_score': safe_float(result.get('confidence_score', 0.0)),
        'timestamp': result.get('timestamp'),
    }

    # Add optional fields if present
    if 'normalized_data' in result:
        formatted_data['normalized_data'] = result.get('normalized_data')

    if 'raw_text' in result:
        formatted_data['raw_text'] = result.get('raw_text', '')

    if 'analysis_id' in result:
        formatted_data['analysis_id'] = result.get('analysis_id')

    logger.info(
        f"{document_type.title()} response formatted - "
        f"fraud_risk_score: {ml_fields['fraud_risk_score']}, "
        f"risk_level: {ml_fields['risk_level']}"
    )

    return {
        'success': True,
        'data': formatted_data,
        'message': f'{document_type.title()} analyzed successfully'
    }


def format_bank_statement_response(structured_data, risk_analysis, ai_analysis, anomalies, confidence_score):
    """
    Format bank statement analysis response.

    Args:
        structured_data: Parsed bank statement data
        risk_analysis: Risk analysis results
        ai_analysis: AI analysis results
        anomalies: List of detected anomalies
        confidence_score: Overall confidence score

    Returns:
        dict: Formatted response
    """
    formatted_data = {
        **structured_data,
        'fraud_risk_score': risk_analysis.get('fraud_risk_score', 0.0),
        'model_confidence': risk_analysis.get('model_confidence', 0.0),
        'risk_level': risk_analysis.get('risk_level', 'UNKNOWN'),
        'ai_recommendation': ai_analysis.get('recommendation', 'UNKNOWN'),
        'ai_confidence': ai_analysis.get('confidence', 0.0),
        'ml_analysis': risk_analysis,
        'ai_analysis': ai_analysis,
        'anomalies': anomalies,
        'confidence_score': confidence_score,
    }

    return {
        'success': True,
        'data': formatted_data,
        'message': 'Bank statement analyzed successfully'
    }
