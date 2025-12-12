-- Add fraud_type column to checks table
ALTER TABLE public.checks 
ADD COLUMN IF NOT EXISTS fraud_type VARCHAR(100) NULL;

-- Add index for fraud_type for faster filtering
CREATE INDEX IF NOT EXISTS idx_checks_fraud_type 
ON public.checks USING btree (fraud_type);

-- Add comment to document the column
COMMENT ON COLUMN public.checks.fraud_type IS 'Primary fraud type detected (e.g., SIGNATURE_FORGERY, AMOUNT_ALTERATION, COUNTERFEIT_CHECK, REPEAT_OFFENDER, STALE_CHECK)';
