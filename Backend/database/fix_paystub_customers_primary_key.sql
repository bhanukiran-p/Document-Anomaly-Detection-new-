-- Migration: Fix paystub_customers table schema to allow multiple rows per customer_id
-- Problem: customer_id was PRIMARY KEY, preventing multiple rows with same customer_id
-- Solution: Create a new row ID as PRIMARY KEY, keep customer_id as indexed column
-- This matches the money_order_customers table structure

-- Step 1: Create a new table with correct schema
CREATE TABLE IF NOT EXISTS paystub_customers_new (
    id SERIAL PRIMARY KEY,
    customer_id UUID NOT NULL,
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

-- Step 2: Create indexes for performance and employee-based lookups
CREATE INDEX IF NOT EXISTS idx_paystub_customers_new_customer_id ON paystub_customers_new(customer_id);
CREATE INDEX IF NOT EXISTS idx_paystub_customers_new_name ON paystub_customers_new(name);
CREATE INDEX IF NOT EXISTS idx_paystub_customers_new_fraud ON paystub_customers_new(has_fraud_history);
CREATE INDEX IF NOT EXISTS idx_paystub_customers_new_last_analysis ON paystub_customers_new(last_analysis_date DESC);

-- Step 3: Migrate data from old table to new table
-- Copy all existing records as-is (they will have auto-generated id values)
INSERT INTO paystub_customers_new (customer_id, name, has_fraud_history, fraud_count, escalate_count, last_recommendation, last_analysis_date, total_paystubs, created_at, updated_at)
SELECT 
    customer_id,
    name,
    has_fraud_history,
    fraud_count,
    escalate_count,
    last_recommendation,
    last_analysis_date,
    total_paystubs,
    created_at,
    updated_at
FROM paystub_customers
ON CONFLICT DO NOTHING;

-- Step 4: Drop old table
DROP TABLE IF EXISTS paystub_customers CASCADE;

-- Step 5: Rename new table to original name
ALTER TABLE paystub_customers_new RENAME TO paystub_customers;

-- Step 6: Verify migration
SELECT COUNT(*) as total_records, COUNT(DISTINCT customer_id) as unique_customers FROM paystub_customers;

