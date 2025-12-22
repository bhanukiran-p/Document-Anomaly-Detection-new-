"""
LLM Guardrails for Real-Time Transaction Analysis
Provides comprehensive safety, rate limiting, and validation for OpenAI API calls
"""

import time
import logging
import re
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps
from collections import deque
import tiktoken

logger = logging.getLogger(__name__)


# ==================== CONFIGURATION ====================

class LLMGuardrailConfig:
    """Configuration for LLM guardrails"""

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_REQUESTS_PER_HOUR = 1000
    MAX_TOKENS_PER_MINUTE = 90000
    MAX_TOKENS_PER_DAY = 2000000

    # Timeouts (increased for better reliability)
    DEFAULT_TIMEOUT_SECONDS = 60
    MAX_TIMEOUT_SECONDS = 120

    # Retries
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    EXPONENTIAL_BACKOFF = True

    # Input Validation
    MAX_INPUT_LENGTH = 100000  # characters
    MAX_PROMPT_TOKENS = 8000
    MAX_TRANSACTIONS_PER_REQUEST = 1000

    # Output Validation
    MAX_OUTPUT_LENGTH = 50000  # characters
    MAX_COMPLETION_TOKENS = 8000

    # Content Safety
    BLOCK_PII_IN_LOGS = True
    SANITIZE_OUTPUTS = True

    # Allowed Models
    ALLOWED_MODELS = [
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-4-turbo',
        'gpt-4',
        'gpt-3.5-turbo',
        'o1',
        'o1-mini',
        'o4',
        'o4-mini'
    ]

    # Cost Limits (in USD)
    MAX_COST_PER_REQUEST = 1.00
    MAX_COST_PER_HOUR = 10.00
    MAX_COST_PER_DAY = 50.00


# ==================== RATE LIMITER ====================

class RateLimiter:
    """Token bucket rate limiter for API calls"""

    def __init__(self, config: LLMGuardrailConfig):
        self.config = config
        self.request_timestamps = deque(maxlen=config.MAX_REQUESTS_PER_HOUR)
        self.token_usage = deque(maxlen=1000)
        self.cost_tracking = deque(maxlen=10000)

    def check_rate_limit(self) -> tuple[bool, Optional[str]]:
        """
        Check if request can proceed based on rate limits

        Returns:
            (allowed, error_message)
        """
        now = datetime.now()

        # Check requests per minute
        one_minute_ago = now - timedelta(minutes=1)
        recent_requests = sum(1 for ts in self.request_timestamps if ts > one_minute_ago)

        if recent_requests >= self.config.MAX_REQUESTS_PER_MINUTE:
            return False, f"Rate limit exceeded: {recent_requests} requests in last minute (max: {self.config.MAX_REQUESTS_PER_MINUTE})"

        # Check requests per hour
        one_hour_ago = now - timedelta(hours=1)
        hourly_requests = sum(1 for ts in self.request_timestamps if ts > one_hour_ago)

        if hourly_requests >= self.config.MAX_REQUESTS_PER_HOUR:
            return False, f"Rate limit exceeded: {hourly_requests} requests in last hour (max: {self.config.MAX_REQUESTS_PER_HOUR})"

        # Check tokens per minute
        token_usage_minute = sum(
            usage['total_tokens']
            for usage in self.token_usage
            if usage['timestamp'] > one_minute_ago
        )

        if token_usage_minute >= self.config.MAX_TOKENS_PER_MINUTE:
            return False, f"Token rate limit exceeded: {token_usage_minute} tokens in last minute (max: {self.config.MAX_TOKENS_PER_MINUTE})"

        # Check tokens per day
        one_day_ago = now - timedelta(days=1)
        token_usage_day = sum(
            usage['total_tokens']
            for usage in self.token_usage
            if usage['timestamp'] > one_day_ago
        )

        if token_usage_day >= self.config.MAX_TOKENS_PER_DAY:
            return False, f"Daily token limit exceeded: {token_usage_day} tokens in last 24 hours (max: {self.config.MAX_TOKENS_PER_DAY})"

        return True, None

    def check_cost_limits(self, estimated_cost: float) -> tuple[bool, Optional[str]]:
        """Check if request is within cost limits"""
        now = datetime.now()

        # Check cost per request
        if estimated_cost > self.config.MAX_COST_PER_REQUEST:
            return False, f"Request cost ${estimated_cost:.4f} exceeds limit ${self.config.MAX_COST_PER_REQUEST}"

        # Check hourly cost
        one_hour_ago = now - timedelta(hours=1)
        hourly_cost = sum(
            cost['amount']
            for cost in self.cost_tracking
            if cost['timestamp'] > one_hour_ago
        )

        if hourly_cost + estimated_cost > self.config.MAX_COST_PER_HOUR:
            return False, f"Hourly cost limit exceeded: ${hourly_cost:.4f} (max: ${self.config.MAX_COST_PER_HOUR})"

        # Check daily cost
        one_day_ago = now - timedelta(days=1)
        daily_cost = sum(
            cost['amount']
            for cost in self.cost_tracking
            if cost['timestamp'] > one_day_ago
        )

        if daily_cost + estimated_cost > self.config.MAX_COST_PER_DAY:
            return False, f"Daily cost limit exceeded: ${daily_cost:.4f} (max: ${self.config.MAX_COST_PER_DAY})"

        return True, None

    def record_request(self, tokens_used: int, cost: float):
        """Record a successful request"""
        now = datetime.now()
        self.request_timestamps.append(now)
        self.token_usage.append({
            'timestamp': now,
            'total_tokens': tokens_used
        })
        self.cost_tracking.append({
            'timestamp': now,
            'amount': cost
        })

    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limit statistics"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        return {
            'requests_last_minute': sum(1 for ts in self.request_timestamps if ts > one_minute_ago),
            'requests_last_hour': sum(1 for ts in self.request_timestamps if ts > one_hour_ago),
            'tokens_last_minute': sum(u['total_tokens'] for u in self.token_usage if u['timestamp'] > one_minute_ago),
            'tokens_last_day': sum(u['total_tokens'] for u in self.token_usage if u['timestamp'] > one_day_ago),
            'cost_last_hour': sum(c['amount'] for c in self.cost_tracking if c['timestamp'] > one_hour_ago),
            'cost_last_day': sum(c['amount'] for c in self.cost_tracking if c['timestamp'] > one_day_ago),
        }


