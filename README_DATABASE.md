# Database Architecture & Data Ingestion

**Complete guide to Supabase database implementation in XFORIA DAD**

---

## 🗄️ Database Overview

### Technology Stack
- **Database**: Supabase (PostgreSQL)
- **Client Library**: `supabase==2.10.0` (Python)
- **Connection**: REST API over HTTPS
- **Authentication**: Row Level Security (RLS) with API keys

### Why Supabase?

1. **Managed PostgreSQL**: Full PostgreSQL features without server management
2. **Built-in Auth**: User authentication and authorization
3. **Real-time**: Real-time subscriptions (future use)
4. **REST API**: Auto-generated REST API from schema
5. **Row Level Security**: Fine-grained access control
6. **Easy Integration**: Simple Python client library

---

## 🔑 API Keys: Anon Key vs Service Role Key

### Simple Explanation

Think of Supabase keys like **house keys**:

#### 🟢 **Anon Key** = Regular House Key
- **What it is**: Normal key that follows house rules
- **Access**: Can only open doors you're allowed to enter
- **Safety**: Safe to give to guests (can expose publicly)
- **Rules**: Must follow security rules (Row Level Security)
- **Use**: 99% of the time - all normal operations

**Real Example:**
```
You (user) → Anon Key → Supabase → "Can I see my documents?"
Supabase → "Yes, here are YOUR documents only"
```

#### 🔴 **Service Role Key** = Master Key / Admin Key
- **What it is**: Master key that bypasses all rules
- **Access**: Can open ANY door, access ANY room
- **Safety**: DANGEROUS - never give to anyone (backend only)
- **Rules**: Ignores all security rules (bypasses RLS)
- **Use**: Only 1% of the time - migrations and admin tasks

**Real Example:**
```
Admin Script → Service Role Key → Supabase → "Show me ALL documents"
Supabase → "Here's everything, no questions asked"
```

### Visual Comparison

```
┌─────────────────────────────────────────────────────────┐
│                    ANON KEY                              │
├─────────────────────────────────────────────────────────┤
│  🔓 Opens: Only YOUR data                                │
│  🛡️ Security: Enforced (RLS active)                      │
│  👥 Who can use: Anyone (safe to expose)                 │
│  📍 Used: API endpoints, normal queries                 │
│  ✅ Safe: Yes - respects user permissions                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              SERVICE ROLE KEY                            │
├─────────────────────────────────────────────────────────┤
│  🔓 Opens: EVERYTHING (all data)                         │
│  🛡️ Security: Bypassed (RLS disabled)                    │
│  👥 Who can use: Backend scripts only                     │
│  📍 Used: Migrations, admin tasks                        │
│  ⚠️ Dangerous: Yes - can access/modify anything          │
└─────────────────────────────────────────────────────────┘
```

### Real-World Analogy

**Anon Key = Employee Badge**
- Gets you into the building
- Can only access your department
- Security guards check your permissions
- Safe to wear in public

**Service Role Key = Master Keycard**
- Gets you into EVERY room
- Security guards don't stop you
- Can access CEO's office, server room, everything
- Must keep locked away, never share

### When to Use Each

#### ✅ Use Anon Key For:
- ✅ Storing documents (`INSERT INTO checks`)
- ✅ Reading data (`SELECT FROM checks`)
- ✅ Updating customer records (`UPDATE check_customers`)
- ✅ All API endpoint operations
- ✅ Frontend queries (if needed)

#### ⚠️ Use Service Role Key For:
- ⚠️ Database migrations (`ALTER TABLE`)
- ⚠️ Creating tables (`CREATE TABLE`)
- ⚠️ Admin scripts (bulk updates)
- ⚠️ System maintenance
- ⚠️ Initial setup

### Code Examples

**Anon Key (Normal Operations):**
```python
# Backend/database/supabase_client.py
# This is what we use 99% of the time
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Anon key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Safe operations - respects user permissions
supabase.table('checks').insert([check_data]).execute()
supabase.table('checks').select('*').eq('payer_name', 'John').execute()
```

**Service Role Key (Admin Only):**
```python
# Backend/database/run_migration.py
# Only used for migrations/admin
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Admin operations - bypasses all security
# Can modify schema, access all data
supabase.rpc('exec_sql', {'sql': 'ALTER TABLE checks ADD COLUMN ...'})
```

### Quick Decision Guide

