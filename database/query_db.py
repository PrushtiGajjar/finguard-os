import sqlite3
import pandas as pd

def query_database():
    db_path = "finguard.db"
    print(f"Connecting to database: {db_path}...\n")
    
    conn = sqlite3.connect(db_path)
    
    # 1. Query Accounts
    print("====================================================")
    print("           PERSISTED CUSTOMER ACCOUNTS")
    print("====================================================")
    accounts_df = pd.read_sql_query("SELECT * FROM accounts", conn)
    if accounts_df.empty:
        print("No accounts saved yet.")
    else:
        print(accounts_df.to_string(index=False))
        
    # 2. Query Transactions
    print("\n====================================================")
    print("           PERSISTED TRANSACTION LOGS")
    print("====================================================")
    tx_df = pd.read_sql_query(
        "SELECT id, origin_account_id, dest_account_id, amount, transaction_type, is_fraud, fraud_score FROM transactions", 
        conn
    )
    if tx_df.empty:
        print("No transactions saved yet.")
    else:
        print(tx_df.to_string(index=False))
        
    conn.close()

if __name__ == "__main__":
    query_database()
