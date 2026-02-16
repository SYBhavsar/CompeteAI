"""
Test suite for Historical Intelligence API Endpoints

Tests the REST API for historical analysis features:
- Timeline visualization
- Change detection results
- Manual snapshot creation
- Analytics/velocity tracking

Following TDD - these tests will FAIL initially.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.competitive_snapshot import CompetitiveSnapshot
from app.models.change_detection import ChangeEvent
from app.models.timeline import CompetitorTimeline


@pytest.fixture
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_and_token(client):
    """Create test user and get auth token"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }

    # Register user
    client.post("/auth/register", json=user_data)

    # Login to get token
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }

    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def test_competitor_with_history(test_user_and_token):
    """Create competitor with historical data"""
    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter(User.email == "test@example.com").first()

        # Create competitor
        competitor = Competitor(
            name="Test Competitor",
            domain="competitor.com",
            user_id=user.id
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)

        # Create snapshots
        snapshot1 = CompetitiveSnapshot(
            competitor_id=competitor.id,
            snapshot_date=datetime.utcnow() - timedelta(days=7),
            data_hash="hash1",
            snapshot_data={"pricing": "$99/month"}
        )
        snapshot2 = CompetitiveSnapshot(
            competitor_id=competitor.id,
            snapshot_date=datetime.utcnow() - timedelta(days=3),
            data_hash="hash2",
            snapshot_data={"pricing": "$149/month"}
        )
        snapshot3 = CompetitiveSnapshot(
            competitor_id=competitor.id,
            snapshot_date=datetime.utcnow(),
            data_hash="hash3",
            snapshot_data={"pricing": "$149/month"}
        )
        db.add_all([snapshot1, snapshot2, snapshot3])
        db.commit()

        # Create change events
        change1 = ChangeEvent(
            competitor_id=competitor.id,
            change_type="pricing",
            severity="major",
            before_snapshot_id=snapshot1.id,
            after_snapshot_id=snapshot2.id,
            change_summary="Price increased 50%",
            strategic_impact="Opportunity to win price-sensitive customers",
            confidence_score=0.95
        )
        db.add(change1)
        db.commit()

        # Create timeline events
        timeline1 = CompetitorTimeline(
            competitor_id=competitor.id,
            event_type="pricing_change",
            event_date=datetime.utcnow() - timedelta(days=3),
            title="Major Price Increase",
            description="Increased pricing by 50%",
            source_urls=["https://competitor.com/pricing"]
        )
        timeline2 = CompetitorTimeline(
            competitor_id=competitor.id,
            event_type="product_launch",
            event_date=datetime.utcnow() - timedelta(days=30),
            title="Launched New AI Feature",
            description="Released AI-powered analytics",
            source_urls=["https://competitor.com/blog/ai-launch"]
        )
        db.add_all([timeline1, timeline2])
        db.commit()

        return {
            "competitor_id": competitor.id,
            "snapshot_ids": [snapshot1.id, snapshot2.id, snapshot3.id],
            "change_ids": [change1.id],
            "timeline_ids": [timeline1.id, timeline2.id],
            **test_user_and_token
        }
    finally:
        db.close()


