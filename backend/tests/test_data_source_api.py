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


@pytest.fixture
def test_competitor(client, authenticated_user):
    """Create a test competitor"""
    competitor_data = {
        "name": "Test Company",
        "domain": "testcompany.com",
        "industry": "Technology"
    }
    response = client.post("/competitors/", json=competitor_data, headers=authenticated_user)
    return response.json()


def test_create_data_source_success(client, authenticated_user, test_competitor):
    """Test creating a data source for competitor"""
    competitor_id = test_competitor["id"]
    source_data = {
        "source_type": "website",
        "url": "https://testcompany.com/blog",
        "is_active": True
    }
    
    response = client.post(
        f"/competitors/{competitor_id}/sources",
        json=source_data,
        headers=authenticated_user
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "website"
    assert data["url"] == "https://testcompany.com/blog"
    assert data["competitor_id"] == competitor_id
    assert data["is_active"] is True


def test_get_competitor_sources(client, authenticated_user, test_competitor):
    """Test getting all sources for a competitor"""
    competitor_id = test_competitor["id"]
    
    # Create multiple sources
    sources = [
        {"source_type": "website", "url": "https://testcompany.com"},
        {"source_type": "blog", "url": "https://testcompany.com/blog"},
        {"source_type": "social_media", "url": "https://twitter.com/testcompany"}
    ]
    
    for source in sources:
        client.post(f"/competitors/{competitor_id}/sources", json=source, headers=authenticated_user)
    
    # Get all sources
    response = client.get(f"/competitors/{competitor_id}/sources", headers=authenticated_user)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["source_type"] in ["website", "blog", "social_media"]


def test_create_source_unauthenticated(client, test_competitor):
    """Test creating source without authentication fails"""
    competitor_id = test_competitor["id"]
    source_data = {
        "source_type": "website",
        "url": "https://testcompany.com"
    }
    
    response = client.post(f"/competitors/{competitor_id}/sources", json=source_data)
    
    assert response.status_code == 403


def test_create_source_invalid_competitor(client, authenticated_user):
    """Test creating source for non-existent competitor"""
    source_data = {
        "source_type": "website",
        "url": "https://testcompany.com"
    }
    
    response = client.post("/competitors/9999/sources", json=source_data, headers=authenticated_user)
    
    assert response.status_code == 404