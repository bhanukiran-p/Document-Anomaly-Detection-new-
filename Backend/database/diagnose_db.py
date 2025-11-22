"""
Diagnose the users table structure in Supabase
"""

import os
from dotenv import load_dotenv
from supabase_client import get_supabase
import json

load_dotenv()

def diagnose_users_table():
    """Check the current structure of the users table"""
    try:
        supabase = get_supabase()

        print("Attempting to read from users table...")

        try:
            # Try to get any data from the table
            response = supabase.table('users').select('*').limit(1).execute()
            print("✓ Table exists and is accessible")
            print(f"Data: {response.data}")
            print(f"Count: {response.count}")
        except Exception as e:
            error_str = str(e)
            print(f"✗ Error accessing table: {error_str}")

            if "column" in error_str.lower() and "does not exist" in error_str.lower():
                print("\n⚠️  Column missing issue detected!")
                print("The table exists but columns are not defined properly.")

        # Try to get table info via PostgREST
        print("\nAttempting to query table schema...")
        try:
            response = supabase.rpc('get_columns_from_table', {'table_name': 'users'}).execute()
            print(f"Columns: {response.data}")
        except Exception as e:
            print(f"Could not retrieve schema: {str(e)}")

        print("\n" + "="*60)
        print("SOLUTION: Drop and recreate the table")
        print("="*60)
        print("""
Run this SQL in Supabase SQL Editor:

-- Drop the old table if it exists
DROP TABLE IF EXISTS users CASCADE;

-- Create the table with proper columns
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster email lookups
CREATE INDEX idx_users_email ON users(email);

-- Enable RLS (Row Level Security) if needed
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
""")
        print("="*60)

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == '__main__':
    diagnose_users_table()
