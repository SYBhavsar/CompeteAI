"""
Test suite for SWOT & Threat Assessment API Endpoints

Tests REST API for Phase 4 features:
- GET /swot/{competitor_id}/swot
- GET /swot/{competitor_id}/threat-assessment
- POST /swot/{competitor_id}/regenerate
- GET /swot/threat-landscape
- Auth protection (401/403)

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.swot import SWOTAnalysis
from app.models.threat_assessment import ThreatAssessment
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
def seeded_swot(db, test_competitor):
    swot = SWOTAnalysis(
        competitor_id=test_competitor.id,
        analysis_date=datetime.now(timezone.utc),
        strengths=[{"description": "Strong brand", "evidence": "Top search rank", "impact_score": 0.85}],
        weaknesses=[{"description": "High pricing", "evidence": "Price survey", "impact_score": 0.70}],
        opportunities=[{"description": "SMB gap", "evidence": "Market data", "impact_score": 0.75}],
        threats=[{"description": "New entrants", "evidence": "3 new launches", "impact_score": 0.80}],
        overall_assessment="Solid player with pricing risk",
        confidence_score=0.84
    )
    db.add(swot)
    db.commit()
    db.refresh(swot)
    return swot


@pytest.fixture
def seeded_threat(db, test_competitor):
    threat = ThreatAssessment(
        competitor_id=test_competitor.id,
        threat_score=72.5,
        threat_categories={
            "pricing": 80,
            "innovation": 65,
            "market_share": 75,
            "resource_strength": 70,
            "partnerships": 60
        },
        assessment_text="High threat - aggressive pricing and strong market position",
        mitigation_recommendations=[
            "Differentiate on service quality",
            "Lock in key accounts with multi-year contracts"
        ],
        updated_at=datetime.now(timezone.utc)
    )
    db.add(threat)
    db.commit()
    db.refresh(threat)
    return threat


class TestSWOTAPI:

    def test_get_swot_returns_analysis(
        self, client, db, test_competitor, auth_headers, seeded_swot
    ):
        """
        GIVEN: SWOT analysis exists in DB
        WHEN: GET /swot/{competitor_id}/swot
        THEN: Returns full analysis with all 4 quadrants
        """
        response = client.get(
            f"/swot/{test_competitor.id}/swot",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "strengths" in data
        assert "weaknesses" in data
        assert "opportunities" in data
        assert "threats" in data
        assert "overall_assessment" in data
        assert "confidence_score" in data
        assert len(data["strengths"]) >= 1

    def test_get_swot_404_when_none_exists(
        self, client, db, test_competitor, auth_headers
    ):
        """
        GIVEN: No SWOT analysis exists for competitor
        WHEN: GET /swot/{competitor_id}/swot
        THEN: Returns 404
        """
        response = client.get(
            f"/swot/{test_competitor.id}/swot",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_threat_assessment(
        self, client, db, test_competitor, auth_headers, seeded_threat
    ):
        """
        GIVEN: ThreatAssessment exists in DB
        WHEN: GET /swot/{competitor_id}/threat-assessment
        THEN: Returns threat score and category breakdown
        """
        response = client.get(
            f"/swot/{test_competitor.id}/threat-assessment",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "threat_score" in data
        assert "threat_categories" in data
        assert 0 <= data["threat_score"] <= 100
        cats = data["threat_categories"]
        for key in ("pricing", "innovation", "market_share", "resource_strength", "partnerships"):
            assert key in cats

    def test_regenerate_swot_triggers_service(
        self, client, db, test_competitor, auth_headers, seeded_swot
    ):
        """
        GIVEN: A competitor with an existing SWOT
        WHEN: POST /swot/{competitor_id}/regenerate
        THEN: Returns 200/202 and calls generate_swot on the service
        """
        with patch('app.api.swot.StrategicFrameworkService') as mock_svc_cls:
            mock_svc = Mock()
            # Return the already-committed seeded_swot so response serialization works
            mock_svc.generate_swot.return_value = seeded_swot
            mock_svc_cls.return_value = mock_svc

            response = client.post(
                f"/swot/{test_competitor.id}/regenerate",
                headers=auth_headers
            )

        assert response.status_code in (200, 202)
        mock_svc.generate_swot.assert_called_once()

    def test_threat_landscape_returns_all_competitors(
        self, client, db, test_user, auth_headers
    ):
        """
        GIVEN: Multiple competitors with threat assessments
        WHEN: GET /swot/threat-landscape
        THEN: Returns list of all competitors with threat scores
        """
        # Create two competitors explicitly
        comp1 = Competitor(name="Competitor A", domain="compa.com", user_id=test_user.id)
        comp2 = Competitor(name="Competitor B", domain="compb.com", user_id=test_user.id)
        db.add(comp1)
        db.add(comp2)
        db.commit()
        db.refresh(comp1)
        db.refresh(comp2)

        for comp in [comp1, comp2]:
            threat = ThreatAssessment(
                competitor_id=comp.id,
                threat_score=float(60 + comp.id),
                threat_categories={"pricing": 60, "innovation": 65, "market_share": 70,
                                   "resource_strength": 55, "partnerships": 50},
                assessment_text="Moderate threat",
                mitigation_recommendations=["Monitor closely"],
                updated_at=datetime.now(timezone.utc)
            )
            db.add(threat)
        db.commit()

        response = client.get("/swot/threat-landscape", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all("threat_score" in item for item in data)
        assert all("competitor_id" in item for item in data)

    def test_unauthenticated_returns_401(self, client, test_competitor):
        """
        GIVEN: No auth token
        WHEN: GET /swot/{competitor_id}/swot
        THEN: Returns 401 or 403
        """
        response = client.get(f"/swot/{test_competitor.id}/swot")

        assert response.status_code in (401, 403)
