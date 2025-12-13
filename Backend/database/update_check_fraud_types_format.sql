-- Update existing check fraud_type values to use spaces instead of underscores
-- This converts formats like "SIGNATURE_FORGERY" to "Signature Forgery"

UPDATE checks
SET fraud_type = CASE
    WHEN fraud_type = 'SIGNATURE_FORGERY' THEN 'Signature Forgery'
    WHEN fraud_type = 'AMOUNT_ALTERATION' THEN 'Amount Alteration'
    WHEN fraud_type = 'COUNTERFEIT_CHECK' THEN 'Counterfeit Check'
    WHEN fraud_type = 'REPEAT_OFFENDER' THEN 'Repeat Offender'
    WHEN fraud_type = 'STALE_CHECK' THEN 'Stale Check'
    ELSE fraud_type  -- Keep as is if already formatted or NULL
END
WHERE fraud_type IS NOT NULL
  AND fraud_type LIKE '%\_%' ESCAPE '\';  -- Only update values with underscores

-- Verify the update
SELECT DISTINCT fraud_type FROM checks WHERE fraud_type IS NOT NULL ORDER BY fraud_type;
