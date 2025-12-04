-- Add fraud_types column to bank_statements table
-- This matches the paystubs table structure

ALTER TABLE bank_statements
  ADD COLUMN IF NOT EXISTS fraud_types TEXT DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN bank_statements.fraud_types IS 'Primary fraud type detected (human-readable label, e.g., "Balance Consistency Violation")';

