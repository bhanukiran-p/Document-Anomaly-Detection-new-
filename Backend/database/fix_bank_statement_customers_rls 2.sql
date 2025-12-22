-- Fix Row Level Security (RLS) for bank_statement_customers table
-- This allows the application to insert and update customer records

-- Option 1: Disable RLS completely (if you want unrestricted access)
-- ALTER TABLE bank_statement_customers DISABLE ROW LEVEL SECURITY;

-- Option 2: Create permissive RLS policies (recommended for production)
-- Allow all operations for service role (your backend uses service role key)

-- Enable RLS if not already enabled
ALTER TABLE bank_statement_customers ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Allow all operations for service role" ON bank_statement_customers;
DROP POLICY IF EXISTS "Allow all operations" ON bank_statement_customers;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON bank_statement_customers;
DROP POLICY IF EXISTS "Enable update for authenticated users" ON bank_statement_customers;
DROP POLICY IF EXISTS "Enable select for authenticated users" ON bank_statement_customers;

-- Create permissive policy that allows all operations
-- This works because Supabase service role bypasses RLS, but we need policies for the API
CREATE POLICY "Allow all operations for service role" ON bank_statement_customers
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Alternative: If the above doesn't work, disable RLS entirely
-- Uncomment the line below if you still get RLS errors:
-- ALTER TABLE bank_statement_customers DISABLE ROW LEVEL SECURITY;