**Ask yourself:**
- "Am I doing normal data operations?" → Use **Anon Key**
- "Am I modifying database structure?" → Use **Service Role Key**
- "Am I running a migration script?" → Use **Service Role Key**
- "Am I in an API endpoint?" → Use **Anon Key**

### Security Rules

**Anon Key:**
- ✅ Can expose in frontend (if needed)
- ✅ Safe for production
- ✅ Respects user permissions
- ✅ Follows security policies

**Service Role Key:**
- ❌ NEVER expose to frontend
- ❌ Backend scripts only
- ❌ Keep in `.env` file
- ❌ Use sparingly

### Summary

| Question | Anon Key | Service Role Key |
|----------|----------|------------------|
| **Who can use it?** | Anyone | Backend only |
| **What can it access?** | User's own data | Everything |
| **Does it follow rules?** | Yes (RLS enforced) | No (bypasses RLS) |
| **Is it safe to expose?** | Yes | No (never!) |
| **When to use?** | Always (99%) | Rarely (1%) |
| **Like a...** | Regular key | Master key |

**Remember**: 
- **Anon Key** = Normal operations, safe, follows rules
- **Service Role Key** = Admin operations, dangerous, bypasses rules

---

## 📊 Database Schema

### Core Tables

#### 1. **`documents`** (Master Table)
```sql
CREATE TABLE documents (
  document_id UUID PRIMARY KEY,
  file_name VARCHAR,
  document_type VARCHAR,  -- 'check', 'paystub', 'money_order', 'bank_statement'
  upload_date TIMESTAMP,
  user_id VARCHAR,
  status VARCHAR  -- 'pending', 'analyzed', 'rejected'
);
```

**Purpose**: Master record for all uploaded documents

#### 2. **`checks`** Table
```sql
CREATE TABLE checks (
  check_id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(document_id),
  check_number VARCHAR,
  amount DECIMAL,
  check_date DATE,
  payer_name VARCHAR,
  payee_name VARCHAR,
  bank_name VARCHAR,
  routing_number VARCHAR,
  account_number VARCHAR,
  fraud_risk_score DECIMAL(5,4),  -- 0.0000-1.0000
  model_confidence DECIMAL(5,4),
  ai_recommendation VARCHAR,  -- 'APPROVE', 'REJECT', 'ESCALATE'
  fraud_type VARCHAR,
  fraud_types JSONB,
  fraud_explanations JSONB,
  created_at TIMESTAMP
);
```

#### 3. **`check_customers`** (Customer Tracking)
```sql
CREATE TABLE check_customers (
  customer_id UUID PRIMARY KEY,
  payer_name VARCHAR UNIQUE,  -- Unique constraint for payer-based tracking
  payee_name VARCHAR,
  address TEXT,
  total_submissions INTEGER DEFAULT 0,
  high_risk_count INTEGER DEFAULT 0,
  fraud_count INTEGER DEFAULT 0,  -- Count of REJECT recommendations
  escalate_count INTEGER DEFAULT 0,  -- Count of ESCALATE recommendations
  last_submission_date TIMESTAMP,
  fraud_status VARCHAR,  -- 'APPROVE', 'REJECT', 'ESCALATE'
  last_recommendation VARCHAR,
  last_analysis_date TIMESTAMP
);
```

**Purpose**: Track customer fraud history for repeat offender detection

**Similar Tables:**
- `paystub_customers` - Employee tracking
- `money_order_customers` - Money order purchaser tracking
- `bank_statement_customers` - Account holder tracking

#### 4. **`financial_institutions`** (Bank Dictionary)
```sql
CREATE TABLE financial_institutions (
  institution_id UUID PRIMARY KEY,
  name VARCHAR UNIQUE,  -- Bank name (UPPERCASE)
  routing_number VARCHAR,
  address TEXT
);
```

**Purpose**: Validated list of supported banks

### Database Views

#### **`v_checks_analysis`** (Aggregated View)
```sql
CREATE VIEW v_checks_analysis AS
SELECT
  c.check_id,
  c.document_id,
  c.check_number,
  c.amount,
  c.check_date,
  c.payer_name,
  c.payee_name,
  c.bank_name,
  c.fraud_risk_score,
  c.model_confidence,
  c.ai_recommendation,
  c.created_at
FROM checks c
ORDER BY c.created_at DESC;
```

