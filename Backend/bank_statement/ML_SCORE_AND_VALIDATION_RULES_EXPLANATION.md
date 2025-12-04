# ML Score Calculation & Validation Rules - Detailed Explanation

## Part 1: How ML Models Get the Score (89.1% and 79.8%)

### Step-by-Step Process:

#### 1. **Model Training (What Models Learned)**

The models were trained as **REGRESSORS** (not classifiers):
- **Random Forest Regressor**: Predicts a continuous number (0-100)
- **XGBoost Regressor**: Predicts a continuous number (0-100)

**Training Process:**
```
1. Generated 2000 dummy bank statements with 35 features each
2. For each statement, calculated a "ground truth" risk score (0-100) based on rules:
   - Missing bank name → +30 points
   - Future period → +25 points
   - Balance inconsistency → +30 points
   - Missing critical fields → +40 points
   - etc.
3. Models learned patterns like:
   "If bank_validity=0 AND future_period=1 AND balance_consistency<0.5 
    → Then risk_score should be around 85-100"
```

**What Models Learned:**
- **Pattern Recognition**: Models learned which combinations of features indicate high fraud risk
- **Feature Weights**: Models learned which features are more important (e.g., balance_consistency is more important than transaction_count)
- **Non-linear Relationships**: Models learned complex patterns (e.g., "missing bank + missing account holder + low quality = very high risk")

#### 2. **Feature Extraction (35 Features)**

When a bank statement is uploaded, the system extracts **35 features**:

**Example Features:**
- Feature 1: `bank_validity` = 0.0 (unsupported bank)
- Feature 2: `account_number_present` = 0.0 (missing)
- Feature 3: `account_holder_present` = 0.0 (missing)
- Feature 12: `future_period` = 1.0 (statement is in future)
- Feature 18: `negative_ending_balance` = 0.0 (not negative)
- Feature 19: `balance_consistency` = 0.3 (inconsistent - should be 1.0)
- Feature 25: `critical_missing_count` = 6.0 (6 critical fields missing)
- ... (35 total features)

#### 3. **Feature Scaling**

Before prediction, features are **normalized** using StandardScaler:
```python
# Features are scaled to have mean=0 and std=1
# Example: balance_consistency = 0.3 → scaled to -0.5 (standardized)
X_scaled = scaler.transform([features])
```

**Why Scaling?**
- Different features have different ranges (e.g., balance=1000000, but bank_validity=0 or 1)
- Scaling ensures all features are on the same scale, so models can compare them fairly

#### 4. **Model Prediction**

**Random Forest Model:**
```python
# Model takes 35 scaled features as input
rf_pred = rf_model.predict(X_scaled)[0]
# Output: 89.1 (raw prediction, 0-100 range)
rf_score = rf_pred / 100.0  # Normalize to 0-1: 0.891 = 89.1%
```

**XGBoost Model:**
```python
# Model takes same 35 scaled features as input
xgb_pred = xgb_model.predict(X_scaled)[0]
# Output: 79.8 (raw prediction, 0-100 range)
xgb_score = xgb_pred / 100.0  # Normalize to 0-1: 0.798 = 79.8%
```

**What's Happening Inside Models:**
1. **Random Forest**: 
   - Creates multiple decision trees
   - Each tree asks questions like: "Is bank_validity < 0.5? Is balance_consistency < 0.5?"
   - Each tree votes on the risk score
   - Final score = average of all tree predictions
   - **Result: 89.1%** (most trees agreed this is very high risk)

2. **XGBoost**:
   - Builds trees sequentially, each correcting the previous tree's errors
   - Learns complex patterns through gradient boosting
   - **Result: 79.8%** (slightly lower than RF, but still high risk)

**Why Different Scores?**
- Models have different algorithms and learned slightly different patterns
- Random Forest might weight balance_consistency more heavily
- XGBoost might weight missing fields more heavily
- Both agree it's high risk, but RF is more certain

#### 5. **Ensemble Score**

```python
ensemble_score = (0.4 × 0.891) + (0.6 × 0.798)
                = 0.3564 + 0.4788
                = 0.8352
                = 83.52%
```

**Why Ensemble?**
- Combines strengths of both models
- Random Forest: Good at handling missing data
- XGBoost: Good at finding complex patterns
- Weighted average: 40% RF + 60% XGB (XGBoost is slightly more trusted)

---

## Part 2: Validation Rules (Applied AFTER ML Score)

### What Are Validation Rules?

Validation rules are **hardcoded business rules** that are applied **AFTER** the ML models make their prediction. They ensure certain critical issues **always** result in high risk, even if the ML model didn't catch them.

### When Are They Applied?

**Order of Operations:**
```
1. Extract 35 features from bank statement
   ↓
2. Scale features
   ↓
3. Random Forest predicts: 89.1%
   ↓
4. XGBoost predicts: 79.8%
   ↓
5. Ensemble: 83.52%
   ↓
6. ⚠️ VALIDATION RULES APPLIED HERE ⚠️
   ↓
7. Final adjusted score: 100%
```

