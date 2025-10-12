import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

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
def test_competitor_with_sources(client, authenticated_user):
    """Create a test competitor with data sources"""
    # Create competitor
    competitor_data = {
        "name": "Test Company",
        "domain": "testcompany.com",
        "industry": "Technology"
    }
    competitor_response = client.post("/competitors/", json=competitor_data, headers=authenticated_user)
    competitor = competitor_response.json()
    
    # Create data sources
    sources_data = [
        {"source_type": "website", "url": "https://testcompany.com", "is_active": True},
        {"source_type": "blog", "url": "https://testcompany.com/blog", "is_active": True}
    ]
    
    for source_data in sources_data:
        client.post(f"/competitors/{competitor['id']}/sources", json=source_data, headers=authenticated_user)
    
    return competitor


@patch('app.api.scraping.scrape_data_source.delay')
def test_trigger_scraping_for_competitor(mock_task, client, authenticated_user, test_competitor_with_sources):
    """Test triggering scraping for all competitor sources"""
    competitor_id = test_competitor_with_sources["id"]
    
    # Mock task
    mock_task.return_value = Mock(id="task-123")
    
    response = client.post(f"/scraping/competitors/{competitor_id}/scrape", headers=authenticated_user)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Scraping tasks started"
    assert data["competitor_id"] == competitor_id
    assert len(data["task_ids"]) == 2  # Two sources
    assert mock_task.call_count == 2


@patch('app.api.scraping.scrape_data_source.delay')
def test_trigger_scraping_for_single_source(mock_task, client, authenticated_user, test_competitor_with_sources):
    """Test triggering scraping for single data source"""
    competitor_id = test_competitor_with_sources["id"]
    
    # Get first source
    sources_response = client.get(f"/competitors/{competitor_id}/sources", headers=authenticated_user)
    sources = sources_response.json()
    source_id = sources[0]["id"]
    
    # Mock task
    mock_task.return_value = Mock(id="task-456")
    
    response = client.post(f"/scraping/sources/{source_id}/scrape", headers=authenticated_user)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Scraping task started"
    assert data["source_id"] == source_id
    assert "task_id" in data
    mock_task.assert_called_once_with(source_id)


def test_trigger_scraping_unauthenticated(client, test_competitor_with_sources):
    """Test triggering scraping without authentication fails"""
    competitor_id = test_competitor_with_sources["id"]
    
    response = client.post(f"/scraping/competitors/{competitor_id}/scrape")
    
    assert response.status_code == 403


def test_trigger_scraping_nonexistent_competitor(client, authenticated_user):
    """Test triggering scraping for non-existent competitor"""
    response = client.post("/scraping/competitors/9999/scrape", headers=authenticated_user)
    
    assert response.status_code == 404
    assert "Competitor not found" in response.json()["detail"]


def test_trigger_scraping_nonexistent_source(client, authenticated_user):
    """Test triggering scraping for non-existent source"""
    response = client.post("/scraping/sources/9999/scrape", headers=authenticated_user)
    
    assert response.status_code == 404
    assert "Data source not found" in response.json()["detail"]