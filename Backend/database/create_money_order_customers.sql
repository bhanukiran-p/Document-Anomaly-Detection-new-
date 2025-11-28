-- Create money_order_customers table to store purchaser/customer information
-- This normalizes customer data and removes the unique constraint on money_order_number

-- Step 1: Create the new money_order_customers table
CREATE TABLE IF NOT EXISTS money_order_customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- Create index for faster lookups by name
CREATE INDEX IF NOT EXISTS idx_money_order_customers_name ON money_order_customers(name);

-- Step 2: Remove the UNIQUE constraint on money_order_number (allows multiple uploads of same money order)
-- Note: First, you may need to drop the constraint if it exists
DO $$
BEGIN
    ALTER TABLE money_orders DROP CONSTRAINT IF EXISTS money_orders_new_money_order_number_key;
EXCEPTION WHEN undefined_object THEN
    NULL;
END $$;

-- Step 3: Add customer_id foreign key to money_orders table if it doesn't exist
ALTER TABLE money_orders
ADD COLUMN IF NOT EXISTS purchaser_customer_id UUID REFERENCES money_order_customers(customer_id) ON DELETE SET NULL;

-- Step 4: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_money_orders_purchaser_customer ON money_orders(purchaser_customer_id);

-- Step 5: Add audit timestamp columns if missing
ALTER TABLE money_orders
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
