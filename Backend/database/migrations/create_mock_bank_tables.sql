-- Mock Bank Database Schema
-- Creates tables for synthetic banking data

-- Table 1: Synthetic Customers
CREATE TABLE IF NOT EXISTS synthetic_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    home_city VARCHAR(100),
    home_country VARCHAR(50) DEFAULT 'USA',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 2: Synthetic Accounts
CREATE TABLE IF NOT EXISTS synthetic_accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES synthetic_customers(customer_id) ON DELETE CASCADE,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('checking', 'savings', 'credit')),
    account_number VARCHAR(20) NOT NULL,
    current_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    available_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 3: Synthetic Transactions (Raw bank data - NO fraud labels)
CREATE TABLE IF NOT EXISTS synthetic_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL REFERENCES synthetic_accounts(account_id) ON DELETE CASCADE,
    customer_id VARCHAR(50) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    merchant VARCHAR(255),
    category VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    transaction_city VARCHAR(100),
    transaction_country VARCHAR(50),
    login_city VARCHAR(100),
    login_country VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 4: Mock Bank Connections
CREATE TABLE IF NOT EXISTS mock_bank_connections (
    connection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(50) REFERENCES synthetic_customers(customer_id),
    institution_name VARCHAR(255) DEFAULT 'Mock Bank',
    connected_at TIMESTAMP DEFAULT NOW(),
    last_synced_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_synthetic_accounts_customer ON synthetic_accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_synthetic_transactions_account ON synthetic_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_synthetic_transactions_customer ON synthetic_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_synthetic_transactions_timestamp ON synthetic_transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_mock_bank_connections_user ON mock_bank_connections(user_id);
