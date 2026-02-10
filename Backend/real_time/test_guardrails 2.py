"""
Test LLM Guardrails
Verifies that InputGuard correctly redacts PII and sanitizes inputs.
"""

import sys
import os
import unittest

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_time.guardrails import InputGuard

class TestInputGuard(unittest.TestCase):
    
    def test_email_redaction(self):
        text = "Contact me at user@example.com for more info."
        sanitized = InputGuard.sanitize(text)
        self.assertEqual(sanitized, "Contact me at [EMAIL] for more info.")
        
    def test_phone_redaction(self):
        text = "Call 555-123-4567 or (555) 123-4567 immediately."
        sanitized = InputGuard.sanitize(text)
        # Note: Regex might match differently depending on pattern overlap, check output
        self.assertIn("[PHONE]", sanitized)
        self.assertNotIn("555-123-4567", sanitized)
        
    def test_ssn_redaction(self):
        text = "My SSN is 123-45-6789."
        sanitized = InputGuard.sanitize(text)
        self.assertEqual(sanitized, "My SSN is [SSN].")
        
    def test_credit_card_redaction(self):
        text = "Pay with 1234 5678 1234 5678 now."
        sanitized = InputGuard.sanitize(text)
        self.assertEqual(sanitized, "Pay with [CREDIT_CARD] now.")
        
    def test_mixed_pii(self):
        text = "User john.doe@email.com called 123-456-7890 regarding card 1111-2222-3333-4444."
        sanitized = InputGuard.sanitize(text)
        self.assertEqual(sanitized, "User [EMAIL] called [PHONE] regarding card [CREDIT_CARD].")
        
    def test_sanitize_dict(self):
        data = {
            "user": "admin@test.com",
            "meta": {
                "phone": "555-000-0000",
                "safe": "value"
            },
            "list": ["valid", "123-45-6789"]
        }
        clean = InputGuard.sanitize_dict(data)
        self.assertEqual(clean['user'], "[EMAIL]")
        self.assertEqual(clean['meta']['phone'], "[PHONE]")
        self.assertEqual(clean['meta']['safe'], "value")
        self.assertEqual(clean['list'][1], "[SSN]")

if __name__ == '__main__':
    unittest.main()
