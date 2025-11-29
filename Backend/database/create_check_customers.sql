-- Create check_customers table to store payer/customer information for checks
CREATE TABLE IF NOT EXISTS check_customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    payee_name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    phone TEXT,
    email TEXT,
    has_fraud_history BOOLEAN DEFAULT FALSE,
    fraud_count INTEGER DEFAULT 0,
    escalate_count INTEGER DEFAULT 0,
    last_recommendation TEXT,
    last_analysis_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on customer name for fast lookups
CREATE INDEX IF NOT EXISTS idx_check_customers_name ON check_customers(name);

-- Add payer_customer_id foreign key to checks table
ALTER TABLE checks ADD COLUMN IF NOT EXISTS payer_customer_id UUID REFERENCES check_customers(customer_id) ON DELETE SET NULL;

-- Create index on foreign key for performance
CREATE INDEX IF NOT EXISTS idx_checks_payer_customer ON checks(payer_customer_id);
