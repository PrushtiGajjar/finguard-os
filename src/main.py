import os
import uuid
import json
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from src.schemas import TransactionInput, TransactionEvaluationResponse
from src.ml_engine import MLEngine
from src.database import engine, Base, get_db
from src.models import AccountDB, TransactionDB

app = FastAPI(
    title="FinGuard: Real-Time Fraud Detection API",
    description="Asynchronous fraud evaluation, persistence, and explainable AI server.",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ML Engine container
ml_engine = None

@app.on_event("startup")
def startup_load_models_and_db():
    global ml_engine
    try:
        # Create database tables if they do not exist
        print("FastAPI Application: Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Resolve path relative to this script
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models", "trained", "lgbm_model.pkl")
        scaler_path = os.path.join(base_dir, "models", "trained", "scaler.pkl")
        
        ml_engine = MLEngine(model_path=model_path, scaler_path=scaler_path)
        print("FastAPI Application: ML weights and database initialized successfully.")
    except Exception as e:
        print(f"CRITICAL: Failed to load ML components. Details: {e}")
        raise e

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Simple service availability check."""
    if ml_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="ML components are not ready."
        )
    return {"status": "healthy", "service": "FinGuard Fraud API"}

@app.post(
    "/api/v1/transactions/evaluate", 
    response_model=TransactionEvaluationResponse, 
    status_code=status.HTTP_200_OK
)
def evaluate_transaction(tx: TransactionInput, db: Session = Depends(get_db)):
    """
    Evaluate an incoming financial transaction for fraud risk in real-time.
    Persists the transaction records and updates account states in the database.
    """
    if ml_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="ML Inference engine is offline."
        )
    try:
        # 1. Get-or-Create Origin Account
        orig_account = db.query(AccountDB).filter(AccountDB.id == tx.nameOrig).first()
        if not orig_account:
            orig_account = AccountDB(
                id=tx.nameOrig,
                customer_name=f"Customer {tx.nameOrig[1:]}",
                current_balance=tx.oldbalanceOrg,
                status="active"
            )
            db.add(orig_account)
            
        # 2. Get-or-Create Destination Account
        dest_account = db.query(AccountDB).filter(AccountDB.id == tx.nameDest).first()
        if not dest_account:
            dest_account = AccountDB(
                id=tx.nameDest,
                customer_name="Merchant Portal" if tx.nameDest.startswith('M') else f"Customer {tx.nameDest[1:]}",
                current_balance=tx.oldbalanceDest,
                status="active"
            )
            db.add(dest_account)
            
        # Commit account creations so far to prevent foreign key errors
        db.commit()

        # 3. Dynamic Velocity Feature Engineering (Query past 24 hours of transactions)
        # Note: Since the simulation uses 'step' (hours), in a real DB we use timestamps.
        # We will approximate this by grabbing all transactions for the origin account in the last 24h.
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        
        velocity_stats = db.query(
            func.count(TransactionDB.id).label('tx_count'),
            func.sum(TransactionDB.amount).label('tx_sum')
        ).filter(
            TransactionDB.origin_account_id == tx.nameOrig,
            TransactionDB.timestamp >= time_threshold
        ).first()

        tx.velocity_count_24h = float(velocity_stats.tx_count or 0.0)
        tx.velocity_amount_24h = float(velocity_stats.tx_sum or 0.0)

        # 4. Call ML Engine for Fraud Score & SHAP
        result = ml_engine.evaluate_transaction(tx, threshold=0.5)
        
        # 4. Update balance records to match the incoming transaction state
        orig_account.current_balance = tx.newbalanceOrig
        dest_account.current_balance = tx.newbalanceDest
        
        # If flagged, raise customer/account risk score
        if result.is_fraud:
            orig_account.risk_score = max(orig_account.risk_score, result.fraud_score)
            if orig_account.risk_score > 0.8:
                orig_account.status = "under_review"

        # 5. Persist Transaction Record
        tx_id = str(uuid.uuid4())
        shap_str = json.dumps(result.explanations) if result.explanations else None
        
        db_tx = TransactionDB(
            id=tx_id,
            origin_account_id=tx.nameOrig,
            dest_account_id=tx.nameDest,
            amount=tx.amount,
            transaction_type=tx.type,
            old_balance_orig=tx.oldbalanceOrg,
            new_balance_orig=tx.newbalanceOrig,
            old_balance_dest=tx.oldbalanceDest,
            new_balance_dest=tx.newbalanceDest,
            is_fraud=result.is_fraud,
            fraud_score=result.fraud_score,
            needs_review=result.needs_review,
            shap_values=shap_str
        )
        
        db.add(db_tx)
        db.commit()
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}"
        )

@app.get("/api/v1/accounts/{account_id}")
def get_account_dossier(account_id: str, db: Session = Depends(get_db)):
    """Fetch an account profile and its transaction history."""
    account = db.query(AccountDB).filter(AccountDB.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    transactions = db.query(TransactionDB).filter(
        (TransactionDB.origin_account_id == account_id) | 
        (TransactionDB.dest_account_id == account_id)
    ).order_by(TransactionDB.timestamp.desc()).all()
    
    return {
        "account_id": account.id,
        "customer_name": account.customer_name,
        "current_balance": account.current_balance,
        "status": account.status,
        "risk_score": account.risk_score,
        "transactions": [
            {
                "id": tx.id,
                "origin_account_id": tx.origin_account_id,
                "dest_account_id": tx.dest_account_id,
                "amount": tx.amount,
                "type": tx.transaction_type,
                "is_fraud": tx.is_fraud,
                "fraud_score": tx.fraud_score,
                "timestamp": tx.timestamp.isoformat()
            } for tx in transactions
        ]
    }


# Mount the static directory to serve the frontend dashboard
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    print(f"FastAPI Application: Mounted static files from {static_dir}")
else:
    print(f"WARNING: Static dashboard files directory not found at {static_dir}")
