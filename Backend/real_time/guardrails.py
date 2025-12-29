"""
LLM Input Guardrails
Provides data sanitization and validation for LLM inputs to prevent PII leakage and injection attacks.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class InputGuard:
    """
    Guardrail system for LLM inputs.
    Redacts PII and sanitizes text before sending to external APIs.
    """
    
    # Pre-compiled regex patterns for performance
    PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        'ipv4': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    }
    
    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Redact PII from text string.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text with PII replaced by placeholders (e.g. [EMAIL])
        """
        if not text or not isinstance(text, str):
            return text
            
        sanitized = text
        sanitized = cls.PATTERNS['email'].sub('[EMAIL]', sanitized)
        sanitized = cls.PATTERNS['phone'].sub('[PHONE]', sanitized)
        sanitized = cls.PATTERNS['ssn'].sub('[SSN]', sanitized)
        sanitized = cls.PATTERNS['credit_card'].sub('[CREDIT_CARD]', sanitized)
        # sanitized = cls.PATTERNS['ipv4'].sub('[IP_ADDRESS]', sanitized) # Optional, maybe too aggressive for some logs
        
        return sanitized
    
    @classmethod
    def validate_length(cls, text: str, max_chars: int = 15000) -> bool:
        """
        Validate input length to prevent token exhauston attacks.
        
        Args:
            text: Input text
            max_chars: Maximum allowed characters
            
        Returns:
            True if valid, False if too long
        """
        if not text:
            return True
        return len(text) <= max_chars

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize generic dictionary values (useful for unstructured inputs).
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            New dictionary with sanitized string values
        """
        if not isinstance(data, dict):
            return data
            
        clean_data = {}
        for k, v in data.items():
            if isinstance(v, str):
                clean_data[k] = cls.sanitize(v)
            elif isinstance(v, dict):
                clean_data[k] = cls.sanitize_dict(v)
            elif isinstance(v, list):
                clean_data[k] = [cls.sanitize(item) if isinstance(item, str) else item for item in v]
            else:
                clean_data[k] = v
        return clean_data
