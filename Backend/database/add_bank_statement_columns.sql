-- Add missing columns to bank_statements table
-- This aligns the database schema with what the code expects

-- Document reference
-- Note: If documents table doesn't exist, this will just be a UUID column
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS document_id UUID;

-- Add foreign key constraint only if documents table exists
-- If you get an error, run this separately after creating documents table:
-- ALTER TABLE bank_statements 
-- ADD CONSTRAINT fk_bank_statements_document 
-- FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE SET NULL;

-- Account holder details (expanded)
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS account_holder_name TEXT,
ADD COLUMN IF NOT EXISTS account_holder_address TEXT,
ADD COLUMN IF NOT EXISTS account_holder_city TEXT,
ADD COLUMN IF NOT EXISTS account_holder_state TEXT,
ADD COLUMN IF NOT EXISTS account_holder_zip TEXT;

-- Bank details (expanded)
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS institution_id UUID REFERENCES financial_institutions(institution_id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS bank_address TEXT,
ADD COLUMN IF NOT EXISTS bank_city TEXT,
ADD COLUMN IF NOT EXISTS bank_state TEXT,
ADD COLUMN IF NOT EXISTS bank_zip TEXT,
ADD COLUMN IF NOT EXISTS routing_number TEXT;

-- Account details
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS account_type TEXT,
ADD COLUMN IF NOT EXISTS currency TEXT DEFAULT 'USD';

-- Statement period (expanded)
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS statement_period_start_date DATE,
ADD COLUMN IF NOT EXISTS statement_period_end_date DATE;

-- Balance details (separate columns, in addition to existing balances JSON)
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS opening_balance NUMERIC,
ADD COLUMN IF NOT EXISTS ending_balance NUMERIC,
ADD COLUMN IF NOT EXISTS available_balance NUMERIC;

-- Transaction summary (separate columns)
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS total_transactions INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_credits NUMERIC,
ADD COLUMN IF NOT EXISTS total_debits NUMERIC,
ADD COLUMN IF NOT EXISTS net_activity NUMERIC;

-- Transaction details
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS transactions JSONB;

-- Anomaly details (expanded)
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS top_anomalies JSONB;

-- Timestamp (in addition to created_at)
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bank_statements_document_id ON bank_statements(document_id);
CREATE INDEX IF NOT EXISTS idx_bank_statements_account_holder_name ON bank_statements(account_holder_name);
CREATE INDEX IF NOT EXISTS idx_bank_statements_statement_period_start_date ON bank_statements(statement_period_start_date);
CREATE INDEX IF NOT EXISTS idx_bank_statements_account_number ON bank_statements(account_number);

-- Note: Keep existing columns (account_holder, balances, transaction_count, anomalies, created_at)
-- for backward compatibility. The code will use the new columns going forward.

