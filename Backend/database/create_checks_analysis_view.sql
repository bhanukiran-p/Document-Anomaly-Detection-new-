-- Drop existing v_checks_analysis view and recreate with ai_recommendation
DROP VIEW IF EXISTS v_checks_analysis CASCADE;

-- Create v_checks_analysis view with selected columns including ai_recommendation
CREATE VIEW v_checks_analysis AS
SELECT
  c.check_id,
  c.document_id,
  c.check_number,
  c.amount,
  c.check_date,
  c.payer_name,
  c.payee_name,
  c.bank_name,
  c.fraud_risk_score,
  c.model_confidence,
  c.ai_recommendation,
  c.created_at,
  c.timestamp
FROM
  checks c
ORDER BY
  c.timestamp DESC;
