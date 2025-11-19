# Understanding Risk Score vs Risk Factors

## The Issue

You may see a **LOW RISK score (e.g., 20.7%)** but still see **HIGH or MEDIUM severity risk factors**. This can be confusing, but it's actually correct behavior. Here's why:

## How Risk Score is Calculated

The **overall risk score** is a **weighted average** of multiple risk components:

### For Checks:
- **Missing Critical Fields** (30% weight): bank_name, payee_name, amount, date
- **Amount Anomalies** (25% weight): Suspicious amounts
- **Date Anomalies** (15% weight): Future/invalid dates
- **Signature Issues** (10% weight): Missing signature
- **Text Quality** (10% weight): Poor OCR quality
- **Pattern Anomalies** (10% weight): Unusual patterns

### Example Calculation:

If a check has:
- ✅ All critical fields present (0% missing) → 0 points × 30% = **0.0**
- ✅ No amount anomalies → 0 points × 25% = **0.0**
- ⚠️ Date anomaly (50 points) → 50 × 15% = **7.5**
- ⚠️ Missing signature (40 points) → 40 × 10% = **4.0**
- ✅ Good text quality → 0 points × 10% = **0.0**
- ✅ No pattern anomalies → 0 points × 10% = **0.0**

**Total Risk Score: 0 + 0 + 7.5 + 4.0 + 0 + 0 = 11.5% (LOW RISK)**

## Why HIGH Severity Factors Can Still Result in LOW Risk

### Example: Missing Signature

- **Component Score**: 40 points (out of 100)
- **Weight**: 10%
- **Contribution to Overall Risk**: 40 × 0.10 = **4.0 points**

Even though missing a signature is a **HIGH severity issue** (it's important!), it only contributes **4%** to the overall risk score because:
1. It has a relatively low weight (10%)
2. Other factors (like missing critical fields) have higher weights (30%)

### Example: Date Anomaly

- **Component Score**: 50 points (out of 100)
- **Weight**: 15%
- **Contribution to Overall Risk**: 50 × 0.15 = **7.5 points**

A date anomaly contributes **7.5%** to the overall risk, which is still relatively low.

## Updated Severity Logic

The system now calculates the **actual contribution** of each factor to the overall risk score and adjusts severity accordingly:

### Severity Thresholds (Based on Contribution to Overall Risk):

- **HIGH Severity**: Contributes **>8%** to overall risk score
- **MEDIUM Severity**: Contributes **3-8%** to overall risk score
- **LOW Severity**: Contributes **<3%** to overall risk score

### Example with Updated Logic:

For a check with 20.7% risk score:
- **Missing Signature**: 40 points × 10% weight = **4.0% contribution** → **MEDIUM severity** (was HIGH)
- **Date Anomaly**: 50 points × 15% weight = **7.5% contribution** → **MEDIUM severity** (correct)
- **Missing Routing**: Not in risk calculation → **LOW severity** (informational only)

## Why This Makes Sense

1. **Individual Issues vs Overall Risk**: A single issue (like missing signature) is important, but if everything else is good, the overall document is still relatively low risk.

2. **Weighted Importance**: The system weights different factors based on their importance:
   - Missing critical fields (30% weight) is more important than missing signature (10% weight)
   - This reflects real-world fraud patterns

3. **Context Matters**: A missing signature on an otherwise perfect check is less risky than a check with multiple missing fields, suspicious amounts, and poor quality.

## What the Risk Factors Tell You

Risk factors identify **specific issues** that need attention, even if they don't push the overall risk score high. They help you:

1. **Understand what's wrong**: See exactly which fields or aspects have issues
2. **Prioritize fixes**: HIGH severity factors need more attention than LOW ones
3. **Take action**: Even with LOW overall risk, you should address HIGH/MEDIUM severity factors

## Recommendations

The recommendations are tailored to the **overall risk score**:
- **LOW RISK (<40%)**: Standard verification, but still address identified issues
- **MEDIUM RISK (40-69%)**: Additional verification needed
- **HIGH RISK (≥70%)**: Requires manual review and extensive verification

## Summary

- **Risk Score**: Overall assessment (weighted average of all factors)
- **Risk Factors**: Individual issues that need attention
- **Severity**: How much each factor contributes to the overall risk
- **Action**: Address HIGH/MEDIUM severity factors even if overall risk is LOW

This design helps you:
1. Get an overall risk assessment (the score)
2. Understand specific issues (the factors)
3. Know which issues are most critical (the severity)
4. Take appropriate action (the recommendations)

