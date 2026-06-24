import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_basic_eda(csv_path="data/raw/transactions.csv", output_dir="notebooks"):
    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # 1. Basic Dimensions
    print("\n--- 1. Dataset Shape ---")
    print(f"Total Rows (Transactions): {df.shape[0]}")
    print(f"Total Columns (Features): {df.shape[1]}")
    print(f"Columns: {list(df.columns)}")
    
    # 2. Check for missing values
    print("\n--- 2. Missing Values Check ---")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("No missing values found in the dataset! Clean ingestion.")
    else:
        print(missing[missing > 0])
        
    # 3. Class Imbalance
    print("\n--- 3. Class Distribution (isFraud) ---")
    counts = df['isFraud'].value_counts()
    percentages = df['isFraud'].value_counts(normalize=True) * 100
    for idx in counts.index:
        label = "Fraudulent" if idx == 1 else "Legitimate"
        print(f"  {label:12}: {counts[idx]:6d} records ({percentages[idx]:.3f}%)")
        
    # 4. Transaction Types Analysis
    print("\n--- 4. Transaction Type Distribution ---")
    type_counts = df['type'].value_counts()
    type_pct = df['type'].value_counts(normalize=True) * 100
    for idx in type_counts.index:
         print(f"  {idx:10}: {type_counts[idx]:6d} records ({type_pct[idx]:.1f}%)")
         
    # 5. Fraud occurrences by transaction type
    print("\n--- 5. Fraud Occurrences by Transaction Type ---")
    fraud_by_type = df.groupby('type')['isFraud'].sum()
    fraud_rates = df.groupby('type')['isFraud'].mean() * 100
    for idx in fraud_by_type.index:
        print(f"  {idx:10}: {fraud_by_type[idx]:4d} fraud cases (Rate: {fraud_rates[idx]:.3f}%)")

    # Generate Visualizations
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style="darkgrid")
    
    # Plot 1: Class Distribution
    plt.figure(figsize=(6, 5))
    ax = sns.countplot(x='isFraud', data=df, palette=['#4f46e5', '#ef4444'])
    plt.title("Class Distribution (0 = Legitimate, 1 = Fraudulent)")
    plt.xticks([0, 1], ["Legitimate", "Fraudulent"])
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', xytext=(0, 5), textcoords='offset points')
    plot1_path = os.path.join(output_dir, "class_distribution.png")
    plt.tight_layout()
    plt.savefig(plot1_path)
    plt.close()
    print(f"\n[Saved Plot] {plot1_path}")
    
    # Plot 2: Transaction Types Distribution
    plt.figure(figsize=(8, 5))
    sns.countplot(x='type', data=df, order=df['type'].value_counts().index, palette="viridis")
    plt.title("Transaction Volume by Type")
    plt.xlabel("Transaction Type")
    plt.ylabel("Count")
    plot2_path = os.path.join(output_dir, "transaction_types.png")
    plt.tight_layout()
    plt.savefig(plot2_path)
    plt.close()
    print(f"[Saved Plot] {plot2_path}")
    
    # Plot 3: Fraud cases by transaction type (only showing types with fraud)
    plt.figure(figsize=(8, 5))
    fraud_df = df[df['isFraud'] == 1]
    if not fraud_df.empty:
        sns.countplot(x='type', data=fraud_df, order=df['type'].value_counts().index, palette="flare")
        plt.title("Fraudulent Transactions by Type")
        plt.xlabel("Transaction Type")
        plt.ylabel("Fraud Count")
    else:
        plt.text(0.5, 0.5, "No fraud cases to plot", ha='center', va='center')
    plot3_path = os.path.join(output_dir, "fraud_by_type.png")
    plt.tight_layout()
    plt.savefig(plot3_path)
    plt.close()
    print(f"[Saved Plot] {plot3_path}")
    
    print("\nEDA Completed successfully! Plots generated in the 'notebooks' folder.")

if __name__ == "__main__":
    run_basic_eda()
