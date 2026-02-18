"""
Test suite for Strategic Detection Service

Tests AI-powered detection of strategic moves:
- Market entries, M&A, partnerships, product launches
- Pricing changes, leadership changes, funding rounds
- Pattern library + GPT-4 reasoning

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.strategic_event import StrategicEvent
from app.models.entity import Entity
from app.services.strategic_detection_service import StrategicDetectionService


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
def mock_openai():
    """Mock LLMFactory.create to control the LLM instance used by the service."""
    with patch('app.core.llm_factory.LLMFactory.create') as mock:
        yield mock


class TestStrategicDetectionService:
    """Test StrategicDetectionService"""

    def test_service_initialization(self, mock_openai):
        """
        GIVEN: StrategicDetectionService class
        WHEN: Initializing the service
        THEN: Service is created with GPT-4
        """
        service = StrategicDetectionService()
        assert service is not None

    def test_detect_market_entry(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content about market expansion
        WHEN: Detecting strategic moves
        THEN: Market entry event is detected
        """
        content = """
        We're excited to announce our expansion into the European market,
        launching operations in Germany, France, and the UK starting Q2 2026.
        """

        # Mock GPT-4 response
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "market_entry", "confidence": 0.92, "title": "European Market Expansion", "description": "Expanding to Germany, France, UK", "strategic_implications": "Threat to our European operations", "entities": ["Germany", "France", "UK"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 1
        assert events[0].event_category == "market_entry"
        assert events[0].confidence >= 0.8

    def test_detect_acquisition(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content about acquisition
        WHEN: Detecting strategic moves
        THEN: Acquisition event is detected
        """
        content = """
        Today we announced the acquisition of TechCo for $50 million to
        enhance our AI capabilities and expand our engineering team.
        """

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "acquisition", "confidence": 0.95, "title": "Acquired TechCo", "description": "Acquisition for $50M to enhance AI", "strategic_implications": "Strengthens AI position", "entities": ["TechCo", "$50M"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 1
        assert events[0].event_category == "acquisition"

    def test_detect_partnership(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content about strategic partnership
        WHEN: Detecting strategic moves
        THEN: Partnership event is detected
        """
        content = """
        We're thrilled to announce a strategic partnership with Microsoft
        to integrate our platform with Azure cloud services.
        """

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "partnership", "confidence": 0.94, "title": "Microsoft Partnership", "description": "Azure integration partnership", "strategic_implications": "Microsoft gives them enterprise credibility", "entities": ["Microsoft", "Azure"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 1
        assert events[0].event_category == "partnership"

    def test_detect_product_launch(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content about product launch
        WHEN: Detecting strategic moves
        THEN: Product launch event is detected
        """
        content = """
        Introducing our new AI Analytics Suite v2.0 - featuring real-time
        insights, predictive analytics, and custom dashboards. Available now.
        """

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "product_launch", "confidence": 0.96, "title": "AI Analytics Suite v2.0 Launch", "description": "New product with real-time insights", "strategic_implications": "Direct competitor to our analytics product", "entities": ["AI Analytics Suite v2.0"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 1
        assert events[0].event_category == "product_launch"

    def test_detect_pricing_change(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content about pricing change
        WHEN: Detecting strategic moves
        THEN: Pricing change event is detected
        """
        content = """
        Effective March 1st, our Enterprise plan will be priced at $999/month,
        down from $1,499/month - a 33% reduction to better serve our customers.
        """

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "pricing_change", "confidence": 0.98, "title": "33% Price Reduction", "description": "Enterprise plan $1499 to $999/mo", "strategic_implications": "Aggressive pricing threatens our positioning", "entities": ["Enterprise plan", "$999/month"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 1
        assert events[0].event_category == "pricing_change"

    def test_detect_leadership_change(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content about leadership hire
        WHEN: Detecting strategic moves
        THEN: Leadership change event is detected
        """
        content = """
        We're pleased to announce that Jane Smith has joined as our new
        Chief Technology Officer. Jane brings 15 years of experience from Google.
        """

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "leadership_change", "confidence": 0.90, "title": "New CTO Appointed", "description": "Jane Smith from Google as CTO", "strategic_implications": "Strong technical leadership hire", "entities": ["Jane Smith", "Google"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 1
        assert events[0].event_category == "leadership_change"

    def test_detect_funding(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content about funding round
        WHEN: Detecting strategic moves
        THEN: Funding event is detected
        """
        content = """
        We're excited to announce our $50M Series B funding round led by
        Sequoia Capital, bringing our total funding to $75M.
        """

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "funding", "confidence": 0.97, "title": "$50M Series B", "description": "Series B led by Sequoia Capital", "strategic_implications": "Well-funded competitor with growth capital", "entities": ["$50M", "Sequoia Capital"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 1
        assert events[0].event_category == "funding"

    def test_multiple_events_detected(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content with multiple strategic moves
        WHEN: Detecting strategic moves
        THEN: Multiple events are detected
        """
        content = """
        Today marks a major milestone: we've acquired TechCo for $30M and
        partnered with Microsoft to launch our new AI Platform at $499/month.
        """

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='[{"event_category": "acquisition", "confidence": 0.95, "title": "Acquired TechCo", "description": "$30M acquisition", "strategic_implications": "Growth through M&A", "entities": ["TechCo"]}, {"event_category": "partnership", "confidence": 0.90, "title": "Microsoft Partnership", "description": "Partnership for AI Platform", "strategic_implications": "Enterprise credibility", "entities": ["Microsoft"]}]'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert len(events) >= 2

    def test_with_extracted_entities(self, mock_openai, db, test_competitor):
        """
        GIVEN: Pre-extracted entities
        WHEN: Detecting strategic moves
        THEN: Entities are used in detection
        """
        # Create entities
        microsoft = Entity(
            entity_type="company",
            name="Microsoft",
            aliases=[],
            first_mentioned=datetime.utcnow(),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        db.add(microsoft)
        db.commit()

        content = "Partnership with Microsoft announced"

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"event_category": "partnership", "confidence": 0.93, "title": "Microsoft Partnership", "description": "Strategic partnership", "strategic_implications": "Cloud integration", "entities": ["Microsoft"]}'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[microsoft],
            db=db
        )

        assert len(events) >= 1

    def test_no_strategic_moves(self, mock_openai, db, test_competitor):
        """
        GIVEN: Content with no strategic moves
        WHEN: Detecting strategic moves
        THEN: Returns empty list
        """
        content = "Our office will be closed for the holidays."

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='[]'
        )
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content=content,
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert events == []

    def test_error_handling(self, mock_openai, db, test_competitor):
        """
        GIVEN: LLM call fails
        WHEN: Detecting strategic moves
        THEN: Error is handled gracefully
        """
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM Error")
        mock_openai.return_value = mock_llm

        service = StrategicDetectionService()
        events = service.detect_strategic_moves(
            content="Test content",
            competitor_id=test_competitor.id,
            entities=[],
            db=db
        )

        assert events == []
