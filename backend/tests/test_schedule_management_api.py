import pytest
from datetime import datetime, timedelta, timezone
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
def test_data_source_with_schedule(client, authenticated_user):
    """Create competitor, data source, and schedule"""
    # Create competitor
    competitor_data = {
        "name": "Test Company",
        "domain": "testcompany.com",
        "industry": "Technology"
    }
    competitor_response = client.post("/competitors/", json=competitor_data, headers=authenticated_user)
    competitor = competitor_response.json()
    
    # Create data source
    source_data = {
        "source_type": "website",
        "url": "https://testcompany.com/blog",
        "is_active": True
    }
    source_response = client.post(f"/competitors/{competitor['id']}/sources", json=source_data, headers=authenticated_user)
    source = source_response.json()
    
    # Create schedule
    schedule_data = {
        "frequency_minutes": 60,
        "is_active": True
    }
    schedule_response = client.post(f"/schedules/sources/{source['id']}", json=schedule_data, headers=authenticated_user)
    
    return {
        "competitor": competitor,
        "source": source,
        "schedule": schedule_response.json()
    }


def test_create_schedule_for_source(client, authenticated_user):
    """Test creating a schedule for a data source"""
    # Create competitor and source first
    competitor_data = {"name": "Test Company", "domain": "testcompany.com"}
    competitor_response = client.post("/competitors/", json=competitor_data, headers=authenticated_user)
    competitor_id = competitor_response.json()["id"]
    
    source_data = {"source_type": "website", "url": "https://testcompany.com"}
    source_response = client.post(f"/competitors/{competitor_id}/sources", json=source_data, headers=authenticated_user)
    source_id = source_response.json()["id"]
    
    # Create schedule
    schedule_data = {
        "frequency_minutes": 120,  # Every 2 hours
        "is_active": True
    }
    
    response = client.post(f"/schedules/sources/{source_id}", json=schedule_data, headers=authenticated_user)
    
    assert response.status_code == 201
    data = response.json()
    assert data["frequency_minutes"] == 120
    assert data["is_active"] is True
    assert data["data_source_id"] == source_id
    assert "next_run" in data


def test_get_schedule_for_source(client, authenticated_user, test_data_source_with_schedule):
    """Test getting schedule for a data source"""
    source_id = test_data_source_with_schedule["source"]["id"]
    
    response = client.get(f"/schedules/sources/{source_id}", headers=authenticated_user)
    
    assert response.status_code == 200
    data = response.json()
    assert data["frequency_minutes"] == 60
    assert data["data_source_id"] == source_id


def test_update_schedule(client, authenticated_user, test_data_source_with_schedule):
    """Test updating a schedule"""
    schedule_id = test_data_source_with_schedule["schedule"]["id"]
    
    update_data = {
        "frequency_minutes": 180,  # Change to 3 hours
        "is_active": False
    }
    
    response = client.put(f"/schedules/{schedule_id}", json=update_data, headers=authenticated_user)
    
    assert response.status_code == 200
    data = response.json()
    assert data["frequency_minutes"] == 180
    assert data["is_active"] is False


def test_delete_schedule(client, authenticated_user, test_data_source_with_schedule):
    """Test deleting a schedule"""
    schedule_id = test_data_source_with_schedule["schedule"]["id"]
    
    response = client.delete(f"/schedules/{schedule_id}", headers=authenticated_user)
    
    assert response.status_code == 204
    
    # Verify schedule is deleted
    source_id = test_data_source_with_schedule["source"]["id"]
    get_response = client.get(f"/schedules/sources/{source_id}", headers=authenticated_user)
    assert get_response.status_code == 404


def test_get_all_user_schedules(client, authenticated_user, test_data_source_with_schedule):
    """Test getting all schedules for a user"""
    response = client.get("/schedules/", headers=authenticated_user)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["frequency_minutes"] == 60


def test_create_schedule_unauthenticated(client):
    """Test creating schedule without authentication fails"""
    schedule_data = {"frequency_minutes": 60, "is_active": True}
    
    response = client.post("/schedules/sources/1", json=schedule_data)
    
    assert response.status_code == 403


def test_create_schedule_nonexistent_source(client, authenticated_user):
    """Test creating schedule for non-existent source"""
    schedule_data = {"frequency_minutes": 60, "is_active": True}
    
    response = client.post("/schedules/sources/9999", json=schedule_data, headers=authenticated_user)
    
    assert response.status_code == 404


def test_create_duplicate_schedule(client, authenticated_user, test_data_source_with_schedule):
    """Test creating duplicate schedule for same source fails"""
    source_id = test_data_source_with_schedule["source"]["id"]
    schedule_data = {"frequency_minutes": 60, "is_active": True}
    
    response = client.post(f"/schedules/sources/{source_id}", json=schedule_data, headers=authenticated_user)
    
    assert response.status_code == 400
    assert "already has a schedule" in response.json()["detail"]