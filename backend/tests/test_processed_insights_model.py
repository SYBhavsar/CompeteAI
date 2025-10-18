import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights


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


@pytest.fixture
def test_raw_content(db_session: Session):
    """Create test raw content with all dependencies"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    
    competitor = Competitor(
        name="Test Company",
        domain="testcompany.com",
        user_id=user.id
    )
    db_session.add(competitor)
    db_session.commit()
    
    data_source = DataSource(
        competitor_id=competitor.id,
        source_type="website",
        url="https://testcompany.com/blog",
        is_active=True
    )
    db_session.add(data_source)
    db_session.commit()
    
    raw_content = RawContent(
        data_source_id=data_source.id,
        content="Test content for processing",
        content_type="text/html",
        url="https://testcompany.com/blog/post"
    )
    db_session.add(raw_content)
    db_session.commit()
    
    db_session.refresh(raw_content)
    return raw_content


def test_create_processed_insights(db_session: Session, test_raw_content):
    """Test creating processed insights"""
    processed_insights = ProcessedInsights(
        raw_content_id=test_raw_content.id,
        summary="This is a test summary",
        key_points=["Point 1", "Point 2", "Point 3"],
        sentiment="positive",
        insights="Key business insights from the content"
    )
    
    db_session.add(processed_insights)
    db_session.commit()
    db_session.refresh(processed_insights)
    
    assert processed_insights.id is not None
    assert processed_insights.raw_content_id == test_raw_content.id
    assert processed_insights.summary == "This is a test summary"
    assert processed_insights.key_points == ["Point 1", "Point 2", "Point 3"]
    assert processed_insights.sentiment == "positive"
    assert processed_insights.insights == "Key business insights from the content"
    assert processed_insights.created_at is not None
    assert processed_insights.updated_at is not None


def test_processed_insights_relationships(db_session: Session, test_raw_content):
    """Test ProcessedInsights relationships"""
    processed_insights = ProcessedInsights(
        raw_content_id=test_raw_content.id,
        summary="Test summary",
        sentiment="neutral"
    )
    
    db_session.add(processed_insights)
    db_session.commit()
    db_session.refresh(processed_insights)
    
    # Test relationship to raw content
    assert processed_insights.raw_content is not None
    assert processed_insights.raw_content.id == test_raw_content.id
    assert processed_insights.raw_content.content == "Test content for processing"


def test_processed_insights_unique_constraint(db_session: Session, test_raw_content):
    """Test that only one ProcessedInsights can exist per RawContent"""
    # Create first processed insights
    insights1 = ProcessedInsights(
        raw_content_id=test_raw_content.id,
        summary="First summary",
        sentiment="positive"
    )
    db_session.add(insights1)
    db_session.commit()
    
    # Try to create second processed insights for same raw content
    insights2 = ProcessedInsights(
        raw_content_id=test_raw_content.id,
        summary="Second summary", 
        sentiment="negative"
    )
    db_session.add(insights2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_processed_insights_optional_fields(db_session: Session, test_raw_content):
    """Test ProcessedInsights with minimal required fields"""
    processed_insights = ProcessedInsights(
        raw_content_id=test_raw_content.id,
        summary="Minimal summary",
        sentiment="neutral"
    )
    
    db_session.add(processed_insights)
    db_session.commit()
    db_session.refresh(processed_insights)
    
    assert processed_insights.id is not None
    assert processed_insights.key_points is None
    assert processed_insights.insights is None
    assert processed_insights.created_at is not None