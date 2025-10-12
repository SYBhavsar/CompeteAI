import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.competitor import Competitor
from app.models.data_source import DataSource
from app.models.raw_content import RawContent


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
    """Create a test data source with user and competitor"""
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
        url="https://testcompany.com/blog"
    )
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    return data_source


def test_create_raw_content(db_session: Session, test_data_source: DataSource):
    """Test creating raw content"""
    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="This is test content from the blog",
        content_type="text/html",
        url="https://testcompany.com/blog/post-1"
    )
    
    db_session.add(raw_content)
    db_session.commit()
    
    # Verify content was created
    saved_content = db_session.query(RawContent).filter(RawContent.url == "https://testcompany.com/blog/post-1").first()
    assert saved_content is not None
    assert saved_content.content == "This is test content from the blog"
    assert saved_content.content_type == "text/html"
    assert saved_content.data_source_id == test_data_source.id


def test_raw_content_belongs_to_data_source(db_session: Session, test_data_source: DataSource):
    """Test raw content-data source relationship"""
    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="Test content",
        content_type="text/html",
        url="https://testcompany.com/page"
    )
    
    db_session.add(raw_content)
    db_session.commit()
    db_session.refresh(raw_content)
    
    # Test relationship
    assert raw_content.data_source.url == test_data_source.url
    assert test_data_source.raw_contents[0].content == "Test content"


def test_multiple_content_per_source(db_session: Session, test_data_source: DataSource):
    """Test data source can have multiple raw content entries"""
    contents = [
        RawContent(data_source_id=test_data_source.id, content="Content 1", url="https://testcompany.com/1"),
        RawContent(data_source_id=test_data_source.id, content="Content 2", url="https://testcompany.com/2"),
        RawContent(data_source_id=test_data_source.id, content="Content 3", url="https://testcompany.com/3")
    ]
    
    for content in contents:
        db_session.add(content)
    db_session.commit()
    
    # Verify all content is linked to data source
    source_content = db_session.query(RawContent).filter(RawContent.data_source_id == test_data_source.id).all()
    assert len(source_content) == 3
    assert len(test_data_source.raw_contents) == 3


def test_content_hash_for_deduplication(db_session: Session, test_data_source: DataSource):
    """Test content hash field for deduplication"""
    raw_content = RawContent(
        data_source_id=test_data_source.id,
        content="Test content for hashing",
        content_type="text/html",
        url="https://testcompany.com/test",
        content_hash="abc123def456"
    )
    
    db_session.add(raw_content)
    db_session.commit()
    
    saved_content = db_session.query(RawContent).filter(RawContent.content_hash == "abc123def456").first()
    assert saved_content is not None
    assert saved_content.content == "Test content for hashing"