"""
Paystub Database Module
Paystub-specific database operations for customer/employee tracking
Completely independent from other document type database modules
"""

from .paystub_customer_storage import PaystubCustomerStorage

__all__ = ['PaystubCustomerStorage']


