import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights
from app.services.content_processing_service import ContentProcessingService


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
    """Create test raw content"""
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
        content="Test Company announces revolutionary new AI product that will transform the industry. The product features advanced machine learning capabilities and will be available next quarter.",
        content_type="text/html",
        url="https://testcompany.com/blog/new-ai-product"
    )
    db_session.add(raw_content)
    db_session.commit()
    
    db_session.refresh(raw_content)
    return raw_content


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client"""
    mock_client = Mock()
    mock_client.summarize_content.return_value = "Company announces new AI product launch"
    mock_client.extract_insights.return_value = "Strategic focus on AI innovation, targeting Q1 release"
    mock_client.analyze_sentiment.return_value = "positive"
    return mock_client


@pytest.fixture
def content_processing_service(mock_openai_client):
    """Create content processing service with mock OpenAI client"""
    return ContentProcessingService(openai_client=mock_openai_client)


def test_process_raw_content_success(content_processing_service, test_raw_content, db_session):
    """Test successful content processing"""
    result = content_processing_service.process_raw_content(test_raw_content.id, db_session)
    
    assert result is not None
    assert result.summary == "Company announces new AI product launch"
    assert result.insights == "Strategic focus on AI innovation, targeting Q1 release"
    assert result.sentiment == "positive"
    assert result.raw_content_id == test_raw_content.id
    assert result.key_points is not None
    assert isinstance(result.key_points, list)


def test_process_raw_content_with_key_points(content_processing_service, test_raw_content, db_session):
    """Test content processing with key points extraction"""
    result = content_processing_service.process_raw_content(test_raw_content.id, db_session)
    
    assert result.key_points is not None
    assert isinstance(result.key_points, list)
    assert len(result.key_points) > 0


def test_process_raw_content_already_processed(content_processing_service, test_raw_content, db_session):
    """Test processing already processed content returns existing insights"""
    # Create existing processed insights
    existing_insights = ProcessedInsights(
        raw_content_id=test_raw_content.id,
        summary="Existing summary",
        sentiment="neutral",
        insights="Existing insights"
    )
    db_session.add(existing_insights)
    db_session.commit()
    
    result = content_processing_service.process_raw_content(test_raw_content.id, db_session)
    
    assert result.id == existing_insights.id
    assert result.summary == "Existing summary"
    # OpenAI client should not be called for already processed content


def test_process_raw_content_invalid_id(content_processing_service, db_session):
    """Test processing with invalid raw content ID"""
    result = content_processing_service.process_raw_content(99999, db_session)
    
    assert result is None


def test_process_raw_content_openai_error(test_raw_content, db_session):
    """Test handling OpenAI API errors"""
    # Create service with failing OpenAI client
    mock_client = Mock()
    mock_client.summarize_content.side_effect = Exception("API Error")
    service = ContentProcessingService(openai_client=mock_client)
    
    result = service.process_raw_content(test_raw_content.id, db_session)
    
    assert result is None


def test_extract_key_points_from_content(content_processing_service):
    """Test key points extraction from content"""
    content = "Company announces new product. Features include AI and ML. Available next quarter."
    
    key_points = content_processing_service._extract_key_points(content)
    
    assert isinstance(key_points, list)
    assert len(key_points) >= 2
    assert "product" in str(key_points).lower()
    assert "quarter" in str(key_points).lower()


def test_process_multiple_contents(content_processing_service, test_raw_content, db_session):
    """Test processing multiple raw contents"""
    # Process first content
    result1 = content_processing_service.process_raw_content(test_raw_content.id, db_session)
    assert result1 is not None
    
    # Create second raw content
    raw_content2 = RawContent(
        data_source_id=test_raw_content.data_source_id,
        content="Second piece of content about pricing updates",
        content_type="text/html",
        url="https://testcompany.com/blog/pricing-update"
    )
    db_session.add(raw_content2)
    db_session.commit()
    db_session.refresh(raw_content2)
    
    # Process second content
    result2 = content_processing_service.process_raw_content(raw_content2.id, db_session)
    assert result2 is not None
    assert result2.id != result1.id