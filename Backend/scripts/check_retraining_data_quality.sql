-- ============================================================================
-- Database Data Quality Assessment for Model Retraining
-- Run these queries to check if your data is ready for automated retraining
-- ============================================================================

-- ============================================================================
-- SECTION 1: OVERALL DATA AVAILABILITY
-- ============================================================================

-- 1.1 Total documents per type
SELECT 'Total Documents by Type' as check_name;
SELECT
    'paystubs' as document_type,
    COUNT(*) as total_documents,
    COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as with_ai_recommendation,
    COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as without_ai_recommendation
FROM paystubs
UNION ALL
SELECT
    'checks' as document_type,
    COUNT(*) as total_documents,
    COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as with_ai_recommendation,
    COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as without_ai_recommendation
FROM checks
UNION ALL
SELECT
    'money_orders' as document_type,
    COUNT(*) as total_documents,
    COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as with_ai_recommendation,
    COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as without_ai_recommendation
FROM money_orders
UNION ALL
SELECT
    'bank_statements' as document_type,
    COUNT(*) as total_documents,
    COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as with_ai_recommendation,
    COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as without_ai_recommendation
FROM bank_statements;


-- ============================================================================
-- SECTION 2: RECOMMENDATION DISTRIBUTION
-- ============================================================================

-- 2.1 Paystubs - Recommendation breakdown
SELECT 'PAYSTUBS - Recommendation Distribution' as check_name;
SELECT
    ai_recommendation,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
    AVG(fraud_risk_score) as avg_fraud_score,
    MIN(fraud_risk_score) as min_fraud_score,
    MAX(fraud_risk_score) as max_fraud_score
FROM paystubs
WHERE ai_recommendation IS NOT NULL
GROUP BY ai_recommendation
ORDER BY count DESC;

-- 2.2 Checks - Recommendation breakdown
SELECT 'CHECKS - Recommendation Distribution' as check_name;
SELECT
    ai_recommendation,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
    AVG(fraud_risk_score) as avg_fraud_score,
    MIN(fraud_risk_score) as min_fraud_score,
    MAX(fraud_risk_score) as max_fraud_score
FROM checks
WHERE ai_recommendation IS NOT NULL
GROUP BY ai_recommendation
ORDER BY count DESC;

-- 2.3 Money Orders - Recommendation breakdown
SELECT 'MONEY ORDERS - Recommendation Distribution' as check_name;
SELECT
    ai_recommendation,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
    AVG(fraud_risk_score) as avg_fraud_score,
    MIN(fraud_risk_score) as min_fraud_score,
    MAX(fraud_risk_score) as max_fraud_score
FROM money_orders
WHERE ai_recommendation IS NOT NULL
GROUP BY ai_recommendation
ORDER BY count DESC;

-- 2.4 Bank Statements - Recommendation breakdown
SELECT 'BANK STATEMENTS - Recommendation Distribution' as check_name;
SELECT
    ai_recommendation,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
    AVG(fraud_risk_score) as avg_fraud_score,
    MIN(fraud_risk_score) as min_fraud_score,
    MAX(fraud_risk_score) as max_fraud_score
FROM bank_statements
WHERE ai_recommendation IS NOT NULL
GROUP BY ai_recommendation
ORDER BY count DESC;


-- ============================================================================
-- SECTION 3: CONFIDENCE SCORE ANALYSIS
-- ============================================================================

-- 3.1 Paystubs - Confidence distribution
SELECT 'PAYSTUBS - Confidence Score Distribution' as check_name;
SELECT
    CASE
        WHEN confidence_score >= 0.90 THEN '0.90-1.00 (Excellent)'
        WHEN confidence_score >= 0.80 THEN '0.80-0.89 (Good)'
        WHEN confidence_score >= 0.70 THEN '0.70-0.79 (Fair)'
        WHEN confidence_score >= 0.60 THEN '0.60-0.69 (Low)'
        ELSE '< 0.60 (Very Low)'
    END as confidence_range,
    ai_recommendation,
    COUNT(*) as count,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(fraud_risk_score), 3) as avg_fraud_score
