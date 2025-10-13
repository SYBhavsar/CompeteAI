import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User


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

    # Register user
    client.post("/auth/register", json=user_data)

    # Login to get token
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


def test_semantic_search_success(client, test_user_and_token):
    """Test successful semantic search"""
    headers = test_user_and_token["headers"]

    search_data = {
        "query": "AI product launch announcement",
        "top_k": 5
    }

    with patch('app.api.search.EmbeddingService') as mock_service:
        mock_instance = Mock()
        mock_instance.search_similar_insights.return_value = [
            {
                "id": "insight_1",
                "score": 0.95,
                "metadata": {
                    "insight_id": 1,
                    "summary": "Company launches AI product",
                    "sentiment": "positive",
                    "competitor_id": 1
                }
            },
            {
                "id": "insight_2",
                "score": 0.87,
                "metadata": {
                    "insight_id": 2,
                    "summary": "AI product features announced",
                    "sentiment": "positive",
                    "competitor_id": 1
                }
            }
        ]
        mock_service.return_value = mock_instance

        response = client.post("/search/semantic", json=search_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["score"] == 0.95
    assert data["query"] == "AI product launch announcement"


def test_semantic_search_with_competitor_filter(client, test_user_and_token):
    """Test semantic search with competitor filter"""
    headers = test_user_and_token["headers"]

    search_data = {
        "query": "product update",
        "top_k": 10,
        "competitor_id": 1
    }

    with patch('app.api.search.EmbeddingService') as mock_service:
        mock_instance = Mock()
        mock_instance.search_similar_insights.return_value = []
        mock_service.return_value = mock_instance

        response = client.post("/search/semantic", json=search_data, headers=headers)

    assert response.status_code == 200
    # Verify competitor_id was passed to service
    call_args = mock_instance.search_similar_insights.call_args
    assert call_args[1]["competitor_id"] == 1


def test_semantic_search_unauthenticated(client):
    """Test semantic search without authentication"""
    search_data = {
        "query": "test query",
        "top_k": 5
    }

    response = client.post("/search/semantic", json=search_data)

    assert response.status_code == 403


def test_semantic_search_empty_query(client, test_user_and_token):
    """Test semantic search with empty query"""
    headers = test_user_and_token["headers"]

    search_data = {
        "query": "",
        "top_k": 5
    }

    response = client.post("/search/semantic", json=search_data, headers=headers)

    assert response.status_code == 422  # Validation error


def test_semantic_search_invalid_top_k(client, test_user_and_token):
    """Test semantic search with invalid top_k value"""
    headers = test_user_and_token["headers"]

    search_data = {
        "query": "test query",
        "top_k": 150  # Too high
    }

    response = client.post("/search/semantic", json=search_data, headers=headers)

    assert response.status_code == 422  # Validation error


def test_traditional_search_success(client, test_user_and_token):
    """Test traditional keyword search"""
    headers = test_user_and_token["headers"]

    with patch('app.api.search.SessionLocal') as mock_session:
        mock_db = Mock()
        mock_query = Mock()
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_session.return_value.__enter__.return_value = mock_db

        response = client.get(
            "/search/traditional?keyword=AI&limit=10",
            headers=headers
        )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "keyword" in data


def test_traditional_search_with_filters(client, test_user_and_token):
    """Test traditional search with date and competitor filters"""
    headers = test_user_and_token["headers"]

    with patch('app.api.search.SessionLocal') as mock_session:
        mock_db = Mock()
        mock_query = Mock()
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_session.return_value.__enter__.return_value = mock_db

        response = client.get(
            "/search/traditional?keyword=product&competitor_id=1&sentiment=positive",
            headers=headers
        )

    assert response.status_code == 200


def test_traditional_search_unauthenticated(client):
    """Test traditional search without authentication"""
    response = client.get("/search/traditional?keyword=test")

    assert response.status_code == 403


def test_traditional_search_missing_keyword(client, test_user_and_token):
    """Test traditional search without keyword"""
    headers = test_user_and_token["headers"]

    response = client.get("/search/traditional", headers=headers)

    assert response.status_code == 422  # Validation error