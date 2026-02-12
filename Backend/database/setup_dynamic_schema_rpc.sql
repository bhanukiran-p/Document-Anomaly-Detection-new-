-- SQL script to set up RPC functions for dynamic schema management
-- Run this in Supabase SQL Editor to enable automatic column addition

-- Function to get table columns
CREATE OR REPLACE FUNCTION get_table_columns(table_name TEXT)
RETURNS TABLE(column_name TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT c.column_name::TEXT
    FROM information_schema.columns c
    WHERE c.table_name = get_table_columns.table_name
      AND c.table_schema = 'public'
    ORDER BY c.ordinal_position;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to execute SQL (use with caution - security risk)
-- Only enable this if you trust the application code
-- Consider restricting to ALTER TABLE ADD COLUMN only
CREATE OR REPLACE FUNCTION execute_sql(sql_query TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Security check: Only allow ALTER TABLE ADD COLUMN statements
    IF sql_query !~* '^\s*ALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN' THEN
        RAISE EXCEPTION 'Only ALTER TABLE ADD COLUMN statements are allowed';
    END IF;
    
    -- Execute the SQL
    EXECUTE sql_query;
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'SQL execution failed: %', SQLERRM;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions (adjust role as needed)
-- GRANT EXECUTE ON FUNCTION get_table_columns(TEXT) TO authenticated;
-- GRANT EXECUTE ON FUNCTION execute_sql(TEXT) TO authenticated;

-- Note: For production, consider:
-- 1. Restricting execute_sql to service role only
-- 2. Adding more validation to prevent SQL injection
-- 3. Logging all schema changes
-- 4. Requiring admin approval for schema changes

