"""
Test suite for Predictive Analytics API Endpoints

Tests REST API for Phase 3 predictive features:
- GET /predictive/{competitor_id}/predictions
- GET /predictive/{competitor_id}/predictions?status=pending
- POST /predictive/predictions/{id}/validate-outcome
- GET /predictive/{competitor_id}/accuracy-report
- Auth protection (401/403)

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.prediction import CompetitorPrediction
from app.utils.jwt import create_access_token


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    user = User(email="test@example.com", hashed_password="hashed_password")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_competitor(db, test_user):
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
def auth_headers(test_user):
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def predictions(db, test_competitor):
    """Seed DB with mixed predictions"""
    items = [
        CompetitorPrediction(
            competitor_id=test_competitor.id,
            prediction_type="pricing_change",
            confidence=0.82,
            timeframe="30_days",
            reasoning="Pattern suggests pricing update",
            suggested_action="Review our pricing",
            outcome="pending",
            predicted_at=datetime.now(timezone.utc)
        ),
        CompetitorPrediction(
            competitor_id=test_competitor.id,
            prediction_type="product_launch",
            confidence=0.71,
            timeframe="60_days",
            reasoning="Hiring suggests new product",
            suggested_action="Accelerate roadmap",
            outcome="pending",
            predicted_at=datetime.now(timezone.utc)
        ),
        CompetitorPrediction(
            competitor_id=test_competitor.id,
            prediction_type="market_entry",
            confidence=0.65,
            timeframe="90_days",
            reasoning="Geographic expansion signals",
            suggested_action="Strengthen partnerships",
            outcome="correct",
            predicted_at=datetime.now(timezone.utc) - timedelta(days=60),
            resolved_at=datetime.now(timezone.utc) - timedelta(days=5)
        ),
    ]
    for item in items:
        db.add(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


class TestPredictiveAnalyticsAPI:
    """Test Predictive Analytics API endpoints"""

    def test_get_predictions_for_competitor(
        self, client, db, test_competitor, auth_headers, predictions
    ):
        """
        GIVEN: Competitor with predictions in DB
        WHEN: GET /predictive/{competitor_id}/predictions
        THEN: Returns list of all predictions for that competitor
        """
        response = client.get(
            f"/predictive/{test_competitor.id}/predictions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert all("prediction_type" in p for p in data)
        assert all("confidence" in p for p in data)
        assert all("timeframe" in p for p in data)
        assert all("outcome" in p for p in data)

    def test_get_predictions_filtered_by_status(
        self, client, db, test_competitor, auth_headers, predictions
    ):
        """
        GIVEN: Mix of pending and resolved predictions
        WHEN: GET /predictive/{competitor_id}/predictions?status=pending
        THEN: Returns only pending predictions
        """
        response = client.get(
            f"/predictive/{test_competitor.id}/predictions?status=pending",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["outcome"] == "pending" for p in data)

    def test_validate_outcome_updates_prediction(
        self, client, db, test_competitor, auth_headers, predictions
    ):
        """
        GIVEN: A pending prediction
        WHEN: POST /predictive/predictions/{id}/validate-outcome with outcome=correct
        THEN: Prediction outcome is updated to correct
        """
        pending = next(p for p in predictions if p.outcome == "pending")

        response = client.post(
            f"/predictive/predictions/{pending.id}/validate-outcome",
            json={"outcome": "correct"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["outcome"] == "correct"
        assert data["id"] == pending.id

    def test_accuracy_report_returns_stats(
        self, client, db, test_competitor, auth_headers, predictions
    ):
        """
        GIVEN: Mix of correct/pending predictions
        WHEN: GET /predictive/{competitor_id}/accuracy-report
        THEN: Returns accuracy stats (total, correct, accuracy_rate)
        """
        response = client.get(
            f"/predictive/{test_competitor.id}/accuracy-report",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
        assert "correct_predictions" in data
        assert "accuracy_rate" in data
        assert isinstance(data["accuracy_rate"], float)

    def test_unauthenticated_returns_401(self, client, test_competitor):
        """
        GIVEN: No auth token
        WHEN: GET /predictive/{competitor_id}/predictions
        THEN: Returns 401 or 403 (unauthenticated)
        """
        response = client.get(
            f"/predictive/{test_competitor.id}/predictions"
        )

        assert response.status_code in (401, 403)
