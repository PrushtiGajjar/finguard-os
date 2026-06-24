import os
import joblib
import pandas as pd
import numpy as np
import shap
from src.schemas import TransactionInput, TransactionEvaluationResponse

class MLEngine:
    def __init__(self, model_path="models/trained/lgbm_model.pkl", scaler_path="models/trained/scaler.pkl"):
        print("ML Engine: Loading model and scaler components...")
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise FileNotFoundError("Model or Scaler weights missing. Please run preprocessing and training first!")
            
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        
        # Initialize SHAP explainer once to save CPU cycles
        self.explainer = shap.TreeExplainer(self.model)
        
        # Core feature sequence order - must match training format exactly!
        self.feature_columns = [
            'step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
            'oldbalanceDest', 'newbalanceDest', 'errorBalanceOrig', 
            'errorBalanceDest', 'is_merchant_dest', 'type_CASH_IN', 
            'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER',
            'velocity_count_24h', 'velocity_amount_24h'
        ]
        
        print("ML Engine: Initialized successfully.")

    def evaluate_transaction(self, tx: TransactionInput, threshold: float = 0.5) -> TransactionEvaluationResponse:
        # 1. Feature Engineering
        error_orig = tx.oldbalanceOrg - tx.newbalanceOrig - tx.amount
        error_dest = tx.newbalanceDest - tx.oldbalanceDest - tx.amount
        is_merchant = 1 if tx.nameDest.startswith('M') else 0
        
        # Build raw feature dictionary
        features = {
            'step': tx.step,
            'amount': tx.amount,
            'oldbalanceOrg': tx.oldbalanceOrg,
            'newbalanceOrig': tx.newbalanceOrig,
            'oldbalanceDest': tx.oldbalanceDest,
            'newbalanceDest': tx.newbalanceDest,
            'errorBalanceOrig': error_orig,
            'errorBalanceDest': error_dest,
            'is_merchant_dest': is_merchant,
            'velocity_count_24h': getattr(tx, 'velocity_count_24h', 0.0),
            'velocity_amount_24h': getattr(tx, 'velocity_amount_24h', 0.0)
        }
        
        # 2. Categorical Encoding Alignment
        for t in ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']:
            features[f'type_{t}'] = 1 if tx.type == t else 0
            
        # 3. Create DataFrame and enforce order
        df_inf = pd.DataFrame([features])[self.feature_columns]
        
        # 4. Feature Scaling (Transform only)
        cols_to_scale = ['amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest', 'velocity_amount_24h', 'velocity_count_24h']
        df_inf[cols_to_scale] = self.scaler.transform(df_inf[cols_to_scale])
        
        # 5. Model Inference
        # Get probability output
        prob = float(self.model.predict_proba(df_inf)[0, 1])
        is_fraud = prob >= threshold
        needs_review = is_fraud
        
        # 6. Generate local explanation ONLY if flagged (saves latency)
        explanations = None
        if is_fraud:
            shap_values = self.explainer(df_inf)
            
            # Extract impact array
            if len(shap_values.values.shape) == 3:
                # Shape: (1, num_features, 2)
                impact_values = shap_values.values[0, :, 1]
            else:
                # Shape: (1, num_features)
                impact_values = shap_values.values[0, :]
                
            # Create a dictionary matching feature names with SHAP attribution values
            explanations = {
                self.feature_columns[i]: float(impact_values[i])
                for i in range(len(self.feature_columns))
            }
            
            # Sort explanations by absolute impact and keep top 5
            explanations = dict(
                sorted(explanations.items(), key=lambda item: abs(item[1]), reverse=True)[:5]
            )
            
        return TransactionEvaluationResponse(
            is_fraud=is_fraud,
            fraud_score=prob,
            needs_review=needs_review,
            explanations=explanations
        )
