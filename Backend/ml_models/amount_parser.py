"""
Amount Word Parser for Money Order Fraud Detection
Parses written amounts (e.g., "SEVEN HUNDRED FIFTY DOLLARS") and compares to numeric values
"""

import re
from typing import Optional, Tuple


class AmountWordParser:
    """
    Parse written amounts and validate against numeric amounts
    Handles various formats used in money orders
    """

    def __init__(self):
        # Word to number mappings
        self.ones = {
            'ZERO': 0, 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4,
            'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9,
            'TEN': 10, 'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13,
            'FOURTEEN': 14, 'FIFTEEN': 15, 'SIXTEEN': 16, 'SEVENTEEN': 17,
            'EIGHTEEN': 18, 'NINETEEN': 19
        }

        self.tens = {
            'TWENTY': 20, 'THIRTY': 30, 'FORTY': 40, 'FIFTY': 50,
            'SIXTY': 60, 'SEVENTY': 70, 'EIGHTY': 80, 'NINETY': 90
        }

        self.scales = {
            'HUNDRED': 100,
            'THOUSAND': 1000,
            'MILLION': 1000000
        }

    def parse_written_amount(self, written_text: str) -> Optional[float]:
        """
        Parse written amount to numeric value

        Args:
            written_text: Written amount (e.g., "SEVEN HUNDRED FIFTY AND 00/100 DOLLARS")

        Returns:
            Parsed numeric amount or None if parsing fails

        Examples:
            "SEVEN HUNDRED FIFTY AND 00/100 DOLLARS" -> 750.00
            "ONE THOUSAND FIVE HUNDRED" -> 1500.00
            "FIVE THOUSAND AND NO/100" -> 5000.00
        """
        if not written_text:
            return None

        try:
            # Convert to uppercase and clean
            text = written_text.upper().strip()

            # Extract dollar and cent portions
            dollar_amount = self._extract_dollar_amount(text)
            cent_amount = self._extract_cent_amount(text)

            if dollar_amount is None:
                return None

            # Combine dollars and cents
            total = dollar_amount + (cent_amount / 100.0 if cent_amount is not None else 0.0)
            return round(total, 2)

        except Exception as e:
            print(f"Error parsing written amount '{written_text}': {e}")
            return None

    def _extract_dollar_amount(self, text: str) -> Optional[float]:
        """
        Extract dollar portion from written amount

        Args:
            text: Uppercase written text

        Returns:
            Dollar amount as float or None
        """
        # Remove common suffixes
        text = re.sub(r'\s+AND\s+\d{1,2}/100.*$', '', text)  # Remove "AND 00/100 DOLLARS"
        text = re.sub(r'\s+AND\s+NO/100.*$', '', text)       # Remove "AND NO/100"
        text = re.sub(r'\s+DOLLARS?.*$', '', text)           # Remove "DOLLARS"
        text = re.sub(r'\s+ONLY.*$', '', text)               # Remove "ONLY"

        # Split into words
        words = text.split()

        if not words:
            return None

        # Parse the number from words
        try:
            return self._words_to_number(words)
        except Exception:
            return None

    def _extract_cent_amount(self, text: str) -> Optional[int]:
        """
        Extract cent portion from written amount

        Args:
            text: Uppercase written text

        Returns:
            Cents as integer (0-99) or None
        """
        # Pattern: "AND XX/100" or "AND NO/100"
        cent_match = re.search(r'AND\s+(\d{1,2})/100', text)
        if cent_match:
            return int(cent_match.group(1))

        # Check for "NO/100" or "00/100"
        if 'NO/100' in text or '00/100' in text:
            return 0

        # If no cents specified, default to 0
        return 0

    def _words_to_number(self, words: list) -> float:
        """
        Convert list of number words to numeric value

        Args:
            words: List of uppercase number words

        Returns:
            Numeric value as float

        Examples:
            ['SEVEN', 'HUNDRED', 'FIFTY'] -> 750
            ['ONE', 'THOUSAND', 'FIVE', 'HUNDRED'] -> 1500
        """
        current = 0
        result = 0

        i = 0
        while i < len(words):
            word = words[i]

            # Check for ones (0-19)
            if word in self.ones:
                current += self.ones[word]

            # Check for tens (20-90)
            elif word in self.tens:
                current += self.tens[word]

            # Check for scales (hundred, thousand, million)
            elif word in self.scales:
                scale = self.scales[word]

                if word == 'HUNDRED':
                    # Multiply current by 100
                    current = current * scale if current > 0 else scale
                else:
                    # For thousand/million, add to result and reset current
                    current = current * scale if current > 0 else scale
                    result += current
                    current = 0

            # Ignore other words (AND, DOLLARS, etc.)

            i += 1

        # Add remaining current value
        result += current

        return float(result)

    def exact_amount_match(self, numeric_amount: float, written_text: str) -> float:
        """
        Check if numeric amount exactly matches written amount

        Args:
            numeric_amount: Numeric amount (e.g., 750.00)
            written_text: Written amount (e.g., "SEVEN HUNDRED FIFTY")

        Returns:
            1.0 if exact match, 0.0 if mismatch or cannot parse
        """
        if not written_text or numeric_amount is None or numeric_amount == 0:
            return 0.0

        parsed_amount = self.parse_written_amount(written_text)

        if parsed_amount is None:
            return 0.0

        # Check for exact match (allow small floating point tolerance)
        if abs(parsed_amount - numeric_amount) < 0.01:
            return 1.0
        else:
            return 0.0

    def get_amount_confidence(self, numeric_amount: float, written_text: str) -> Tuple[float, Optional[float]]:
        """
        Get confidence score for amount matching

        Args:
            numeric_amount: Numeric amount
            written_text: Written amount

        Returns:
            Tuple of (confidence_score, parsed_amount)
            confidence_score: 0.0-1.0 indicating match quality
            parsed_amount: Parsed numeric value or None
        """
        if not written_text or numeric_amount is None or numeric_amount == 0:
            return (0.0, None)

        parsed_amount = self.parse_written_amount(written_text)

        if parsed_amount is None:
            # Could not parse - low confidence
            return (0.0, None)

        # Calculate difference
        diff = abs(parsed_amount - numeric_amount)

        if diff < 0.01:
            # Exact match - perfect confidence
            return (1.0, parsed_amount)
        elif diff < 10:
            # Close match (within $10) - medium confidence
            return (0.5, parsed_amount)
        else:
            # Large mismatch - no confidence
            return (0.0, parsed_amount)

    def validate_amount_consistency(self, numeric_amount: float, written_text: str) -> dict:
        """
        Comprehensive amount validation with detailed results

        Args:
            numeric_amount: Numeric amount
            written_text: Written amount

        Returns:
            Dictionary with validation results:
            {
                'is_match': bool,
                'confidence': float,
                'numeric_amount': float,
                'parsed_amount': float or None,
                'difference': float,
                'fraud_indicator': bool
            }
        """
        confidence, parsed_amount = self.get_amount_confidence(numeric_amount, written_text)

        is_match = confidence == 1.0
        difference = abs(parsed_amount - numeric_amount) if parsed_amount else 0.0
        fraud_indicator = not is_match and parsed_amount is not None

        return {
            'is_match': is_match,
            'confidence': confidence,
            'numeric_amount': numeric_amount,
            'parsed_amount': parsed_amount,
            'difference': difference,
            'fraud_indicator': fraud_indicator
        }


# Singleton instance for easy import
amount_parser = AmountWordParser()


# Convenience functions
def parse_amount(written_text: str) -> Optional[float]:
    """Parse written amount to numeric value"""
    return amount_parser.parse_written_amount(written_text)


def check_amount_match(numeric: float, written: str) -> float:
    """Check if amounts match (returns 1.0 or 0.0)"""
    return amount_parser.exact_amount_match(numeric, written)


def get_match_confidence(numeric: float, written: str) -> float:
    """Get confidence score for amount match (0.0-1.0)"""
    confidence, _ = amount_parser.get_amount_confidence(numeric, written)
    return confidence
