from pydantic import BaseModel, Field
from typing import Optional, Dict

class TransactionInput(BaseModel):
    step: int = Field(..., description="Hour of the month (1-744)", ge=1, le=744)
    type: str = Field(..., description="Transaction category", pattern="^(PAYMENT|TRANSFER|CASH_OUT|CASH_IN|DEBIT)$")
    amount: float = Field(..., description="Value of transaction in currency units", gt=0)
    nameOrig: str = Field(..., description="Initiating customer ID", min_length=3)
    oldbalanceOrg: float = Field(..., description="Origin balance before transaction", ge=0)
    newbalanceOrig: float = Field(..., description="Origin balance after transaction", ge=0)
    nameDest: str = Field(..., description="Recipient customer/merchant ID", min_length=3)
    oldbalanceDest: float = Field(..., description="Destination balance before transaction", ge=0)
    newbalanceDest: float = Field(..., description="Destination balance after transaction", ge=0)
    
    # Dynamically injected by backend
    velocity_count_24h: float = 0.0
    velocity_amount_24h: float = 0.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "step": 12,
                "type": "TRANSFER",
                "amount": 250000.00,
                "nameOrig": "C192837465",
                "oldbalanceOrg": 250000.00,
                "newbalanceOrig": 0.00,
                "nameDest": "C987654321",
                "oldbalanceDest": 0.00,
                "newbalanceDest": 0.00
            }
        }
    }

class TransactionEvaluationResponse(BaseModel):
    is_fraud: bool
    fraud_score: float = Field(..., description="Model prediction probability")
    needs_review: bool = Field(..., description="Set to true if probability is high or flagged by rules")
    explanations: Optional[Dict[str, float]] = Field(None, description="SHAP feature attribution impact logs")