FROM paystubs
WHERE ai_recommendation IN ('APPROVE', 'REJECT')
  AND confidence_score IS NOT NULL
GROUP BY confidence_range, ai_recommendation
ORDER BY confidence_range DESC, ai_recommendation;

-- 3.2 Checks - Confidence distribution
SELECT 'CHECKS - Confidence Score Distribution' as check_name;
SELECT
    CASE
        WHEN confidence_score >= 0.90 THEN '0.90-1.00 (Excellent)'
        WHEN confidence_score >= 0.80 THEN '0.80-0.89 (Good)'
        WHEN confidence_score >= 0.70 THEN '0.70-0.79 (Fair)'
        WHEN confidence_score >= 0.60 THEN '0.60-0.69 (Low)'
        ELSE '< 0.60 (Very Low)'
    END as confidence_range,
    ai_recommendation,
    COUNT(*) as count,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(fraud_risk_score), 3) as avg_fraud_score
FROM checks
WHERE ai_recommendation IN ('APPROVE', 'REJECT')
  AND confidence_score IS NOT NULL
GROUP BY confidence_range, ai_recommendation
ORDER BY confidence_range DESC, ai_recommendation;

-- 3.3 Money Orders - Confidence distribution
SELECT 'MONEY ORDERS - Confidence Score Distribution' as check_name;
SELECT
    CASE
        WHEN confidence_score >= 0.90 THEN '0.90-1.00 (Excellent)'
        WHEN confidence_score >= 0.80 THEN '0.80-0.89 (Good)'
        WHEN confidence_score >= 0.70 THEN '0.70-0.79 (Fair)'
        WHEN confidence_score >= 0.60 THEN '0.60-0.69 (Low)'
        ELSE '< 0.60 (Very Low)'
    END as confidence_range,
    ai_recommendation,
    COUNT(*) as count,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(fraud_risk_score), 3) as avg_fraud_score
FROM money_orders
WHERE ai_recommendation IN ('APPROVE', 'REJECT')
  AND confidence_score IS NOT NULL
GROUP BY confidence_range, ai_recommendation
ORDER BY confidence_range DESC, ai_recommendation;

-- 3.4 Bank Statements - Confidence distribution
SELECT 'BANK STATEMENTS - Confidence Score Distribution' as check_name;
SELECT
    CASE
        WHEN confidence_score >= 0.90 THEN '0.90-1.00 (Excellent)'
        WHEN confidence_score >= 0.80 THEN '0.80-0.89 (Good)'
        WHEN confidence_score >= 0.70 THEN '0.70-0.79 (Fair)'
        WHEN confidence_score >= 0.60 THEN '0.60-0.69 (Low)'
        ELSE '< 0.60 (Very Low)'
    END as confidence_range,
    ai_recommendation,
    COUNT(*) as count,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(fraud_risk_score), 3) as avg_fraud_score
FROM bank_statements
WHERE ai_recommendation IN ('APPROVE', 'REJECT')
  AND confidence_score IS NOT NULL
GROUP BY confidence_range, ai_recommendation
ORDER BY confidence_range DESC, ai_recommendation;


-- ============================================================================
-- SECTION 4: HIGH-CONFIDENCE DATA AVAILABILITY (≥0.80 threshold)
-- ============================================================================

SELECT 'HIGH-CONFIDENCE DATA (≥0.80) - Training Readiness Assessment' as check_name;
SELECT
    document_type,
    total_usable,
    high_conf_count,
    approve_count,
    reject_count,
    ROUND(fraud_ratio * 100, 1) as fraud_percentage,
    CASE
        WHEN high_conf_count >= 500 THEN 'REAL MODE (100% real data)'
        WHEN high_conf_count >= 100 THEN 'HYBRID MODE (synthetic + real)'
        ELSE 'SYNTHETIC MODE (100% synthetic)'
    END as retraining_mode,
    CASE
        WHEN high_conf_count >= 50 AND approve_count >= 20 AND reject_count >= 20
             AND fraud_ratio >= 0.10 AND fraud_ratio <= 0.60
        THEN 'READY ✓'
        WHEN high_conf_count < 50 THEN 'NOT READY - Insufficient samples'
        WHEN approve_count < 20 THEN 'NOT READY - Too few APPROVE samples'
        WHEN reject_count < 20 THEN 'NOT READY - Too few REJECT samples'
        WHEN fraud_ratio < 0.10 THEN 'WARNING - Fraud ratio too low (<10%)'
        WHEN fraud_ratio > 0.60 THEN 'WARNING - Fraud ratio too high (>60%)'
        ELSE 'CHECK DATA'
    END as status
