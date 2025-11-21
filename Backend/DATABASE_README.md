# Database Documentation

This document provides a comprehensive guide to all database-associated files in the Document Anomaly Detection (DAD) application.

## Overview

The application uses **Supabase** (PostgreSQL-based) as the primary database with a **local JSON file** as a fallback option. All database operations are handled in the Backend directory.

---

## Database Architecture

### Primary Database: Supabase
- **Type**: PostgreSQL (cloud-hosted via Supabase)
- **Authentication**: JWT tokens via ANON_KEY and SERVICE_ROLE_KEY
- **Main Table**: `users`

### Fallback Storage: Local JSON
- **File**: `users.json`
- **Purpose**: Used when Supabase is unavailable
- **Use Case**: Development and testing

---

## Database Files Reference

### 1. [supabase_client.py](Backend/supabase_client.py)

**Purpose**: Manages Supabase database connection and initialization.

**Key Functions**:
- `initialize_supabase()` - Initializes the Supabase client with credentials from environment variables
- `get_supabase()` - Returns the singleton Supabase client instance
- `check_connection()` - Tests the connection to Supabase and returns status

**Environment Variables Required**:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Anonymous key for client-side operations
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for admin operations

**Usage Example**:
```python
from supabase_client import get_supabase

supabase = get_supabase()
response = supabase.table('users').select('*').execute()
```

**Error Handling**:
- Logs all connection errors
- Raises `ValueError` if required environment variables are missing
- Returns connection status dict on check

---

### 2. [auth_supabase.py](Backend/auth_supabase.py)

**Purpose**: Handles user authentication and password management using Supabase.

**Key Functions**:

#### `hash_password(password: str) -> str`
- Hashes passwords using PBKDF2-HMAC-SHA256 with salt
- Salt: 16-byte random hex string
- Iterations: 100,000
- Returns: `"{salt}${hash}"` format

#### `verify_password(stored_hash: str, password: str) -> bool`
- Verifies a password against a stored hash
- Returns: `True` if password matches, `False` otherwise

#### `generate_token(email: str, user_id: str) -> str`
- Generates a JWT token for authenticated users
- Token expiry: 24 hours
- Payload includes: `email`, `user_id`, `iat`, `exp`
- Algorithm: HS256

#### `verify_token(token: str) -> dict`
- Validates and decodes JWT tokens
- Returns: Token payload dict or error dict
- Handles: Expired tokens, invalid tokens

#### `register_user_supabase(email: str, password: str) -> tuple`
- Creates a new user in Supabase
- Validation:
  - Email must be valid (contain '@')
  - Password must be at least 8 characters
  - Email must be unique
- Returns: `(response_dict, status_code)`
- Response includes: `token`, `user` object with `user_id`, `email`, `username`

#### `login_user_supabase(email: str, password: str) -> tuple`
- Authenticates user and returns JWT token
- Looks up user by email
- Verifies password against stored hash
- Returns: `(response_dict, status_code)`
- Status codes: `200` (success), `401` (invalid credentials), `500` (error)

**Database Table Used**: `users`

**Table Columns**:
- `UserID` (TEXT PRIMARY KEY) - Unique user identifier
- `UserName` (TEXT) - Username derived from email
- `Email` (TEXT UNIQUE) - User email address
- `password_hash` (TEXT) - PBKDF2 hashed password with salt
- `created_at` (TIMESTAMP) - Account creation timestamp

**Usage Example**:
```python
from auth_supabase import register_user_supabase, login_user_supabase

# Register
result, status = register_user_supabase('user@example.com', 'password123')

# Login
result, status = login_user_supabase('user@example.com', 'password123')
token = result['token']
```

---

### 3. [setup_supabase.py](Backend/setup_supabase.py)

**Purpose**: Database schema initialization script. Provides instructions for creating the users table.

**Key Function**:
- `setup_users_table()` - Guides user through table creation

**What It Does**:
1. Connects to Supabase
2. Displays SQL script needed to create the users table
3. Provides step-by-step instructions for Supabase dashboard
4. Tests if table exists and reports status

