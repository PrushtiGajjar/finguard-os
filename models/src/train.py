import os
import joblib
import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTE
from sklearn.linear_model import LogisticRegression
from lightgbm import LGBMClassifier
from sklearn.metrics import classification_report, precision_recall_curve, auc, f1_score

def train_and_evaluate(processed_dir="data/processed", models_dir="models/trained"):
    print("Loading processed datasets...")
    train_path = os.path.join(processed_dir, "train.csv")
    test_path = os.path.join(processed_dir, "test.csv")
    
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    # Separate features and target
    X_train = train_df.drop(columns=['isFraud'])
    y_train = train_df['isFraud']
    X_test = test_df.drop(columns=['isFraud'])
    y_test = test_df['isFraud']
    
    print(f"Original Training shape: {X_train.shape} (Fraud cases: {y_train.sum()})")
    
    # 1. Baseline Model: Logistic Regression (No class balance handling)
    print("\n--- Training Baseline: Logistic Regression (No Balances) ---")
    lr_model = LogisticRegression(max_iter=1000, random_state=42)
    lr_model.fit(X_train, y_train)
    
    lr_preds = lr_model.predict(X_test)
    lr_probs = lr_model.predict_proba(X_test)[:, 1]
    
    lr_precision, lr_recall, _ = precision_recall_curve(y_test, lr_probs)
    lr_pr_auc = auc(lr_recall, lr_precision)
    
    print("Logistic Regression Results:")
    print(classification_report(y_test, lr_preds, zero_division=0))
    print(f"PR-AUC: {lr_pr_auc:.4f}")
    
    # 2. Imbalance Mitigation: Apply SMOTE only to the Training Set
    print("\n--- Applying SMOTE to Training Partition ---")
    # We set k_neighbors=5 (default)
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    print(f"Resampled Training shape: {X_train_res.shape} (Fraud cases: {y_train_res.sum()})")
    
    # 3. Advanced Model: LightGBM Classifier (Trained on SMOTE Resampled Data)
    print("\n--- Training Advanced Model: LightGBM (on SMOTE data) ---")
    # verbosity=-1 silences warnings about multi-threading
    lgbm_model = LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=6,
        random_state=42,
        verbosity=-1
    )
    lgbm_model.fit(X_train_res, y_train_res)
    
    lgbm_preds = lgbm_model.predict(X_test)
    lgbm_probs = lgbm_model.predict_proba(X_test)[:, 1]
    
    lgbm_precision, lgbm_recall, _ = precision_recall_curve(y_test, lgbm_probs)
    lgbm_pr_auc = auc(lgbm_recall, lgbm_precision)
    lgbm_f1 = f1_score(y_test, lgbm_preds)
    
    print("LightGBM Results:")
    print(classification_report(y_test, lgbm_preds))
    print(f"PR-AUC  : {lgbm_pr_auc:.4f}")
    print(f"F1-Score: {lgbm_f1:.4f}")
    
    # 4. Save the best model
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "lgbm_model.pkl")
    joblib.dump(lgbm_model, model_path)
    print(f"\nSaved best performing model (LightGBM) to {model_path}")
    
if __name__ == "__main__":
    train_and_evaluate()
