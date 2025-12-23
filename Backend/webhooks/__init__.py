"""
Webhooks Module
Contains webhook endpoints for external integrations
"""

from .mock_bank_webhook import webhook_bp

__all__ = ['webhook_bp']
