"""
Setup script to create the users table in Supabase
Run this once to initialize the database schema
"""

import os
from dotenv import load_dotenv
from supabase_client import get_supabase

# Load environment variables
load_dotenv()

def setup_users_table():
    """Create the users table in Supabase"""
    try:
        supabase = get_supabase()

        print("Setting up users table in Supabase...")

        # Create table using SQL
        # Note: This uses Supabase's SQL editor via the client
        # You may need to run this SQL directly in the Supabase dashboard:

        sql_query = """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create index on email for faster lookups
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """

        print("\n" + "="*60)
        print("SQL SCRIPT TO RUN IN SUPABASE DASHBOARD:")
        print("="*60)
        print(sql_query)
        print("="*60)
        print("\nSteps:")
        print("1. Go to https://app.supabase.com")
        print("2. Select your project 'oizqvffzgrunpdifrmvu'")
        print("3. Go to SQL Editor")
        print("4. Create a new query")
        print("5. Copy and paste the SQL above")
        print("6. Click 'Run'")
        print("\nOnce the table is created, your login/register endpoints will work!")
        print("="*60 + "\n")

        # Try to verify connection
        print("Testing Supabase connection...")
        try:
            # Try to list tables (this may fail depending on permissions)
            response = supabase.table('users').select('*').limit(1).execute()
            print("✓ Connection successful! Users table exists.")
            return True
        except Exception as e:
            if 'does not exist' in str(e).lower() or 'relation' in str(e).lower():
                print("✗ Users table does not exist yet.")
                print("Please run the SQL script above in the Supabase dashboard.\n")
                return False
            else:
                print(f"Connection test: {str(e)}")
                return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == '__main__':
    setup_users_table()
