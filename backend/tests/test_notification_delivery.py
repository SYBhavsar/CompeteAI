import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.notification_delivery_service import NotificationDeliveryService
from app.models.alert import Notification
from app.models import User
from app.core.database import SessionLocal, Base, engine
from app.utils.auth import hash_password


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def notification_service():
    """Create notification delivery service instance"""
    return NotificationDeliveryService()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_notification(db_session, test_user):
    """Create test notification"""
    notification = Notification(
        user_id=test_user.id,
        message="Test notification message",
        is_read=False
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


def test_get_unread_notifications(db_session, notification_service, test_user):
    """Test retrieving unread notifications for a user"""
    # Create multiple notifications
    notif1 = Notification(
        user_id=test_user.id,
        message="Unread notification 1",
        is_read=False
    )
    notif2 = Notification(
        user_id=test_user.id,
        message="Read notification",
        is_read=True
    )
    notif3 = Notification(
        user_id=test_user.id,
        message="Unread notification 2",
        is_read=False
    )
    db_session.add_all([notif1, notif2, notif3])
    db_session.commit()

    unread = notification_service.get_unread_notifications(test_user.id, db_session)

    assert len(unread) == 2
    assert all(n.is_read is False for n in unread)


def test_send_email_notification(notification_service, test_user, test_notification):
    """Test sending email notification"""
    with patch('app.services.notification_delivery_service.send_email') as mock_send:
        mock_send.return_value = True

        result = notification_service.send_email_notification(
            user_email=test_user.email,
            subject="Alert Notification",
            message=test_notification.message
        )

        assert result is True
        mock_send.assert_called_once_with(
            to_email=test_user.email,
            subject="Alert Notification",
            body=test_notification.message
        )


def test_send_email_notification_failure(notification_service, test_user):
    """Test email notification failure handling"""
    with patch('app.services.notification_delivery_service.send_email') as mock_send:
        mock_send.side_effect = Exception("SMTP error")

        result = notification_service.send_email_notification(
            user_email=test_user.email,
            subject="Alert Notification",
            message="Test message"
        )

        assert result is False


def test_format_notification_email(notification_service, test_notification):
    """Test formatting notification for email"""
    formatted = notification_service.format_notification_email(
        notification=test_notification
    )

    assert "Test notification message" in formatted
    assert isinstance(formatted, str)


def test_deliver_notification_to_user(db_session, notification_service, test_user, test_notification):
    """Test delivering notification to user via email"""
    with patch.object(notification_service, 'send_email_notification') as mock_send:
        mock_send.return_value = True

        result = notification_service.deliver_notification(
            notification_id=test_notification.id,
            db=db_session
        )

        assert result is True
        mock_send.assert_called_once()


def test_deliver_notification_not_found(db_session, notification_service):
    """Test delivering non-existent notification"""
    result = notification_service.deliver_notification(
        notification_id=99999,
        db=db_session
    )

    assert result is False


def test_batch_deliver_unread_notifications(db_session, notification_service, test_user):
    """Test batch delivery of unread notifications"""
    # Create multiple unread notifications
    notif1 = Notification(
        user_id=test_user.id,
        message="Notification 1",
        is_read=False
    )
    notif2 = Notification(
        user_id=test_user.id,
        message="Notification 2",
        is_read=False
    )
    db_session.add_all([notif1, notif2])
    db_session.commit()

    with patch.object(notification_service, 'send_email_notification') as mock_send:
        mock_send.return_value = True

        delivered_count = notification_service.batch_deliver_notifications(
            user_id=test_user.id,
            db=db_session
        )

        assert delivered_count == 2
        assert mock_send.call_count == 2


def test_mark_notification_as_delivered(db_session, notification_service, test_notification):
    """Test marking notification as delivered"""
    result = notification_service.mark_as_delivered(
        notification_id=test_notification.id,
        db=db_session
    )

    assert result is True

    # Verify notification was marked as read
    db_session.refresh(test_notification)
    assert test_notification.is_read is True


def test_get_notification_summary(db_session, notification_service, test_user):
    """Test getting notification summary for a user"""
    # Create notifications
    notif1 = Notification(
        user_id=test_user.id,
        message="Unread 1",
        is_read=False
    )
    notif2 = Notification(
        user_id=test_user.id,
        message="Unread 2",
        is_read=False
    )
    notif3 = Notification(
        user_id=test_user.id,
        message="Read",
        is_read=True
    )
    db_session.add_all([notif1, notif2, notif3])
    db_session.commit()

    summary = notification_service.get_notification_summary(test_user.id, db_session)

    assert summary["total"] == 3
    assert summary["unread"] == 2
    assert summary["read"] == 1
