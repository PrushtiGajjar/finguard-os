from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class AccountDB(Base):
    __tablename__ = "accounts"
    
    id = Column(String(50), primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    current_balance = Column(Float, default=0.0)
    status = Column(String(20), default="active")
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    outgoing_transactions = relationship(
        "TransactionDB", 
        foreign_keys="TransactionDB.origin_account_id", 
        backref="origin_account"
    )
    incoming_transactions = relationship(
        "TransactionDB", 
        foreign_keys="TransactionDB.dest_account_id", 
        backref="dest_account"
    )

class TransactionDB(Base):
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, index=True)
    origin_account_id = Column(String(50), ForeignKey("accounts.id"), nullable=False)
    dest_account_id = Column(String(50), ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)
    old_balance_orig = Column(Float, nullable=False)
    new_balance_orig = Column(Float, nullable=False)
    old_balance_dest = Column(Float, nullable=False)
    new_balance_dest = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # ML Scoring Outputs
    is_fraud = Column(Boolean, default=False, index=True)
    fraud_score = Column(Float, default=0.0)
    needs_review = Column(Boolean, default=False)
    shap_values = Column(Text, nullable=True) # Stores JSON serialized SHAP feature impacts
    
    # Resolution fields
    analyst_decision = Column(String(20), default=None, nullable=True)
    reviewed_at = Column(DateTime, default=None, nullable=True)
