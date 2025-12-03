# Paystub ML Model - 22 Features Implementation

## Summary

Successfully expanded the paystub fraud detection ML model from **10 features to 22 features** with **NO FALLBACK METHODS**. All features are required and the system will raise errors if any are missing.

## Changes Made

### 1. Feature Extractor (`Backend/paystub/ml/paystub_feature_extractor.py`)

**Updated from 10 to 22 features:**

#### Original 10 Features (Kept):
1. `has_company` - Company name present (binary)
2. `has_employee` - Employee name present (binary)
3. `has_gross` - Gross pay present (binary)
4. `has_net` - Net pay present (binary)
5. `has_date` - Pay period dates present (binary)
6. `gross_pay` - Gross pay amount (numeric, capped at $100k)
7. `net_pay` - Net pay amount (numeric, capped at $100k)
8. `tax_error` - Net >= Gross flag (binary)
9. `text_quality` - OCR quality score (0.5-1.0)
10. `missing_fields_count` - Count of missing fields (0-5)

#### New 12 Features (Added):
11. `ytd_gross` - Year-to-date gross pay (numeric, capped at $500k)
12. `ytd_net` - Year-to-date net pay (numeric, capped at $500k)
13. `ytd_gross_ratio` - YTD gross / current gross (numeric, capped at 100)
14. `ytd_net_ratio` - YTD net / current net (numeric, capped at 100)
15. `has_federal_tax` - Federal tax present (binary)
16. `has_state_tax` - State tax present (binary)
17. `has_social_security` - Social Security tax present (binary)
18. `has_medicare` - Medicare tax present (binary)
19. `total_tax_amount` - Sum of all taxes (numeric, capped at $50k)
20. `tax_to_gross_ratio` - Total tax / gross pay (numeric, 0-1)
21. `net_to_gross_ratio` - Net pay / gross pay (numeric, 0-1)
22. `deduction_percentage` - (Gross - Net) / Gross (numeric, 0-1)

**Key Changes:**
- Added validation to ensure exactly 22 features are extracted
- All features use 0.0 as default (not fallback, but valid feature value)
- No try-except fallbacks - errors are raised if extraction fails

### 2. Training Script (`Backend/training/train_risk_model.py`)

**Updated `generate_dummy_paystub_data()`:**
- Generates all 22 features with realistic distributions
- YTD features: Generated based on risk level (legitimate have proper YTD, suspicious have YTD issues)
- Tax features: Generated based on risk level (legitimate have taxes, suspicious missing taxes)
- Proportion features: Calculated from generated amounts
- Enhanced risk score calculation incorporates all new features

**Updated `prepare_features()`:**
- Feature list expanded to include all 22 features
- Feature order matches extractor exactly

### 3. Fraud Detector (`Backend/paystub/ml/paystub_fraud_detector.py`)

**Added 5 New Fraud Types:**
1. `FABRICATED_DOCUMENT` - Fake paystub with non-existent employer
2. `UNREALISTIC_PROPORTIONS` - Net/gross ratios and tax percentages don't make sense
3. `ALTERED_LEGITIMATE_DOCUMENT` - Real paystub that's been tampered with
4. `YTD_LOGIC_FAILURE` - YTD values don't accumulate logically
5. `ZERO_WITHHOLDING_SUSPICIOUS` - No taxes where they should exist

**Updated `_classify_fraud_types()`:**
- Extracts all 22 features from feature_dict
- Implements detection logic for all 5 new fraud types
- Uses new features (YTD ratios, tax ratios, net/gross ratios) for detection
- NO FALLBACKS - all features must be present

**Updated `_generate_indicators()`:**
- Uses all 22 features to generate fraud indicators
- Checks zero withholding, unrealistic proportions, YTD logic failures
- NO FALLBACKS - uses feature_dict with 0.0 defaults

**Updated `_predict_with_model()`:**
- Validates feature count is exactly 22 (raises error if not)
- Removed fallback for missing model (raises error instead)
- NO FALLBACKS - strict error handling

### 4. No Fallback Policy

**All fallbacks removed:**
- ✅ Feature extraction: Raises error if not exactly 22 features
- ✅ Model loading: Raises error if model not found
- ✅ Model prediction: Raises error if model is None
- ✅ Feature validation: Raises error if feature count mismatch
- ✅ All features use 0.0 as valid default (not fallback)

## Fraud Type Detection Logic

### FABRICATED_DOCUMENT
- Detected when: Missing company + low text quality (< 0.6)
- Or: Missing company + missing employee + 3+ missing fields

### UNREALISTIC_PROPORTIONS
- Detected when:
  - Net > 95% of gross (net_to_gross_ratio > 0.95)
  - Tax < 2% of gross (tax_to_gross_ratio < 0.02) for gross > $1000
  - Deductions > 50% (deduction_percentage > 0.50)

### YTD_LOGIC_FAILURE
- Detected when:
  - YTD gross < current gross (ytd_gross < gross_pay)
  - YTD net < current net (ytd_net < net_pay)
  - YTD ratio < 1.0 (ytd_gross_ratio < 1.0)

### ZERO_WITHHOLDING_SUSPICIOUS
- Detected when:
  - No taxes at all (no federal, state, SS, Medicare) for gross > $1000
  - Missing mandatory FICA taxes (SS or Medicare)
  - Total taxes < 2% of gross (tax_to_gross_ratio < 0.02)

### ALTERED_LEGITIMATE_DOCUMENT
- Detected when:
  - Low text quality (< 0.6) + suspicious ratios (net/gross > 0.90 or tax/gross < 0.05)
  - Low quality (< 0.7) + missing fields + tax errors or high net/gross ratio

## Next Steps

1. **Train the Model:**
   ```bash
   cd Backend
   python training/train_risk_model.py
   ```

2. **Verify Model:**
   - Check that model has 22 features
   - Verify metadata includes all feature names
   - Test with sample paystub data

3. **Test Pipeline:**
   - Test feature extraction with real paystub data
   - Verify all 22 features are extracted
   - Test fraud type detection

## Files Modified

1. `Backend/paystub/ml/paystub_feature_extractor.py` - Added 12 new features
2. `Backend/training/train_risk_model.py` - Updated training data generation
3. `Backend/paystub/ml/paystub_fraud_detector.py` - Added fraud types and detection logic

## Model Requirements

- **Feature Count:** Exactly 22 features (no more, no less)
- **Feature Order:** Must match extractor exactly
- **Model Type:** Random Forest (as before)
- **Scaler:** StandardScaler (if available)

## Testing Checklist

- [ ] Train model with 22 features
- [ ] Verify model loads correctly
- [ ] Test feature extraction with sample data
- [ ] Verify all 22 features are extracted
- [ ] Test fraud type detection
- [ ] Verify no fallbacks exist (errors raised instead)
- [ ] Test with real paystub data
- [ ] Verify API responses include new fraud types