**Purpose**: Simplified view for API queries (hides internal fields)

**Other Views:**
- `v_money_orders_analysis` - Money order aggregated data
- `v_documents_with_risk` - All documents with risk scores
- `v_paystub_insights_clean` - Paystub insights for dashboards

---

## 🔄 Data Ingestion Flow

### Complete Ingestion Pipeline

```
Document Analysis Complete
    ↓
API Endpoint (api_server.py)
    ↓
store_check_analysis() / store_paystub_analysis() / etc.
    ↓
DocumentStorage Class (database/document_storage.py)
    ├─ Step 1: Store Document Record
    │   └─ INSERT INTO documents (document_id, file_name, document_type)
    │
    ├─ Step 2: Get/Create Customer
    │   ├─ Query customer table by name
    │   ├─ If exists: Get customer_id
    │   └─ If new: Create customer record
    │
    ├─ Step 3: Store Document-Specific Data
    │   ├─ INSERT INTO checks/paystubs/money_orders/bank_statements
    │   ├─ Link to document_id
    │   └─ Store ML/AI analysis results
    │
    ├─ Step 4: Update Customer Fraud History
    │   ├─ Get current fraud counts
    │   ├─ Update based on AI recommendation:
    │   │   ├─ REJECT → fraud_count += 1
    │   │   ├─ ESCALATE → escalate_count += 1
    │   │   └─ APPROVE → no change
    │   └─ UPDATE customer table
    │
    └─ Step 5: Return document_id
```

### Step-by-Step Ingestion Process

#### Step 1: Store Document Record

```python
def _store_document(self, user_id: str, document_type: str, file_name: str) -> str:
    """Create master document record"""
    document_id = str(uuid.uuid4())
    doc_data = {
        'document_id': document_id,
        'user_id': user_id,
        'document_type': document_type,  # 'check', 'paystub', etc.
        'file_name': file_name,
        'upload_date': datetime.utcnow().isoformat(),
        'status': 'processing'
    }
    
    # Insert into documents table
    self.supabase.table('documents').insert([doc_data]).execute()
    return document_id
```

**Result**: Master record created, `document_id` returned

#### Step 2: Get or Create Customer

**For Checks:**
```python
def get_or_create_customer(self, payer_name: str, payee_name: str, address: str):
    """Get existing customer or create new"""
    # Query by payer_name
    result = self.supabase.table('check_customers')\
        .select('*')\
        .eq('payer_name', payer_name)\
        .execute()
    
    if result.data:
        # Customer exists - return existing customer_id
        return result.data[0]['customer_id']
    else:
        # Create new customer
        customer_id = str(uuid.uuid4())
        customer_data = {
            'customer_id': customer_id,
            'payer_name': payer_name,
            'payee_name': payee_name,
            'address': address,
            'fraud_count': 0,
            'escalate_count': 0,
            'has_fraud_history': False
        }
        self.supabase.table('check_customers').insert([customer_data]).execute()
        return customer_id
```

**Logic:**
- **Check if exists**: Query by `payer_name` (unique constraint)
- **If exists**: Return existing `customer_id` (preserves fraud history)
- **If new**: Create new customer with `fraud_count=0`, `escalate_count=0`

#### Step 3: Store Document-Specific Data

**For Checks:**
```python
def store_check_analysis(self, user_id: str, file_name: str, analysis_data: Dict):
    """Store complete check analysis"""
    # Step 1: Store document record
    document_id = self._store_document(user_id, 'check', file_name)
    
    # Step 2: Get/create customer
    payer_name = analysis_data.get('normalized_data', {}).get('payer_name')
    customer_id = self.get_or_create_customer(payer_name, ...)
    
    # Step 3: Store check data
    check_data = {
        'check_id': str(uuid.uuid4()),
        'document_id': document_id,
        'check_number': normalized_data.get('check_number'),
        'amount': self._parse_amount(normalized_data.get('amount')),
        'payer_name': payer_name,
        'payee_name': normalized_data.get('payee_name'),
        'bank_name': normalized_data.get('bank_name'),
        'fraud_risk_score': ml_analysis.get('fraud_risk_score'),
        'model_confidence': ml_analysis.get('model_confidence'),
        'ai_recommendation': ai_analysis.get('recommendation'),
        'fraud_type': ai_analysis.get('fraud_types', [])[0] if ai_analysis.get('fraud_types') else None,
        'fraud_types': ai_analysis.get('fraud_types', []),
        'fraud_explanations': ai_analysis.get('fraud_explanations', [])
    }
    
    # Insert into checks table
    self.supabase.table('checks').insert([check_data]).execute()
    
    return document_id
```

