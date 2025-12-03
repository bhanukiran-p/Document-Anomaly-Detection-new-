# Check Customers Database Migration Guide

## Overview

This migration creates the `check_customers` table in Supabase to track check payer/customer information and fraud history. This enables the system to implement the fraud tracking logic where:

- **First fraud detection** → Recommendation: `ESCALATE`
- **Second occurrence** (escalate_count > 0) → Recommendation: `REJECT`

## Database Schema

The `check_customers` table tracks:
- **name** (UNIQUE): Customer/payer name
- **fraud_count**: Number of fraudulent checks detected
- **escalate_count**: Number of escalations (second-time offenders trigger auto-reject)
- **has_fraud_history**: Boolean flag for quick lookups
- **last_recommendation**: Most recent AI recommendation
- **Additional fields**: payee_name, address, city, state, zip_code, phone, email

## How It Works

1. When a check is submitted, the system looks up the payer name in `check_customers`
2. If new customer → Database creates a new record
3. System retrieves customer's fraud_count and escalate_count
4. AI decision engine applies these rules (from `check/ai/check_prompts.py` lines 80-83):
   - If `escalate_count > 0` → **AUTO-REJECT** (repeat offender policy)
   - If `fraud_count > 0` and risk ≥ 30% → **REJECT**
   - If new customer with 30-95% risk → **ESCALATE**
5. After decision:
   - If recommendation = `REJECT` → fraud_count incremented
   - If recommendation = `ESCALATE` → escalate_count incremented

## Migration Steps

### Step 1: Create the Table in Supabase

1. Go to your Supabase dashboard
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy and execute the SQL from: `Backend/database/create_check_customers.sql`

The SQL includes:
```sql
-- Create check_customers table
CREATE TABLE IF NOT EXISTS check_customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    payee_name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    phone TEXT,
    email TEXT,
    has_fraud_history BOOLEAN DEFAULT FALSE,
    fraud_count INTEGER DEFAULT 0,
    escalate_count INTEGER DEFAULT 0,
    last_recommendation TEXT,
    last_analysis_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast customer lookups
CREATE INDEX IF NOT EXISTS idx_check_customers_name ON check_customers(name);

-- Add foreign key to checks table
ALTER TABLE checks ADD COLUMN IF NOT EXISTS payer_customer_id UUID
    REFERENCES check_customers(customer_id) ON DELETE SET NULL;

-- Create index on foreign key
CREATE INDEX IF NOT EXISTS idx_checks_payer_customer ON checks(payer_customer_id);
```

### Step 2: Verify Table Creation

1. In Supabase SQL Editor, run:
```sql
SELECT * FROM check_customers LIMIT 1;
```

You should see the table structure with the columns defined above.

### Step 3: Disable Mock Mode (Backend Code)

The backend code in `Backend/check/ai/check_tools.py` currently has mock data fallback. Once the table is created, the code will automatically use the real database:

- **Lines 29-36**: Initialization tries to load `CheckCustomerStorage`
- **Lines 50-54**: If database available, uses real data; otherwise falls back to mock
- **Lines 85-89**: Duplicate check uses real database

No code changes needed - the database connection will be detected automatically!

### Step 4: Test the Integration

1. Upload a check with payer name "Charles Wilson"
2. System should:
   - Look up "Charles Wilson" in check_customers (not found, so default empty values)
   - Proceed with normal fraud analysis
   - Create a new record if fraud is detected

3. Upload the same check again:
   - System should find existing record
   - Apply escalation/rejection logic based on fraud history

## File References

- **Migration SQL**: [Backend/database/create_check_customers.sql](Backend/database/create_check_customers.sql)
- **Database Module**: [Backend/database/check_customer_storage.py](Backend/database/check_customer_storage.py)
- **Data Access Tools**: [Backend/check/ai/check_tools.py](Backend/check/ai/check_tools.py)
- **Decision Logic**: [Backend/check/ai/check_prompts.py](Backend/check/ai/check_prompts.py) (lines 75-170)

## Backend Code Flow

```
User uploads check
    ↓
[check_extractor.py] Extracts check data
    ↓
[check_tools.py] _get_customer_info() calls CheckCustomerStorage
    ↓
[check_customer_storage.py] Queries check_customers table
    ↓
Returns: {fraud_count, escalate_count, has_fraud_history, ...}
    ↓
[check_fraud_analysis_agent.py] Uses customer history in AI decision
    ↓
[check_prompts.py] Decision rules:
   - escalate_count > 0 → REJECT
   - fraud_count > 0 + risk ≥ 30% → REJECT
   - New customer + 30-95% risk → ESCALATE
    ↓
[check_customer_storage.py] update_customer_fraud_status()
   - Increments fraud_count or escalate_count based on decision
    ↓
Final recommendation returned to frontend
```

## Implementation Details

### CheckCustomerStorage Class Methods

The `check_customer_storage.py` file (lines 1-226) provides these methods:

- **`get_or_create_customer(name)`**: Find or create customer record
- **`get_customer_history(name)`**: Get fraud/escalation counts for a payer
- **`update_customer_fraud_status(recommendation, ...)`**: Update counters after AI decision
- **`check_duplicate_check(check_number, payer_name)`**: Detect duplicate submissions
- **`link_check_to_customer(check_id, payer_customer_id)`**: Create audit trail

### Decision Rules Summary

From `check_prompts.py` lines 75-170:

| Customer Type | Risk Score | Decision |
|---|---|---|
| Escalate_count > 0 (repeat offender) | Any | **REJECT** (auto) |
| Fraud_count > 0 (fraud history) | ≥ 30% | **REJECT** |
| Fraud_count > 0 | < 30% | **APPROVE** |
| New customer | ≥ 95% | **ESCALATE** |
| New customer | 30-95% | **ESCALATE** |
| New customer | < 30% | **APPROVE** |
| Clean history | > 85% | **REJECT** |
| Clean history | 30-85% | **ESCALATE** |
| Clean history | < 30% | **APPROVE** |

## Status

- ✅ SQL migration file created: `Backend/database/create_check_customers.sql`
- ✅ Python storage class implemented: `Backend/database/check_customer_storage.py`
- ✅ Data access tools ready: `Backend/check/ai/check_tools.py`
- ⏳ **PENDING**: Execute SQL migration in Supabase dashboard
- ⏳ **PENDING**: Restart backend to load from database

## Next Steps

1. **Execute the migration** in Supabase SQL Editor
2. **Restart the backend** server
3. **Upload a test check** to verify database is being queried
4. **Monitor logs** for "CheckCustomerStorage" initialization messages

## Troubleshooting

### Issue: "CheckDataAccessTools in mock mode"
- **Cause**: Backend couldn't connect to database
- **Solution**: Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set
- **Check**: Look at backend logs during startup

### Issue: "table check_customers does not exist"
- **Cause**: SQL migration wasn't executed
- **Solution**: Go to Supabase → SQL Editor and run the migration SQL

### Issue: Duplicate records for same customer
- **Cause**: Customer name format varies (e.g., "John Doe" vs "JOHN DOE")
- **Solution**: Normalize payer names to uppercase before lookup

## Testing Checklist

- [ ] Migration SQL executed in Supabase
- [ ] Table appears in Supabase Tables view
- [ ] Backend logs show database connection successful
- [ ] First check upload → ESCALATE recommendation (if fraudulent)
- [ ] Second check from same payer → REJECT recommendation
- [ ] New customer check → Correct risk-based decision
