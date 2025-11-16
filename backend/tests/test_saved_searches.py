import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User
from app.models.search import SavedSearch, SearchHistory


@pytest.fixture
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_and_token(client):
    """Create test user and get auth token"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    client.post("/auth/register", json=user_data)

    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


def test_create_saved_search(client, test_user_and_token):
    """Test creating a saved search"""
    headers = test_user_and_token["headers"]

    search_data = {
        "name": "My Important Search",
        "search_type": "semantic",
        "query": "product launches",
        "filters": {"competitor_id": 1}
    }

    response = client.post("/search/saved", json=search_data, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Important Search"
    assert data["search_type"] == "semantic"
    assert data["query"] == "product launches"
    assert data["filters"]["competitor_id"] == 1


def test_get_all_saved_searches(client, test_user_and_token):
    """Test getting all saved searches"""
    headers = test_user_and_token["headers"]

    # Create a saved search first
    search_data = {
        "name": "Test Search",
        "search_type": "traditional",
        "query": "competitor analysis"
    }
    client.post("/search/saved", json=search_data, headers=headers)

    response = client.get("/search/saved", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Test Search"


def test_get_saved_search_by_id(client, test_user_and_token):
    """Test getting a specific saved search"""
    headers = test_user_and_token["headers"]

    # Create saved search
    search_data = {
        "name": "Specific Search",
        "search_type": "semantic",
        "query": "market trends"
    }
    create_response = client.post("/search/saved", json=search_data, headers=headers)
    search_id = create_response.json()["id"]

    response = client.get(f"/search/saved/{search_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == search_id
    assert data["name"] == "Specific Search"


def test_update_saved_search(client, test_user_and_token):
    """Test updating a saved search"""
    headers = test_user_and_token["headers"]

    # Create saved search
    search_data = {
        "name": "Original Name",
        "search_type": "semantic",
        "query": "original query"
    }
    create_response = client.post("/search/saved", json=search_data, headers=headers)
    search_id = create_response.json()["id"]

    # Update saved search
    update_data = {
        "name": "Updated Name",
        "query": "updated query"
    }
    response = client.put(f"/search/saved/{search_id}", json=update_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["query"] == "updated query"
    assert data["search_type"] == "semantic"  # Should remain unchanged


def test_delete_saved_search(client, test_user_and_token):
    """Test deleting a saved search"""
    headers = test_user_and_token["headers"]

    # Create saved search
    search_data = {
        "name": "To Delete",
        "search_type": "traditional",
        "query": "delete me"
    }
    create_response = client.post("/search/saved", json=search_data, headers=headers)
    search_id = create_response.json()["id"]

    # Delete saved search
    response = client.delete(f"/search/saved/{search_id}", headers=headers)

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/search/saved/{search_id}", headers=headers)
    assert get_response.status_code == 404


def test_get_saved_search_not_found(client, test_user_and_token):
    """Test getting non-existent saved search"""
    headers = test_user_and_token["headers"]

    response = client.get("/search/saved/99999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved search not found"


def test_search_history_logged_on_traditional_search(client, test_user_and_token):
    """Test that traditional search logs to history"""
    headers = test_user_and_token["headers"]

    # Perform a traditional search
    response = client.get(
        "/search/traditional?keyword=test&limit=10",
        headers=headers
    )

    assert response.status_code == 200

    # Check history
    history_response = client.get("/search/history", headers=headers)
    assert history_response.status_code == 200
    history = history_response.json()

    assert len(history) >= 1
    assert history[0]["search_type"] == "traditional"
    assert history[0]["query"] == "test"


def test_get_search_history(client, test_user_and_token):
    """Test getting search history"""
    headers = test_user_and_token["headers"]

    response = client.get("/search/history", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_search_history_with_pagination(client, test_user_and_token):
    """Test search history pagination"""
    headers = test_user_and_token["headers"]

    response = client.get("/search/history?limit=5&offset=0", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_clear_search_history(client, test_user_and_token):
    """Test clearing search history"""
    headers = test_user_and_token["headers"]

    # First, ensure there's some history (from other tests or create one)
    client.get("/search/traditional?keyword=test", headers=headers)

    # Clear history
    response = client.delete("/search/history", headers=headers)

    assert response.status_code == 204

    # Verify history is empty
    history_response = client.get("/search/history", headers=headers)
    assert len(history_response.json()) == 0


def test_saved_search_belongs_to_user(client, test_user_and_token):
    """Test that users can only access their own saved searches"""
    headers = test_user_and_token["headers"]

    # Create saved search
    search_data = {
        "name": "User1 Search",
        "search_type": "semantic",
        "query": "private search"
    }
    create_response = client.post("/search/saved", json=search_data, headers=headers)
    search_id = create_response.json()["id"]

    # Create another user
    user2_data = {
        "email": "user2@example.com",
        "password": "password123",
        "full_name": "User Two"
    }
    client.post("/auth/register", json=user2_data)

    login2_data = {
        "email": "user2@example.com",
        "password": "password123"
    }
    login2_response = client.post("/auth/login", json=login2_data)
    user2_token = login2_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # Try to access user1's saved search
    response = client.get(f"/search/saved/{search_id}", headers=user2_headers)

    assert response.status_code == 404
