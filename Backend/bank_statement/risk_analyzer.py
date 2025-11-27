"""
Bank statement risk analysis utilities.
"""
import logging
from .parser import safe_parse_currency

logger = logging.getLogger(__name__)


def evaluate_risk(data):
    """
    Evaluate fraud risk for bank statement.

    Args:
        data: Structured bank statement data

    Returns:
        dict: Risk analysis results
    """
    score = 0.25
    indicators = []

    raw_text = (data.get('raw_text') or '').lower()
    summary = data.get('summary') or {}
    balances = data.get('balances') or {}

    # Missing critical information
    if not data.get('bank_name'):
        score += 0.15
        indicators.append("Bank name missing")

    if not data.get('account_number'):
        score += 0.15
        indicators.append("Account number missing")

    # Low transaction count
    if summary.get('transaction_count', 0) < 3:
        score += 0.1
        indicators.append("Very few transactions detected")

    # Suspicious keywords
    suspicious_keywords = ['nsf', 'overdraft', 'chargeback', 'return item', 'fraud alert']
    if any(keyword in raw_text for keyword in suspicious_keywords):
        score += 0.25
        indicators.append("Suspicious activity keywords found")

    # Balance consistency check
    opening = safe_parse_currency(balances.get('opening_balance'))
    ending = safe_parse_currency(balances.get('ending_balance'))
    net = summary.get('net_activity')

    if opening is not None and ending is not None and isinstance(net, (int, float)):
        if abs((opening + net) - ending) > max(50, abs(ending) * 0.05):
            score += 0.2
            indicators.append("Balances inconsistent with net activity")

    # Debit/credit ratio
    total_debits = summary.get('total_debits') or 0.0
    total_credits = summary.get('total_credits') or 0.0
    if total_credits > 0 and total_debits > total_credits * 2:
        score += 0.15
        indicators.append("Debits significantly exceed credits")

    # Normalize score
    score = max(0.0, min(1.0, score))

    # Determine risk level
    if score < 0.35:
        level = 'LOW'
    elif score < 0.6:
        level = 'MEDIUM'
    elif score < 0.85:
        level = 'HIGH'
    else:
        level = 'CRITICAL'

    # Calculate model confidence
    model_confidence = 0.65
    if summary.get('transaction_count', 0) >= 5:
        model_confidence = 0.75
    if summary.get('transaction_count', 0) >= 10:
        model_confidence = 0.85

    return {
        'fraud_risk_score': round(score, 3),
        'risk_level': level,
        'model_confidence': round(model_confidence, 3),
        'feature_importance': indicators,
        'prediction_type': 'bank_statement_rules'
    }


def build_ai_analysis(risk):
    """
    Build AI analysis based on risk evaluation.

    Args:
        risk: Risk analysis results

    Returns:
        dict: AI analysis results
    """
    score = risk.get('fraud_risk_score', 0.0)
    level = risk.get('risk_level', 'UNKNOWN')

    # Determine recommendation
    if level in ['HIGH', 'CRITICAL']:
        recommendation = 'REJECT'
        confidence = 0.9
    elif level == 'MEDIUM':
        recommendation = 'ESCALATE'
        confidence = 0.75
    else:
        recommendation = 'APPROVE'
        confidence = 0.65

    summary = f"{level.title()} fraud risk ({score * 100:.1f}%)."
    reasoning = "Heuristic analysis evaluated transaction patterns, balance changes, and metadata for anomalies."

    return {
        'recommendation': recommendation,
        'confidence': confidence,
        'summary': summary,
        'reasoning': reasoning,
        'key_indicators': risk.get('feature_importance', []),
        'verification_notes': "Manual review recommended when anomalies are detected.",
        'analysis_type': 'rule_based',
        'model_used': 'bank_statement_heuristics'
    }


def collect_anomalies(risk, ai_analysis):
    """
    Collect all anomalies from risk and AI analysis.

    Args:
        risk: Risk analysis results
        ai_analysis: AI analysis results

    Returns:
        list: List of anomaly descriptions
    """
    anomalies = []

    level = risk.get('risk_level')
    score = risk.get('fraud_risk_score', 0.0) * 100

    if level in ['HIGH', 'CRITICAL']:
        anomalies.append(f"High fraud risk detected: {level} (score: {score:.2f}%)")

    if ai_analysis.get('recommendation'):
        anomalies.append(f"AI recommendation: {ai_analysis['recommendation']}")

    anomalies.extend(risk.get('feature_importance', []))

    return anomalies