**SQL Schema Created**:
```sql
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

**Manual Setup Steps**:
1. Go to [Supabase Console](https://app.supabase.com)
2. Select your project
3. Navigate to "SQL Editor"
4. Create a new query
5. Copy and paste the SQL schema
6. Click "Run"

**Running the Script**:
```bash
python setup_supabase.py
```

**Note**: The script displays the SQL you need to run manually in the Supabase dashboard. It does not directly execute DDL commands due to Supabase client limitations.

---

### 4. [diagnose_db.py](Backend/diagnose_db.py)

**Purpose**: Database diagnostic and troubleshooting utility.

**Key Function**:
- `diagnose_users_table()` - Checks table existence, accessibility, and structure

**What It Does**:
1. Tests connection to Supabase
2. Attempts to read from the users table
3. Detects common issues:
   - Table doesn't exist
   - Missing or incorrectly defined columns
4. Provides SQL fix scripts

**Common Issues Detected**:
- **Table not found**: Suggests running the setup script
- **Column missing**: Indicates schema mismatch
- **Access denied**: Suggests checking permissions

**Recovery SQL Provided**:
```sql
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

**Running the Script**:
```bash
python diagnose_db.py
```

**Output Example**:
```
✓ Table exists and is accessible
Data: [...]
Count: 5
```

---

### 5. [auth.py](Backend/auth.py)

**Purpose**: Local JSON-based authentication (fallback when Supabase is unavailable).

**Key Functions**:
- `register_user(email, password)` - Creates user in users.json
- `login_user(email, password)` - Authenticates against JSON users database
- `load_users()` - Loads users.json into memory
- `save_users()` - Persists users to JSON file
- `token_required` - Flask decorator for JWT validation on protected endpoints

**Storage File**: `users.json`

**When Used**:
- During development
- When Supabase is unavailable
- As fallback in api_server.py

**Usage Example**:
```python
from auth import register_user, login_user, token_required
from flask import Flask

app = Flask(__name__)

@app.route('/protected')
@token_required
def protected_route():
    return 'Protected content'

# Register
token, status = register_user('user@example.com', 'password123')

# Login
token, status = login_user('user@example.com', 'password123')
```

---

### 6. [users.json](Backend/users.json)

**Purpose**: Local user data storage in JSON format.

**File Structure**:
```json
{
  "user_id_hex_string": {
    "user_id": "user_id_hex_string",
    "email": "user@example.com",
    "password_hash": "salt$hash",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

**Sample Entry**:
```json
{
  "abc123def456": {
    "user_id": "abc123def456",
    "email": "test@example.com",
    "password_hash": "a1b2c3d4$e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6",
    "created_at": "2024-11-15T10:30:00"
  }
}
```

---

### 7. [.env](Backend/.env)

**Purpose**: Environment configuration file for database credentials.

**Database-Related Variables**:
```
SUPABASE_URL=https://oizqvffzgrunpdifrmvu.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SECRET_KEY=your_secret_key_for_jwt_signing
```

**Security Notes**:
- Never commit `.env` to version control
- Use `.env.example` as template
- Keep SECRET_KEY confidential
- Use strong, random SECRET_KEY in production

---

### 8. [.env.example](Backend/.env.example)

**Purpose**: Template for environment configuration.

**Content**:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SECRET_KEY=your_secret_key
```

**Usage**:
1. Copy `.env.example` to `.env`
2. Fill in your actual Supabase credentials
3. Use the values from Supabase console

---

### 9. [api_server.py](Backend/api_server.py)

**Purpose**: Flask API server with integrated database operations.

**Database Integration**:
- Imports and conditionally loads Supabase modules
- Falls back to local auth if Supabase unavailable
- Initializes Supabase connection at startup
- Provides health check endpoint for database status

**Authentication Endpoints**:
- `/register` - Uses `register_user_supabase()` or `register_user()`
- `/login` - Uses `login_user_supabase()` or `login_user()`
- Protected endpoints - Use `token_required` decorator

**Endpoint Examples**:
```python
POST /register
{
  "email": "user@example.com",
  "password": "securepassword123"
}

POST /login
{
  "email": "user@example.com",
  "password": "securepassword123"
}

GET /health
# Returns database connection status
```

---

## Setup Instructions

### Initial Database Setup

#### Step 1: Configure Environment Variables
```bash
cd Backend
cp .env.example .env
# Edit .env with your Supabase credentials
```

