-- Drop existing v_money_orders_analysis view and recreate with ai_recommendation
DROP VIEW IF EXISTS v_money_orders_analysis CASCADE;

-- Create v_money_orders_analysis view with selected columns including ai_recommendation and issuer as institute
CREATE VIEW v_money_orders_analysis AS
SELECT
  m.money_order_id,
  m.document_id,
  m.money_order_number,
  m.amount,
  m.issue_date,
  m.issuer_name AS money_order_institute,
  m.purchaser_name,
  m.payee_name,
  m.fraud_risk_score,
  m.model_confidence,
  m.ai_recommendation,
  m.created_at,
  m.timestamp
FROM
  money_orders m
ORDER BY
  m.created_at DESC;
