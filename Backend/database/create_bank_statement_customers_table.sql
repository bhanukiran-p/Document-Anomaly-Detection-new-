-- Create bank_statement_customers table to store account holder/customer information
-- This matches the structure of money_order_customers and check_customers tables

CREATE TABLE IF NOT EXISTS bank_statement_customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    -- Fraud tracking fields
    has_fraud_history BOOLEAN DEFAULT FALSE,
    fraud_count INTEGER DEFAULT 0,
    escalate_count INTEGER DEFAULT 0,
    last_recommendation TEXT,
    last_analysis_date TIMESTAMP,
    total_statements INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups by name
CREATE INDEX IF NOT EXISTS idx_bank_statement_customers_name ON bank_statement_customers(name);

-- Disable Row Level Security (RLS) to allow backend inserts
-- If you need RLS, use the fix_bank_statement_customers_rls.sql file instead
ALTER TABLE bank_statement_customers DISABLE ROW LEVEL SECURITY;

-- If table already exists, add missing columns
ALTER TABLE bank_statement_customers 
ADD COLUMN IF NOT EXISTS last_recommendation TEXT,
ADD COLUMN IF NOT EXISTS last_analysis_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS total_statements INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