#### Step 2: Get Supabase Credentials
1. Go to [Supabase Console](https://app.supabase.com)
2. Create or select your project
3. In "Settings" → "API", copy:
   - Project URL → `SUPABASE_URL`
   - Anon Public Key → `SUPABASE_ANON_KEY`
   - Service Role Secret → `SUPABASE_SERVICE_ROLE_KEY`
4. Generate and add `SECRET_KEY` (use a strong random string)

#### Step 3: Create Database Schema
```bash
# Run setup script
python setup_supabase.py

# The script will display SQL to run
# Go to Supabase SQL Editor and paste the SQL
# Click Run
```

#### Step 4: Verify Setup
```bash
# Run diagnostic script
python diagnose_db.py

# Should output: ✓ Table exists and is accessible
```

---

## Common Tasks

### Register a New User
```python
from auth_supabase import register_user_supabase

response, status = register_user_supabase('newuser@example.com', 'password123')
if status == 201:
    print(f"User registered: {response['user']}")
    print(f"Token: {response['token']}")
```

### Login and Get Token
```python
from auth_supabase import login_user_supabase

response, status = login_user_supabase('user@example.com', 'password123')
if status == 200:
    token = response['token']
    # Use token for authenticated requests
```

### Verify a Token
```python
from auth_supabase import verify_token

payload = verify_token(token)
if 'error' not in payload:
    print(f"Token valid for user: {payload['email']}")
else:
    print(f"Token invalid: {payload['error']}")
```

### Check Database Connection
```python
from supabase_client import check_connection

status = check_connection()
print(status)
# {'status': 'connected', 'message': '...', 'url': '...'}
```

### Diagnose Issues
```bash
python diagnose_db.py
```

---

## Troubleshooting

### Issue: "SUPABASE_URL and SUPABASE_ANON_KEY must be set"
**Solution**: Ensure `.env` file exists in Backend directory with proper credentials

### Issue: "Users table does not exist"
**Solution**: Run `python setup_supabase.py` and follow instructions to create table in Supabase dashboard

### Issue: "Invalid email or password" on login
**Solution**:
- Verify user exists in table
- Check password matches stored hash
- Use `diagnose_db.py` to verify table structure

### Issue: "Token expired"
**Solution**: Re-login to get a new token. Tokens expire after 24 hours.

### Issue: Supabase connection fails
**Solution**:
1. Check SUPABASE_URL is correct
2. Verify SUPABASE_ANON_KEY is valid
3. Check internet connection
4. Run `python diagnose_db.py` for detailed error

---

## Database Security

### Password Security
- Passwords are hashed using PBKDF2-HMAC-SHA256
- 100,000 iterations for key stretching
- 16-byte random salt per password
- Never stored in plaintext

### JWT Token Security
- Tokens use HS256 algorithm
- Signed with SECRET_KEY
- Expire after 24 hours
- Include email and user_id in payload

### Access Control
- Supabase ANON_KEY for client operations
- SERVICE_ROLE_KEY for admin operations
- Row Level Security (RLS) can be enabled on users table
- Email field has unique constraint to prevent duplicates

### Best Practices
1. Change SECRET_KEY in production to a strong random value
2. Use environment variables for all sensitive data
3. Never commit `.env` to version control
4. Regularly rotate Supabase API keys
5. Enable RLS policies for production

---

## File Dependency Map

```
api_server.py
├── supabase_client.py
│   └── .env (SUPABASE_URL, SUPABASE_ANON_KEY)
├── auth_supabase.py
│   └── supabase_client.py
│       └── users table (Supabase)
└── auth.py
    └── users.json

setup_supabase.py
└── supabase_client.py

diagnose_db.py
└── supabase_client.py
```

---

## Summary

| File | Purpose | Type | Dependencies |
|------|---------|------|--------------|
| `supabase_client.py` | DB connection | Module | `.env` |
| `auth_supabase.py` | Supabase auth | Module | `supabase_client.py` |
| `setup_supabase.py` | Schema setup | Script | `supabase_client.py` |
| `diagnose_db.py` | DB troubleshooting | Script | `supabase_client.py` |
| `auth.py` | Fallback auth | Module | `users.json` |
| `users.json` | Local user storage | Data | None |
| `.env` | Configuration | Config | None |
| `.env.example` | Config template | Config | None |

---

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [JWT Introduction](https://jwt.io)
- [PBKDF2 Hash Function](https://en.wikipedia.org/wiki/PBKDF2)
- [Flask Authentication](https://flask.palletsprojects.com/authentication)

---

**Last Updated**: November 2024
**Project**: Document Anomaly Detection (DAD)