**Data Stored:**
- Extracted fields (payer, payee, amount, check_number, etc.)
- ML analysis results (fraud_risk_score, model_confidence)
- AI analysis results (recommendation, fraud_type, explanations)
- Links to `document_id` and `customer_id`

#### Step 4: Update Customer Fraud History

**After Analysis Completes:**
```python
def update_customer_fraud_status(self, customer_id: str, recommendation: str):
    """Update customer fraud counters"""
    # Get current customer data
    customer = self.supabase.table('check_customers')\
        .select('*')\
        .eq('customer_id', customer_id)\
        .execute()
        .data[0]
    
    fraud_count = customer.get('fraud_count', 0)
    escalate_count = customer.get('escalate_count', 0)
    
    # Update based on recommendation
    if recommendation == 'REJECT':
        fraud_count += 1
        has_fraud_history = True
    elif recommendation == 'ESCALATE':
        escalate_count += 1
    # APPROVE: no change
    
    # Update customer record
    update_data = {
        'fraud_count': fraud_count,
        'escalate_count': escalate_count,
        'has_fraud_history': has_fraud_history,
        'last_recommendation': recommendation,
        'last_analysis_date': datetime.utcnow().isoformat()
    }
    
    self.supabase.table('check_customers')\
        .update(update_data)\
        .eq('customer_id', customer_id)\
        .execute()
```

**Fraud History Logic:**
- **REJECT**: `fraud_count += 1`, `has_fraud_history = True`
- **ESCALATE**: `escalate_count += 1` (no fraud flag)
- **APPROVE**: No change to counters

**Purpose**: Track repeat offenders for future fraud detection

---

## 🔐 Row Level Security (RLS)

### How RLS Works

**RLS Policies**: Control which rows users can access

**Example Policy:**
```sql
-- Users can only see their own documents
CREATE POLICY "Users can view own documents"
ON documents
FOR SELECT
USING (auth.uid()::text = user_id);
```

**Anon Key Behavior:**
- Respects RLS policies
- Users can only access their own data
- Enforced by Supabase automatically

**Service Role Key Behavior:**
- Bypasses RLS policies
- Can access all data
- Used for admin operations

### Current RLS Setup

**Documents Table:**
- Users can only see documents with their `user_id`
- Admin operations use service role key

**Customer Tables:**
- No RLS (all users can query)
- Customer data is not user-specific
- Fraud history is shared for detection

---

## 📥 Data Ingestion Examples

### Check Ingestion Flow

```python
# 1. Analysis completes
analysis_result = {
    'normalized_data': {
        'payer_name': 'John Doe',
        'payee_name': 'Jane Smith',
        'amount': 1500.00,
        'check_number': '1001'
    },
    'ml_analysis': {
        'fraud_risk_score': 0.75,
        'model_confidence': 0.89
    },
    'ai_analysis': {
        'recommendation': 'REJECT',
        'fraud_type': 'SIGNATURE_FORGERY'
    }
}

# 2. Store to database
document_id = store_check_analysis(user_id='user123', 
                                   file_name='check.jpg',
                                   analysis_data=analysis_result)

# 3. Database operations:
#    a) INSERT INTO documents (document_id='uuid', document_type='check', ...)
#    b) SELECT FROM check_customers WHERE payer_name='John Doe'
#       → If exists: customer_id='existing-uuid'
#       → If new: INSERT INTO check_customers (customer_id='new-uuid', ...)
#    c) INSERT INTO checks (check_id='uuid', document_id='uuid', 
#                          payer_name='John Doe', fraud_risk_score=0.75, ...)
#    d) UPDATE check_customers SET fraud_count=fraud_count+1 
#       WHERE customer_id='uuid'
```

### Money Order Ingestion Flow

**Special Case: Payer-Based Tracking**

