import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor, DataSource, ScrapingSchedule
from app.tasks.scheduling_tasks import check_and_execute_due_schedules, update_schedule_after_scraping


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
def test_scheduled_source(db_session: Session):
    """Create a test data source with schedule"""
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
    
    # Create schedule that's due now
    schedule = ScrapingSchedule(
        data_source_id=data_source.id,
        frequency_minutes=60,
        next_run=datetime.now(timezone.utc) - timedelta(minutes=5),  # 5 minutes ago
        is_active=True
    )
    db_session.add(schedule)
    db_session.commit()
    
    db_session.refresh(data_source)
    return data_source


@patch('app.tasks.scheduling_tasks.celery_app.send_task')
def test_check_and_execute_due_schedules_success(mock_send_task, test_scheduled_source):
    """Test checking and executing due schedules"""
    # Mock task
    mock_task = Mock()
    mock_task.id = "task-123"
    mock_send_task.return_value = mock_task
    
    # Execute scheduler
    result = check_and_execute_due_schedules()
    
    # Verify task was triggered
    assert result["scheduled_count"] == 1
    assert result["task_ids"] == ["task-123"]
    mock_send_task.assert_called_once_with(
        'app.tasks.scraping_tasks.scrape_data_source',
        args=[test_scheduled_source.id]
    )


@patch('app.tasks.scheduling_tasks.celery_app.send_task')
def test_check_and_execute_due_schedules_no_due(mock_send_task, db_session):
    """Test scheduler when no schedules are due"""
    # Create future schedule
    user = User(email="test@example.com", hashed_password="hash", full_name="User")
    db_session.add(user)
    db_session.commit()
    
    competitor = Competitor(name="Company", domain="company.com", user_id=user.id)
    db_session.add(competitor)
    db_session.commit()
    
    data_source = DataSource(
        competitor_id=competitor.id,
        source_type="website",
        url="https://company.com",
        is_active=True
    )
    db_session.add(data_source)
    db_session.commit()
    
    # Schedule in future
    schedule = ScrapingSchedule(
        data_source_id=data_source.id,
        frequency_minutes=60,
        next_run=datetime.now(timezone.utc) + timedelta(hours=1),  # 1 hour from now
        is_active=True
    )
    db_session.add(schedule)
    db_session.commit()
    
    # Execute scheduler
    result = check_and_execute_due_schedules()
    
    # Verify no tasks triggered
    assert result["scheduled_count"] == 0
    assert result["task_ids"] == []
    mock_send_task.assert_not_called()


def test_update_schedule_after_scraping(test_scheduled_source, db_session):
    """Test updating schedule after successful scraping"""
    data_source_id = test_scheduled_source.id
    
    # Get original schedule
    original_schedule = db_session.query(ScrapingSchedule).filter(
        ScrapingSchedule.data_source_id == data_source_id
    ).first()
    original_next_run = original_schedule.next_run
    
    # Update schedule after scraping
    result = update_schedule_after_scraping(data_source_id)
    
    # Verify schedule was updated
    assert result["status"] == "success"
    
    # Refresh database session
    db_session.refresh(original_schedule)
    
    assert original_schedule.last_run is not None
    assert original_schedule.next_run > original_next_run
    # Should be scheduled 60 minutes from last_run
    expected_next = original_schedule.last_run + timedelta(minutes=60)
    assert abs((original_schedule.next_run - expected_next).total_seconds()) < 60  # Within 1 minute


def test_update_schedule_nonexistent_source(db_session):
    """Test updating schedule for non-existent data source"""
    result = update_schedule_after_scraping(9999)
    
    assert result["status"] == "error"
    assert "not found" in result["message"]


def test_check_due_schedules_inactive_sources(db_session):
    """Test that inactive data sources are not scheduled"""
    # Create inactive data source with due schedule
    user = User(email="test@example.com", hashed_password="hash", full_name="User")
    db_session.add(user)
    db_session.commit()
    
    competitor = Competitor(name="Company", domain="company.com", user_id=user.id)
    db_session.add(competitor)
    db_session.commit()
    
    data_source = DataSource(
        competitor_id=competitor.id,
        source_type="website",
        url="https://company.com",
        is_active=False  # Inactive
    )
    db_session.add(data_source)
    db_session.commit()
    
    # Schedule that's due
    schedule = ScrapingSchedule(
        data_source_id=data_source.id,
        frequency_minutes=60,
        next_run=datetime.now(timezone.utc) - timedelta(minutes=5),
        is_active=True
    )
    db_session.add(schedule)
    db_session.commit()
    
    # Execute scheduler
    with patch('app.tasks.scheduling_tasks.celery_app.send_task') as mock_send_task:
        result = check_and_execute_due_schedules()
        
        # Should not schedule inactive sources
        assert result["scheduled_count"] == 0
        mock_send_task.assert_not_called()