"""
Test suite for Strategic Framework Service

Tests AI-powered SWOT analysis and threat assessment:
- Generate full SWOT with all 4 quadrants
- Required field validation per SWOT item
- Threat scoring (0-100) with category breakdown
- DB persistence and regeneration (replace, not duplicate)
- Graceful error handling

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.swot import SWOTAnalysis
from app.models.threat_assessment import ThreatAssessment
from app.services.strategic_framework_service import StrategicFrameworkService


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
def mock_llm():
    with patch('app.core.llm_factory.LLMFactory.create') as mock:
        mock.return_value = Mock()
        yield mock.return_value


@pytest.fixture
def mock_embedding():
    with patch('app.services.strategic_framework_service.EmbeddingService') as mock_cls:
        instance = Mock()
        instance.search_similar_insights.return_value = []
        mock_cls.return_value = instance
        yield instance


class TestStrategicFrameworkService:

    def test_service_initialization(self, mock_llm, mock_embedding):
        """
        GIVEN: StrategicFrameworkService class
        WHEN: Initializing the service
        THEN: Service is created with llm attribute
        """
        service = StrategicFrameworkService()
        assert service is not None
        assert hasattr(service, 'llm')

    def test_generate_swot_returns_all_four_quadrants(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: A competitor
        WHEN: generate_swot is called
        THEN: Returns SWOTAnalysis with all 4 quadrants populated
        """
        mock_llm.invoke.return_value = Mock(content="""
        {
            "strengths": [
                {"description": "Strong brand recognition", "evidence": "Top search results", "impact_score": 0.85}
            ],
            "weaknesses": [
                {"description": "High pricing", "evidence": "Price comparison shows 30% premium", "impact_score": 0.70}
            ],
            "opportunities": [
                {"description": "Enterprise market expansion", "evidence": "Recent enterprise-focused messaging", "impact_score": 0.80}
            ],
            "threats": [
                {"description": "New low-cost entrants", "evidence": "3 new competitors launched this quarter", "impact_score": 0.75}
            ],
            "overall_assessment": "Strong market position but pricing vulnerability",
            "confidence_score": 0.85
        }
        """)

        service = StrategicFrameworkService()
        swot = service.generate_swot(competitor_id=test_competitor.id, db=db)

        assert swot is not None
        assert len(swot.strengths) >= 1
        assert len(swot.weaknesses) >= 1
        assert len(swot.opportunities) >= 1
        assert len(swot.threats) >= 1

    def test_swot_items_have_required_fields(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: LLM returns valid SWOT data
        WHEN: generate_swot is called
        THEN: Each item has description, evidence, impact_score
        """
        mock_llm.invoke.return_value = Mock(content="""
        {
            "strengths": [
                {"description": "Market leader in SMB", "evidence": "40% market share", "impact_score": 0.90}
            ],
            "weaknesses": [
                {"description": "Limited enterprise features", "evidence": "Missing SSO, audit logs", "impact_score": 0.65}
            ],
            "opportunities": [
                {"description": "API marketplace growth", "evidence": "3x developer signups", "impact_score": 0.78}
            ],
            "threats": [
                {"description": "Microsoft entering space", "evidence": "Teams feature announcement", "impact_score": 0.88}
            ],
            "overall_assessment": "Solid SMB player facing upmarket pressure",
            "confidence_score": 0.82
        }
        """)

        service = StrategicFrameworkService()
        swot = service.generate_swot(competitor_id=test_competitor.id, db=db)

        for item in swot.strengths + swot.weaknesses + swot.opportunities + swot.threats:
            assert "description" in item
            assert "evidence" in item
            assert "impact_score" in item
            assert 0.0 <= item["impact_score"] <= 1.0

    def test_swot_saved_to_db(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: generate_swot is called
        WHEN: Analysis completes
        THEN: SWOTAnalysis record is persisted to DB
        """
        mock_llm.invoke.return_value = Mock(content="""
        {
            "strengths": [{"description": "Fast execution", "evidence": "Speed metrics", "impact_score": 0.80}],
            "weaknesses": [{"description": "Poor docs", "evidence": "User feedback", "impact_score": 0.60}],
            "opportunities": [{"description": "New market", "evidence": "Industry report", "impact_score": 0.75}],
            "threats": [{"description": "Bigger competitor", "evidence": "Recent funding", "impact_score": 0.85}],
            "overall_assessment": "Growing but vulnerable",
            "confidence_score": 0.78
        }
        """)

        service = StrategicFrameworkService()
        service.generate_swot(competitor_id=test_competitor.id, db=db)

        saved = db.query(SWOTAnalysis).filter(
            SWOTAnalysis.competitor_id == test_competitor.id
        ).first()
        assert saved is not None
        assert saved.competitor_id == test_competitor.id
        assert saved.confidence_score > 0.0

    def test_calculate_threat_score_returns_0_to_100(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: A competitor
        WHEN: calculate_threat_score is called
        THEN: Returns float between 0 and 100
        """
        mock_llm.invoke.return_value = Mock(content="""
        {
            "pricing": 72,
            "innovation": 65,
            "market_share": 80,
            "resource_strength": 70,
            "partnerships": 55
        }
        """)

        service = StrategicFrameworkService()
        assessment = service.calculate_threat_score(
            competitor_id=test_competitor.id,
            db=db
        )

        assert assessment is not None
        assert 0.0 <= assessment.threat_score <= 100.0

    def test_threat_assessment_saved_to_db(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: calculate_threat_score is called
        WHEN: Scoring completes
        THEN: ThreatAssessment record is persisted to DB
        """
        mock_llm.invoke.return_value = Mock(content="""
        {
            "pricing": 60,
            "innovation": 70,
            "market_share": 65,
            "resource_strength": 75,
            "partnerships": 50
        }
        """)

        service = StrategicFrameworkService()
        service.calculate_threat_score(competitor_id=test_competitor.id, db=db)

        saved = db.query(ThreatAssessment).filter(
            ThreatAssessment.competitor_id == test_competitor.id
        ).first()
        assert saved is not None
        assert saved.threat_score is not None

    def test_threat_assessment_has_category_keys(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: calculate_threat_score is called
        WHEN: Scoring completes
        THEN: threat_categories contains pricing, innovation, market_share,
              resource_strength, partnerships
        """
        mock_llm.invoke.return_value = Mock(content="""
        {
            "pricing": 78,
            "innovation": 82,
            "market_share": 55,
            "resource_strength": 90,
            "partnerships": 68
        }
        """)

        service = StrategicFrameworkService()
        assessment = service.calculate_threat_score(
            competitor_id=test_competitor.id,
            db=db
        )

        cats = assessment.threat_categories
        for key in ("pricing", "innovation", "market_share", "resource_strength", "partnerships"):
            assert key in cats
            assert 0 <= cats[key] <= 100

    def test_llm_failure_returns_none_gracefully(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: LLM raises an exception
        WHEN: generate_swot is called
        THEN: Returns None without raising
        """
        mock_llm.invoke.side_effect = Exception("LLM API timeout")

        service = StrategicFrameworkService()
        result = service.generate_swot(competitor_id=test_competitor.id, db=db)

        assert result is None

    def test_regenerate_swot_replaces_existing(
        self, db, test_competitor, mock_llm, mock_embedding
    ):
        """
        GIVEN: An existing SWOTAnalysis for a competitor
        WHEN: generate_swot is called again
        THEN: Old record is replaced - only 1 record exists in DB
        """
        # Seed an existing SWOT
        existing = SWOTAnalysis(
            competitor_id=test_competitor.id,
            analysis_date=datetime.utcnow(),
            strengths=[{"description": "Old strength", "evidence": "Old evidence", "impact_score": 0.5}],
            weaknesses=[],
            opportunities=[],
            threats=[],
            overall_assessment="Old assessment",
            confidence_score=0.60
        )
        db.add(existing)
        db.commit()

        mock_llm.invoke.return_value = Mock(content="""
        {
            "strengths": [{"description": "New strength", "evidence": "New evidence", "impact_score": 0.90}],
            "weaknesses": [{"description": "New weakness", "evidence": "New evidence", "impact_score": 0.55}],
            "opportunities": [{"description": "New opportunity", "evidence": "New evidence", "impact_score": 0.70}],
            "threats": [{"description": "New threat", "evidence": "New evidence", "impact_score": 0.80}],
            "overall_assessment": "Updated assessment",
            "confidence_score": 0.88
        }
        """)

        service = StrategicFrameworkService()
        service.generate_swot(competitor_id=test_competitor.id, db=db)

        count = db.query(SWOTAnalysis).filter(
            SWOTAnalysis.competitor_id == test_competitor.id
        ).count()
        assert count == 1

        latest = db.query(SWOTAnalysis).filter(
            SWOTAnalysis.competitor_id == test_competitor.id
        ).first()
        assert latest.overall_assessment == "Updated assessment"