# ==================== INPUT VALIDATION ====================

class InputValidator:
    """Validates and sanitizes LLM inputs"""

    def __init__(self, config: LLMGuardrailConfig):
        self.config = config

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}. Using character approximation.")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4

    def validate_input(self, prompt: str, model: str) -> tuple[bool, Optional[str]]:
        """
        Validate input prompt

        Returns:
            (valid, error_message)
        """
        # Check input length
        if len(prompt) > self.config.MAX_INPUT_LENGTH:
            return False, f"Input too long: {len(prompt)} characters (max: {self.config.MAX_INPUT_LENGTH})"

        # Check token count
        token_count = self.count_tokens(prompt, model)
        if token_count > self.config.MAX_PROMPT_TOKENS:
            return False, f"Input too many tokens: {token_count} (max: {self.config.MAX_PROMPT_TOKENS})"

        # Check for empty input
        if not prompt or not prompt.strip():
            return False, "Input prompt is empty"

        return True, None

    def validate_model(self, model: str) -> tuple[bool, Optional[str]]:
        """Validate model name"""
        if not model:
            return False, "Model name is required"

        if model not in self.config.ALLOWED_MODELS:
            return False, f"Model '{model}' not allowed. Allowed models: {', '.join(self.config.ALLOWED_MODELS)}"

        return True, None

    def sanitize_transaction_data(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitize transaction data to remove PII and sensitive information

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Sanitized transactions
        """
        if len(transactions) > self.config.MAX_TRANSACTIONS_PER_REQUEST:
            logger.warning(f"Too many transactions ({len(transactions)}), limiting to {self.config.MAX_TRANSACTIONS_PER_REQUEST}")
            transactions = transactions[:self.config.MAX_TRANSACTIONS_PER_REQUEST]

        sanitized = []
        for txn in transactions:
            sanitized_txn = {}

            # Safe fields to include
            safe_fields = [
                'transaction_id', 'amount', 'fraud_probability', 'fraud_reason',
                'fraud_type', 'category', 'merchant', 'timestamp', 'is_fraud',
                'currency', 'transaction_type'
            ]

            for field in safe_fields:
                if field in txn:
                    value = txn[field]
                    # Sanitize merchant names (keep first 3 chars + asterisks)
                    if field == 'merchant' and isinstance(value, str) and len(value) > 3:
                        sanitized_txn[field] = value[:3] + '*' * min(5, len(value) - 3)
                    else:
                        sanitized_txn[field] = value

            sanitized.append(sanitized_txn)

        return sanitized

    def detect_prompt_injection(self, prompt: str) -> tuple[bool, Optional[str]]:
        """
        Detect potential prompt injection attacks

        Returns:
            (is_safe, warning_message)
        """
        # Patterns that might indicate prompt injection
        suspicious_patterns = [
            r'ignore\s+(previous|above|all)\s+instructions',
            r'disregard\s+(previous|above|all)',
            r'you\s+are\s+now',
            r'new\s+instructions',
            r'system\s*:\s*you',
            r'<\s*\|im_start\|>',
            r'<\s*\|im_end\|>',
            r'\[INST\]',
            r'\[/INST\]',
        ]

        prompt_lower = prompt.lower()

        for pattern in suspicious_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                return False, f"Potential prompt injection detected: pattern '{pattern}'"

        return True, None


# ==================== OUTPUT VALIDATION ====================

class OutputValidator:
    """Validates and sanitizes LLM outputs"""

    def __init__(self, config: LLMGuardrailConfig):
        self.config = config

    def validate_output(self, output: str) -> tuple[bool, Optional[str]]:
        """
        Validate LLM output

        Returns:
            (valid, error_message)
        """
        # Check output length
        if len(output) > self.config.MAX_OUTPUT_LENGTH:
            logger.warning(f"Output too long: {len(output)} characters, truncating to {self.config.MAX_OUTPUT_LENGTH}")
            return True, None  # Still valid, but will be truncated

        # Check for empty output
        if not output or not output.strip():
            return False, "LLM returned empty output"

        return True, None

    def sanitize_output(self, output: str) -> str:
        """Sanitize LLM output for safety"""
        if not self.config.SANITIZE_OUTPUTS:
            return output

        # Truncate if too long
        if len(output) > self.config.MAX_OUTPUT_LENGTH:
            output = output[:self.config.MAX_OUTPUT_LENGTH] + "\n\n[Output truncated]"

        # Remove potential script tags (basic XSS prevention)
        output = re.sub(r'<script[^>]*>.*?</script>', '', output, flags=re.IGNORECASE | re.DOTALL)

        # Remove potential SQL injection patterns (basic)
        suspicious_sql = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r';\s*UPDATE\s+.*\s+SET',
            r'UNION\s+SELECT',
        ]

        for pattern in suspicious_sql:
            if re.search(pattern, output, re.IGNORECASE):
                logger.warning(f"Suspicious SQL pattern detected in output: {pattern}")
                output = re.sub(pattern, '[REDACTED]', output, flags=re.IGNORECASE)

        return output

    def validate_json_output(self, output: str) -> tuple[bool, Optional[str], Optional[Any]]:
        """
        Validate and parse JSON output

        Returns:
            (valid, error_message, parsed_json)
        """
        try:
            parsed = json.loads(output)
            return True, None, parsed
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON output: {str(e)}", None


# ==================== TIMEOUT & RETRY ====================

class TimeoutRetryHandler:
    """Handles timeouts and retries for LLM calls"""

    def __init__(self, config: LLMGuardrailConfig):
        self.config = config

    def with_timeout_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with timeout and retry logic

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.config.MAX_RETRIES):
            try:
                # Set timeout
                timeout = kwargs.pop('timeout', self.config.DEFAULT_TIMEOUT_SECONDS)
                timeout = min(timeout, self.config.MAX_TIMEOUT_SECONDS)

                # Execute with timeout
                result = func(*args, timeout=timeout, **kwargs)

                logger.info(f"LLM call succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"LLM call failed on attempt {attempt + 1}/{self.config.MAX_RETRIES}: {str(e)}")

                # Don't retry on certain errors
                error_str = str(e).lower()
                if any(x in error_str for x in ['invalid api key', 'authentication', 'unauthorized']):
                    logger.error("Authentication error, not retrying")
                    raise

                if any(x in error_str for x in ['content filter', 'policy violation']):
                    logger.error("Content policy violation, not retrying")
                    raise

                # Wait before retry
                if attempt < self.config.MAX_RETRIES - 1:
                    if self.config.EXPONENTIAL_BACKOFF:
                        delay = self.config.RETRY_DELAY_SECONDS * (2 ** attempt)
                    else:
                        delay = self.config.RETRY_DELAY_SECONDS

                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        # All retries failed
        logger.error(f"All {self.config.MAX_RETRIES} retry attempts failed")
        raise last_exception


# ==================== COST ESTIMATOR ====================

class CostEstimator:
    """Estimates costs for LLM API calls"""

    # Pricing per 1M tokens (as of 2024, update as needed)
    PRICING = {
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-4': {'input': 30.00, 'output': 60.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
        'o1': {'input': 15.00, 'output': 60.00},
        'o1-mini': {'input': 3.00, 'output': 12.00},
        'o4': {'input': 5.00, 'output': 15.00},
        'o4-mini': {'input': 1.00, 'output': 4.00},
    }

    @classmethod
    def estimate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost of API call

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (estimated)

        Returns:
            Estimated cost in USD
        """
        if model not in cls.PRICING:
            logger.warning(f"Unknown model '{model}', using gpt-4o pricing as default")
            model = 'gpt-4o'

        pricing = cls.PRICING[model]

        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']

        total_cost = input_cost + output_cost

        logger.debug(f"Cost estimate for {model}: ${total_cost:.6f} ({input_tokens} input + {output_tokens} output tokens)")

        return total_cost


# ==================== MAIN GUARDRAIL CLASS ====================

class LLMGuardrails:
    """
    Comprehensive LLM guardrails for real-time fraud detection

    Features:
    - Rate limiting (requests and tokens)
    - Cost tracking and limits
    - Input validation and sanitization
    - Output validation and sanitization
    - Timeout and retry handling
    - Prompt injection detection
    - PII protection
    """

    def __init__(self, config: Optional[LLMGuardrailConfig] = None):
        self.config = config or LLMGuardrailConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.input_validator = InputValidator(self.config)
        self.output_validator = OutputValidator(self.config)
        self.timeout_handler = TimeoutRetryHandler(self.config)

        logger.info("LLM Guardrails initialized")
        logger.info(f"Rate limits: {self.config.MAX_REQUESTS_PER_MINUTE} req/min, {self.config.MAX_TOKENS_PER_MINUTE} tokens/min")
        logger.info(f"Cost limits: ${self.config.MAX_COST_PER_REQUEST}/req, ${self.config.MAX_COST_PER_HOUR}/hr, ${self.config.MAX_COST_PER_DAY}/day")

    def validate_request(
        self,
        prompt: str,
        model: str,
        expected_output_tokens: int = 2000
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate request before sending to LLM

        Returns:
            (valid, error_message, metadata)
        """
        # Validate model
        valid, error = self.input_validator.validate_model(model)
        if not valid:
            return False, error, None

        # Validate input
        valid, error = self.input_validator.validate_input(prompt, model)
        if not valid:
            return False, error, None

        # Check for prompt injection
        safe, warning = self.input_validator.detect_prompt_injection(prompt)
        if not safe:
            logger.error(f"Prompt injection detected: {warning}")
            return False, warning, None

        # Count tokens
        input_tokens = self.input_validator.count_tokens(prompt, model)

        # Estimate cost
        estimated_cost = CostEstimator.estimate_cost(model, input_tokens, expected_output_tokens)

        # Check cost limits
        valid, error = self.rate_limiter.check_cost_limits(estimated_cost)
        if not valid:
            return False, error, None

        # Check rate limits
        valid, error = self.rate_limiter.check_rate_limit()
        if not valid:
            return False, error, None

        metadata = {
            'input_tokens': input_tokens,
            'estimated_output_tokens': expected_output_tokens,
            'estimated_cost': estimated_cost,
            'model': model
        }

        return True, None, metadata

    def validate_response(self, output: str, expected_json: bool = False) -> tuple[bool, Optional[str], str]:
        """
        Validate and sanitize LLM response

        Returns:
            (valid, error_message, sanitized_output)
        """
        # Validate output
        valid, error = self.output_validator.validate_output(output)
        if not valid:
            return False, error, ""

        # Sanitize output
        sanitized = self.output_validator.sanitize_output(output)

        # Validate JSON if expected
        if expected_json:
            valid, error, _ = self.output_validator.validate_json_output(sanitized)
            if not valid:
                return False, error, sanitized

        return True, None, sanitized

    def record_usage(self, input_tokens: int, output_tokens: int, cost: float):
        """Record successful API call"""
        total_tokens = input_tokens + output_tokens
        self.rate_limiter.record_request(total_tokens, cost)
        logger.info(f"Recorded usage: {total_tokens} tokens, ${cost:.6f}")

    def get_stats(self) -> Dict[str, Any]:
        """Get guardrail statistics"""
        return self.rate_limiter.get_stats()

    def sanitize_for_logging(self, text: str, max_length: int = 200) -> str:
        """Sanitize text for safe logging (remove PII)"""
        if not self.config.BLOCK_PII_IN_LOGS:
            return text[:max_length]

        # Redact potential PII
        sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)  # SSN
        sanitized = re.sub(r'\b\d{16}\b', '[CARD]', sanitized)  # Credit card
        sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', sanitized)  # Email

        return sanitized[:max_length] + ('...' if len(sanitized) > max_length else '')


# ==================== SINGLETON INSTANCE ====================

_guardrails_instance = None

def get_guardrails(config: Optional[LLMGuardrailConfig] = None) -> LLMGuardrails:
    """Get singleton guardrails instance"""
    global _guardrails_instance
    if _guardrails_instance is None:
        _guardrails_instance = LLMGuardrails(config)
    return _guardrails_instance
