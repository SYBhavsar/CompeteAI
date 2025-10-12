import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.competitor import Competitor
from app.models.data_source import DataSource
from app.models.raw_content import RawContent
from app.tasks.scraping_tasks import scrape_data_source


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
def test_data_source(db_session: Session):
    """Create a test data source"""
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
    db_session.refresh(data_source)
    return data_source


@patch('app.tasks.scraping_tasks.ScrapingService')
def test_scrape_data_source_success(mock_scraping_service, test_data_source):
    """Test successful data source scraping task"""
    # Mock scraping service
    mock_service_instance = Mock()
    mock_service_instance.scrape_url.return_value = {
        "content": "<html><body>Test content</body></html>",
        "content_type": "text/html",
        "url": "https://testcompany.com/blog",
        "content_hash": "abc123"
    }
    mock_scraping_service.return_value = mock_service_instance
    
    # Execute task
    result = scrape_data_source(test_data_source.id)
    
    # Verify task executed successfully
    assert result is not None
    assert result["status"] == "success"
    assert result["content_saved"] is True
    mock_service_instance.scrape_url.assert_called_once_with("https://testcompany.com/blog")


@patch('app.tasks.scraping_tasks.ScrapingService')
def test_scrape_data_source_failure(mock_scraping_service, test_data_source):
    """Test failed data source scraping task"""
    # Mock scraping service failure
    mock_service_instance = Mock()
    mock_service_instance.scrape_url.return_value = None
    mock_scraping_service.return_value = mock_service_instance
    
    # Execute task
    result = scrape_data_source(test_data_source.id)
    
    # Verify task handled failure
    assert result is not None
    assert result["status"] == "failed"
    assert result["content_saved"] is False


def test_scrape_data_source_inactive_source(test_data_source, db_session):
    """Test scraping inactive data source"""
    # Make data source inactive and commit to DB
    test_data_source.is_active = False
    db_session.commit()
    
    # Execute task
    result = scrape_data_source(test_data_source.id)
    
    # Verify task skipped inactive source
    assert result is not None
    assert result["status"] == "skipped"
    assert result["reason"] == "Data source is inactive"


def test_scrape_data_source_not_found(db_session):
    """Test scraping non-existent data source"""
    # Execute task with invalid ID
    result = scrape_data_source(9999)
    
    # Verify task handled missing source
    assert result is not None
    assert result["status"] == "failed"
    assert result["error"] == "Data source not found"