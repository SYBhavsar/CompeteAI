import pytest
from datetime import datetime
from unittest.mock import Mock

from app.services.alert_trigger_service import AlertTriggerService
from app.models.alert import Alert, Notification
from app.models.processed_insights import ProcessedInsights
from app.models.raw_content import RawContent
from app.models import User, Competitor
from app.models.data_source import DataSource
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
def alert_trigger_service():
    """Create alert trigger service instance"""
    return AlertTriggerService()


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
def test_competitor(db_session, test_user):
    """Create test competitor"""
    competitor = Competitor(
        name="Test Competitor",
        domain="competitor.com",
        industry="Technology",
        user_id=test_user.id
    )
    db_session.add(competitor)
    db_session.commit()
    db_session.refresh(competitor)
    return competitor


@pytest.fixture
def test_data_source(db_session, test_competitor):
    """Create test data source"""
    data_source = DataSource(
        competitor_id=test_competitor.id,
        source_type="website",
        url="https://competitor.com",
        is_active=True
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


def test_check_sentiment_change_alert_triggered(db_session, alert_trigger_service, test_user, test_competitor, test_data_source):
    """Test sentiment change alert is triggered when sentiment changes to negative"""
    # Create alert for sentiment change
    alert = Alert(
        name="Test Sentiment Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="sentiment_change",
        conditions={"threshold": "negative"},
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    # Create insight with negative sentiment
    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="Bad news",
        content_type="article",
        url="http://test.com"
    )
    db_session.add(raw_content)
    db_session.commit()

    insight = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Negative news detected",
        sentiment="negative",
        insights="Company facing challenges"
    )
    db_session.add(insight)
    db_session.commit()
    db_session.refresh(insight)

    # Check if alert should be triggered
    result = alert_trigger_service.check_sentiment_alert(alert, insight, db_session)

    assert result is True


def test_check_sentiment_change_alert_not_triggered(db_session, alert_trigger_service, test_user, test_competitor, test_data_source):
    """Test sentiment change alert is not triggered for positive sentiment"""
    alert = Alert(
        name="Test Sentiment Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="sentiment_change",
        conditions={"threshold": "negative"},
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()

    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="Good news",
        content_type="article",
        url="http://test.com"
    )
    db_session.add(raw_content)
    db_session.commit()

    insight = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Positive news",
        sentiment="positive",
        insights="Company doing well"
    )
    db_session.add(insight)
    db_session.commit()

    result = alert_trigger_service.check_sentiment_alert(alert, insight, db_session)

    assert result is False


def test_check_new_content_alert_triggered(db_session, alert_trigger_service, test_user, test_competitor, test_data_source):
    """Test new content alert is triggered when new content is added"""
    alert = Alert(
        name="Test New Content Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="new_content",
        conditions={},
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()

    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="New content",
        content_type="article",
        url="http://test.com"
    )
    db_session.add(raw_content)
    db_session.commit()

    result = alert_trigger_service.check_new_content_alert(alert, raw_content, db_session)

    assert result is True


def test_check_keyword_match_alert_triggered(db_session, alert_trigger_service, test_user, test_competitor, test_data_source):
    """Test keyword match alert is triggered when keyword is found"""
    alert = Alert(
        name="Test Keyword Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="keyword_match",
        conditions={"keywords": ["acquisition", "merger"]},
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()

    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="Company announces major acquisition",
        content_type="article",
        url="http://test.com"
    )
    db_session.add(raw_content)
    db_session.commit()

    insight = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Acquisition news",
        sentiment="neutral",
        insights="Strategic acquisition announced"
    )
    db_session.add(insight)
    db_session.commit()

    result = alert_trigger_service.check_keyword_alert(alert, insight, db_session)

    assert result is True


def test_check_keyword_match_alert_not_triggered(db_session, alert_trigger_service, test_user, test_competitor, test_data_source):
    """Test keyword match alert is not triggered when keyword is not found"""
    alert = Alert(
        name="Test Keyword Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="keyword_match",
        conditions={"keywords": ["bankruptcy", "lawsuit"]},
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()

    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="Company doing well",
        content_type="article",
        url="http://test.com"
    )
    db_session.add(raw_content)
    db_session.commit()

    insight = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Positive news",
        sentiment="positive",
        insights="Growth continues"
    )
    db_session.add(insight)
    db_session.commit()

    result = alert_trigger_service.check_keyword_alert(alert, insight, db_session)

    assert result is False


def test_create_notification_for_triggered_alert(db_session, alert_trigger_service, test_user, test_competitor):
    """Test notification is created when alert is triggered"""
    alert = Alert(
        name="Test Notification Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="sentiment_change",
        conditions={"threshold": "negative"},
        is_active=True
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    message = "Negative sentiment detected for competitor"

    notification = alert_trigger_service.create_notification(
        alert_id=alert.id,
        user_id=alert.user_id,
        message=message,
        db=db_session
    )

    assert notification is not None
    assert notification.alert_id == alert.id
    assert notification.user_id == alert.user_id
    assert notification.message == message
    assert notification.is_read is False


def test_process_alerts_for_insight(db_session, alert_trigger_service, test_user, test_competitor, test_data_source):
    """Test processing all alerts for a new insight"""
    # Create multiple alerts
    alert1 = Alert(
        name="Test Sentiment Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="sentiment_change",
        conditions={"threshold": "negative"},
        is_active=True
    )
    alert2 = Alert(
        name="Test Keyword Alert",
        user_id=test_user.id,
        competitor_id=test_competitor.id,
        alert_type="keyword_match",
        conditions={"keywords": ["crisis"]},
        is_active=True
    )
    db_session.add_all([alert1, alert2])
    db_session.commit()

    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="Company in crisis",
        content_type="article",
        url="http://test.com"
    )
    db_session.add(raw_content)
    db_session.commit()

    insight = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Crisis situation",
        sentiment="negative",
        insights="Company facing major crisis"
    )
    db_session.add(insight)
    db_session.commit()
    db_session.refresh(insight)

    triggered_count = alert_trigger_service.process_alerts_for_insight(
        insight_id=insight.id,
        db=db_session
    )

    assert triggered_count == 2

    # Check notifications were created
    notifications = db_session.query(Notification).filter(
        Notification.user_id == test_user.id
    ).all()

    assert len(notifications) == 2