FROM (
    SELECT
        'paystubs' as document_type,
        COUNT(*) as total_usable,
        COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) as high_conf_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'APPROVE' THEN 1 END) as approve_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END) as reject_count,
        CASE
            WHEN COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) > 0
            THEN COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END)::float /
                 COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END)
            ELSE 0
        END as fraud_ratio
    FROM paystubs
    WHERE ai_recommendation IN ('APPROVE', 'REJECT')

    UNION ALL

    SELECT
        'checks' as document_type,
        COUNT(*) as total_usable,
        COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) as high_conf_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'APPROVE' THEN 1 END) as approve_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END) as reject_count,
        CASE
            WHEN COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) > 0
            THEN COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END)::float /
                 COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END)
            ELSE 0
        END as fraud_ratio
    FROM checks
    WHERE ai_recommendation IN ('APPROVE', 'REJECT')

    UNION ALL

    SELECT
        'money_orders' as document_type,
        COUNT(*) as total_usable,
        COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) as high_conf_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'APPROVE' THEN 1 END) as approve_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END) as reject_count,
        CASE
            WHEN COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) > 0
            THEN COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END)::float /
                 COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END)
            ELSE 0
        END as fraud_ratio
    FROM money_orders
    WHERE ai_recommendation IN ('APPROVE', 'REJECT')

    UNION ALL

    SELECT
        'bank_statements' as document_type,
        COUNT(*) as total_usable,
        COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) as high_conf_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'APPROVE' THEN 1 END) as approve_count,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END) as reject_count,
        CASE
            WHEN COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END) > 0
            THEN COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation = 'REJECT' THEN 1 END)::float /
                 COUNT(CASE WHEN confidence_score >= 0.80 THEN 1 END)
            ELSE 0
        END as fraud_ratio
    FROM bank_statements
    WHERE ai_recommendation IN ('APPROVE', 'REJECT')
) as summary
ORDER BY high_conf_count DESC;


-- ============================================================================
-- SECTION 5: DATA QUALITY ISSUES
-- ============================================================================

-- 5.1 Missing critical fields check
SELECT 'DATA QUALITY - Missing Critical Fields' as check_name;
SELECT
    document_type,
    missing_recommendation,
    missing_fraud_score,
    missing_confidence,
    total_docs
FROM (
    SELECT
        'paystubs' as document_type,
        COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as missing_recommendation,
        COUNT(CASE WHEN fraud_risk_score IS NULL THEN 1 END) as missing_fraud_score,
        COUNT(CASE WHEN confidence_score IS NULL THEN 1 END) as missing_confidence,
        COUNT(*) as total_docs
    FROM paystubs

    UNION ALL

    SELECT
        'checks' as document_type,
        COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as missing_recommendation,
        COUNT(CASE WHEN fraud_risk_score IS NULL THEN 1 END) as missing_fraud_score,
        COUNT(CASE WHEN confidence_score IS NULL THEN 1 END) as missing_confidence,
        COUNT(*) as total_docs
    FROM checks

    UNION ALL

    SELECT
        'money_orders' as document_type,
        COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as missing_recommendation,
        COUNT(CASE WHEN fraud_risk_score IS NULL THEN 1 END) as missing_fraud_score,
        COUNT(CASE WHEN confidence_score IS NULL THEN 1 END) as missing_confidence,
        COUNT(*) as total_docs
    FROM money_orders

    UNION ALL

    SELECT
        'bank_statements' as document_type,
        COUNT(CASE WHEN ai_recommendation IS NULL THEN 1 END) as missing_recommendation,
        COUNT(CASE WHEN fraud_risk_score IS NULL THEN 1 END) as missing_fraud_score,
        COUNT(CASE WHEN confidence_score IS NULL THEN 1 END) as missing_confidence,
        COUNT(*) as total_docs
    FROM bank_statements
) as missing_data;


