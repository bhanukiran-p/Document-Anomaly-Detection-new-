# Dynamic Column Addition

Automatically adds new columns to database tables when new fields appear in extracted document data.

## How It Works

1. **Field Detection**: When documents are processed, the system extracts all fields
2. **Column Check**: Compares extracted fields with existing table columns
3. **Auto-Add**: Missing columns are automatically added with appropriate types
4. **Data Storage**: New fields are included in the insert data

## Technical Implementation

### Step-by-Step Process

#### 1. Document Processing Trigger
When a document is stored via `document_storage.py`:
```python
# In store_check(), store_paystub(), store_bank_statement(), store_money_order()
schema_manager = get_schema_manager()
schema_manager.ensure_columns_exist('check', extracted_data)
```

#### 2. Field Extraction & Normalization
- **Flatten nested data**: Converts nested dictionaries to flat structure
  - Example: `{'issuer': {'name': 'Bank', 'phone': '123'}}` → `{'issuer_name': 'Bank', 'issuer_phone': '123'}`
- **Normalize field names**: Converts to PostgreSQL-compatible column names
  - Removes special characters, converts to lowercase
  - Example: `"Issuer Phone#"` → `"issuer_phone"`
- **Filter excluded fields**: Removes metadata fields (`raw_text`, `status`, etc.)

#### 3. Column Detection
- **Query existing columns**: Uses Supabase API to get current table schema
  - Method 1: Query `information_schema.columns` via direct DB connection
  - Method 2: Query sample row and infer columns from keys
  - Method 3: Use cached column list (performance optimization)
- **Compare fields**: Identifies fields that don't have corresponding columns

#### 4. Type Inference
For each new field, determines PostgreSQL type:
```python
# Based on field value and name patterns
if 'date' in field_name.lower():
    return 'DATE'
if 'amount' in field_name.lower():
    return 'NUMERIC'
if isinstance(value, bool):
    return 'BOOLEAN'
if isinstance(value, (list, dict)):
    return 'JSONB'
# Default: TEXT
```

#### 5. SQL Generation
Creates `ALTER TABLE` statement:
```sql
ALTER TABLE checks
ADD COLUMN IF NOT EXISTS issuer_phone TEXT DEFAULT NULL;
```
- Uses `IF NOT EXISTS` to prevent errors if column already exists
- Sets `DEFAULT NULL` for nullable columns
- Normalized column name matches inferred type

#### 6. SQL Execution
Attempts multiple methods (in order):

**Method 1: Direct PostgreSQL Connection**
```python
conn = psycopg2.connect(
    host='project.db.supabase.co',
    database='postgres',
    user='postgres',
    password=SUPABASE_DB_PASSWORD,
    port=5432,
    sslmode='require'
)
cursor.execute(sql)
```
- Fastest method
- Requires `SUPABASE_DB_PASSWORD` in `.env`
- Falls back if connection fails

**Method 2: Connection Pooler**
```python
# Same as Method 1 but port 6543
conn = psycopg2.connect(..., port=6543)
```
- Uses Supabase connection pooler
- Better for high-concurrency scenarios

**Method 3: Supabase RPC Function** ⭐ (Primary Method)
```python
# Via Supabase REST API
response = supabase.rpc('execute_sql', {'sql_query': sql})
```
- Uses `execute_sql` RPC function created by `setup_auto_execute_rpc.sql`
- Works via REST API (no direct DB connection needed)
- Has built-in security restrictions
- **This is the method currently used**

**Method 4: Manual Execution**
- If all methods fail, logs SQL statement
- Developer can run manually in Supabase SQL Editor

#### 7. Cache Update
- Updates column cache after successful addition
- Prevents redundant queries for same table
- Cache cleared when columns are added

#### 8. Data Insertion
- New fields included in insert data via `_add_unmapped_fields()`
- Fields normalized and type-converted
- Inserted into table with new columns

### Code Flow Example

```python
# 1. Document processed
extracted = {'issuer_phone': '555-1234', 'new_field': 123}

# 2. Schema manager called
schema_manager.ensure_columns_exist('money_order', extracted)

# 3. Fields normalized
# 'issuer_phone' → 'issuer_phone' (TEXT)
# 'new_field' → 'new_field' (NUMERIC)

# 4. Columns checked
existing = ['money_order_id', 'amount', 'issuer_name', ...]
missing = ['issuer_phone', 'new_field']

# 5. SQL generated
sql1 = "ALTER TABLE money_orders ADD COLUMN IF NOT EXISTS issuer_phone TEXT DEFAULT NULL;"
sql2 = "ALTER TABLE money_orders ADD COLUMN IF NOT EXISTS new_field NUMERIC DEFAULT NULL;"

# 6. SQL executed via RPC
supabase.rpc('execute_sql', {'sql_query': sql1})  # ✅ Success
supabase.rpc('execute_sql', {'sql_query': sql2})  # ✅ Success

# 7. Data inserted with new fields
money_order_data = {
    'money_order_id': '...',
    'issuer_phone': '555-1234',  # New field
    'new_field': 123             # New field
}
supabase.table('money_orders').insert([money_order_data])
```

