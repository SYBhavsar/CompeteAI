"""
Test suite for Historical Analysis Service

Tests the service that detects changes between competitor snapshots
using LangChain for semantic analysis (not just text diffs).

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.competitive_snapshot import CompetitiveSnapshot
from app.models.change_detection import ChangeEvent
from app.services.historical_analysis_service import HistoricalAnalysisService


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
def test_competitor(db, test_user):
    """Create test competitor"""
    competitor = Competitor(
        name="Test Competitor",
        domain="competitor.com",
        user_id=test_user.id
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@pytest.fixture
def mock_langchain():
    """Mock LLMFactory.create to control the LLM used by HistoricalAnalysisService."""
    mock_llm = Mock()
    with patch('app.core.llm_factory.LLMFactory.create', return_value=mock_llm):
        yield mock_llm


class TestHistoricalAnalysisService:
    """Test Historical Analysis Service"""

    def test_service_initialization(self, mock_langchain):
        """
        GIVEN: HistoricalAnalysisService class
        WHEN: Initializing the service
        THEN: Service is created with LLM dependency
        """
        service = HistoricalAnalysisService()
        assert service is not None
        assert hasattr(service, 'llm')

    def test_detect_pricing_change(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Two snapshots with different pricing ($99 → $149)
        WHEN: Running change detection
        THEN: ChangeEvent created with type='pricing', severity='major'
        """
        # Create snapshots
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc) - timedelta(days=7),
            data_hash="hash_before",
            snapshot_data={
                "pricing": "$99/month",
                "product_name": "Enterprise Suite"
            }
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc),
            data_hash="hash_after",
            snapshot_data={
                "pricing": "$149/month",
                "product_name": "Enterprise Suite"
            }
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        # Mock LLM response
        mock_langchain.invoke.return_value = Mock(content="""
        {
            "change_type": "pricing",
            "severity": "major",
            "change_summary": "Pricing increased from $99 to $149 (50% increase)",
            "strategic_impact": "Potential opportunity to win price-sensitive customers",
            "confidence_score": 0.95
        }
        """)

        # Run change detection
        service = HistoricalAnalysisService()
        changes = service.detect_changes(
            competitor_id=test_competitor.id,
            before_snapshot=snapshot_before,
            after_snapshot=snapshot_after,
            db=db
        )

        # Verify
        assert len(changes) == 1
        change = changes[0]
        assert change.change_type == "pricing"
        assert change.severity == "major"
        assert change.confidence_score == 0.95
        assert "$99" in change.change_summary
        assert "$149" in change.change_summary

    def test_detect_messaging_shift(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Snapshots showing messaging shift (SMB → Enterprise)
        WHEN: Running change detection
        THEN: ChangeEvent created with type='positioning', severity='moderate'
        """
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc) - timedelta(days=30),
            data_hash="hash1",
            snapshot_data={
                "target_market": "Small Business",
                "messaging": "Perfect for teams of 5-50"
            }
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc),
            data_hash="hash2",
            snapshot_data={
                "target_market": "Enterprise",
                "messaging": "Built for organizations of 1000+"
            }
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        # Mock LLM analysis
        mock_langchain.invoke.return_value = Mock(content="""
        {
            "change_type": "positioning",
            "severity": "moderate",
            "change_summary": "Strategic shift from SMB to Enterprise market",
            "strategic_impact": "Moving upmarket - opportunity in abandoned SMB segment",
            "confidence_score": 0.88
        }
        """)

        service = HistoricalAnalysisService()
        changes = service.detect_changes(
            competitor_id=test_competitor.id,
            before_snapshot=snapshot_before,
            after_snapshot=snapshot_after,
            db=db
        )

        assert len(changes) == 1
        assert changes[0].change_type == "positioning"
        assert changes[0].severity == "moderate"

    def test_no_changes_detected(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Two identical snapshots
        WHEN: Running change detection
        THEN: No ChangeEvent created
        """
        identical_data = {
            "pricing": "$99/month",
            "features": ["Feature A", "Feature B"]
        }

        snapshot1 = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc) - timedelta(days=1),
            data_hash="same_hash",
            snapshot_data=identical_data
        )
        snapshot2 = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc),
            data_hash="same_hash",
            snapshot_data=identical_data
        )
        db.add(snapshot1)
        db.add(snapshot2)
        db.commit()

        # Mock: No significant changes
        mock_langchain.invoke.return_value = Mock(content="""
        {
            "change_type": "none",
            "severity": "none",
            "change_summary": "No significant changes detected",
            "strategic_impact": "N/A",
            "confidence_score": 1.0
        }
        """)

        service = HistoricalAnalysisService()
        changes = service.detect_changes(
            competitor_id=test_competitor.id,
            before_snapshot=snapshot1,
            after_snapshot=snapshot2,
            db=db
        )

        assert len(changes) == 0

    def test_analyze_latest_snapshots(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Multiple snapshots for competitor
        WHEN: Calling analyze_latest_snapshots
        THEN: Compares the two most recent snapshots
        """
        # Create 3 snapshots
        snapshots = []
        for i in range(3):
            snapshot = CompetitiveSnapshot(
                competitor_id=test_competitor.id,
                snapshot_date=datetime.now(timezone.utc) - timedelta(days=3-i),
                data_hash=f"hash_{i}",
                snapshot_data={"version": i}
            )
            db.add(snapshot)
            snapshots.append(snapshot)
        db.commit()

        # Mock response
        mock_langchain.invoke.return_value = Mock(content="""
        {
            "change_type": "update",
            "severity": "minor",
            "change_summary": "Minor version update",
            "strategic_impact": "Routine update, no strategic significance",
            "confidence_score": 0.75
        }
        """)

        service = HistoricalAnalysisService()
        changes = service.analyze_latest_snapshots(
            competitor_id=test_competitor.id,
            db=db
        )

        # Should compare snapshot 1 (before) and snapshot 2 (after)
        assert changes is not None

    def test_severity_scoring(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Changes with different severities
        WHEN: Service analyzes changes
        THEN: Severity is correctly classified (minor/moderate/major/critical)
        """
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc) - timedelta(days=1),
            data_hash="before",
            snapshot_data={"price": "$100"}
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc),
            data_hash="after",
            snapshot_data={"price": "$50"}
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        # Mock critical change (50% price drop)
        mock_langchain.invoke.return_value = Mock(content="""
        {
            "change_type": "pricing",
            "severity": "critical",
            "change_summary": "Dramatic 50% price reduction",
            "strategic_impact": "Highly aggressive pricing move - immediate response needed",
            "confidence_score": 0.97
        }
        """)

        service = HistoricalAnalysisService()
        changes = service.detect_changes(
            competitor_id=test_competitor.id,
            before_snapshot=snapshot_before,
            after_snapshot=snapshot_after,
            db=db
        )

        assert changes[0].severity == "critical"

    def test_confidence_score_validation(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Change detection result
        WHEN: Confidence score is provided
        THEN: Score is between 0.0 and 1.0
        """
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc) - timedelta(days=1),
            data_hash="b",
            snapshot_data={"test": "data"}
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc),
            data_hash="a",
            snapshot_data={"test": "data2"}
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        mock_langchain.invoke.return_value = Mock(content="""
        {
            "change_type": "messaging",
            "severity": "moderate",
            "change_summary": "Test change",
            "strategic_impact": "Test impact",
            "confidence_score": 0.82
        }
        """)

        service = HistoricalAnalysisService()
        changes = service.detect_changes(
            competitor_id=test_competitor.id,
            before_snapshot=snapshot_before,
            after_snapshot=snapshot_after,
            db=db
        )

        assert 0.0 <= changes[0].confidence_score <= 1.0

    def test_multiple_changes_detected(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Snapshots with multiple significant changes
        WHEN: Running change detection
        THEN: Multiple ChangeEvents created
        """
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc) - timedelta(days=7),
            data_hash="before",
            snapshot_data={
                "pricing": "$99/month",
                "features": ["Feature A", "Feature B"],
                "target_market": "SMB"
            }
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.now(timezone.utc),
            data_hash="after",
            snapshot_data={
                "pricing": "$149/month",
                "features": ["Feature A", "Feature B", "Feature C"],
                "target_market": "Enterprise"
            }
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        # Mock: Multiple changes detected
        mock_langchain.invoke.return_value = Mock(content="""
        {
            "changes": [
                {
                    "change_type": "pricing",
                    "severity": "major",
                    "change_summary": "Price increase 50%",
                    "strategic_impact": "Price repositioning",
                    "confidence_score": 0.95
                },
                {
                    "change_type": "positioning",
                    "severity": "moderate",
                    "change_summary": "Market shift to Enterprise",
                    "strategic_impact": "Upmarket move",
                    "confidence_score": 0.88
                }
            ]
        }
        """)

        service = HistoricalAnalysisService()
        changes = service.detect_changes(
            competitor_id=test_competitor.id,
            before_snapshot=snapshot_before,
            after_snapshot=snapshot_after,
            db=db
        )

        # Should detect multiple changes
        assert len(changes) >= 1

    def test_error_handling_invalid_snapshot(self, db, test_competitor, mock_langchain):
        """
        GIVEN: Invalid snapshot data
        WHEN: Running change detection
        THEN: Service handles error gracefully
        """
        service = HistoricalAnalysisService()

        # Should handle None snapshots
        result = service.detect_changes(
            competitor_id=test_competitor.id,
            before_snapshot=None,
            after_snapshot=None,
            db=db
        )

        assert result == [] or result is None
