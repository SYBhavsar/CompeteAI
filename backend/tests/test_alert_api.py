import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.alert import Alert


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


def test_create_alert(client, test_user_and_token):
    """Test creating an alert"""
    headers = test_user_and_token["headers"]

    alert_data = {
        "alert_type": "sentiment_change",
        "conditions": {"threshold": "negative"},
        "is_active": True
    }

    response = client.post("/alerts", json=alert_data, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["alert_type"] == "sentiment_change"
    assert data["is_active"] is True


def test_get_all_alerts(client, test_user_and_token):
    """Test getting all user alerts"""
    headers = test_user_and_token["headers"]

    response = client.get("/alerts", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_alert_by_id(client, test_user_and_token):
    """Test getting specific alert"""
    headers = test_user_and_token["headers"]

    # Create alert first
    alert_data = {"alert_type": "new_content", "is_active": True}
    create_response = client.post("/alerts", json=alert_data, headers=headers)
    alert_id = create_response.json()["id"]

    response = client.get(f"/alerts/{alert_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == alert_id


def test_update_alert(client, test_user_and_token):
    """Test updating an alert"""
    headers = test_user_and_token["headers"]

    # Create alert
    alert_data = {"alert_type": "new_content", "is_active": True}
    create_response = client.post("/alerts", json=alert_data, headers=headers)
    alert_id = create_response.json()["id"]

    # Update alert
    update_data = {"is_active": False}
    response = client.put(f"/alerts/{alert_id}", json=update_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


def test_delete_alert(client, test_user_and_token):
    """Test deleting an alert"""
    headers = test_user_and_token["headers"]

    # Create alert
    alert_data = {"alert_type": "new_content", "is_active": True}
    create_response = client.post("/alerts", json=alert_data, headers=headers)
    alert_id = create_response.json()["id"]

    # Delete alert
    response = client.delete(f"/alerts/{alert_id}", headers=headers)

    assert response.status_code == 200


def test_get_notifications(client, test_user_and_token):
    """Test getting user notifications"""
    headers = test_user_and_token["headers"]

    response = client.get("/notifications", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_mark_notification_read(client, test_user_and_token):
    """Test marking notification as read"""
    headers = test_user_and_token["headers"]

    # Create notification manually
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        from app.models.alert import Notification
        notification = Notification(
            user_id=user.id,
            message="Test notification",
            is_read=False
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        notification_id = notification.id
    finally:
        db.close()

    response = client.put(f"/notifications/{notification_id}/read", headers=headers)

    assert response.status_code == 200