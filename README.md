# FinGuard OS: Enterprise A.I. Fraud Command Center

FinGuard OS is a next-generation, A.I.-powered threat detection and response system designed to protect financial networks from sophisticated cyber attacks, including rapid-fire "smurfing" techniques and complex concept drift scenarios.

Built with an ultra-responsive, cyber-themed frontend and an intelligent machine learning backend, FinGuard OS actively monitors network traffic, evaluates transaction risk in real-time, and provides forensic explainability for every security decision.

## 🚀 Core Features

- **Real-Time Threat Detection API**: Powered by a robust FastAPI backend, the system instantly evaluates incoming transactions, checking them against historical data and advanced machine learning models.
- **Velocity & Smurfing Defense**: Unlike traditional systems that evaluate transactions in a vacuum, FinGuard OS tracks 24-hour rolling velocity metrics. It catches malicious actors attempting to drain accounts using hundreds of micro-transactions (smurfing) by tracking `velocity_count_24h` and `velocity_amount_24h`.
- **LightGBM Classification Core**: The brain of the operation uses an optimized LightGBM model trained on highly imbalanced synthetic financial datasets (using SMOTE), capable of detecting microscopic anomalies in behavior.
- **SHAP Forensic Explainability**: When a transaction is blocked, the AI doesn't just return a score—it provides a comprehensive SHAP (SHapley Additive exPlanations) attribution graph. This allows security analysts to see exactly *why* the AI flagged a transaction (e.g., "Origin balance was fully drained," or "Velocity count exceeded threshold").
- **Interactive Cyber Dashboard**: A beautiful, fully responsive vanilla HTML/CSS/JS frontend featuring a high-contrast theme, live system stats tickers, and a manual injection portal for testing payload vectors.
- **Dynamic Account Dossiers**: Instantly pull up an entity's complete transaction history and risk profile via the built-in search.

## 🛠️ Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Uvicorn
- **Machine Learning**: Scikit-Learn, LightGBM, SHAP, Pandas, Imbalanced-Learn
- **Database**: SQLite
- **Frontend**: Vanilla HTML5, CSS3, JavaScript, Chart.js

## ⚙️ Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/finguard-os.git
   cd finguard-os
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Train the ML Model:**
   *Note: Place your dataset in the `data/` folder before running.*
   ```bash
   python src/train_model.py
   ```

4. **Launch the Server:**
   ```bash
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the Dashboard:**
   Open your browser and navigate to `http://localhost:8000/`.
