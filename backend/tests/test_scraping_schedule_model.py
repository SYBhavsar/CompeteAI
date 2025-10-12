import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor, DataSource, ScrapingSchedule


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


def test_create_scraping_schedule(db_session: Session, test_data_source: DataSource):
    """Test creating a scraping schedule"""
    next_run = datetime.now(timezone.utc) + timedelta(hours=1)
    
    schedule = ScrapingSchedule(
        data_source_id=test_data_source.id,
        frequency_minutes=60,  # Every hour
        next_run=next_run,
        is_active=True
    )
    
    db_session.add(schedule)
    db_session.commit()
    
    # Verify schedule was created
    saved_schedule = db_session.query(ScrapingSchedule).filter(
        ScrapingSchedule.data_source_id == test_data_source.id
    ).first()
    
    assert saved_schedule is not None
    assert saved_schedule.frequency_minutes == 60
    assert saved_schedule.is_active is True
    assert saved_schedule.next_run == next_run


def test_schedule_belongs_to_data_source(db_session: Session, test_data_source: DataSource):
    """Test schedule-data source relationship"""
    schedule = ScrapingSchedule(
        data_source_id=test_data_source.id,
        frequency_minutes=120,
        next_run=datetime.now(timezone.utc) + timedelta(hours=2)
    )
    
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    
    # Test relationship
    assert schedule.data_source.url == test_data_source.url
    assert test_data_source.scraping_schedule.frequency_minutes == 120


def test_schedule_update_next_run(db_session: Session, test_data_source: DataSource):
    """Test updating next_run after successful scrape"""
    initial_next_run = datetime.now(timezone.utc) + timedelta(hours=1)
    
    schedule = ScrapingSchedule(
        data_source_id=test_data_source.id,
        frequency_minutes=60,
        next_run=initial_next_run,
        is_active=True
    )
    
    db_session.add(schedule)
    db_session.commit()
    
    # Simulate updating next_run after scraping
    new_next_run = initial_next_run + timedelta(minutes=schedule.frequency_minutes)
    schedule.next_run = new_next_run
    schedule.last_run = initial_next_run
    
    db_session.commit()
    
    # Verify update
    updated_schedule = db_session.query(ScrapingSchedule).filter(
        ScrapingSchedule.data_source_id == test_data_source.id
    ).first()
    
    assert updated_schedule.next_run == new_next_run
    assert updated_schedule.last_run == initial_next_run


def test_schedule_due_for_scraping(db_session: Session, test_data_source: DataSource):
    """Test identifying schedules due for scraping"""
    # Create schedule that's due now
    due_schedule = ScrapingSchedule(
        data_source_id=test_data_source.id,
        frequency_minutes=60,
        next_run=datetime.now(timezone.utc) - timedelta(minutes=5),  # 5 minutes ago
        is_active=True
    )
    
    db_session.add(due_schedule)
    db_session.commit()
    
    # Query for due schedules
    due_schedules = db_session.query(ScrapingSchedule).filter(
        ScrapingSchedule.next_run <= datetime.now(timezone.utc),
        ScrapingSchedule.is_active == True
    ).all()
    
    assert len(due_schedules) == 1
    assert due_schedules[0].data_source_id == test_data_source.id


def test_inactive_schedule_not_due(db_session: Session, test_data_source: DataSource):
    """Test that inactive schedules are not considered due"""
    inactive_schedule = ScrapingSchedule(
        data_source_id=test_data_source.id,
        frequency_minutes=60,
        next_run=datetime.now(timezone.utc) - timedelta(minutes=5),  # 5 minutes ago
        is_active=False  # Inactive
    )
    
    db_session.add(inactive_schedule)
    db_session.commit()
    
    # Query for due schedules
    due_schedules = db_session.query(ScrapingSchedule).filter(
        ScrapingSchedule.next_run <= datetime.now(timezone.utc),
        ScrapingSchedule.is_active == True
    ).all()
    
    assert len(due_schedules) == 0