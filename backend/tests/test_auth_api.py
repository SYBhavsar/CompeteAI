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


def test_register_user_success(client):
    """Test successful user registration"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "password" not in data  # Password should not be returned


def test_register_user_duplicate_email(client):
    """Test registration with duplicate email fails"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    # Register first user
    client.post("/auth/register", json=user_data)
    
    # Try to register with same email
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_user_success(client):
    """Test successful user login"""
    # First register a user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    client.post("/auth/register", json=user_data)
    
    # Now login
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_invalid_credentials(client):
    """Test login with invalid credentials fails"""
    # Register a user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    client.post("/auth/register", json=user_data)
    
    # Try login with wrong password
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]