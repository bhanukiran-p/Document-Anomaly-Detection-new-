-- Add fraud_type column to money_orders table
ALTER TABLE public.money_orders 
ADD COLUMN IF NOT EXISTS fraud_type VARCHAR(100) NULL;

-- Add index for fraud_type for faster filtering
CREATE INDEX IF NOT EXISTS idx_money_orders_fraud_type 
ON public.money_orders USING btree (fraud_type);

-- Add comment to document the column
COMMENT ON COLUMN public.money_orders.fraud_type IS 'Primary fraud type detected (e.g., SIGNATURE_FORGERY, REPEAT_OFFENDER, COUNTERFEIT_FORGERY, AMOUNT_ALTERATION)';
