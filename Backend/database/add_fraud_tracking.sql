-- Migration: Add fraud tracking columns to money_order_customers table
-- This migration adds fields to track customer fraud history and recommendations

-- Add fraud tracking columns if they don't exist
ALTER TABLE money_order_customers
ADD COLUMN IF NOT EXISTS has_fraud_history BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS fraud_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS escalate_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_recommendation TEXT,
ADD COLUMN IF NOT EXISTS last_analysis_date TIMESTAMP;

-- Create an index for faster queries on has_fraud_history
CREATE INDEX IF NOT EXISTS idx_money_order_customers_fraud ON money_order_customers(has_fraud_history);

-- Create an index for faster queries on last_analysis_date
CREATE INDEX IF NOT EXISTS idx_money_order_customers_last_analysis ON money_order_customers(last_analysis_date DESC);

-- Log the migration
SELECT 'Fraud tracking columns added successfully' as status;
