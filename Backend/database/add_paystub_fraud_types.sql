-- Add fraud_types and fraud_explanations columns to paystubs table
-- These columns store ML-detected fraud types and AI-refined explanations

ALTER TABLE paystubs
  ADD COLUMN IF NOT EXISTS fraud_types JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS fraud_explanations JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN paystubs.fraud_types IS 'Array of fraud type IDs detected by ML (e.g., ["PAY_AMOUNT_TAMPERING", "MISSING_CRITICAL_FIELDS"])';
COMMENT ON COLUMN paystubs.fraud_explanations IS 'Array of fraud explanation objects with type and reasons (e.g., [{"type": "PAY_AMOUNT_TAMPERING", "reasons": ["Net pay is greater than gross pay"]}])';

