"""
Authentication module supporting both local and Supabase auth
"""
# Try to import both local and Supabase auth
try:
    from .local_auth import login_user, register_user
    LOCAL_AUTH_AVAILABLE = True
except ImportError:
    LOCAL_AUTH_AVAILABLE = False
    login_user = None
    register_user = None

try:
    from .supabase_auth import login_user_supabase, register_user_supabase, verify_token
    SUPABASE_AUTH_AVAILABLE = True
except ImportError:
    SUPABASE_AUTH_AVAILABLE = False
    login_user_supabase = None
    register_user_supabase = None
    verify_token = None

__all__ = [
    'login_user',
    'register_user',
    'login_user_supabase',
    'register_user_supabase',
    'verify_token',
    'LOCAL_AUTH_AVAILABLE',
    'SUPABASE_AUTH_AVAILABLE'
]
