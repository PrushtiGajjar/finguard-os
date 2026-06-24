import pandas as pd

def run_detailed_eda(csv_path="data/raw/transactions.csv"):
    df = pd.read_csv(csv_path)
    
    print("====================================================")
    print("           DETAILED DATA STRUCTURE EXPLORATION")
    print("====================================================")
    
    # 1. Column Info and Data Types
    print("\n--- 1. Feature Info & Data Types ---")
    print(df.dtypes)
    
    # 2. Basic Descriptive Statistics
    print("\n--- 2. Numerical Features Statistical Summary ---")
    print(df.describe().to_string())
    
    # 3. Legitimate Transaction Sample
    print("\n--- 3. Legitimate Transactions Sample (First 3) ---")
    legit_df = df[df['isFraud'] == 0].head(3)
    print(legit_df[['step', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']].to_string())
    
    # 4. Fraudulent Transaction Sample
    print("\n--- 4. Fraudulent Transactions Sample (First 3) ---")
    fraud_df = df[df['isFraud'] == 1].head(3)
    print(fraud_df[['step', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest', 'isFlaggedFraud']].to_string())
    
    # 5. balance discrepancies calculation example
    print("\n--- 5. Key Feature Insight: Origin Balance Discrepancy ---")
    # Legitimate transactions balance discrepancy mean
    legit_diff = (df[df['isFraud'] == 0]['oldbalanceOrg'] - df[df['isFraud'] == 0]['newbalanceOrig'] - df[df['isFraud'] == 0]['amount']).mean()
    # Fraud transactions balance discrepancy mean
    fraud_diff = (df[df['isFraud'] == 1]['oldbalanceOrg'] - df[df['isFraud'] == 1]['newbalanceOrig'] - df[df['isFraud'] == 1]['amount']).mean()
    
    print(f"Average Origin Balance Discrepancy (oldBalance - newBalance - amount):")
    print(f"  Legitimate Transactions: {legit_diff:.2f}")
    print(f"  Fraudulent Transactions: {fraud_diff:.2f}")
    
    print("\n--- 6. Key Feature Insight: Destination Balance Discrepancy ---")
    # For TRANSFER transactions (dest balance should increase by amount)
    transfers = df[df['type'] == 'TRANSFER']
    legit_trans = transfers[transfers['isFraud'] == 0]
    fraud_trans = transfers[transfers['isFraud'] == 1]
    
    legit_dest_diff = (legit_trans['newbalanceDest'] - legit_trans['oldbalanceDest'] - legit_trans['amount']).mean()
    fraud_dest_diff = (fraud_trans['newbalanceDest'] - fraud_trans['oldbalanceDest'] - fraud_trans['amount']).mean()
    
    print(f"Average Destination Balance Discrepancy (newBalance - oldBalance - amount) for TRANSFERs:")
    print(f"  Legitimate Transfers: {legit_dest_diff:.2f}")
    print(f"  Fraudulent Transfers: {fraud_dest_diff:.2f}")
    
    print("====================================================")

if __name__ == "__main__":
    run_detailed_eda()
