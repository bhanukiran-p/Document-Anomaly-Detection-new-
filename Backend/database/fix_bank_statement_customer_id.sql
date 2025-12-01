-- Fix bank_statements table to allow NULL customer_id
-- This allows storing bank statements even when account holder name is missing

-- Make customer_id nullable (if it's currently NOT NULL)
ALTER TABLE bank_statements 
ALTER COLUMN customer_id DROP NOT NULL;

-- Add comment explaining why customer_id can be NULL
COMMENT ON COLUMN bank_statements.customer_id IS 'Customer ID from bank_statement_customers table. Can be NULL if account holder name is missing from statement.';

