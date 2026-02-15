"""
Test suite for Phase 1: Historical Intelligence Models

Following TDD principles:
- Tests for CompetitiveSnapshot, ChangeEvent, CompetitorTimeline models
- Tests should FAIL initially (models don't exist yet)
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.competitor import Competitor

# Models to be created
from app.models.competitive_snapshot import CompetitiveSnapshot
from app.models.change_detection import ChangeEvent
from app.models.timeline import CompetitorTimeline


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
        hashed_password="hashed_password_here"
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


class TestCompetitiveSnapshot:
    """Test CompetitiveSnapshot model"""

    def test_create_snapshot(self, db, test_competitor):
        """
        GIVEN: Valid competitor and snapshot data
        WHEN: Creating CompetitiveSnapshot
        THEN: Snapshot is saved with correct attributes
        """
        snapshot = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow(),
            data_hash="abc123def456",
            snapshot_data={
                "pricing": "$99/month",
                "product_name": "Enterprise Suite",
                "target_market": "SMB"
            }
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        assert snapshot.id is not None
        assert snapshot.competitor_id == test_competitor.id
        assert snapshot.data_hash == "abc123def456"
        assert snapshot.snapshot_data["pricing"] == "$99/month"

    def test_snapshot_hash_deduplication(self, db, test_competitor):
        """
        GIVEN: Two snapshots with identical data_hash
        WHEN: Attempting to save both
        THEN: Should allow (hash is for tracking, not uniqueness constraint)
        """
        snapshot1 = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow(),
            data_hash="identical_hash",
            snapshot_data={"data": "version1"}
        )
        snapshot2 = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow() + timedelta(days=1),
            data_hash="identical_hash",
            snapshot_data={"data": "version1"}
        )

        db.add(snapshot1)
        db.add(snapshot2)
        db.commit()

        snapshots = db.query(CompetitiveSnapshot).filter_by(data_hash="identical_hash").all()
        assert len(snapshots) == 2

    def test_snapshot_requires_competitor_id(self, db):
        """
        GIVEN: Snapshot without competitor_id
        WHEN: Attempting to save
        THEN: IntegrityError raised
        """
        with pytest.raises(IntegrityError):
            snapshot = CompetitiveSnapshot(
                competitor_id=None,
                snapshot_date=datetime.utcnow(),
                data_hash="test_hash",
                snapshot_data={}
            )
            db.add(snapshot)
            db.commit()


class TestChangeEvent:
    """Test ChangeEvent model"""

    def test_create_change_event(self, db, test_competitor):
        """
        GIVEN: Two snapshots with differences
        WHEN: Creating ChangeEvent
        THEN: Event is saved with correct attributes
        """
        # Create two snapshots
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow() - timedelta(days=7),
            data_hash="hash_before",
            snapshot_data={"pricing": "$99/month"}
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow(),
            data_hash="hash_after",
            snapshot_data={"pricing": "$149/month"}
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        # Create change event
        change_event = ChangeEvent(
            competitor_id=test_competitor.id,
            change_type="pricing",
            severity="major",
            before_snapshot_id=snapshot_before.id,
            after_snapshot_id=snapshot_after.id,
            change_summary="Pricing increased from $99 to $149 (50% increase)",
            strategic_impact="Potential opportunity to win price-sensitive customers",
            confidence_score=0.95
        )
        db.add(change_event)
        db.commit()
        db.refresh(change_event)

        assert change_event.id is not None
        assert change_event.change_type == "pricing"
        assert change_event.severity == "major"
        assert change_event.confidence_score == 0.95

    def test_change_event_severity_values(self, db, test_competitor):
        """
        GIVEN: Valid severity values
        WHEN: Creating ChangeEvents with different severities
        THEN: All valid severities are accepted
        """
        # Create snapshots first
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow() - timedelta(days=1),
            data_hash="before_hash",
            snapshot_data={"test": "data"}
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow(),
            data_hash="after_hash",
            snapshot_data={"test": "data"}
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        valid_severities = ["minor", "moderate", "major", "critical"]

        for severity in valid_severities:
            change_event = ChangeEvent(
                competitor_id=test_competitor.id,
                change_type="test",
                severity=severity,
                before_snapshot_id=snapshot_before.id,
                after_snapshot_id=snapshot_after.id,
                change_summary=f"Test {severity} change",
                strategic_impact="Test impact",
                confidence_score=0.8
            )
            db.add(change_event)

        db.commit()

        events = db.query(ChangeEvent).all()
        assert len(events) == len(valid_severities)

    def test_confidence_score_range(self, db, test_competitor):
        """
        GIVEN: ChangeEvent with confidence score
        WHEN: Score is between 0.0 and 1.0
        THEN: Event is saved successfully
        """
        # Create snapshots first
        snapshot_before = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow() - timedelta(days=1),
            data_hash="before_hash",
            snapshot_data={"test": "data"}
        )
        snapshot_after = CompetitiveSnapshot(
            competitor_id=test_competitor.id,
            snapshot_date=datetime.utcnow(),
            data_hash="after_hash",
            snapshot_data={"test": "data"}
        )
        db.add(snapshot_before)
        db.add(snapshot_after)
        db.commit()

        change_event = ChangeEvent(
            competitor_id=test_competitor.id,
            change_type="messaging",
            severity="moderate",
            before_snapshot_id=snapshot_before.id,
            after_snapshot_id=snapshot_after.id,
            change_summary="Messaging shift detected",
            strategic_impact="Monitor for further changes",
            confidence_score=0.75
        )
        db.add(change_event)
        db.commit()

        assert 0.0 <= change_event.confidence_score <= 1.0


class TestCompetitorTimeline:
    """Test CompetitorTimeline model"""

    def test_create_timeline_event(self, db, test_competitor):
        """
        GIVEN: Valid timeline event data
        WHEN: Creating CompetitorTimeline entry
        THEN: Event is saved with correct attributes
        """
        timeline_event = CompetitorTimeline(
            competitor_id=test_competitor.id,
            event_type="product_launch",
            event_date=datetime(2026, 1, 15),
            title="Launched AI Analytics Suite",
            description="Competitor launched new AI-powered analytics product targeting enterprise customers",
            source_urls=["https://competitor.com/blog/ai-launch", "https://news.com/competitor-ai"]
        )
        db.add(timeline_event)
        db.commit()
        db.refresh(timeline_event)

        assert timeline_event.id is not None
        assert timeline_event.event_type == "product_launch"
        assert timeline_event.title == "Launched AI Analytics Suite"
        assert len(timeline_event.source_urls) == 2

    def test_timeline_chronological_order(self, db, test_competitor):
        """
        GIVEN: Multiple timeline events
        WHEN: Querying events ordered by date
        THEN: Events are returned in chronological order
        """
        events = [
            CompetitorTimeline(
                competitor_id=test_competitor.id,
                event_type="funding",
                event_date=datetime(2026, 1, 1),
                title="Series A Funding",
                description="Raised $10M",
                source_urls=[]
            ),
            CompetitorTimeline(
                competitor_id=test_competitor.id,
                event_type="product_launch",
                event_date=datetime(2026, 2, 1),
                title="Product Launch",
                description="Launched new product",
                source_urls=[]
            ),
            CompetitorTimeline(
                competitor_id=test_competitor.id,
                event_type="partnership",
                event_date=datetime(2025, 12, 1),
                title="Partnership Announced",
                description="Partnered with Microsoft",
                source_urls=[]
            )
        ]

        for event in events:
            db.add(event)
        db.commit()

        # Query in chronological order
        timeline = db.query(CompetitorTimeline)\
            .filter_by(competitor_id=test_competitor.id)\
            .order_by(CompetitorTimeline.event_date.asc())\
            .all()

        assert timeline[0].title == "Partnership Announced"
        assert timeline[1].title == "Series A Funding"
        assert timeline[2].title == "Product Launch"

    def test_timeline_event_types(self, db, test_competitor):
        """
        GIVEN: Various event types
        WHEN: Creating timeline events
        THEN: Different event types are supported
        """
        event_types = [
            "product_launch", "pricing_change", "partnership",
            "acquisition", "leadership_change", "funding",
            "market_entry", "messaging_change"
        ]

        for event_type in event_types:
            timeline_event = CompetitorTimeline(
                competitor_id=test_competitor.id,
                event_type=event_type,
                event_date=datetime.utcnow(),
                title=f"Test {event_type}",
                description=f"Test event of type {event_type}",
                source_urls=[]
            )
            db.add(timeline_event)

        db.commit()

        events = db.query(CompetitorTimeline).all()
        assert len(events) == len(event_types)
