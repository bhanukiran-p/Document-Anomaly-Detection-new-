"""
LLM Input Guardrails
Provides data sanitization and validation for LLM inputs to prevent PII leakage and injection attacks.
Includes profanity filtering and content moderation.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try to import better-profanity, fallback gracefully if not available
try:
    from better_profanity import profanity
    PROFANITY_AVAILABLE = True
except ImportError:
    PROFANITY_AVAILABLE = False
    logger.warning("better-profanity not available. Profanity filtering disabled. Install with: pip install better-profanity")

class InputGuard:
    """
    Guardrail system for LLM inputs.
    Redacts PII, filters profanity, and sanitizes text before sending to external APIs.
    """
    
    # Pre-compiled regex patterns for performance
    PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        'ipv4': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    }
    
    # Initialize profanity filter if available
    _profanity_initialized = False
    
    @classmethod
    def _init_profanity(cls):
        """Initialize profanity filter if available."""
        if PROFANITY_AVAILABLE and not cls._profanity_initialized:
            try:
                profanity.load_censor_words()
                cls._profanity_initialized = True
                logger.info("Profanity filter initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize profanity filter: {e}")
                cls._profanity_initialized = False
    
    @classmethod
    def sanitize(cls, text: str, filter_profanity: bool = True) -> str:
        """
        Redact PII and filter profanity from text string.
        
        Args:
            text: Input text to sanitize
            filter_profanity: Whether to filter profanity (default: True)
            
        Returns:
            Sanitized text with PII replaced by placeholders and profanity censored
        """
        if not text or not isinstance(text, str):
            return text
        
        # Initialize profanity filter if needed
        if filter_profanity:
            cls._init_profanity()
            
        sanitized = text
        
        # Step 1: Filter profanity (before PII redaction to avoid interfering with patterns)
        if filter_profanity and PROFANITY_AVAILABLE and cls._profanity_initialized:
            try:
                sanitized = profanity.censor(sanitized)
            except Exception as e:
                logger.warning(f"Profanity filtering failed: {e}")
        
        # Step 2: Redact PII
        sanitized = cls.PATTERNS['email'].sub('[EMAIL]', sanitized)
        sanitized = cls.PATTERNS['phone'].sub('[PHONE]', sanitized)
        sanitized = cls.PATTERNS['ssn'].sub('[SSN]', sanitized)
        sanitized = cls.PATTERNS['credit_card'].sub('[CREDIT_CARD]', sanitized)
        # sanitized = cls.PATTERNS['ipv4'].sub('[IP_ADDRESS]', sanitized) # Optional, maybe too aggressive for some logs
        
        return sanitized
    
    @classmethod
    def contains_profanity(cls, text: str) -> bool:
        """
        Check if text contains profanity without censoring it.
        
        Args:
            text: Input text to check
            
        Returns:
            True if profanity detected, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
        
        cls._init_profanity()
        
        if PROFANITY_AVAILABLE and cls._profanity_initialized:
            try:
                return profanity.contains_profanity(text)
            except Exception as e:
                logger.warning(f"Profanity check failed: {e}")
                return False
        
        return False
    
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
    def sanitize_dict(cls, data: Dict[str, Any], filter_profanity: bool = True) -> Dict[str, Any]:
        """
        Recursively sanitize generic dictionary values (useful for unstructured inputs).
        Includes PII redaction and profanity filtering.
        
        Args:
            data: Dictionary to sanitize
            filter_profanity: Whether to filter profanity (default: True)
            
        Returns:
            New dictionary with sanitized string values
        """
        if not isinstance(data, dict):
            return data
            
        clean_data = {}
        for k, v in data.items():
            if isinstance(v, str):
                clean_data[k] = cls.sanitize(v, filter_profanity=filter_profanity)
            elif isinstance(v, dict):
                clean_data[k] = cls.sanitize_dict(v, filter_profanity=filter_profanity)
            elif isinstance(v, list):
                clean_data[k] = [
                    cls.sanitize(item, filter_profanity=filter_profanity) if isinstance(item, str) else item 
                    for item in v
                ]
            else:
                clean_data[k] = v
        return clean_data
