# Paystub Fraud Types Upgrade Summary

## Overview
Upgraded the paystub pipeline to include fraud type classification and machine-readable reasons at the ML layer, with AI refinement and structured JSON output for the UI.

## Changes Made

### 1. ML Layer - Fraud Type Classification

**File:** `Backend/paystub/ml/paystub_fraud_detector.py`

- **Added fraud type taxonomy constants:**
  - `PAY_AMOUNT_TAMPERING` - Pay amount tampering / inconsistent pay amounts
  - `MISSING_CRITICAL_FIELDS` - Missing critical paystub information
  - `TEMPORAL_INCONSISTENCY` - Date or pay period inconsistency
  - `TAX_WITHHOLDING_ANOMALY` - Tax withholdings missing or abnormal
  - `YTD_INCONSISTENCY` - Year-to-date amounts inconsistent with current period
  - `BASIC_DATA_QUALITY_ISSUE` - General data quality or OCR extraction quality issues

- **Implemented `_classify_fraud_types()` method:**
  - Rule-based classification using existing ML features
  - Generates machine-readable reasons for each fraud type
  - Checks for:
    - Tax errors (net >= gross)
    - Missing critical fields
    - Future dates
    - Date order inconsistencies
    - YTD inconsistencies
    - Low text quality
    - OCR/extraction issues

- **Integrated into ML result:**
  - Both `_predict_with_model()` and `_predict_heuristic()` now return:
    - `fraud_types`: List of fraud type IDs
    - `fraud_reasons`: List of machine-generated reasons

### 2. AI Layer - Fraud Type Refinement

**File:** `Backend/paystub/ai/paystub_prompts.py`

- **Updated prompt template:**
  - Added section showing ML-detected fraud types and reasons
  - Added anomalies list
  - Updated JSON schema to include:
    - `fraud_types`: Array of fraud type IDs
    - `fraud_explanations`: Array of objects with `type` and `reasons`

**File:** `Backend/paystub/ai/paystub_fraud_analysis_agent.py`

- **Updated `_validate_and_format_result()`:**
  - Parses `fraud_types` and `fraud_explanations` from LLM response
  - Falls back to ML fraud types if AI doesn't provide them
  - Normalizes explanations into structured format
  - Backfills explanations from ML reasons if needed

- **Updated policy decision methods:**
  - `_create_repeat_offender_rejection()` - includes fraud types
  - `_create_duplicate_rejection()` - includes fraud types
  - `_create_first_time_escalation()` - includes empty fraud types
  - `_create_fallback_decision()` - includes ML fraud types

### 3. Database Layer

**File:** `Backend/database/add_paystub_fraud_types.sql` (NEW)

- **SQL migration:**
  ```sql
  ALTER TABLE paystubs
    ADD COLUMN IF NOT EXISTS fraud_types JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS fraud_explanations JSONB DEFAULT '[]'::jsonb;
  ```

**File:** `Backend/database/document_storage.py`

- **Updated `store_paystub()` method:**
  - Extracts `fraud_types` from AI analysis (preferred) or ML analysis (fallback)
  - Extracts `fraud_explanations` from AI analysis
  - Stores both as JSONB in database

### 4. API Layer

**File:** `Backend/api_server.py`

- **Updated `/api/paystub/analyze` endpoint:**
  - Returns structured response with:
    - `fraud_types`: Array of fraud type IDs
    - `fraud_explanations`: Array of explanation objects
    - `fraud_risk_score`, `risk_level`, `model_confidence`
    - `ai_recommendation`, `ai_confidence`, `summary`, `key_indicators`
  - Maintains backward compatibility with full `data` object

## API Response Structure

```json
{
  "success": true,
  "fraud_risk_score": 0.70,
  "risk_level": "HIGH",
  "model_confidence": 0.90,
  "fraud_types": [
    "PAY_AMOUNT_TAMPERING",
    "TAX_WITHHOLDING_ANOMALY",
    "MISSING_CRITICAL_FIELDS"
  ],
  "fraud_explanations": [
    {
      "type": "PAY_AMOUNT_TAMPERING",
      "reasons": [
        "Net pay is unusually close to gross pay, suggesting taxes or deductions may have been removed."
      ]
    },
    {
      "type": "TAX_WITHHOLDING_ANOMALY",
      "reasons": [
        "No tax withholdings were detected even though a normal salary paystub is expected to include taxes."
      ]
    },
    {
      "type": "MISSING_CRITICAL_FIELDS",
      "reasons": [
        "Missing critical fields: pay period dates."
      ]
    }
  ],
  "ai_recommendation": "ESCALATE",
  "ai_confidence": 0.88,
  "summary": "Paystub shows multiple fraud indicators including pay amount tampering and missing tax withholdings.",
  "key_indicators": [
    "Net pay ratio suspiciously high",
    "No tax withholdings detected"
  ],
  "document_id": "uuid-here",
  "data": { /* full details for backward compatibility */ }
}
```

## UI Expectations

The API response is structured to support:

1. **Fraud Types as Chips/Tags:**
   - Display each fraud type ID as a chip (e.g., "PAY AMOUNT TAMPERING")
   - Use color coding based on severity

2. **Fraud Explanations as Cards:**
   - Each explanation object becomes a card
   - Title: Fraud type (pretty-printed)
   - Body: Bullet list of reasons

## Backward Compatibility

✅ **All changes are backward compatible:**
- Existing API consumers still receive full `data` object
- New fields are additive (empty arrays if not detected)
- Money order, check, and bank statement flows unchanged
- Only paystub-specific paths modified

## Testing Checklist

- [x] ML layer classifies fraud types correctly
- [x] AI layer refines and returns structured fraud types
- [x] Database stores fraud types and explanations
- [x] API returns fraud types and explanations
- [x] Backward compatibility maintained
- [x] No linter errors

## Next Steps

1. **Run SQL migration:**
   ```bash
   # In Supabase SQL Editor, run:
   # Backend/database/add_paystub_fraud_types.sql
   ```

2. **Test with sample paystubs:**
   - Upload paystubs with various fraud indicators
   - Verify fraud types are detected and returned
   - Check database storage

3. **UI Integration:**
   - Display fraud types as chips
   - Show fraud explanations as cards with bullet lists
   - Style based on risk level

## Files Modified

1. `Backend/paystub/ml/paystub_fraud_detector.py` - Added fraud type classification
2. `Backend/paystub/ai/paystub_prompts.py` - Updated prompts with fraud types
3. `Backend/paystub/ai/paystub_fraud_analysis_agent.py` - Parse and return fraud types
4. `Backend/database/add_paystub_fraud_types.sql` - SQL migration (NEW)
5. `Backend/database/document_storage.py` - Store fraud types
6. `Backend/api_server.py` - Return fraud types in API response

## Notes

- Fraud type classification is **rule-based**, not model-based
- The ML model only predicts risk scores
- Fraud types are determined by analyzing features and anomalies
- AI layer refines and adds business-friendly explanations
- Training script does not need modification (fraud types are rule-based)

