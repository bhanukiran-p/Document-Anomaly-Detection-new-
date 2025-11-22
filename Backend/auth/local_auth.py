"""
Authentication module for XFORIA DAD API
Handles user login, JWT token generation, and validation
"""

import os
import json
from datetime import datetime, timedelta
from functools import wraps
import jwt
import hashlib
import secrets

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
TOKEN_EXPIRY_HOURS = 24
USERS_FILE = 'users.json'

# Simple in-memory user store (in production, use a real database)
USERS_DB = {}


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


def load_users():
    """Load users from JSON file"""
    global USERS_DB
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                USERS_DB = json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            USERS_DB = {}
    else:
        USERS_DB = {}


def save_users():
    """Save users to JSON file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(USERS_DB, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")


def register_user(email, password):
    """Register a new user"""
    load_users()

    if email in USERS_DB:
        return {'error': 'Email already registered'}, 400

    # Validate email and password
    if not email or '@' not in email:
        return {'error': 'Invalid email'}, 400

    if len(password) < 8:
        return {'error': 'Password must be at least 8 characters'}, 400

    # Create user
    user_id = secrets.token_hex(8)
    USERS_DB[email] = {
        'user_id': user_id,
        'email': email,
        'password_hash': hash_password(password),
        'created_at': datetime.utcnow().isoformat()
    }

    save_users()

    # Generate token
    token = generate_token(email, user_id)

    return {
        'token': token,
        'user': {
            'user_id': user_id,
            'email': email
        }
    }, 201


def login_user(email, password):
    """Login user and return JWT token"""
    load_users()

    if email not in USERS_DB:
        return {'error': 'Invalid email or password'}, 401

    user = USERS_DB[email]

    if not verify_password(user['password_hash'], password):
        return {'error': 'Invalid email or password'}, 401

    # Generate token
    token = generate_token(email, user['user_id'])

    return {
        'token': token,
        'user': {
            'user_id': user['user_id'],
            'email': email
        }
    }, 200


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request, jsonify

        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401

        if not token:
            return jsonify({'error': 'Token missing'}), 401

        payload = verify_token(token)

        if 'error' in payload:
            return jsonify(payload), 401

        return f(payload, *args, **kwargs)

    return decorated
