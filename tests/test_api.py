import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="module")
def client():
    """Fixture to provide a test client with startup and shutdown events triggered."""
    # Using 'with' context manager ensures FastAPI startup event handlers run!
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    """Verify health status endpoint responds correctly."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_legitimate_transaction(client):
    """Verify that a normal, small amount transaction is marked legitimate."""
    payload = {
        "step": 1,
        "type": "PAYMENT",
        "amount": 125.50,
        "nameOrig": "C100000001",
        "oldbalanceOrg": 5000.00,
        "newbalanceOrig": 4874.50,
        "nameDest": "M999999999",
        "oldbalanceDest": 0.00,
        "newbalanceDest": 0.00
    }
    response = client.post("/api/v1/transactions/evaluate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "is_fraud" in data
    assert "fraud_score" in data
    assert "needs_review" in data
    
    # Legit payment should not flag as fraud
    assert data["is_fraud"] is False
    assert data["explanations"] is None

def test_fraudulent_transaction(client):
    """Verify that a high-value account-draining transfer is flagged with SHAP explanations."""
    payload = {
        "step": 10,
        "type": "TRANSFER",
        "amount": 500000.00,
        "nameOrig": "C200000002",
        # Balance is completely drained
        "oldbalanceOrg": 500000.00,
        "newbalanceOrig": 0.00,
        "nameDest": "C300000003",
        # Recipient balance does not increase correctly (classic fraud discrepancy)
        "oldbalanceDest": 0.00,
        "newbalanceDest": 0.00
    }
    response = client.post("/api/v1/transactions/evaluate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    # High probability fraud check
    assert data["is_fraud"] is True
    assert data["fraud_score"] > 0.5
    
    # Check that SHAP explanations are successfully populated for flagged transactions
    assert data["explanations"] is not None
    assert isinstance(data["explanations"], dict)
    assert len(data["explanations"]) > 0
    
    # Check that key features like newbalanceOrig or errorBalanceDest are represented in explanation
    features_present = list(data["explanations"].keys())
    assert any(feat in features_present for feat in ['newbalanceOrig', 'errorBalanceDest'])
