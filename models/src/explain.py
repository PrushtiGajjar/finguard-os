import os
import joblib
import pandas as pd
import shap
import matplotlib.pyplot as plt

def generate_explanations(processed_csv_path="data/processed/test.csv", models_dir="models/trained", output_dir="notebooks"):
    print("Loading test data and model...")
    test_df = pd.read_csv(processed_csv_path)
    X_test = test_df.drop(columns=['isFraud'])
    y_test = test_df['isFraud']
    
    model_path = os.path.join(models_dir, "lgbm_model.pkl")
    model = joblib.load(model_path)
    
    # 1. Initialize the SHAP TreeExplainer
    print("Initializing SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    
    # Let's find some fraud cases in the test set to explain
    fraud_indices = y_test[y_test == 1].index.tolist()
    
    if not fraud_indices:
        print("No fraud cases found in the test split to explain.")
        return
        
    print(f"Found {len(fraud_indices)} fraud cases in the test set.")
    
    # Select the first fraud transaction to analyze
    target_idx = fraud_indices[0]
    transaction = X_test.iloc[[target_idx]]
    actual_label = y_test.iloc[target_idx]
    
    print(f"\nAnalyzing Transaction Index: {target_idx} (Actual: {'FRAUD' if actual_label == 1 else 'LEGITIMATE'})")
    print("Transaction Data:")
    print(transaction.to_string())
    
    # Calculate prediction probability
    pred_prob = model.predict_proba(transaction)[0, 1]
    print(f"Model Prediction Probability (Fraud Risk): {pred_prob * 100:.2f}%")
    
    # 2. Compute SHAP Values
    shap_values = explainer(transaction)
    
    # For LightGBM binary classifier, SHAP outputs values for both classes (0 and 1)
    # We take the values corresponding to Class 1 (Fraud)
    # Note: Depending on SHAP version, shape can be (1, num_features, 2) or (1, num_features)
    if len(shap_values.values.shape) == 3:
        # shape is (1, num_features, 2) -> take index 1 (Fraud)
        instance_shap = shap_values.values[0, :, 1]
        base_value = shap_values.base_values[0, 1]
    else:
        # shape is (1, num_features)
        instance_shap = shap_values.values[0, :]
        base_value = shap_values.base_values[0]
        
    feature_names = X_test.columns.tolist()
    
    # Match features with their SHAP values
    shap_df = pd.DataFrame({
        'Feature': feature_names,
        'Value': transaction.values[0],
        'SHAP Value (Impact)': instance_shap
    })
    
    # Sort by absolute impact
    shap_df['Absolute Impact'] = shap_df['SHAP Value (Impact)'].abs()
    shap_df = shap_df.sort_values(by='Absolute Impact', ascending=False)
    
    print("\n--- SHAP Feature Impact Breakdown (Ordered by Importance) ---")
    print(shap_df[['Feature', 'Value', 'SHAP Value (Impact)']].to_string(index=False))
    
    print("\nInterpretation:")
    print(f"Base Probability Value (prior log-odds): {base_value:.4f}")
    print("Positive SHAP values push the prediction toward FRAUD, negative values push it toward LEGITIMATE.")
    
    # Let's save a summary plot of the entire test set to see global model behavior
    print("\nGenerating Global SHAP Summary Plot on 200 random test samples...")
    sample_size = min(200, len(X_test))
    X_sample = X_test.sample(n=sample_size, random_state=42)
    
    plt.figure(figsize=(10, 6))
    shap_values_global = explainer(X_sample)
    
    if len(shap_values_global.values.shape) == 3:
        shap.summary_plot(shap_values_global.values[:, :, 1], X_sample, show=False)
    else:
        shap.summary_plot(shap_values_global, X_sample, show=False)
        
    plt.title("Global Feature Importance (SHAP Summary Plot)", fontsize=14)
    os.makedirs(output_dir, exist_ok=True)
    summary_plot_path = os.path.join(output_dir, "shap_summary_plot.png")
    plt.tight_layout()
    plt.savefig(summary_plot_path)
    plt.close()
    print(f"[Saved Plot] {summary_plot_path}")

if __name__ == "__main__":
    generate_explanations()
