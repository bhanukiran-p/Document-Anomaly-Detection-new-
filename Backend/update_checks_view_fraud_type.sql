-- Drop the existing view
DROP VIEW IF EXISTS public.v_checks_analysis;

-- Recreate the view with fraud_type column
CREATE VIEW public.v_checks_analysis AS
SELECT
  check_id,
  document_id,
  check_number,
  amount,
  check_date,
  payer_name,
  payee_name,
  bank_name,
  fraud_risk_score,
  model_confidence,
  ai_recommendation,
  fraud_type,  -- Added fraud_type column
  created_at
FROM
  checks c;
