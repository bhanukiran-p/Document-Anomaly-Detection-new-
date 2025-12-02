-- Query to check for repeat purchasers in money_orders table
-- Repeat purchasers = purchasers with multiple MOs AND average risk >= 50%

SELECT 
    purchaser_name,
    COUNT(*) as mo_count,
    ROUND(AVG(fraud_risk_score) * 100, 1) as avg_risk_percent,
    ROUND(MAX(fraud_risk_score) * 100, 1) as max_risk_percent,
    ROUND(MIN(fraud_risk_score) * 100, 1) as min_risk_percent,
    SUM(CASE WHEN fraud_risk_score >= 0.75 THEN 1 ELSE 0 END) as high_risk_count,
    STRING_AGG(DISTINCT money_order_institute, ', ') as issuers
FROM money_orders
WHERE purchaser_name IS NOT NULL 
    AND purchaser_name != ''
    AND purchaser_name != 'Unknown'
GROUP BY purchaser_name
HAVING COUNT(*) > 1  -- Multiple money orders
    AND AVG(fraud_risk_score) >= 0.50  -- Average risk >= 50%
ORDER BY avg_risk_percent DESC, mo_count DESC;

-- Alternative: Show ALL purchasers with multiple MOs (regardless of risk)
-- Uncomment to see all repeat purchasers even if avg risk < 50%

/*
SELECT 
    purchaser_name,
    COUNT(*) as mo_count,
    ROUND(AVG(fraud_risk_score) * 100, 1) as avg_risk_percent,
    ROUND(MAX(fraud_risk_score) * 100, 1) as max_risk_percent,
    SUM(CASE WHEN fraud_risk_score >= 0.75 THEN 1 ELSE 0 END) as high_risk_count,
    STRING_AGG(DISTINCT money_order_institute, ', ') as issuers
FROM money_orders
WHERE purchaser_name IS NOT NULL 
    AND purchaser_name != ''
    AND purchaser_name != 'Unknown'
GROUP BY purchaser_name
HAVING COUNT(*) > 1
ORDER BY mo_count DESC, avg_risk_percent DESC;
*/

-- Check specific purchaser (e.g., JENNIFER LEE)
/*
SELECT 
    money_order_id,
    purchaser_name,
    money_order_number,
    amount,
    money_order_institute,
    ROUND(fraud_risk_score * 100, 1) as risk_percent,
    ai_recommendation,
    created_at
FROM money_orders
WHERE UPPER(purchaser_name) LIKE '%JENNIFER LEE%'
ORDER BY created_at DESC;
*/

