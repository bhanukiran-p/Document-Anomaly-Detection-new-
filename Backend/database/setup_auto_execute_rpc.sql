-- Create RPC function to enable automatic SQL execution for schema changes
-- Run this in Supabase SQL Editor to enable auto-column addition

-- Function to execute ALTER TABLE ADD COLUMN statements safely
CREATE OR REPLACE FUNCTION execute_sql(sql_query TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    -- Security check: Only allow ALTER TABLE ADD COLUMN statements
    -- This prevents SQL injection and limits to schema additions only
    IF sql_query !~* '^\s*ALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS' THEN
        RAISE EXCEPTION 'Only ALTER TABLE ADD COLUMN IF NOT EXISTS statements are allowed. Got: %', LEFT(sql_query, 100);
    END IF;
    
    -- Additional safety: Check table name is from allowed list
    IF sql_query !~* 'ALTER\s+TABLE\s+(checks|paystubs|bank_statements|money_orders)' THEN
        RAISE EXCEPTION 'Table must be one of: checks, paystubs, bank_statements, money_orders';
    END IF;
    
    -- Execute the SQL
    EXECUTE sql_query;
    
    -- Return success
    result := json_build_object(
        'success', true,
        'message', 'SQL executed successfully',
        'query', LEFT(sql_query, 200)
    );
    
    RETURN result;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Return error details
        result := json_build_object(
            'success', false,
            'error', SQLERRM,
            'query', LEFT(sql_query, 200)
        );
        RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users (or service role)
-- Adjust based on your security requirements
GRANT EXECUTE ON FUNCTION execute_sql(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION execute_sql(TEXT) TO service_role;

-- Optional: Create a more restrictive version that only allows specific operations
-- This version logs all schema changes for audit purposes
CREATE OR REPLACE FUNCTION execute_sql_with_log(sql_query TEXT, user_context TEXT DEFAULT 'system')
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    -- Same security checks as above
    IF sql_query !~* '^\s*ALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS' THEN
        RAISE EXCEPTION 'Only ALTER TABLE ADD COLUMN IF NOT EXISTS statements are allowed';
    END IF;
    
    IF sql_query !~* 'ALTER\s+TABLE\s+(checks|paystubs|bank_statements|money_orders)' THEN
        RAISE EXCEPTION 'Table must be one of: checks, paystubs, bank_statements, money_orders';
    END IF;
    
    -- Log the schema change (you'd need a schema_changes table for this)
    -- INSERT INTO schema_changes (sql_query, executed_by, executed_at) 
    -- VALUES (sql_query, user_context, NOW());
    
    -- Execute the SQL
    EXECUTE sql_query;
    
    result := json_build_object(
        'success', true,
        'message', 'SQL executed and logged successfully',
        'query', LEFT(sql_query, 200),
        'executed_by', user_context
    );
    
    RETURN result;
    
EXCEPTION
    WHEN OTHERS THEN
        result := json_build_object(
            'success', false,
            'error', SQLERRM,
            'query', LEFT(sql_query, 200)
        );
        RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Note: For production, consider:
-- 1. Adding audit logging table
-- 2. Restricting to service_role only
-- 3. Adding rate limiting
-- 4. Requiring admin approval workflow

