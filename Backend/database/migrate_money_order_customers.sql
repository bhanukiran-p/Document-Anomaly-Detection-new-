-- Migration script to consolidate existing money order customer records
-- This script adds the payee_name to existing purchaser records and updates references

-- Step 1: Add payee_name column if it doesn't exist
ALTER TABLE money_order_customers
ADD COLUMN IF NOT EXISTS payee_name TEXT;

-- Step 2: Update purchaser customer records with payee information from related payee records
-- This matches based on the money order association
UPDATE money_order_customers AS purchaser
SET payee_name = payee.name
FROM money_orders AS mo
INNER JOIN money_order_customers AS payee
  ON mo.payee_customer_id = payee.customer_id
WHERE mo.purchaser_customer_id = purchaser.customer_id
  AND purchaser.payee_name IS NULL;

-- Step 3: Check if there are any orphaned payee-only records (optional - for cleanup)
-- SELECT * FROM money_order_customers
-- WHERE customer_id NOT IN (
--     SELECT purchaser_customer_id FROM money_orders WHERE purchaser_customer_id IS NOT NULL
-- )
-- AND customer_id NOT IN (
--     SELECT payee_customer_id FROM money_orders WHERE payee_customer_id IS NOT NULL
-- );

-- Note: You can delete orphaned records manually after verifying the data migration was successful
-- DELETE FROM money_order_customers WHERE customer_id NOT IN (
--     SELECT purchaser_customer_id FROM money_orders WHERE purchaser_customer_id IS NOT NULL
-- );
