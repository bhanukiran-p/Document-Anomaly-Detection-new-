"""
Enhanced signature detection for checks and documents.
Uses multiple detection methods for better accuracy.
"""
import re
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class SignatureDetector:
    """
    Advanced signature detection using multiple heuristics.
    Combines OCR text analysis, field presence, and pattern matching.
    """

    def __init__(self):
        # Common signature-related keywords in OCR text
        self.signature_keywords = [
            'authorized signature',
            'signature',
            'signed',
            'sign here',
            'signer',
            'signatory',
            'x_______',  # Signature line placeholder
        ]

        # Patterns that indicate handwritten text (likely signature)
        self.handwritten_patterns = [
            r'[A-Z][a-z]+\s+[A-Z][a-z]+',  # Name pattern like "John Doe"
            r'[A-Z]\.\s*[A-Z]\.\s*[A-Z][a-z]+',  # Initials pattern like "J. D. Smith"
            r'[A-Z][a-z]+\s+[A-Z]\.',  # Pattern like "John D."
        ]

    def detect_signature(
        self,
        extracted_data: Dict[str, Any],
        raw_text: str = ""
    ) -> Tuple[bool, float, str]:
        """
        Detect if a signature is present using multiple methods.

        Args:
            extracted_data: Extracted document fields
            raw_text: Raw OCR text from document

        Returns:
            Tuple of (is_present, confidence, detection_method)
            - is_present (bool): Whether signature was detected
            - confidence (float): Confidence score 0.0-1.0
            - detection_method (str): How signature was detected
        """
        methods_detected = []
        confidence_scores = []

        # Method 1: Direct field detection (from Mindee/OCR)
        field_detected, field_confidence = self._check_signature_field(extracted_data)
        if field_detected:
            methods_detected.append("field_extraction")
            confidence_scores.append(field_confidence)

        # Method 2: OCR text analysis
        text_detected, text_confidence = self._analyze_ocr_text(raw_text, extracted_data)
        if text_detected:
            methods_detected.append("text_analysis")
            confidence_scores.append(text_confidence)

        # Method 3: Payer/signer name presence
        name_detected, name_confidence = self._check_signer_name(extracted_data)
        if name_detected:
            methods_detected.append("signer_name")
            confidence_scores.append(name_confidence)

        # Method 4: Check-specific signature detection
        check_detected, check_confidence = self._check_signature_location(extracted_data, raw_text)
        if check_detected:
            methods_detected.append("signature_location")
            confidence_scores.append(check_confidence)

        # Combine results
        if not methods_detected:
            return False, 0.0, "none"

        # Calculate overall confidence (weighted average)
        avg_confidence = sum(confidence_scores) / len(confidence_scores)

        # Boost confidence if multiple methods agree
        if len(methods_detected) >= 2:
            avg_confidence = min(1.0, avg_confidence * 1.2)

        detection_method = "+".join(methods_detected)

        is_present = avg_confidence >= 0.65  # Compromise threshold - balances false positives/negatives, relies on escalate-then-reject for error handling

        logger.info(
            f"Signature detection: present={is_present}, "
            f"confidence={avg_confidence:.2f}, methods={detection_method}"
        )

        return is_present, avg_confidence, detection_method

    def _check_signature_field(self, data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Check if signature field is directly present in extracted data.

        Returns:
            Tuple of (detected, confidence)
        """
        # Check various signature field names
        signature_fields = [
            'signature',
            'signature_detected',
            'signer',
            'authorized_signature',
            'drawer_signature',
            'endorsement'
        ]

        for field in signature_fields:
            value = data.get(field)

            if value is None:
                continue

            # Boolean field
            if isinstance(value, bool):
                return value, 0.9 if value else 0.0

            # String field (signature text/name)
            if isinstance(value, str):
                value = value.strip()
                if value and value.lower() not in ['none', 'null', 'n/a', 'missing', '']:
                    # Has signature text/name
                    confidence = 0.8 if len(value) > 2 else 0.5
                    return True, confidence

            # Numeric confidence score
            if isinstance(value, (int, float)):
                if value > 0:
                    return True, min(0.9, value)

        return False, 0.0

    def _analyze_ocr_text(self, raw_text: str, data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Analyze OCR text for signature indicators.

        Returns:
            Tuple of (detected, confidence)
        """
        if not raw_text:
            return False, 0.0

        text_lower = raw_text.lower()

        # Check for signature keywords
        keyword_found = any(keyword in text_lower for keyword in self.signature_keywords)

        if not keyword_found:
            return False, 0.0

        # Look for name patterns near signature keywords
        # This helps detect handwritten signatures that OCR picked up
        payer_name = (
            data.get('payer_name') or
            data.get('purchaser') or
            data.get('drawer') or
            data.get('signer_name') or
            ''
        )

        if payer_name:
            # Check if payer name appears in text (likely signed)
            payer_pattern = re.escape(payer_name.strip())
            if re.search(payer_pattern, raw_text, re.IGNORECASE):
                return True, 0.75

        # Check for handwritten name patterns
        for pattern in self.handwritten_patterns:
            if re.search(pattern, raw_text):
                return True, 0.6

        # Keyword found but no name detected
        return True, 0.4

    def _check_signer_name(self, data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Check if signer/payer name is present (indirect signature indicator).
        
        DISABLED: This heuristic causes false positives.
        Payer name presence does NOT mean signature is present.
        Only actual signature field detection should be trusted.

        Returns:
            Tuple of (detected, confidence) - always returns False
        """
        # DISABLED: Payer name does not indicate signature presence
        # This was causing false positives where documents with payer names
        # but no actual signatures were incorrectly marked as signed
        return False, 0.0

    def _check_signature_location(self, data: Dict[str, Any], raw_text: str) -> Tuple[bool, float]:
        """
        Check for signature in typical check signature location.

        Returns:
            Tuple of (detected, confidence)
        """
        if not raw_text:
            return False, 0.0

        # For checks, signature typically appears:
        # - Bottom right area
        # - After MICR line
        # - Near "X" or signature line marker

        lines = raw_text.split('\n')
        if len(lines) < 3:
            return False, 0.0

        # Check last few lines (bottom of check)
        bottom_lines = lines[-5:]
        bottom_text = ' '.join(bottom_lines).lower()

        # Look for signature indicators in bottom section
        signature_markers = [
            'x',  # Signature line marker
            '___',  # Signature line
            'authorized',
            'drawer',
        ]

        marker_found = any(marker in bottom_text for marker in signature_markers)

        if marker_found:
            # Check if there's a name-like pattern nearby
            for line in bottom_lines:
                # Name pattern: capitalized words
                if re.search(r'[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}', line):
                    return True, 0.7

            # Marker found but no name
            return True, 0.4

        return False, 0.0

    def get_signature_quality(self, extracted_data: Dict[str, Any]) -> Optional[float]:
        """
        Get signature quality/confidence if available from OCR.

        Returns:
            Quality score 0.0-1.0, or None if not available
        """
        quality_fields = [
            'signature_confidence',
            'signature_quality',
            'signature_score'
        ]

        for field in quality_fields:
            value = extracted_data.get(field)
            if value is not None and isinstance(value, (int, float)):
                return max(0.0, min(1.0, float(value)))

        return None


# Singleton instance
_signature_detector = None


def get_signature_detector() -> SignatureDetector:
    """Get singleton signature detector instance."""
    global _signature_detector
    if _signature_detector is None:
        _signature_detector = SignatureDetector()
    return _signature_detector


def detect_signature(extracted_data: Dict[str, Any], raw_text: str = "") -> bool:
    """
    Convenience function to detect signature presence.

    Args:
        extracted_data: Extracted document fields
        raw_text: Raw OCR text

    Returns:
        bool: True if signature detected with sufficient confidence
    """
    detector = get_signature_detector()
    is_present, confidence, method = detector.detect_signature(extracted_data, raw_text)
    return is_present


def get_signature_confidence(extracted_data: Dict[str, Any], raw_text: str = "") -> float:
    """
    Get signature detection confidence score.

    Args:
        extracted_data: Extracted document fields
        raw_text: Raw OCR text

    Returns:
        float: Confidence score 0.0-1.0
    """
    detector = get_signature_detector()
    _, confidence, _ = detector.detect_signature(extracted_data, raw_text)
    return confidence
