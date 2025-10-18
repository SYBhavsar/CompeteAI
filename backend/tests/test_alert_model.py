import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor
from app.models.alert import Alert, Notification


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_alert(db_session: Session):
    """Test creating an alert"""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()

    alert = Alert(
        user_id=user.id,
        alert_type="sentiment_change",
        conditions={"threshold": "negative"},
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()

    assert alert.id is not None
    assert alert.alert_type == "sentiment_change"
    assert alert.is_active is True


def test_alert_with_competitor(db_session: Session):
    """Test alert associated with specific competitor"""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()

    competitor = Competitor(
        name="Test Company",
        domain="test.com",
        user_id=user.id
    )
    db_session.add(competitor)
    db_session.commit()

    alert = Alert(
        user_id=user.id,
        competitor_id=competitor.id,
        alert_type="new_content",
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()

    assert alert.competitor_id == competitor.id


def test_create_notification(db_session: Session):
    """Test creating a notification"""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()

    notification = Notification(
        user_id=user.id,
        message="Test notification message",
        is_read=False
    )
    db_session.add(notification)
    db_session.commit()

    assert notification.id is not None
    assert notification.message == "Test notification message"
    assert notification.is_read is False