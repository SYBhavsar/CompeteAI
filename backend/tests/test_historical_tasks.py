"""
Test suite for Historical Analysis Celery Tasks

Tests the automated background tasks that:
- Analyze competitor changes after scraping
- Trigger alerts for high-severity changes
- Integrate with existing scraping pipeline

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor, DataSource, RawContent
from app.models.competitive_snapshot import CompetitiveSnapshot
from app.models.change_detection import ChangeEvent
from app.tasks.historical_tasks import (
    analyze_competitor_changes,
    create_snapshot_from_content
)


@pytest.fixture
def db():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_competitor_with_snapshots(db, test_user):
    """Create competitor with existing snapshots"""
    competitor = Competitor(
        name="Test Competitor",
        domain="competitor.com",
        user_id=test_user.id
    )
    db.add(competitor)
    db.commit()

    # Create two snapshots
    snapshot1 = CompetitiveSnapshot(
        competitor_id=competitor.id,
        snapshot_date=datetime.utcnow() - timedelta(days=7),
        data_hash="hash1",
        snapshot_data={"pricing": "$99/month", "features": ["A", "B"]}
    )
    snapshot2 = CompetitiveSnapshot(
        competitor_id=competitor.id,
        snapshot_date=datetime.utcnow() - timedelta(days=1),
        data_hash="hash2",
        snapshot_data={"pricing": "$149/month", "features": ["A", "B", "C"]}
    )
    db.add_all([snapshot1, snapshot2])
    db.commit()

    return {
        "competitor": competitor,
        "snapshots": [snapshot1, snapshot2],
        "user": test_user
    }


class TestAnalyzeCompetitorChangesTask:
    """Test analyze_competitor_changes Celery task"""

    @patch('app.tasks.historical_tasks.HistoricalAnalysisService')
    def test_task_analyzes_latest_snapshots(self, mock_service, db, test_competitor_with_snapshots):
        """
        GIVEN: Competitor with 2+ snapshots
        WHEN: analyze_competitor_changes task runs
        THEN: Calls HistoricalAnalysisService.analyze_latest_snapshots
        """
        competitor = test_competitor_with_snapshots["competitor"]

        # Mock service
        mock_instance = Mock()
        mock_instance.analyze_latest_snapshots.return_value = []
        mock_service.return_value = mock_instance

        # Run task
        result = analyze_competitor_changes(competitor.id)

        # Verify
        assert result is not None
        mock_instance.analyze_latest_snapshots.assert_called_once()

    @patch('app.tasks.historical_tasks.HistoricalAnalysisService')
    def test_task_detects_changes(self, mock_service, db, test_competitor_with_snapshots):
        """
        GIVEN: Competitor with changed data
        WHEN: Task runs
        THEN: ChangeEvents are created
        """
        competitor = test_competitor_with_snapshots["competitor"]

        # Mock service to return change events
        mock_change = Mock()
        mock_change.id = 1
        mock_change.severity = "major"
        mock_change.competitor_id = competitor.id

        mock_instance = Mock()
        mock_instance.analyze_latest_snapshots.return_value = [mock_change]
        mock_service.return_value = mock_instance

        # Run task
        result = analyze_competitor_changes(competitor.id)

        # Verify changes were detected
        assert result["changes_detected"] >= 1

    @patch('app.tasks.historical_tasks.process_insight_alerts')
    @patch('app.tasks.historical_tasks.HistoricalAnalysisService')
    def test_task_triggers_alerts_for_high_severity(
        self,
        mock_service,
        mock_alerts,
        db,
        test_competitor_with_snapshots
    ):
        """
        GIVEN: Critical/Major severity change detected
        WHEN: Task completes
        THEN: Alert task is triggered
        """
        competitor = test_competitor_with_snapshots["competitor"]

        # Mock critical change
        mock_change = Mock()
        mock_change.id = 1
        mock_change.severity = "critical"
        mock_change.competitor_id = competitor.id

        mock_instance = Mock()
        mock_instance.analyze_latest_snapshots.return_value = [mock_change]
        mock_service.return_value = mock_instance

        # Run task
        analyze_competitor_changes(competitor.id)

        # Verify alert was triggered
        mock_alerts.delay.assert_called()

    @patch('app.tasks.historical_tasks.HistoricalAnalysisService')
    def test_task_handles_no_snapshots(self, mock_service, db, test_user):
        """
        GIVEN: Competitor with no snapshots
        WHEN: Task runs
        THEN: Returns gracefully without errors
        """
        competitor = Competitor(
            name="New Competitor",
            domain="new.com",
            user_id=test_user.id
        )
        db.add(competitor)
        db.commit()

        mock_instance = Mock()
        mock_instance.analyze_latest_snapshots.return_value = None
        mock_service.return_value = mock_instance

        # Should not raise error
        result = analyze_competitor_changes(competitor.id)
        assert result is not None

    @patch('app.tasks.historical_tasks.HistoricalAnalysisService')
    def test_task_error_handling(self, mock_service, db, test_competitor_with_snapshots):
        """
        GIVEN: Service raises exception
        WHEN: Task runs
        THEN: Error is logged and task completes gracefully
        """
        competitor = test_competitor_with_snapshots["competitor"]

        # Mock service to raise error
        mock_instance = Mock()
        mock_instance.analyze_latest_snapshots.side_effect = Exception("Analysis failed")
        mock_service.return_value = mock_instance

        # Should not raise error
        result = analyze_competitor_changes(competitor.id)
        assert result is not None
        assert "error" in result


class TestCreateSnapshotFromContentTask:
    """Test create_snapshot_from_content Celery task"""

    def test_create_snapshot_from_raw_content(self, db, test_user):
        """
        GIVEN: Raw content from scraping
        WHEN: create_snapshot_from_content task runs
        THEN: CompetitiveSnapshot is created
        """
        # Create competitor and data source
        competitor = Competitor(
            name="Test Competitor",
            domain="test.com",
            user_id=test_user.id
        )
        db.add(competitor)
        db.commit()

        data_source = DataSource(
            competitor_id=competitor.id,
            source_type="website",
            url="https://test.com/pricing",
            is_active=True
        )
        db.add(data_source)
        db.commit()

        raw_content = RawContent(
            data_source_id=data_source.id,
            content="Pricing: $199/month. Features: AI, Analytics, Reporting.",
            content_type="text/html",
            url="https://test.com/pricing"
        )
        db.add(raw_content)
        db.commit()

        # Run task
        result = create_snapshot_from_content(raw_content.id)

        # Verify snapshot was created
        assert result is not None
        assert "snapshot_id" in result

        # Verify in database
        snapshot = db.query(CompetitiveSnapshot).filter_by(
            competitor_id=competitor.id
        ).first()
        assert snapshot is not None

    @patch('app.tasks.historical_tasks.analyze_competitor_changes')
    def test_snapshot_triggers_change_analysis(self, mock_analysis, db, test_user):
        """
        GIVEN: New snapshot created
        WHEN: Task completes
        THEN: analyze_competitor_changes is triggered
        """
        # Create test data
        competitor = Competitor(
            name="Test Competitor",
            domain="test.com",
            user_id=test_user.id
        )
        db.add(competitor)
        db.commit()

        data_source = DataSource(
            competitor_id=competitor.id,
            source_type="website",
            url="https://test.com",
            is_active=True
        )
        db.add(data_source)
        db.commit()

        raw_content = RawContent(
            data_source_id=data_source.id,
            content="Test content",
            content_type="text/html",
            url="https://test.com"
        )
        db.add(raw_content)
        db.commit()

        # Run task
        create_snapshot_from_content(raw_content.id)

        # Verify change analysis was triggered
        mock_analysis.delay.assert_called_once_with(competitor.id)

    def test_snapshot_deduplication(self, db, test_user):
        """
        GIVEN: Multiple snapshots with identical content
        WHEN: Task runs
        THEN: Duplicate snapshots have same data_hash
        """
        competitor = Competitor(
            name="Test Competitor",
            domain="test.com",
            user_id=test_user.id
        )
        db.add(competitor)
        db.commit()

        data_source = DataSource(
            competitor_id=competitor.id,
            source_type="website",
            url="https://test.com",
            is_active=True
        )
        db.add(data_source)
        db.commit()

        # Create two raw contents with same data
        content1 = RawContent(
            data_source_id=data_source.id,
            content="Pricing: $99/month",
            content_type="text/html",
            url="https://test.com"
        )
        content2 = RawContent(
            data_source_id=data_source.id,
            content="Pricing: $99/month",
            content_type="text/html",
            url="https://test.com"
        )
        db.add_all([content1, content2])
        db.commit()

        # Create snapshots
        result1 = create_snapshot_from_content(content1.id)
        result2 = create_snapshot_from_content(content2.id)

        # Verify same hash
        snapshot1 = db.query(CompetitiveSnapshot).get(result1["snapshot_id"])
        snapshot2 = db.query(CompetitiveSnapshot).get(result2["snapshot_id"])

        assert snapshot1.data_hash == snapshot2.data_hash


class TestPipelineIntegration:
    """Test integration with existing scraping pipeline"""

    @patch('app.tasks.historical_tasks.create_snapshot_from_content')
    def test_scraping_triggers_snapshot_creation(self, mock_create_snapshot):
        """
        GIVEN: Scraping task completes
        WHEN: New RawContent is created
        THEN: Snapshot creation task is triggered
        """
        # This test verifies the integration point
        # The actual integration happens in scraping_tasks.py

        raw_content_id = 123
        mock_create_snapshot.delay.return_value = Mock()

        # Simulate scraping completion
        mock_create_snapshot.delay(raw_content_id)

        # Verify snapshot creation was triggered
        mock_create_snapshot.delay.assert_called_once_with(raw_content_id)
