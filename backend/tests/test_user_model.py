import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User


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


def test_create_user(db_session: Session):
    """Test creating a user with required fields"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
        full_name="Test User"
    )
    
    db_session.add(user)
    db_session.commit()
    
    # Verify user was created
    saved_user = db_session.query(User).filter(User.email == "test@example.com").first()
    assert saved_user is not None
    assert saved_user.email == "test@example.com"
    assert saved_user.full_name == "Test User"
    assert saved_user.is_active is True


def test_user_email_unique(db_session: Session):
    """Test that user email must be unique"""
    user1 = User(email="test@example.com", hashed_password="hash1")
    user2 = User(email="test@example.com", hashed_password="hash2")
    
    db_session.add(user1)
    db_session.commit()
    
    db_session.add(user2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        db_session.commit()