-- 5.2 Check for confidence_score column existence
SELECT 'SCHEMA CHECK - Confidence Score Column' as check_name;
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('paystubs', 'checks', 'money_orders', 'bank_statements')
  AND column_name = 'confidence_score'
ORDER BY table_name;


-- ============================================================================
-- SECTION 6: RECENT DATA TRENDS (Last 30 days)
-- ============================================================================

-- 6.1 Recent activity check
SELECT 'RECENT ACTIVITY - Last 30 Days' as check_name;
SELECT
    document_type,
    recent_docs,
    recent_with_ai,
    recent_high_conf,
    ROUND(recent_high_conf * 100.0 / NULLIF(recent_with_ai, 0), 1) as high_conf_percentage
FROM (
    SELECT
        'paystubs' as document_type,
        COUNT(*) as recent_docs,
        COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as recent_with_ai,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation IN ('APPROVE', 'REJECT') THEN 1 END) as recent_high_conf
    FROM paystubs
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'

    UNION ALL

    SELECT
        'checks' as document_type,
        COUNT(*) as recent_docs,
        COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as recent_with_ai,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation IN ('APPROVE', 'REJECT') THEN 1 END) as recent_high_conf
    FROM checks
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'

    UNION ALL

    SELECT
        'money_orders' as document_type,
        COUNT(*) as recent_docs,
        COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as recent_with_ai,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation IN ('APPROVE', 'REJECT') THEN 1 END) as recent_high_conf
    FROM money_orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'

    UNION ALL

    SELECT
        'bank_statements' as document_type,
        COUNT(*) as recent_docs,
        COUNT(CASE WHEN ai_recommendation IS NOT NULL THEN 1 END) as recent_with_ai,
        COUNT(CASE WHEN confidence_score >= 0.80 AND ai_recommendation IN ('APPROVE', 'REJECT') THEN 1 END) as recent_high_conf
    FROM bank_statements
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
) as recent_activity;


-- ============================================================================
-- INTERPRETATION GUIDE
-- ============================================================================

/*
SECTION 1: OVERALL DATA AVAILABILITY
- Look for "with_ai_recommendation" count
- Need at least 50 total documents per type for any retraining

SECTION 2: RECOMMENDATION DISTRIBUTION
- Check for presence of both APPROVE and REJECT
- ESCALATE will be excluded from training
- Fraud percentage should be between 10-60% (from REJECT count)

SECTION 3: CONFIDENCE SCORE DISTRIBUTION
- Focus on "0.80-0.89" and "0.90-1.00" rows
- These are what will be used for training (with 0.80 threshold)
- If most data is in lower confidence ranges, consider lowering threshold

SECTION 4: HIGH-CONFIDENCE DATA AVAILABILITY
- This is the KEY section for retraining readiness
- Status column shows if ready:
  * "READY ✓" - Can proceed with retraining
  * "NOT READY" - Insufficient data, use synthetic only
  * "WARNING" - Can train but check fraud ratio
- Retraining mode shows what blend will be used

SECTION 5: DATA QUALITY ISSUES
- Check for missing critical fields
- If confidence_score column doesn't exist, it needs to be added

SECTION 6: RECENT DATA TRENDS
- Shows data accumulation rate
- Helps estimate when you'll have enough data

DECISION MATRIX:
- high_conf_count >= 500: Use 100% real data ✓
- high_conf_count >= 100: Use hybrid (40% synthetic + 60% real) ✓
- high_conf_count < 100: Use 100% synthetic (not ready for real data)

MINIMUM REQUIREMENTS FOR RETRAINING WITH REAL DATA:
- At least 50 high-confidence samples total
- At least 20 high-confidence APPROVE samples
- At least 20 high-confidence REJECT samples
- Fraud ratio between 10-60%
*/
