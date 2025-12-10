# Database Migration Guide: Adding AI Analysis Columns

## Overview
This guide explains how to add the necessary AI analysis columns to your Supabase tables to enable full document analysis storage.

## Required Columns

The following columns need to be added to all four document type tables:

- `ai_recommendation` (TEXT) - AI system's recommendation for the document
- `fraud_risk_score` (NUMERIC) - ML model fraud risk score (0-1)
- `risk_level` (TEXT) - Risk level classification (LOW, MEDIUM, HIGH, CRITICAL)
- `model_confidence` (NUMERIC) - ML model confidence score (0-1)
- `anomaly_count` (INTEGER) - Count of detected anomalies
- `top_anomalies` (JSONB) - Top 5 anomalies in JSON format

For **money_orders table only**, also add:
- `ai_confidence` (NUMERIC) - AI confidence score for money order analysis

## Steps to Add Columns

### Option 1: Supabase Dashboard (Recommended for Users)

1. **Open Supabase Dashboard**
   - Go to https://app.supabase.com
   - Select your project

2. **Navigate to SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New Query"

3. **For money_orders table:**
   ```sql
   ALTER TABLE money_orders
   ADD COLUMN IF NOT EXISTS ai_confidence NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
   ```
   - Click "RUN" button

4. **For checks table:**
   ```sql
   ALTER TABLE checks
   ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
   ```
   - Click "RUN" button

5. **For bank_statements table:**
   ```sql
   ALTER TABLE bank_statements
   ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
   ```
   - Click "RUN" button

6. **For paystubs table:**
   ```sql
   ALTER TABLE paystubs
   ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
   ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
   ```
   - Click "RUN" button

### Option 2: Via SQL File

A pre-made SQL file is included at: `Backend/database/add_ai_columns.sql`

You can copy the contents and paste into Supabase SQL Editor.

## Verification

After running the migrations, verify the columns were added:

```sql
-- Check money_orders table structure
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'money_orders'
ORDER BY column_name;

-- Check checks table structure
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'checks'
ORDER BY column_name;

-- Check bank_statements table structure
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'bank_statements'
ORDER BY column_name;

-- Check paystubs table structure
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'paystubs'
ORDER BY column_name;
```

## Code Changes Made

The following changes have been made to support the new columns:

### 1. Backend/database/document_storage.py
- **store_money_order()** (lines 186-245) - Stores money order with all AI fields
- **store_bank_statement()** (lines 249-323) - Stores bank statement with all AI fields
- **store_paystub()** (lines 327-404) - Stores paystub with all AI fields
- **store_check()** (lines 408-467) - Stores check with all AI fields

Helper methods:
- **_safe_string()** (lines 50-57) - Safely converts values to string, returns None for empty
- **_parse_amount()** (lines 26-40) - Converts amounts to float
- **_parse_date()** (lines 42-48) - Converts dates, handles empty strings as None

### 2. Backend/api_server.py
- Line 19: Imports all four storage functions
- Lines 297-300: Updated check endpoint to store results
- Lines 376-379: Updated paystub endpoint to store results
- Lines 650-653: Updated bank_statement endpoint to store results
- Lines 498-501: Money order endpoint already had storage integrated

## Data Structure Details

### AI Recommendation (TEXT)
Example: "Document appears legitimate. Monitor account for unusual activity."

### Fraud Risk Score (NUMERIC)
- Range: 0.0 to 1.0
- 0.0 = No risk
- 1.0 = Maximum risk

### Risk Level (TEXT)
- Possible values: "LOW", "MEDIUM", "HIGH", "CRITICAL"

### Model Confidence (NUMERIC)
- Range: 0.0 to 1.0
- How confident the ML model is in its prediction

### Anomaly Count (INTEGER)
- Number of anomalies detected in the document
- Example: 3 anomalies detected

### Top Anomalies (JSONB)
Array of up to 5 anomalies. Example:
```json
[
  {
    "type": "Date Mismatch",
    "severity": "MEDIUM",
    "details": "Check date does not match account opening date"
  },
  {
    "type": "Unusual Amount",
    "severity": "LOW",
    "details": "Amount is 50% higher than typical transaction"
  }
]
```

## Testing the Integration

After migrations are complete:

1. **Restart the backend:**
   ```bash
   cd Backend
   python3 api_server.py
   ```

2. **Test a money order upload:**
   ```bash
   curl -X POST http://localhost:5001/api/money-order/analyze \
     -F "file=@/path/to/money_order.png" \
     -F "user_id=test_user"
   ```

3. **Check the response:**
   You should see a `document_id` in the response indicating successful storage.

4. **Verify in Supabase:**
   - Open Supabase Dashboard
   - Go to "Table Editor"
   - Select the respective table (money_orders, checks, etc.)
   - You should see the new row with all AI fields populated

## Troubleshooting

### Error: "Could not find the column..."
- Run the ALTER TABLE statement again to ensure all columns were created
- Check spelling of column names
- Verify you're using the correct table name

### Error: "Object of type float32 is not JSON serializable"
- This is likely from numpy float32 values in ML results
- The code already has a `convert_numpy_types()` function to handle this

### document_id returns as None
- Check the backend logs for detailed error messages
- Ensure the migration columns were actually added
- Verify Supabase credentials are correct

## Column Nullability

All columns have `DEFAULT NULL` to allow documents to be stored even if AI analysis is incomplete.

## Future Enhancements

Consider adding:
- `ai_explanation` (TEXT) - Detailed explanation of AI recommendation
- `model_version` (TEXT) - Version of ML model used
- `analysis_timestamp` (TIMESTAMP) - When the analysis was performed
- `confidence_breakdown` (JSONB) - Detailed confidence scores for each component
