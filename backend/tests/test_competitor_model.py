import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.competitor import Competitor


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
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_competitor(db_session: Session, test_user: User):
    """Test creating a competitor"""
    competitor = Competitor(
        name="Test Company",
        domain="testcompany.com",
        industry="Technology",
        user_id=test_user.id
    )
    
    db_session.add(competitor)
    db_session.commit()
    
    # Verify competitor was created
    saved_competitor = db_session.query(Competitor).filter(Competitor.name == "Test Company").first()
    assert saved_competitor is not None
    assert saved_competitor.name == "Test Company"
    assert saved_competitor.domain == "testcompany.com"
    assert saved_competitor.industry == "Technology"
    assert saved_competitor.user_id == test_user.id


def test_competitor_belongs_to_user(db_session: Session, test_user: User):
    """Test competitor-user relationship"""
    competitor = Competitor(
        name="Test Company",
        domain="testcompany.com",
        user_id=test_user.id
    )
    
    db_session.add(competitor)
    db_session.commit()
    db_session.refresh(competitor)
    
    # Test relationship
    assert competitor.user.email == test_user.email
    assert test_user.competitors[0].name == "Test Company"