-- Create paystub_customers table to store employee/customer information for paystubs
-- This matches the structure of bank_statement_customers and check_customers tables

CREATE TABLE IF NOT EXISTS paystub_customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    -- Fraud tracking fields
    has_fraud_history BOOLEAN DEFAULT FALSE,
    fraud_count INTEGER DEFAULT 0,
    escalate_count INTEGER DEFAULT 0,
    last_recommendation TEXT,
    last_analysis_date TIMESTAMP,
    total_paystubs INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups by name
CREATE INDEX IF NOT EXISTS idx_paystub_customers_name ON paystub_customers(name);

-- Disable Row Level Security (RLS) to allow backend inserts
ALTER TABLE paystub_customers DISABLE ROW LEVEL SECURITY;

-- If table already exists, add missing columns
ALTER TABLE paystub_customers 
ADD COLUMN IF NOT EXISTS last_recommendation TEXT,
ADD COLUMN IF NOT EXISTS last_analysis_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS total_paystubs INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;


