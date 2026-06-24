import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

def preprocess_pipeline(raw_csv_path="data/raw/transactions.csv", processed_dir="data/processed", models_dir="models/trained"):
    print("Starting Preprocessing and Feature Engineering Pipeline...")
    
    # 1. Load raw dataset
    df = pd.read_csv(raw_csv_path)
    
    # 2. Feature Engineering
    print("  Creating engineered balance discrepancy features...")
    # Sender account balance discrepancy
    df['errorBalanceOrig'] = df['oldbalanceOrg'] - df['newbalanceOrig'] - df['amount']
    # Recipient account balance discrepancy
    df['errorBalanceDest'] = df['newbalanceDest'] - df['oldbalanceDest'] - df['amount']
    
    # Create simple binary flags
    df['is_merchant_dest'] = df['nameDest'].str.startswith('M').astype(int)
    
    # 3. Categorical Encoding
    print("  Encoding categorical transaction types...")
    # One-hot encode the 'type' column
    type_dummies = pd.get_dummies(df['type'], prefix='type', dtype=int)
    df = pd.concat([df, type_dummies], axis=1)
    
    # Drop identifier columns and columns that are now one-hot encoded
    columns_to_drop = ['nameOrig', 'nameDest', 'type', 'isFlaggedFraud']
    df = df.drop(columns=columns_to_drop, errors='ignore')
    
    # 4. Stratified Split (80% Train, 20% Test)
    print("  Splitting dataset into stratified train and test partitions...")
    X = df.drop(columns=['isFraud'])
    y = df['isFraud']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.20, 
        random_state=42, 
        stratify=y  # Critical for maintaining fraud ratio in both splits
    )
    
    # 5. Feature Scaling (RobustScaler handles outliers much better than StandardScaler)
    print("  Scaling numerical features using RobustScaler...")
    cols_to_scale = ['amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
    
    scaler = RobustScaler()
    
    # Fit ONLY on the training split to prevent data leakage
    X_train[cols_to_scale] = scaler.fit_transform(X_train[cols_to_scale])
    
    # Transform test split using the FITTED scaler parameters
    X_test[cols_to_scale] = scaler.transform(X_test[cols_to_scale])
    
    # 6. Save Artifacts
    print("  Saving outputs and serializing scaler...")
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    # Save datasets
    train_df = pd.concat([X_train, y_train], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)
    
    train_path = os.path.join(processed_dir, "train.csv")
    test_path = os.path.join(processed_dir, "test.csv")
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    # Serialize scaler for use during real-time API inference
    scaler_path = os.path.join(models_dir, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    
    print("\nPreprocessing completed successfully!")
    print(f"  - Scaler weights saved: {scaler_path}")
    print(f"  - Train Split shape   : {train_df.shape} (Fraud cases: {y_train.sum()})")
    print(f"  - Test Split shape    : {test_df.shape} (Fraud cases: {y_test.sum()})")

if __name__ == "__main__":
    preprocess_pipeline()