```python
# Money orders use payer-based tracking (multiple rows per customer_id)
def _get_or_create_money_order_customer(self, customer_data):
    payer_name = customer_data.get('name')
    
    # Query by payer name (not customer_id)
    existing = self.supabase.table('money_order_customers')\
        .select('customer_id, escalate_count, fraud_count')\
        .eq('name', payer_name)\
        .order('created_at', desc=True)\
        .limit(1)\
        .execute()
    
    if existing.data:
        # Payer exists - reuse customer_id
        customer_id = existing.data[0]['customer_id']
        # Create NEW row with same customer_id
        # (allows tracking multiple payees for same payer)
        new_row = {
            'customer_id': customer_id,  # Same ID
            'name': payer_name,
            'payee_name': customer_data.get('payee_name'),
            'escalate_count': existing.data[0]['escalate_count'],  # Preserve history
            'fraud_count': existing.data[0]['fraud_count']
        }
        self.supabase.table('money_order_customers').insert([new_row]).execute()
    else:
        # New payer - create new customer_id
        customer_id = str(uuid.uuid4())
        new_row = {
            'customer_id': customer_id,
            'name': payer_name,
            'escalate_count': 0,
            'fraud_count': 0
        }
        self.supabase.table('money_order_customers').insert([new_row]).execute()
    
    return customer_id
```

**Key Difference**: Money orders create multiple rows per `customer_id` (one per payee), allowing tracking of payer's activity across multiple payees.

---

## 🔍 Query Patterns

### Standard Queries (Using Anon Key)

**Get All Checks:**
```python
supabase = get_supabase()  # Uses anon key
response = supabase.table('checks').select('*').execute()
```

**Get Checks by Payer:**
```python
response = supabase.table('checks')\
    .select('*')\
    .eq('payer_name', 'John Doe')\
    .execute()
```

**Get Customer History:**
```python
response = supabase.table('check_customers')\
    .select('*')\
    .eq('payer_name', 'John Doe')\
    .execute()
```

**Pagination:**
```python
# Fetch 1000 records per page
page_size = 1000
offset = 0

while True:
    response = supabase.table('checks')\
        .select('*', count='exact')\
        .order('created_at', desc=True)\
        .range(offset, offset + page_size - 1)\
        .execute()
    
    if not response.data:
        break
    
    # Process data
    process_data(response.data)
    
    offset += page_size
```

### Admin Queries (Using Service Role Key)

**Database Migration:**
```python
# run_migration.py
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Execute SQL directly
supabase.rpc('exec_sql', {'sql': 'ALTER TABLE checks ADD COLUMN ...'})
```

**Bulk Updates:**
```python
# Update all customers (bypasses RLS)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
supabase.table('check_customers')\
    .update({'fraud_status': 'APPROVE'})\
    .execute()  # Updates ALL rows
```

---

## 🎯 Customer Tracking Logic

### Check Customers (One Row Per Payer)

**Schema**: `payer_name` has UNIQUE constraint

**Logic:**
- One customer record per payer name
- Updates same record for repeat submissions
- Fraud counts accumulate on same record

**Example:**
```
Payer: "John Doe"
Submission 1: REJECT → fraud_count = 1
Submission 2: ESCALATE → escalate_count = 1, fraud_count = 1
Submission 3: REJECT → fraud_count = 2, escalate_count = 1
```

### Money Order Customers (Multiple Rows Per Customer)

**Schema**: No UNIQUE constraint on `name` (payer)

**Logic:**
- Multiple rows can have same `customer_id`
- One row per upload (payer + payee combination)
- Fraud counts preserved across rows
- Allows tracking payer activity across multiple payees

**Example:**
```
Payer: "John Doe"
Row 1: customer_id='uuid-1', payee='Alice', escalate_count=0
Row 2: customer_id='uuid-1', payee='Bob', escalate_count=1 (from Row 1)
Row 3: customer_id='uuid-1', payee='Charlie', fraud_count=1 (from Row 2)
```

**Why Multiple Rows?**
- Tracks payer activity across different payees
- Preserves fraud history for repeat offender detection
- Allows querying by payee while maintaining payer history

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              Document Analysis Complete                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         API Endpoint: store_check_analysis()               │
│         Uses: Anon Key (SUPABASE_KEY)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Step 1: Store Document Record                       │
│         INSERT INTO documents                               │
│         Returns: document_id                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Step 2: Get/Create Customer                         │
│         SELECT FROM check_customers WHERE payer_name=...    │
│         If exists: Get customer_id                         │
│         If new: INSERT INTO check_customers                 │
│         Returns: customer_id                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Step 3: Store Check Data                           │
│         INSERT INTO checks                                  │
│         Links: document_id, customer_id                    │
│         Stores: ML scores, AI recommendation, fraud_type   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Step 4: Update Customer Fraud History              │
│         GET current fraud_count, escalate_count            │
│         UPDATE check_customers SET                          │
│           fraud_count = fraud_count + 1 (if REJECT)        │
│           escalate_count = escalate_count + 1 (if ESCALATE)│
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Return: document_id                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Database Operations

