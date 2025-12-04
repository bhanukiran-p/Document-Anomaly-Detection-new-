# Debug: Model Confidence 0.0% and REPEAT OFFENDER Issue

## Issue 1: Model Confidence is 0.0%

### What's Happening:

1. **Models ARE loaded** (files exist in `bank_statement/ml/models/`)
2. **But confidence is 0.0%** - This means both `rf_score` and `xgb_score` are returning 0.0
3. **Fraud risk score is 50%** - This suggests mock scoring is being used OR models are returning 0.5

### Possible Causes:

1. **Models are regressors returning 0-100 range, but prediction is 0:**
   - If models predict 0, then `rf_score = 0 / 100 = 0.0`
   - But then `ensemble_score = (0.4 * 0.0) + (0.6 * 0.0) = 0.0`, not 0.5
   - So this doesn't explain the 50% score

2. **Exception in `_predict_with_models()` causing fallback to mock:**
   - If there's an error, it falls back to `_predict_mock()`
   - Mock returns `model_confidence: 0.75` but user sees 0.0%
   - Mock returns `fraud_risk_score: 0.5` (50%) which matches

3. **Models aren't actually loaded despite files existing:**
   - `models_loaded = False` even though files exist
   - Using mock scoring which returns 0.75 confidence, but something is overriding it to 0.0

### Solution:

Check backend logs to see:
- Are models actually loading? (`Loaded Random Forest model` or `model not found`)
- Is there an exception in `_predict_with_models()`?
- What are the actual `rf_score` and `xgb_score` values?

---

## Issue 2: REPEAT OFFENDER for First Upload

### What's Happening:

- User uploads statement for **first time**
- System shows **REPEAT OFFENDER** fraud type
- This means `escalate_count > 0`

### Root Cause:

The duplicate record issue we fixed earlier:
1. **First record created** by `get_or_create_customer()` (before fix) with `escalate_count = 0`
2. **Second record created** by `update_customer_fraud_status()` with `escalate_count = 1` (because recommendation was ESCALATE)
3. **When checking customer history**, it gets the **latest record** (second one) with `escalate_count = 1`
4. **AI agent sees `escalate_count = 1`** → triggers REPEAT OFFENDER

### The Problem:

Even though we fixed `get_or_create_customer()` to NOT create records, the **existing duplicate records** in the database are causing this issue.

### Solution:

1. **For new uploads:** The fix should work (only one record created)
2. **For existing data:** Need to clean up duplicate records OR check the FIRST record instead of latest

### Why This Happens:

```python
# In get_customer_history():
response = self.supabase.table('bank_statement_customers')
    .select('*')
    .eq('name', account_holder_name)
    .order('created_at', desc=True)  # Gets LATEST record
    .limit(1)
    .execute()
```

If there are two records:
- Record 1: `escalate_count = 0` (created first)
- Record 2: `escalate_count = 1` (created second, latest)

The query gets Record 2 (latest) → `escalate_count = 1` → REPEAT OFFENDER

---

## Immediate Fixes Needed:

1. **Model Confidence:** Check why models aren't working or why scores are 0.0
2. **REPEAT OFFENDER:** 
   - For new uploads: Should be fixed (only one record)
   - For existing customers: May need to clean up duplicate records OR change logic to check FIRST record, not latest

