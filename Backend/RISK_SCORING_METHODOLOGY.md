# ML Risk Scoring Methodology

## Overview
The ML-based risk scoring system calculates a risk score (0-100) for each document, where **higher scores indicate higher risk**. The score is calculated using weighted risk components specific to each document type.

## Risk Score Calculation Process

### Step 1: Feature Extraction
The system extracts features from the document:
- **Field Completeness**: Checks if critical fields are present
- **Numeric Anomalies**: Detects suspicious amounts (e.g., >$100,000 or negative)
- **Date Anomalies**: Identifies future dates or invalid dates
- **Text Quality**: Detects suspicious characters or poor OCR quality
- **Pattern Anomalies**: Identifies unusual patterns (extensible)

### Step 2: Risk Component Calculation
Each document type has specific risk components with individual scores (0-100):

#### For Checks:
- **Missing Critical Fields** (30% weight): bank_name, payee_name, amount_numeric, date
- **Amount Anomalies** (25% weight): Suspicious amounts (>$100k or negative)
- **Date Anomalies** (15% weight): Future dates (70 points) or invalid dates (50 points)
- **Signature Issues** (10% weight): Missing signature (40 points)
- **Text Quality** (10% weight): Poor OCR quality (60 points if >5 suspicious chars)
- **Pattern Anomalies** (10% weight): Unusual patterns

#### For Paystubs:
- **Missing Critical Fields** (25% weight): company_name, employee_name, gross_pay, net_pay, pay_date
- **Amount Anomalies** (20% weight): Suspicious amounts
- **Tax Calculation Errors** (20% weight): Net pay ≥ Gross pay (90 points) - indicates fraud
- **Date Anomalies** (15% weight): Future/invalid dates
- **Text Quality** (10% weight): Poor OCR quality
- **Pattern Anomalies** (10% weight): Unusual patterns

#### For Money Orders:
- **Missing Critical Fields** (30% weight): issuer, amount, payee, serial_number
- **Amount Anomalies** (25% weight): Suspicious amounts
- **Issuer Verification** (15% weight): Unknown issuer (50 points)
- **Date Anomalies** (10% weight): Future/invalid dates
- **Text Quality** (10% weight): Poor OCR quality
- **Pattern Anomalies** (10% weight): Unusual patterns

#### For Bank Statements:
- **Missing Critical Fields** (25% weight): bank_name, account_number, statement_period, balances
- **Transaction Anomalies** (25% weight): No transactions found (60 points)
- **Balance Inconsistencies** (20% weight): Missing balances (50 points)
- **Date Anomalies** (15% weight): Future/invalid dates
- **Text Quality** (10% weight): Poor OCR quality
- **Pattern Anomalies** (5% weight): Unusual patterns

### Step 3: Weighted Risk Score Calculation
The overall risk score is calculated using a weighted sum:

```
Risk Score = Σ (Component_Score × Component_Weight)
```

Example for a Paystub:
- Missing 1 out of 5 critical fields: 20% missing = 20 points × 25% weight = 5.0
- No amount anomalies: 0 points × 20% weight = 0.0
- Tax calculation correct: 0 points × 20% weight = 0.0
- No date anomalies: 0 points × 15% weight = 0.0
- Good text quality: 0 points × 10% weight = 0.0
- No pattern anomalies: 0 points × 10% weight = 0.0
- **Total Risk Score: 5.0** (LOW RISK)

### Step 4: Risk Level Classification
- **LOW RISK**: 0-39 (Green)
- **MEDIUM RISK**: 40-69 (Yellow)
- **HIGH RISK**: 70-100 (Red)

### Step 5: Risk Factor Identification
The system identifies specific risk factors based on component thresholds:
- **Missing Fields** (>30%): High severity
- **Amount Anomalies** (>50 points): High severity
- **Date Anomalies** (>40 points): Medium severity
- **Tax Calculation Errors** (>50 points): High severity (paystubs)
- **Signature Missing** (>30 points): High severity (checks)
- **Issuer Verification** (>30 points): Medium severity (money orders)
- **Transaction Anomalies** (>40 points): Medium severity (bank statements)

### Step 6: Recommendations Generation
Based on the risk score and factors, the system generates actionable recommendations:
- **HIGH RISK (≥70)**: Request additional verification, contact issuing institution, manual review
- **MEDIUM RISK (40-69)**: Verify key information, cross-reference documents
- **LOW RISK (<40)**: Standard verification process

## Example Calculations

### Example 1: Low Risk Paystub (Score: 18.0)
- All critical fields present: 0% missing × 25% = 0.0
- No amount anomalies: 0 × 20% = 0.0
- Tax calculations correct: 0 × 20% = 0.0
- No date issues: 0 × 15% = 0.0
- Good text quality: 0 × 10% = 0.0
- No patterns: 0 × 10% = 0.0
- **Total: 18.0** (Some minor field completeness issues)

### Example 2: High Risk Check (Score: 75.0)
- Missing 2 critical fields: 50% missing × 30% = 15.0
- Suspicious amount (>$100k): 80 × 25% = 20.0
- Future date: 70 × 15% = 10.5
- Missing signature: 40 × 10% = 4.0
- Poor text quality: 60 × 10% = 6.0
- Pattern anomalies: 0 × 10% = 0.0
- **Total: 55.5** (Would be higher with more issues)

## Key Features

1. **Document-Specific Weights**: Each document type has optimized weights based on fraud patterns
2. **Feature-Based Analysis**: Uses extracted data and OCR text quality
3. **Contextual Risk Factors**: Identifies specific issues with severity levels
4. **Actionable Recommendations**: Provides next steps based on risk level
5. **Extensible Design**: Easy to add new risk components or adjust weights

## Future Enhancements

- Machine Learning Model Integration: Can replace weighted scoring with trained ML models
- Historical Pattern Analysis: Compare against known fraud patterns
- Cross-Document Validation: Verify consistency across related documents
- Advanced Pattern Recognition: Detect sophisticated fraud techniques

