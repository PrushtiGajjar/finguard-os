import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from imblearn.over_sampling import SMOTE
from lightgbm import LGBMClassifier

def run_ml_pipeline():
    print("--- FINGUARD MLOps PIPELINE ---")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "raw", "transactions.csv")
    models_dir = os.path.join(base_dir, "models", "trained")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Raw dataset missing at {data_path}")
        
    print(f"[1/5] Loading raw data from {data_path}...")
    df = pd.read_csv(data_path)
    
    print("[2/5] Engineering core and advanced velocity features...")
    # Base engineered features
    df['errorBalanceOrig'] = df['oldbalanceOrg'] - df['newbalanceOrig'] - df['amount']
    df['errorBalanceDest'] = df['newbalanceDest'] - df['oldbalanceDest'] - df['amount']
    df['is_merchant_dest'] = df['nameDest'].str.startswith('M').astype(int)
    
    # One-hot encode types
    type_dummies = pd.get_dummies(df['type'], prefix='type', dtype=int)
    # Ensure all columns exist even if not in dataset
    for t in ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']:
        col = f'type_{t}'
        if col not in type_dummies.columns:
            type_dummies[col] = 0
            
    # Reorder type_dummies to match the explicit order
    type_dummies = type_dummies[['type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER']]
    df = pd.concat([df, type_dummies], axis=1)
    
    # --- NEW: VELOCITY FEATURE ENGINEERING ---
    # Sort by origin account and step (time)
    df.sort_values(by=['nameOrig', 'step'], inplace=True)
    
    # Calculate historical count and amount for each account BEFORE the current transaction
    df['velocity_count_24h'] = df.groupby('nameOrig').cumcount()
    
    # Cumulative sum of amounts minus the current transaction amount
    df['velocity_amount_24h'] = df.groupby('nameOrig')['amount'].cumsum() - df['amount']
    # ----------------------------------------
    
    # Revert to original index just in case
    df.sort_index(inplace=True)
    
    columns_to_drop = ['nameOrig', 'nameDest', 'type', 'isFlaggedFraud']
    df = df.drop(columns=columns_to_drop, errors='ignore')
    
    # Important: Reorder X exactly how MLEngine expects it
    feature_columns = [
        'step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
        'oldbalanceDest', 'newbalanceDest', 'errorBalanceOrig', 
        'errorBalanceDest', 'is_merchant_dest', 'type_CASH_IN', 
        'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER',
        'velocity_count_24h', 'velocity_amount_24h'
    ]
    
    X = df[feature_columns]
    y = df['isFraud']
    
    print(f"Features mapped: {list(X.columns)}")
    
    print("[3/5] Splitting data and applying RobustScaler...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    cols_to_scale = ['amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest', 'velocity_amount_24h', 'velocity_count_24h']
    scaler = RobustScaler()
    X_train[cols_to_scale] = scaler.fit_transform(X_train[cols_to_scale])
    X_test[cols_to_scale] = scaler.transform(X_test[cols_to_scale])
    
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(scaler, os.path.join(models_dir, "scaler.pkl"))
    
    print("[4/5] Applying SMOTE for severe class imbalance...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    
    print(f"   Original Training Shape: {X_train.shape}, Frauds: {sum(y_train)}")
    print(f"   Resampled Training Shape: {X_train_res.shape}, Frauds: {sum(y_train_res)}")
    
    print("[5/5] Training LightGBM Model with Velocity Rules...")
    lgbm_model = LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=6,
        random_state=42,
        verbosity=-1
    )
    lgbm_model.fit(X_train_res, y_train_res)
    
    joblib.dump(lgbm_model, os.path.join(models_dir, "lgbm_model.pkl"))
    
    print("--- SUCCESS: PIPELINE COMPLETE ---")
    print(f"Weights saved to {models_dir}")

if __name__ == "__main__":
    run_ml_pipeline()
