"""
Supabase Authentication Module
Handles user registration and login using Supabase database
Adapts to existing table schema with UserID, UserName, Email columns
"""

import hashlib
import secrets
from datetime import datetime, timedelta
import jwt
import os
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
TOKEN_EXPIRY_HOURS = 24
USERS_TABLE = 'users'


def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    try:
        salt, pwd_hash = stored_hash.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return new_hash.hex() == pwd_hash
    except Exception:
        return False


def generate_token(email, user_id):
    """Generate JWT token"""
    payload = {
        'email': email,
        'user_id': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}


def register_user_supabase(email, password):
    """Register a new user in Supabase"""
    try:
        from database.supabase_client import get_supabase
        supabase = get_supabase()

        # Validate email and password
        if not email or '@' not in email:
            return {'error': 'Invalid email'}, 400

        if len(password) < 8:
            return {'error': 'Password must be at least 8 characters'}, 400

        # Extract username from email (part before @)
        username = email.split('@')[0]

        # Check if user already exists (using Email column name)
        try:
            existing_user = supabase.table(USERS_TABLE).select('UserID').eq('Email', email).execute()
            if existing_user.data and len(existing_user.data) > 0:
                return {'error': 'Email already registered'}, 400
        except Exception as e:
            logger.warning(f"Error checking existing user: {e}")
            pass

        # Hash the password
        password_hash = hash_password(password)

        # Create user in Supabase using existing schema
        user_id = secrets.token_hex(8)
        user_data = {
            'UserID': user_id,
            'UserName': username,
            'Email': email,
            'password_hash': password_hash,
            'created_at': datetime.utcnow().isoformat()
        }

        response = supabase.table(USERS_TABLE).insert(user_data).execute()

        if response.data:
            # Generate JWT token
            token = generate_token(email, user_id)

            return {
                'token': token,
                'user': {
                    'user_id': user_id,
                    'email': email,
                    'username': username
                }
            }, 201
        else:
            return {'error': 'Failed to create user'}, 500

    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return {'error': f'Registration failed: {str(e)}'}, 500


def login_user_supabase(username_or_email, password):
    """Login user with username OR email and return JWT token"""
    try:
        from database.supabase_client import get_supabase
        supabase = get_supabase()

        # Try to find user by username first, then by email
        response = None

        # Check if input contains @ (likely email)
        if '@' in username_or_email:
            # Try email lookup first
            response = supabase.table(USERS_TABLE).select('*').eq('Email', username_or_email).execute()
        else:
            # Try username lookup first
            response = supabase.table(USERS_TABLE).select('*').eq('UserName', username_or_email).execute()

        # If not found and doesn't contain @, try as email anyway (edge case)
        if (not response or not response.data or len(response.data) == 0) and '@' not in username_or_email:
            response = supabase.table(USERS_TABLE).select('*').eq('Email', username_or_email).execute()

        # If still not found and contains @, try as username (edge case)
        if (not response or not response.data or len(response.data) == 0) and '@' in username_or_email:
            response = supabase.table(USERS_TABLE).select('*').eq('UserName', username_or_email).execute()

        if not response or not response.data or len(response.data) == 0:
            return {'error': 'Invalid username or password'}, 401

        user = response.data[0]

        # Verify password
        password_hash = user.get('password_hash')
        if not password_hash or not verify_password(password_hash, password):
            return {'error': 'Invalid username or password'}, 401

        # Generate token using email
        user_email = user.get('Email', '')
        token = generate_token(user_email, user['UserID'])

        return {
            'token': token,
            'user': {
                'user_id': user['UserID'],
                'email': user_email,
                'username': user.get('UserName', user_email.split('@')[0] if user_email else '')
            }
        }, 200

    except Exception as e:
        logger.error(f"Error logging in user: {str(e)}")
        return {'error': f'Login failed: {str(e)}'}, 500
