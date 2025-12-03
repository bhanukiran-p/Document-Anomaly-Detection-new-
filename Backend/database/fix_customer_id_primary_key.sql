-- Migration: Fix money_order_customers table schema to allow multiple rows per customer_id
-- Problem: customer_id was PRIMARY KEY, preventing multiple rows with same customer_id
-- Solution: Create a new row ID as PRIMARY KEY, keep customer_id as indexed column

-- Step 1: Create a new table with correct schema
CREATE TABLE IF NOT EXISTS money_order_customers_new (
    id SERIAL PRIMARY KEY,
    customer_id UUID NOT NULL,
    name TEXT NOT NULL,
    payee_name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    phone TEXT,
    email TEXT,
    -- Fraud tracking fields
    has_fraud_history BOOLEAN DEFAULT FALSE,
    fraud_count INTEGER DEFAULT 0,
    escalate_count INTEGER DEFAULT 0,
    last_recommendation TEXT,
    last_analysis_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Create indexes for performance and payer-based lookups
CREATE INDEX IF NOT EXISTS idx_money_order_customers_new_customer_id ON money_order_customers_new(customer_id);
CREATE INDEX IF NOT EXISTS idx_money_order_customers_new_name ON money_order_customers_new(name);
CREATE INDEX IF NOT EXISTS idx_money_order_customers_new_fraud ON money_order_customers_new(has_fraud_history);
CREATE INDEX IF NOT EXISTS idx_money_order_customers_new_last_analysis ON money_order_customers_new(last_analysis_date DESC);

-- Step 3: Migrate data from old table to new table
INSERT INTO money_order_customers_new (customer_id, name, payee_name, address, city, state, zip_code, phone, email, has_fraud_history, fraud_count, escalate_count, last_recommendation, last_analysis_date, created_at, updated_at)
SELECT customer_id, name, payee_name, address, city, state, zip_code, phone, email, has_fraud_history, fraud_count, escalate_count, last_recommendation, last_analysis_date, created_at, updated_at
FROM money_order_customers
ON CONFLICT DO NOTHING;

-- Step 4: Drop old table
DROP TABLE IF EXISTS money_order_customers CASCADE;

-- Step 5: Rename new table to original name
ALTER TABLE money_order_customers_new RENAME TO money_order_customers;

-- Step 6: Drop old foreign key if it exists (it's now invalid)
ALTER TABLE money_orders
DROP CONSTRAINT IF EXISTS money_orders_purchaser_customer_id_fkey;

-- NOTE: We're NOT recreating the foreign key because customer_id is no longer unique
-- Instead, the application code will enforce the relationship by looking up by customer_id
-- This is necessary because multiple rows can now have the same customer_id

-- Step 7: Verify migration
SELECT COUNT(*) as total_records, COUNT(DISTINCT customer_id) as unique_customers FROM money_order_customers;
