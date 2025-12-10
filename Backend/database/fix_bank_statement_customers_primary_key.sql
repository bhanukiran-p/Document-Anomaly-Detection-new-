-- Migration: Fix bank_statement_customers table schema to allow multiple rows per customer_id
-- Problem: customer_id was PRIMARY KEY, preventing multiple rows with same customer_id
-- Solution: Create a new row ID as PRIMARY KEY, keep customer_id as indexed column
-- This matches the paystub_customers table structure

-- Step 1: Create a new table with correct schema
CREATE TABLE IF NOT EXISTS bank_statement_customers_new (
    id SERIAL PRIMARY KEY,
    customer_id UUID NOT NULL,
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

-- Step 2: Create indexes for performance and customer-based lookups
CREATE INDEX IF NOT EXISTS idx_bank_statement_customers_new_customer_id ON bank_statement_customers_new(customer_id);
CREATE INDEX IF NOT EXISTS idx_bank_statement_customers_new_name ON bank_statement_customers_new(name);
CREATE INDEX IF NOT EXISTS idx_bank_statement_customers_new_fraud ON bank_statement_customers_new(has_fraud_history);
CREATE INDEX IF NOT EXISTS idx_bank_statement_customers_new_last_analysis ON bank_statement_customers_new(last_analysis_date DESC);

-- Step 3: Migrate data from old table to new table
-- Copy all existing records as-is (they will have auto-generated id values)
INSERT INTO bank_statement_customers_new (customer_id, name, has_fraud_history, fraud_count, escalate_count, last_recommendation, last_analysis_date, total_statements, created_at, updated_at)
SELECT 
    customer_id,
    name,
    has_fraud_history,
    fraud_count,
    escalate_count,
    last_recommendation,
    last_analysis_date,
    total_statements,
    created_at,
    updated_at
FROM bank_statement_customers
ON CONFLICT DO NOTHING;

-- Step 4: Drop old table
DROP TABLE IF EXISTS bank_statement_customers CASCADE;

-- Step 5: Rename new table to original name
ALTER TABLE bank_statement_customers_new RENAME TO bank_statement_customers;

-- Step 6: Verify migration
SELECT COUNT(*) as total_records, COUNT(DISTINCT customer_id) as unique_customers FROM bank_statement_customers;