class TestTimelineAPI:
    """Test GET /competitors/{id}/timeline endpoint"""

    def test_get_timeline_success(self, client, test_competitor_with_history):
        """
        GIVEN: Competitor with timeline events
        WHEN: GET /competitors/{id}/timeline
        THEN: Returns timeline events in chronological order
        """
        competitor_id = test_competitor_with_history["competitor_id"]
        headers = test_competitor_with_history["headers"]

        response = client.get(
            f"/historical/competitors/{competitor_id}/timeline",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify chronological order (most recent first)
        assert data[0]["event_type"] == "pricing_change"
        assert data[1]["event_type"] == "product_launch"
        assert "title" in data[0]
        assert "description" in data[0]

    def test_get_timeline_with_limit(self, client, test_competitor_with_history):
        """
        GIVEN: Competitor with multiple timeline events
        WHEN: GET /competitors/{id}/timeline?limit=1
        THEN: Returns only specified number of events
        """
        competitor_id = test_competitor_with_history["competitor_id"]
        headers = test_competitor_with_history["headers"]

        response = client.get(
            f"/historical/competitors/{competitor_id}/timeline?limit=1",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_timeline_empty(self, client, test_user_and_token):
        """
        GIVEN: Competitor with no timeline events
        WHEN: GET /competitors/{id}/timeline
        THEN: Returns empty list
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == "test@example.com").first()
            competitor = Competitor(
                name="New Competitor",
                domain="new.com",
                user_id=user.id
            )
            db.add(competitor)
            db.commit()
            db.refresh(competitor)

            headers = test_user_and_token["headers"]
            response = client.get(
                f"/historical/competitors/{competitor.id}/timeline",
                headers=headers
            )

            assert response.status_code == 200
            assert response.json() == []
        finally:
            db.close()

    def test_get_timeline_unauthorized(self, client, test_competitor_with_history):
        """
        GIVEN: No authentication
        WHEN: GET /competitors/{id}/timeline
        THEN: Returns 403 Forbidden
        """
        competitor_id = test_competitor_with_history["competitor_id"]

        response = client.get(
            f"/historical/competitors/{competitor_id}/timeline"
        )

        assert response.status_code == 403


class TestChangesAPI:
    """Test GET /competitors/{id}/changes endpoint"""

    def test_get_changes_success(self, client, test_competitor_with_history):
        """
        GIVEN: Competitor with detected changes
        WHEN: GET /competitors/{id}/changes
        THEN: Returns list of change events
        """
        competitor_id = test_competitor_with_history["competitor_id"]
        headers = test_competitor_with_history["headers"]

        response = client.get(
            f"/historical/competitors/{competitor_id}/changes",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["change_type"] == "pricing"
        assert data[0]["severity"] == "major"
        assert data[0]["confidence_score"] == 0.95

    def test_get_changes_filter_by_days(self, client, test_competitor_with_history):
        """
        GIVEN: Competitor with changes
        WHEN: GET /competitors/{id}/changes?days=30
        THEN: Returns only changes from last 30 days
        """
        competitor_id = test_competitor_with_history["competitor_id"]
        headers = test_competitor_with_history["headers"]

        response = client.get(
            f"/historical/competitors/{competitor_id}/changes?days=30",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_changes_filter_by_severity(self, client, test_competitor_with_history):
        """
        GIVEN: Competitor with changes of different severities
        WHEN: GET /competitors/{id}/changes?severity=major
        THEN: Returns only major changes
        """
        competitor_id = test_competitor_with_history["competitor_id"]
        headers = test_competitor_with_history["headers"]

        response = client.get(
            f"/historical/competitors/{competitor_id}/changes?severity=major",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(change["severity"] == "major" for change in data)

    def test_get_changes_nonexistent_competitor(self, client, test_user_and_token):
        """
        GIVEN: Nonexistent competitor ID
        WHEN: GET /competitors/99999/changes
        THEN: Returns 404 Not Found
        """
        headers = test_user_and_token["headers"]

        response = client.get(
            "/historical/competitors/99999/changes",
            headers=headers
        )

        assert response.status_code == 404


class TestSnapshotCreationAPI:
    """Test POST /competitors/{id}/snapshot endpoint"""

    def test_create_snapshot_success(self, client, test_user_and_token):
        """
        GIVEN: Valid competitor and snapshot data
        WHEN: POST /competitors/{id}/snapshot
        THEN: Snapshot is created and returns 201
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == "test@example.com").first()
            competitor = Competitor(
                name="Test Competitor",
                domain="test.com",
                user_id=user.id
            )
            db.add(competitor)
            db.commit()
            db.refresh(competitor)

            headers = test_user_and_token["headers"]
            snapshot_data = {
                "pricing": "$199/month",
                "features": ["Feature A", "Feature B"],
                "target_market": "Enterprise"
            }

            response = client.post(
                f"/historical/competitors/{competitor.id}/snapshot",
                json={"snapshot_data": snapshot_data},
                headers=headers
            )

            assert response.status_code == 201
            data = response.json()
            assert data["competitor_id"] == competitor.id
            assert "data_hash" in data
            assert data["snapshot_data"] == snapshot_data
        finally:
            db.close()

    def test_create_snapshot_auto_detect_changes(self, client, test_competitor_with_history):
        """
        GIVEN: Competitor with existing snapshots
        WHEN: POST /competitors/{id}/snapshot with different data
        THEN: Snapshot created and change detection triggered
        """
        competitor_id = test_competitor_with_history["competitor_id"]
        headers = test_competitor_with_history["headers"]

        new_snapshot_data = {
            "pricing": "$199/month",  # Changed from $149
            "new_feature": "AI Assistant"
        }

        response = client.post(
            f"/historical/competitors/{competitor_id}/snapshot",
            json={"snapshot_data": new_snapshot_data},
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["snapshot_data"]["pricing"] == "$199/month"

    def test_create_snapshot_unauthorized(self, client):
        """
        GIVEN: No authentication
        WHEN: POST /competitors/{id}/snapshot
        THEN: Returns 403 Forbidden
        """
        response = client.post(
            "/historical/competitors/1/snapshot",
            json={"snapshot_data": {}}
        )

        assert response.status_code == 403


class TestAnalyticsAPI:
    """Test GET /analytics/change-velocity endpoint"""

    def test_get_change_velocity_success(self, client, test_competitor_with_history):
        """
        GIVEN: Multiple competitors with changes
        WHEN: GET /analytics/change-velocity
        THEN: Returns velocity metrics for all competitors
        """
        headers = test_competitor_with_history["headers"]

        response = client.get(
            "/historical/analytics/change-velocity",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Verify structure
        assert "competitor_id" in data[0]
        assert "competitor_name" in data[0]
        assert "change_count" in data[0]
        assert "average_severity" in data[0]

    def test_get_change_velocity_with_timeframe(self, client, test_competitor_with_history):
        """
        GIVEN: Competitors with changes
        WHEN: GET /analytics/change-velocity?days=30
        THEN: Returns velocity only for specified timeframe
        """
        headers = test_competitor_with_history["headers"]

        response = client.get(
            "/historical/analytics/change-velocity?days=30",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_change_velocity_empty(self, client, test_user_and_token):
        """
        GIVEN: User with no competitors
        WHEN: GET /analytics/change-velocity
        THEN: Returns empty list
        """
        headers = test_user_and_token["headers"]

        response = client.get(
            "/historical/analytics/change-velocity",
            headers=headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_change_velocity_unauthorized(self, client):
        """
        GIVEN: No authentication
        WHEN: GET /analytics/change-velocity
        THEN: Returns 403 Forbidden
        """
        response = client.get("/historical/analytics/change-velocity")

        assert response.status_code == 403