### Insert Operations

**Insert Document:**
```python
document_data = {
    'document_id': str(uuid.uuid4()),
    'file_name': 'check.jpg',
    'document_type': 'check',
    'user_id': 'user123',
    'upload_date': datetime.utcnow().isoformat(),
    'status': 'analyzed'
}

supabase.table('documents').insert([document_data]).execute()
```

**Insert Check:**
```python
check_data = {
    'check_id': str(uuid.uuid4()),
    'document_id': document_id,
    'payer_name': 'John Doe',
    'amount': 1500.00,
    'fraud_risk_score': 0.75,
    'ai_recommendation': 'REJECT'
}

supabase.table('checks').insert([check_data]).execute()
```

### Update Operations

**Update Customer Fraud Status:**
```python
supabase.table('check_customers')\
    .update({
        'fraud_count': fraud_count + 1,
        'has_fraud_history': True,
        'last_recommendation': 'REJECT'
    })\
    .eq('customer_id', customer_id)\
    .execute()
```

### Query Operations

**Get Checks with Filters:**
```python
# Date filter
response = supabase.table('checks')\
    .select('*')\
    .gte('created_at', '2024-01-01')\
    .lte('created_at', '2024-12-31')\
    .execute()

# Risk level filter
response = supabase.table('checks')\
    .select('*')\
    .gte('fraud_risk_score', 0.7)\
    .execute()

# Search by payer name
response = supabase.table('checks')\
    .select('*')\
    .ilike('payer_name', '%John%')\
    .execute()
```

---

## 🔒 Security Best Practices

### Anon Key Usage
- ✅ Use for all API operations
- ✅ Safe to expose in frontend (if needed)
- ✅ Respects RLS policies
- ✅ User data isolation

### Service Role Key Usage
- ✅ Use only for migrations
- ✅ Use only for admin scripts
- ✅ NEVER expose to frontend
- ✅ Store in backend `.env` only
- ✅ Use sparingly

### Data Protection
- **RLS Policies**: Enforce user-level access
- **Input Validation**: Validate all inputs before insert
- **SQL Injection Prevention**: Use parameterized queries (Supabase handles this)
- **UUID Generation**: Use UUIDs for all IDs (prevents enumeration)

---

## 📊 Performance Considerations

### Pagination
- Supabase default limit: 1000 records
- Use `.range(offset, offset + limit)` for pagination
- Fetch in batches to avoid timeouts

### Indexing
**Recommended Indexes:**
```sql
CREATE INDEX idx_checks_payer_name ON checks(payer_name);
CREATE INDEX idx_checks_created_at ON checks(created_at);
CREATE INDEX idx_check_customers_payer_name ON check_customers(payer_name);
```

### Query Optimization
- Use `.select('column1, column2')` instead of `*` for large tables
- Use `.limit()` to restrict results
- Use `.order()` with indexed columns
- Avoid complex joins (use views instead)

---

## 🚀 Setup & Migration

### Initial Setup

**1. Create Supabase Project:**
- Go to supabase.com
- Create new project
- Get `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`

**2. Run Migrations:**
```bash
# Set service role key
export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Run migration script
python Backend/database/run_migration.py
```

**3. Create Views:**
```bash
psql -h your-supabase-host -U postgres -d postgres \
  -f Backend/database/create_checks_analysis_view.sql
```

### Environment Variables

```bash
# .env file
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

---

## 📝 Key Takeaways

1. **Anon Key**: Default for all operations, respects RLS, safe for production
2. **Service Role Key**: Only for migrations/admin, bypasses RLS, backend only
3. **Data Ingestion**: Document → Customer → Document Data → Fraud History Update
4. **Customer Tracking**: One row per payer (checks) or multiple rows (money orders)
5. **Fraud History**: Tracks `fraud_count` and `escalate_count` for repeat offenders
6. **Views**: Simplify queries, hide internal fields, improve performance

---

**Last Updated:** December 2024

