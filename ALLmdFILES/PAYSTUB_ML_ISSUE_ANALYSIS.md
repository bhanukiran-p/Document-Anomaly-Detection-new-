# Paystub ML Model Issue: Why It's Always Predicting ~5%

## Problem Identified

The ML model is consistently predicting **5.0%** fraud risk for paystubs because:

### 1. Training Data Distribution is Skewed

**Analysis of `models/paystub_training_data.csv` (2000 samples):**

```
Risk Score Distribution:
  0-10%:   1,869 samples (93.5%)  ← MOST SAMPLES ARE HERE!
  10-30%:    115 samples (5.8%)
  30-50%:     16 samples (0.8%)
  50-70%:      0 samples (0.0%)   ← NO SAMPLES!
  70-100%:     0 samples (0.0%)   ← NO SAMPLES!

Statistics:
  Min: 0.00%
  Max: 35.30%  ← MAXIMUM IS ONLY 35%, NOT 100%!
  Mean: 3.09%
```

### 2. Perfect Paystubs Get 0-3% Risk

**Perfect paystubs (all fields present, no errors):**
- 1,516 samples out of 2,000 (75.8%)
- Risk Score Range: **0.00% - 2.99%**
- Average Risk: **0.73%**

This explains why real paystubs get ~5% scores - the model learned that complete paystubs = very low risk!

### 3. Training Data Formula is Too Conservative

**Current formula in `train_risk_model.py` (lines 191-195):**

```python
risk_score = (missing_fields / 5) * 25  # Max 25 points
if tax_error:
    risk_score += 20                     # +20 points
risk_score += random.uniform(-3, 3)     # Random noise
risk_score = max(0, min(100, risk_score))
```

**Maximum possible score:**
- Missing all 5 fields: (5/5) * 25 = 25 points
- Tax error: +20 points
- Random max: +3 points
- **TOTAL MAXIMUM: 25 + 20 + 3 = 48 points (48%)**

**But the actual max in training data is only 35.30%!**

### 4. Why Real Paystubs Get 5%

When you upload a real paystub:
- All fields are present (company, employee, gross, net, dates)
- No tax errors (net < gross)
- Missing fields = 0
- Tax error = 0

**Model prediction:**
- Model sees: `[1, 1, 1, 1, 1, 2500, 1672, 0, 0.9, 0]` (perfect paystub)
- Model learned from training: "Perfect paystubs = 0-3% risk"
- Model predicts: **~5%** (slightly higher due to model variance)

**This is actually CORRECT behavior** - the model is working as trained!

## The Real Issue

The model is **too conservative** because:
1. Training data doesn't have enough high-risk samples (50-100%)
2. Training data formula caps maximum at ~48%
3. Model learned that most paystubs are low-risk (which is true for legitimate ones)

## Solution Options

### Option 1: Fix Training Data Generation (Recommended)

Update `train_risk_model.py` to generate more diverse risk scores:

```python
def generate_dummy_paystub_data(self, n_samples=2000, document_type='paystub'):
    # ... existing code ...
    
    # IMPROVED RISK SCORE FORMULA
    risk_score = 0.0
    
    # Missing fields: up to 30 points (increased from 25)
    risk_score += (missing_fields / 5) * 30
    
    # Tax error: +25 points (increased from 20)
    if tax_error:
        risk_score += 25
    
    # Low text quality: up to 15 points (NEW)
    if text_quality < 0.6:
        risk_score += 15
    elif text_quality < 0.8:
        risk_score += 8
    
    # Suspicious amounts: up to 10 points (NEW)
    if gross_pay > 0:
        if gross_pay > 50000:  # Very high salary
            risk_score += 5
        if gross_pay == net_pay:  # No deductions (suspicious)
            risk_score += 10
    
    # Random noise: increased range
    risk_score += random.uniform(-5, 5)
    
    # Cap at 100
    risk_score = max(0, min(100, risk_score))
```

**New maximum possible:**
- Missing fields: 30 points
- Tax error: 25 points
- Low quality: 15 points
- Suspicious amounts: 10 points
- Random max: 5 points
- **TOTAL: 85 points (85%)** - Much better!

### Option 2: Add More High-Risk Samples

Force generate more high-risk samples:

```python
# Generate 20% high-risk samples
if i < n_samples * 0.2:  # First 20% are high-risk
    # Force high-risk scenarios
    missing_fields = random.randint(3, 5)  # 3-5 missing fields
    tax_error = random.random() > 0.3  # 70% have tax errors
    text_quality = random.uniform(0.3, 0.6)  # Low quality
```

### Option 3: Accept Current Behavior (Not Recommended)

The model is working correctly - it's just that legitimate paystubs ARE low-risk. The 5% score is accurate for complete, error-free paystubs.

However, this doesn't help differentiate between:
- Legitimate paystubs (5%)
- Slightly suspicious paystubs (should be 15-30%)
- Highly suspicious paystubs (should be 50-100%)

## Recommendation

**Fix the training data generation** to create a better distribution:
- 0-10%: 40% of samples (legitimate paystubs)
- 10-30%: 30% of samples (slightly suspicious)
- 30-50%: 20% of samples (moderately suspicious)
- 50-100%: 10% of samples (highly suspicious)

This will help the model better differentiate between different risk levels.

