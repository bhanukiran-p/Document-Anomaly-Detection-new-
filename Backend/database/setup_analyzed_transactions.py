"""
Setup script to create the analyzed_real_time_trn table in Supabase
Run this to initialize the table for storing analyzed real-time transactions
"""

import os
from dotenv import load_dotenv
from supabase_client import get_supabase

# Load environment variables
load_dotenv()

def setup_analyzed_transactions_table():
    """Create the analyzed_real_time_trn table in Supabase"""
    try:
        supabase = get_supabase()

        print("Setting up analyzed_real_time_trn table in Supabase...")

        # SQL to create the table
        sql_query = """
        -- Drop the existing table if it exists (to recreate with new schema)
        DROP TABLE IF EXISTS analyzed_real_time_trn CASCADE;

        CREATE TABLE analyzed_real_time_trn (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            transaction_id TEXT NOT NULL,
            customer_id TEXT,
            amount DECIMAL(15, 2),
            merchant TEXT,
            category TEXT,
            timestamp TIMESTAMP,
            location TEXT,
            account_balance DECIMAL(15, 2),
            card_type TEXT,
            is_fraud INTEGER DEFAULT 0,
            added_at TIMESTAMP,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            home_city TEXT,
            home_country TEXT,
            transaction_city TEXT,
            transaction_country TEXT,
            login_city TEXT,
            login_country TEXT,
            transaction_type TEXT,
            currency TEXT,
            description TEXT,
            is_by_check BOOLEAN,
            account_number NUMERIC,
            swift_bic TEXT,
            receiveraccount NUMERIC,
            receiverswift TEXT,
            balanceafter DECIMAL(15, 2),
            avgdailybalance DECIMAL(15, 2),

            -- Additional analysis fields for tracking
            analysis_id TEXT,
            batch_id TEXT,
            model_type TEXT,
            confidence_score DECIMAL(5, 4),
            fraud_probability DECIMAL(5, 4),
            fraud_reason TEXT,
            fraud_reason_detail TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for faster queries
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_transaction_id ON analyzed_real_time_trn(transaction_id);
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_customer_id ON analyzed_real_time_trn(customer_id);
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_is_fraud ON analyzed_real_time_trn(is_fraud);
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_timestamp ON analyzed_real_time_trn(timestamp);
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_analysis_date ON analyzed_real_time_trn(analysis_date);
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_batch_id ON analyzed_real_time_trn(batch_id);
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_added_at ON analyzed_real_time_trn(added_at);
        CREATE INDEX IF NOT EXISTS idx_analyzed_trn_currency ON analyzed_real_time_trn(currency);
        """

        print("\n" + "="*60)
        print("SQL SCRIPT TO RUN IN SUPABASE DASHBOARD:")
        print("="*60)
        print(sql_query)
        print("="*60)
        print("\nSteps:")
        print("1. Go to https://app.supabase.com")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Create a new query")
        print("5. Copy and paste the SQL above")
        print("6. Click 'Run'")
        print("\nOnce the table is created, real-time analysis results will be stored!")
        print("="*60 + "\n")

        # Try to verify connection
        print("Testing Supabase connection...")
        try:
            # Try to list tables (this may fail depending on permissions)
            response = supabase.table('analyzed_real_time_trn').select('*').limit(1).execute()
            print("✓ Connection successful! Table exists.")
            return True
        except Exception as e:
            if 'does not exist' in str(e).lower() or 'relation' in str(e).lower():
                print("✗ analyzed_real_time_trn table does not exist yet.")
                print("Please run the SQL script above in the Supabase dashboard.\n")
                return False
            else:
                print(f"Connection test: {str(e)}")
                return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == '__main__':
    setup_analyzed_transactions_table()
