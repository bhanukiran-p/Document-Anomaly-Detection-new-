"""
Database module for Supabase client and setup
"""
try:
    from .supabase_client import get_supabase, check_connection
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    get_supabase = None
    check_connection = None

__all__ = ['get_supabase', 'check_connection', 'SUPABASE_AVAILABLE']