### The Validation Rules Code:

```python
def _apply_validation_rules(self, base_score: float, bank_statement_data: Dict, features: List[float]) -> float:
    adjusted_score = base_score  # Start with ML ensemble score (83.52%)
    
    # Extract key features
    bank_valid = features[0]        # Feature 1: bank_validity
    future_period = features[11]     # Feature 12: future_period
    negative_balance = features[17] # Feature 18: negative_ending_balance
    balance_consistency = features[18] # Feature 19: balance_consistency
    critical_missing = features[25]  # Feature 26: critical_missing_count
    
    # Rule 1: Unsupported Bank
    if bank_valid == 0.0:  # Bank not in supported list
        adjusted_score = max(adjusted_score, 0.50)  # Minimum 50%
        # If ML said 30%, this raises it to 50%
        # If ML said 60%, it stays 60% (max keeps higher value)
    
    # Rule 2: Future Period
    if future_period == 1.0:  # Statement date is in the future
        adjusted_score += 0.40  # Add 40% to score
        # 83.52% + 40% = 123.52% → Capped at 100%
    
    # Rule 3: Negative Balance
    if negative_balance == 1.0:  # Ending balance is negative
        adjusted_score += 0.35  # Add 35% to score
    
    # Rule 4: Balance Inconsistency
    if balance_consistency < 0.5:  # Balance doesn't match
        adjusted_score += 0.40  # Add 40% to score
        # Already at 100% from future_period, so stays 100%
    
    # Rule 5: Too Many Missing Fields
    if critical_missing >= 4:  # 4 or more critical fields missing
        adjusted_score += 0.30  # Add 30% to score
    
    # Cap at 100%
    return min(adjusted_score, 1.0)  # Final: 100%
```

### Example Calculation for Your Case:

**Starting Point:**
- ML Ensemble Score: **83.52%** (0.8352)

**Apply Validation Rules:**

1. **Unsupported Bank** (bank_valid = 0.0):
   ```
   adjusted_score = max(0.8352, 0.50) = 0.8352 (no change, already higher)
   ```

2. **Future Period** (future_period = 1.0):
   ```
   adjusted_score = 0.8352 + 0.40 = 1.2352
   → Capped at 1.0 (100%)
   ```

3. **Balance Inconsistency** (balance_consistency < 0.5):
   ```
   adjusted_score = 1.0 + 0.40 = 1.40
   → Capped at 1.0 (100%)
   ```

4. **Critical Missing Fields** (critical_missing >= 4):
   ```
   adjusted_score = 1.0 + 0.30 = 1.30
   → Capped at 1.0 (100%)
   ```

**Final Score: 100%**

### Why Validation Rules Exist?

**Problem Without Validation Rules:**
- ML models might miss critical issues
- Example: ML might predict 30% risk for a statement with future date
- But a future-dated statement is **always** suspicious (can't have a statement from the future!)

**Solution: Validation Rules**
- **Guarantee** certain issues always result in high risk
- **Override** ML predictions when critical issues are detected
- **Add penalties** on top of ML score for specific violations

### Validation Rules vs ML Score:

| Aspect | ML Score | Validation Rules |
|--------|----------|------------------|
| **When Applied** | First (before rules) | After ML prediction |
| **Purpose** | Learn patterns from data | Enforce business rules |
| **Flexibility** | Learns complex patterns | Hardcoded, strict |
| **Can Decrease Score?** | Yes | No (only increases) |
| **Can Override ML?** | No | Yes (can raise score) |

### Why Both Are Needed:

1. **ML Models**: Catch complex, subtle patterns
   - Example: "Many small transactions + round numbers + unusual timing = suspicious"
   - ML learned this from training data

2. **Validation Rules**: Catch obvious, critical issues
   - Example: "Future-dated statement = always suspicious"
   - No ML needed, it's a hard rule

**Together**: ML finds subtle fraud, rules catch obvious fraud

---

## Summary

### ML Score (89.1% and 79.8%):
1. **Extract 35 features** from bank statement
2. **Scale features** to normalize ranges
3. **Random Forest** predicts: 89.1% (learned from training data)
4. **XGBoost** predicts: 79.8% (learned from training data)
5. **Ensemble**: 83.52% (weighted average)

### Validation Rules (Applied After):
1. **Check critical conditions** (unsupported bank, future period, etc.)
2. **Add penalties** to ML score (+40% for future period, +40% for balance inconsistency, etc.)
3. **Cap at 100%** (maximum risk)
4. **Final Score**: 100%

### Key Points:
- **ML models** learn patterns and predict based on what they learned
- **Validation rules** enforce business logic and can override ML
- **Validation rules** are applied **AFTER** ML prediction
- **Validation rules** can only **increase** the score, never decrease it
- **Final score** is the higher of: ML score or ML score + validation penalties

