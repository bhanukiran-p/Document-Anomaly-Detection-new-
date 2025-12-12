"""
API Routes Module
Contains all Flask blueprints for modular API organization
"""

# Currently implemented blueprints
from .health_routes import health_bp
from .auth_routes import auth_bp
from .check_routes import check_bp
from .paystub_routes import paystub_bp
from .money_order_routes import money_order_bp
from .bank_statement_routes import bank_statement_bp

# TODO: Create these blueprints
# from .document_routes import document_bp
# from .real_time_routes import real_time_bp

__all__ = [
    'health_bp',
    'auth_bp',
    'check_bp',
    'paystub_bp',
    'money_order_bp',
    'bank_statement_bp',
    # 'document_bp',  # TODO
    # 'real_time_bp'  # TODO
]
