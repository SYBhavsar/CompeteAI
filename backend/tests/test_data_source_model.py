import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.competitor import Competitor
from app.models.data_source import DataSource


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
def test_competitor(db_session: Session):
    """Create a test competitor with user"""
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
    db_session.refresh(competitor)
    return competitor


def test_create_data_source(db_session: Session, test_competitor: Competitor):
    """Test creating a data source"""
    data_source = DataSource(
        competitor_id=test_competitor.id,
        source_type="website",
        url="https://testcompany.com/blog",
        is_active=True
    )
    
    db_session.add(data_source)
    db_session.commit()
    
    # Verify data source was created
    saved_source = db_session.query(DataSource).filter(DataSource.url == "https://testcompany.com/blog").first()
    assert saved_source is not None
    assert saved_source.source_type == "website"
    assert saved_source.competitor_id == test_competitor.id
    assert saved_source.is_active is True


def test_data_source_belongs_to_competitor(db_session: Session, test_competitor: Competitor):
    """Test data source-competitor relationship"""
    data_source = DataSource(
        competitor_id=test_competitor.id,
        source_type="social_media",
        url="https://twitter.com/testcompany"
    )
    
    db_session.add(data_source)
    db_session.commit()
    db_session.refresh(data_source)
    
    # Test relationship
    assert data_source.competitor.name == test_competitor.name
    assert test_competitor.data_sources[0].source_type == "social_media"


def test_multiple_sources_per_competitor(db_session: Session, test_competitor: Competitor):
    """Test competitor can have multiple data sources"""
    sources = [
        DataSource(competitor_id=test_competitor.id, source_type="website", url="https://testcompany.com"),
        DataSource(competitor_id=test_competitor.id, source_type="blog", url="https://testcompany.com/blog"),
        DataSource(competitor_id=test_competitor.id, source_type="social_media", url="https://twitter.com/test")
    ]
    
    for source in sources:
        db_session.add(source)
    db_session.commit()
    
    # Verify all sources are linked to competitor
    competitor_sources = db_session.query(DataSource).filter(DataSource.competitor_id == test_competitor.id).all()
    assert len(competitor_sources) == 3
    assert len(test_competitor.data_sources) == 3