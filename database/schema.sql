-- FinGuard Relational Database Schema
-- Compatible with PostgreSQL (Production) and SQLite (Local Development)

-- 1. Accounts Table (Customers/Merchants)
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(50) PRIMARY KEY, -- Account ID (e.g. C12345678)
    customer_name VARCHAR(100) NOT NULL,
    current_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'under_review')),
    risk_score FLOAT DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Transactions Table (Financial logs and ML evaluations)
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(36) PRIMARY KEY, -- UUID representation
    origin_account_id VARCHAR(50) NOT NULL,
    dest_account_id VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('PAYMENT', 'TRANSFER', 'CASH_OUT', 'CASH_IN', 'DEBIT')),
    old_balance_orig DECIMAL(15, 2) NOT NULL,
    new_balance_orig DECIMAL(15, 2) NOT NULL,
    old_balance_dest DECIMAL(15, 2) NOT NULL,
    new_balance_dest DECIMAL(15, 2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ML Inference Attributes
    is_fraud BOOLEAN DEFAULT FALSE,
    fraud_score FLOAT DEFAULT 0.00,
    needs_review BOOLEAN DEFAULT FALSE,
    
    -- SHAP value explanations (stored as serialized JSON text)
    shap_values TEXT, 
    
    -- Analyst action logs
    analyst_decision VARCHAR(20) DEFAULT NULL CHECK (analyst_decision IN ('approved', 'rejected', 'false_positive')),
    reviewed_at TIMESTAMP DEFAULT NULL,
    FOREIGN KEY (origin_account_id) REFERENCES accounts(id),
    FOREIGN KEY (dest_account_id) REFERENCES accounts(id)
);

-- Create indexes for performance auditing
CREATE INDEX IF NOT EXISTS idx_tx_is_fraud ON transactions(is_fraud);
CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp);
