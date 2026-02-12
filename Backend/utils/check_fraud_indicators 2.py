"""
Specific fraud indicators for check validation.
Provides detailed one-liner explanations for fraud detection.
"""
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def detect_check_fraud_indicators(extracted_data: Dict[str, Any], raw_text: str = "") -> List[str]:
    """
    Detect specific fraud indicators in checks with detailed explanations.

    Args:
        extracted_data: Extracted check data
        raw_text: Raw OCR text from check

    Returns:
        List of fraud indicator messages (one-liners)
    """
    indicators = []

    # 1. MICR Line Mismatch
    micr_mismatch = _check_micr_mismatch(extracted_data, raw_text)
    if micr_mismatch:
        indicators.append(micr_mismatch)

    # 2. Computer Font Signature
    font_signature = _check_font_signature(extracted_data, raw_text)
    if font_signature:
        indicators.append(font_signature)

    # 3. Wrong Bank Logo/Format
    logo_issue = _check_bank_logo(extracted_data)
    if logo_issue:
        indicators.append(logo_issue)

    # 4. Missing Security Features
    security_features = _check_security_features(extracted_data, raw_text)
    if security_features:
        indicators.append(security_features)

    # 5. All Same Font (Digital Fabrication)
    same_font = _check_font_consistency(raw_text)
    if same_font:
        indicators.append(same_font)

    # 6. Flat Background Color
    background = _check_background_pattern(extracted_data)
    if background:
        indicators.append(background)

    # 7. Future Date
    future_date = _check_future_date(extracted_data)
    if future_date:
        indicators.append(future_date)

    # 8. Check Number 0001
    first_check = _check_number_0001(extracted_data)
    if first_check:
        indicators.append(first_check)

    # 9. Perfect Alignment
    perfect_alignment = _check_perfect_alignment(raw_text)
    if perfect_alignment:
        indicators.append(perfect_alignment)

    # 10. No Watermark/Hologram
    watermark = _check_watermark(extracted_data)
    if watermark:
        indicators.append(watermark)

    return indicators


def _check_micr_mismatch(data: Dict[str, Any], raw_text: str) -> str:
    """Check if check number on top matches MICR line at bottom."""
    check_number = data.get('check_number')

    if not check_number:
        return ""

    # Extract MICR line numbers from raw text
    # MICR format: routing(9) account(variable) check(4)
    micr_pattern = r'[0-9]{9}\s+[0-9]+\s+([0-9]{1,4})'
    micr_match = re.search(micr_pattern, raw_text)

    if micr_match:
        micr_check_num = micr_match.group(1).lstrip('0')
        check_num_clean = str(check_number).lstrip('0')

        if micr_check_num != check_num_clean:
            return f"MICR mismatch: Check number on top ({check_number}) doesn't match bottom MICR line ({micr_match.group(1)}) - instant fraud flag"

    return ""


def _check_font_signature(data: Dict[str, Any], raw_text: str) -> str:
    """Check if signature appears to be a computer font."""
    signature = data.get('signature_detected') or data.get('signature')
    payer_name = data.get('payer_name')

    if not signature and not payer_name:
        return ""

    # Check if signature matches payer name exactly (suggesting computer font)
    if payer_name and signature:
        if isinstance(signature, str) and signature.strip().lower() == payer_name.strip().lower():
            return "Signature appears to be computer font (matches typed name exactly), not real handwritten signature - obvious fake"

    # Check for common script fonts in text
    script_fonts = ['brush script', 'script', 'cursive']
    text_lower = raw_text.lower()

    for font in script_fonts:
        if font in text_lower:
            return "Signature uses computer script font, not authentic handwritten signature"

    return ""


def _check_bank_logo(data: Dict[str, Any]) -> str:
    """Check if bank logo/branding appears legitimate."""
    bank_name = data.get('bank_name', '').lower()

    # Major banks that should have specific branding
    major_banks = {
        'bank of america': 'Bank of America logo should have specific flag icon and official typeface',
        'chase': 'Chase logo should have official blue octagon design',
        'wells fargo': 'Wells Fargo logo should have official stagecoach icon',
        'citibank': 'Citibank logo should have official umbrella arc design',
    }

    for bank, message in major_banks.items():
        if bank in bank_name:
            # If we can't verify proper branding, flag it
            return f"Bank logo may be incorrect - {message}"

    return ""


def _check_security_features(data: Dict[str, Any], raw_text: str) -> str:
    """Check for missing security features."""
    # Look for security indicators in text
    security_keywords = ['secure', 'security', 'microprint', 'padlock', 'hologram', 'watermark']

    has_security = any(keyword in raw_text.lower() for keyword in security_keywords)

    if not has_security:
        return "Missing security features: No microprinting, padlock icon, or security background - real checks have built-in protection"

    return ""


def _check_font_consistency(raw_text: str) -> str:
    """Check if entire check uses same computer font."""
    if not raw_text:
        return ""

    # Simple heuristic: if text is very uniform and clean, likely all computer-generated
    lines = raw_text.strip().split('\n')

    # Check for variation in text (real checks have pre-printed + handwritten/typed)
    # This is a simplified check
    if len(lines) > 5:
        # Real checks should have some variation
        # If all lines are very similar length/format, might be all computer-generated
        # This is a basic heuristic
        pass

    return ""  # Skip this complex check for now


def _check_background_pattern(data: Dict[str, Any]) -> str:
    """Check for security background pattern."""
    # This would require image analysis - placeholder
    # Real implementation would check image for security patterns
    return ""


def _check_future_date(data: Dict[str, Any]) -> str:
    """Check if check is post-dated (future date)."""
    from datetime import datetime

    date_str = data.get('date')
    if not date_str:
        return ""

    try:
        # Try to parse date
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%B %d, %Y']
        check_date = None

        for fmt in date_formats:
            try:
                check_date = datetime.strptime(str(date_str), fmt)
                break
            except ValueError:
                continue

        if check_date:
            today = datetime.now()
            if check_date > today:
                days_future = (check_date - today).days
                return f"Check dated in the future ({date_str}) - post-dated checks are fraud red flags and can't be cashed until that date"
    except Exception:
        pass

    return ""


def _check_number_0001(data: Dict[str, Any]) -> str:
    """Check if check number is 0001 (first check - suspicious)."""
    check_number = data.get('check_number')

    if not check_number:
        return ""

    # Convert to int and check if it's very low
    try:
        check_num = int(str(check_number).lstrip('0') or '0')
        if check_num <= 1:
            return "Check number 0001 (first in checkbook) - usually stolen blanks or fraudulent printing, not from established account"
        elif check_num <= 10:
            return f"Very low check number ({check_number}) - new checkbooks are high fraud risk"
    except ValueError:
        pass

    return ""


def _check_perfect_alignment(raw_text: str) -> str:
    """Check if everything is perfectly aligned (computer-generated)."""
    # This is complex to detect from text alone
    # Would need image analysis
    return ""


def _check_watermark(data: Dict[str, Any]) -> str:
    """Check for watermark/hologram indicators."""
    # This requires image analysis - placeholder
    # Real implementation would check for watermark indicators
    return ""


def get_fraud_summary(indicators: List[str]) -> str:
    """
    Generate a summary of fraud indicators.

    Args:
        indicators: List of fraud indicator messages

    Returns:
        Summary string
    """
    if not indicators:
        return "No specific fraud indicators detected"

    count = len(indicators)
    if count == 1:
        return f"1 fraud indicator detected: {indicators[0]}"
    else:
        return f"{count} fraud indicators detected - check requires manual verification"
