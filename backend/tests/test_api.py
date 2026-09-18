import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_optimize_energy_malformed():
    response = client.post("/optimize-energy", json={"invalid": "data"})
    assert response.status_code == 400
    assert "detail" in response.json()
