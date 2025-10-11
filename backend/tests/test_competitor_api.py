import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, Base, engine


@pytest.fixture
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def authenticated_user(client):
    """Create and authenticate a user"""
    # Register user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    client.post("/auth/register", json=user_data)
    
    # Login and get token
    login_data = {"email": "test@example.com", "password": "testpassword123"}
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


def test_create_competitor_success(client, authenticated_user):
    """Test creating a competitor"""
    competitor_data = {
        "name": "Test Company",
        "domain": "testcompany.com",
        "industry": "Technology"
    }
    
    response = client.post(
        "/competitors/", 
        json=competitor_data,
        headers=authenticated_user
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["domain"] == "testcompany.com"
    assert data["industry"] == "Technology"
    assert "id" in data


def test_get_user_competitors(client, authenticated_user):
    """Test getting user's competitors"""
    # Create a competitor first
    competitor_data = {
        "name": "Test Company",
        "domain": "testcompany.com",
        "industry": "Technology"
    }
    client.post("/competitors/", json=competitor_data, headers=authenticated_user)
    
    # Get competitors
    response = client.get("/competitors/", headers=authenticated_user)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Company"


def test_create_competitor_unauthenticated(client):
    """Test creating competitor without authentication fails"""
    competitor_data = {
        "name": "Test Company",
        "domain": "testcompany.com"
    }
    
    response = client.post("/competitors/", json=competitor_data)
    
    assert response.status_code == 403