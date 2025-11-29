-- Create check_customers table to store payer/customer information
-- This normalizes customer data and tracks fraud history for check payers

-- Step 1: Create the new check_customers table
CREATE TABLE IF NOT EXISTS check_customers (
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
CREATE INDEX IF NOT EXISTS idx_check_customers_name ON check_customers(name);

-- Step 2: Add payer_customer_id foreign key to checks table if it doesn't exist
ALTER TABLE checks
ADD COLUMN IF NOT EXISTS payer_customer_id UUID REFERENCES check_customers(customer_id) ON DELETE SET NULL;

-- Step 3: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_checks_payer_customer ON checks(payer_customer_id);

-- Step 4: Add audit timestamp columns to checks table if missing
ALTER TABLE checks
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Step 5: Add duplicate detection index (check_number + payer_name)
CREATE INDEX IF NOT EXISTS idx_checks_duplicate_detection ON checks(check_number, payer_name);
