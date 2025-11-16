import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor, DataSource, RawContent


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


@pytest.fixture
def test_competitor(test_user_and_token):
    """Create test competitor"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()

        competitor = Competitor(
            name="Test Company",
            domain="testcompany.com",
            industry="Technology",
            user_id=user.id
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)

        return {
            "competitor_id": competitor.id,
            **test_user_and_token
        }
    finally:
        db.close()


def test_get_competitor_by_id_success(client, test_competitor):
    """Test getting individual competitor details"""
    competitor_id = test_competitor["competitor_id"]
    headers = test_competitor["headers"]

    response = client.get(f"/competitors/{competitor_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == competitor_id
    assert data["name"] == "Test Company"
    assert data["domain"] == "testcompany.com"
    assert "industry" in data


def test_get_competitor_by_id_not_found(client, test_user_and_token):
    """Test getting non-existent competitor"""
    headers = test_user_and_token["headers"]

    response = client.get("/competitors/99999", headers=headers)

    assert response.status_code == 404


def test_get_competitor_unauthorized(client, test_competitor):
    """Test getting competitor without ownership"""
    # Create another user
    user_data = {
        "email": "other@example.com",
        "password": "testpassword123",
        "full_name": "Other User"
    }
    client.post("/auth/register", json=user_data)

    login_data = {
        "email": "other@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/login", json=login_data)
    other_token = response.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    competitor_id = test_competitor["competitor_id"]

    response = client.get(f"/competitors/{competitor_id}", headers=other_headers)

    assert response.status_code == 404


def test_update_competitor_success(client, test_competitor):
    """Test updating competitor information"""
    competitor_id = test_competitor["competitor_id"]
    headers = test_competitor["headers"]

    update_data = {
        "name": "Updated Company Name",
        "domain": "updated.com",
        "industry": "FinTech"
    }

    response = client.put(f"/competitors/{competitor_id}", json=update_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Company Name"
    assert data["domain"] == "updated.com"
    assert data["industry"] == "FinTech"


def test_update_competitor_partial(client, test_competitor):
    """Test partial update of competitor"""
    competitor_id = test_competitor["competitor_id"]
    headers = test_competitor["headers"]

    update_data = {
        "name": "New Name Only"
    }

    response = client.put(f"/competitors/{competitor_id}", json=update_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name Only"
    assert data["domain"] == "testcompany.com"  # Unchanged


def test_update_competitor_not_found(client, test_user_and_token):
    """Test updating non-existent competitor"""
    headers = test_user_and_token["headers"]

    update_data = {"name": "New Name"}

    response = client.put("/competitors/99999", json=update_data, headers=headers)

    assert response.status_code == 404


def test_delete_competitor_success(client, test_competitor):
    """Test deleting competitor"""
    competitor_id = test_competitor["competitor_id"]
    headers = test_competitor["headers"]

    response = client.delete(f"/competitors/{competitor_id}", headers=headers)

    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(f"/competitors/{competitor_id}", headers=headers)
    assert get_response.status_code == 404


def test_delete_competitor_not_found(client, test_user_and_token):
    """Test deleting non-existent competitor"""
    headers = test_user_and_token["headers"]

    response = client.delete("/competitors/99999", headers=headers)

    assert response.status_code == 404


def test_get_competitor_all_data(client, test_competitor):
    """Test getting all scraped data for a competitor"""
    competitor_id = test_competitor["competitor_id"]
    headers = test_competitor["headers"]

    # Create test data
    db = SessionLocal()
    try:
        data_source = DataSource(
            competitor_id=competitor_id,
            source_type="website",
            url="https://testcompany.com",
            is_active=True
        )
        db.add(data_source)
        db.commit()

        raw_content = RawContent(
            data_source_id=data_source.id,
            content="Test content",
            content_type="text/html",
            url="https://testcompany.com/blog"
        )
        db.add(raw_content)
        db.commit()
    finally:
        db.close()

    response = client.get(f"/competitors/{competitor_id}/data", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "raw_contents" in data
    assert len(data["raw_contents"]) > 0


def test_get_competitor_data_with_pagination(client, test_competitor):
    """Test getting competitor data with pagination"""
    competitor_id = test_competitor["competitor_id"]
    headers = test_competitor["headers"]

    response = client.get(
        f"/competitors/{competitor_id}/data?limit=10&offset=0",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "raw_contents" in data
    assert "total" in data