### Security Layers

1. **RPC Function Restrictions**: Only allows `ALTER TABLE ADD COLUMN IF NOT EXISTS`
2. **Table Whitelist**: Only works on `checks`, `paystubs`, `bank_statements`, `money_orders`
3. **Service Role Key**: Requires admin-level access (never exposed to frontend)
4. **SQL Injection Prevention**: Field names normalized, no user input in SQL
5. **Type Safety**: Types inferred from actual values, not user input

## Supported Tables

- `checks` → Check documents
- `paystubs` → Paystub documents  
- `bank_statements` → Bank statement documents
- `money_orders` → Money order documents

## Type Inference

Automatically infers PostgreSQL column types:
- **TEXT**: Strings, IDs
- **NUMERIC**: Amounts, prices, balances
- **INTEGER**: Counts, whole numbers
- **DATE**: Date strings
- **BOOLEAN**: Boolean values
- **JSONB**: Lists and dictionaries

## Requirements

1. **RPC Function**: Run `setup_auto_execute_rpc.sql` in Supabase SQL Editor (one-time setup)
2. **Configuration**: `ENABLE_AUTO_COLUMN_ADDITION=true` in `.env` (default: enabled)
3. **Password**: `SUPABASE_DB_PASSWORD` in `.env` (optional, for direct connection fallback)

## Usage

No code changes needed. The feature is integrated into document storage:
- Process documents normally
- New fields automatically create columns
- SQL executed via Supabase RPC function

## Excluded Fields

Metadata fields are excluded: `raw_ocr_text`, `raw_text`, `status`, `timestamp`, `document_id`, `user_id`, etc.

## Security

- Only allows `ALTER TABLE ADD COLUMN IF NOT EXISTS` statements
- Restricted to specific tables (checks, paystubs, bank_statements, money_orders)
- Requires service role key for RPC execution

## Supabase Keys: Anon vs Service Role

### Anon Key (`SUPABASE_ANON_KEY`)

**Purpose**: Client-side operations with Row Level Security (RLS) enforcement

- **Permissions**: Limited by RLS policies
- **Use Case**: Frontend applications, public API access
- **Security**: Respects database RLS policies - can only access data user has permission for
- **Limitations**: Cannot bypass RLS, cannot execute admin functions

**Example Usage**:
```python
# Used for regular database queries that respect RLS
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
response = supabase.table('checks').select('*').execute()  # Respects RLS
```

### Service Role Key (`SUPABASE_SERVICE_ROLE_KEY`)

**Purpose**: Server-side operations with full database access

- **Permissions**: Bypasses RLS policies, full admin access
- **Use Case**: Backend services, admin operations, schema changes
- **Security**: ⚠️ **Never expose to frontend** - grants full database access
- **Capabilities**: Can execute RPC functions, modify schema, bypass RLS

**Example Usage**:
```python
# Used for admin operations like schema changes
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
response = supabase.rpc('execute_sql', {'sql_query': 'ALTER TABLE...'})  # Bypasses RLS
```

### Why Dynamic Columns Uses Service Role Key

The dynamic column feature needs to:
1. **Execute SQL**: Run `ALTER TABLE` statements (requires admin privileges)
2. **Bypass RLS**: Schema changes need full access regardless of user permissions
3. **Call RPC Functions**: The `execute_sql` RPC function requires service role access

**Security Note**: The RPC function (`execute_sql`) has built-in restrictions:
- Only allows `ALTER TABLE ADD COLUMN IF NOT EXISTS`
- Only works on specific tables (checks, paystubs, bank_statements, money_orders)
- Prevents SQL injection and unauthorized schema changes

### Database Password (`SUPABASE_DB_PASSWORD`)

**Purpose**: Direct PostgreSQL connection (alternative to REST API)

- **Use Case**: Direct database connections via psycopg2
- **Access**: Full database access (like service role key)
- **Method**: Bypasses Supabase REST API, connects directly to PostgreSQL
- **Status**: Optional - RPC method works without it

**When to Use**:
- If direct database connection is preferred
- For migration scripts
- When REST API has limitations

**Security**: Same level as service role key - keep secure, never expose publicly

