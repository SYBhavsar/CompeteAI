import pytest
from fastapi.testclient import TestClient


def test_root_endpoint():
    """Test the root endpoint returns correct message"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "AI Competitive Intelligence Platform API"}


def test_health_check_endpoint():
    """Test the health check endpoint returns healthy status"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}