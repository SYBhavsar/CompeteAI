"""
Test suite for Predictive Analysis Service

Tests AI-powered predictions using RAG + LLM chain:
- Predict next competitor moves from historical events
- Required prediction fields (type, confidence, timeframe, reasoning)
- RAG context retrieval via EmbeddingService
- Graceful error handling
- Outcome tracking and accuracy reporting

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.strategic_event import StrategicEvent
from app.models.prediction import CompetitorPrediction
from app.services.predictive_analysis_service import PredictiveAnalysisService


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
def mock_embedding_service():
    with patch('app.services.predictive_analysis_service.EmbeddingService') as mock_cls:
        instance = Mock()
        instance.search_similar_insights.return_value = []
        mock_cls.return_value = instance
        yield instance


class TestPredictiveAnalysisService:
    """Test PredictiveAnalysisService"""

    def test_service_initialization(self, mock_llm, mock_embedding_service):
        """
        GIVEN: PredictiveAnalysisService class
        WHEN: Initializing the service
        THEN: Service is created with LLM and embedding service dependencies
        """
        service = PredictiveAnalysisService()
        assert service is not None
        assert hasattr(service, 'llm')

    def test_predict_next_moves_saves_to_db(
        self, db, test_competitor, mock_llm, mock_embedding_service
    ):
        """
        GIVEN: Competitor with strategic events
        WHEN: Calling predict_next_moves
        THEN: Predictions are saved to DB and returned
        """
        # Create historical events
        for i, category in enumerate(["product_launch", "pricing_change", "partnership"]):
            event = StrategicEvent(
                competitor_id=test_competitor.id,
                event_category=category,
                title=f"Event {i}",
                description=f"Description {i}",
                confidence=0.90,
                event_date=datetime.utcnow() - timedelta(days=30 - i),
                strategic_implications="Competitive threat",
                entities_involved={},
                source_insights={}
            )
            db.add(event)
        db.commit()

        mock_llm.invoke.return_value = Mock(content="""
        [
            {
                "prediction_type": "pricing_change",
                "confidence": 0.82,
                "timeframe": "30_days",
                "reasoning": "Recent product launch typically followed by pricing adjustment",
                "suggested_action": "Review our own pricing strategy"
            },
            {
                "prediction_type": "market_entry",
                "confidence": 0.71,
                "timeframe": "90_days",
                "reasoning": "Partnership + funding pattern suggests geographic expansion",
                "suggested_action": "Strengthen relationships in target markets"
            },
            {
                "prediction_type": "product_launch",
                "confidence": 0.68,
                "timeframe": "60_days",
                "reasoning": "Hiring pattern indicates new product development",
                "suggested_action": "Accelerate our roadmap"
            }
        ]
        """)

        service = PredictiveAnalysisService()
        predictions = service.predict_next_moves(
            competitor_id=test_competitor.id,
            db=db
        )

        assert len(predictions) == 3
        saved = db.query(CompetitorPrediction).filter(
            CompetitorPrediction.competitor_id == test_competitor.id
        ).all()
        assert len(saved) == 3

    def test_predictions_have_required_fields(
        self, db, test_competitor, mock_llm, mock_embedding_service
    ):
        """
        GIVEN: LLM returns valid prediction data
        WHEN: predict_next_moves is called
        THEN: Each prediction has type, confidence, timeframe, reasoning, outcome=pending
        """
        event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="funding",
            title="Series A",
            description="Raised $10M",
            confidence=0.90,
            event_date=datetime.utcnow() - timedelta(days=14),
            strategic_implications="Competitive threat",
            entities_involved={},
            source_insights={}
        )
        db.add(event)
        db.commit()

        mock_llm.invoke.return_value = Mock(content="""
        [
            {
                "prediction_type": "acquisition",
                "confidence": 0.78,
                "timeframe": "90_days",
                "reasoning": "Cash-rich competitor eyeing smaller players",
                "suggested_action": "Monitor M&A activity closely"
            }
        ]
        """)

        service = PredictiveAnalysisService()
        predictions = service.predict_next_moves(
            competitor_id=test_competitor.id,
            db=db
        )

        assert len(predictions) == 1
        p = predictions[0]
        assert p.prediction_type == "acquisition"
        assert 0.0 <= p.confidence <= 1.0
        assert p.timeframe in ("30_days", "60_days", "90_days", "180_days")
        assert p.reasoning is not None and len(p.reasoning) > 0
        assert p.outcome == "pending"
        assert p.competitor_id == test_competitor.id

    def test_rag_search_called_for_context(
        self, db, test_competitor, mock_llm, mock_embedding_service
    ):
        """
        GIVEN: A competitor with historical events
        WHEN: predict_next_moves runs
        THEN: EmbeddingService.search_similar_insights is called to retrieve RAG context
        """
        event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="partnership",
            title="Key Partnership",
            description="Strategic alliance formed",
            confidence=0.88,
            event_date=datetime.utcnow() - timedelta(days=10),
            strategic_implications="Market expansion",
            entities_involved={},
            source_insights={}
        )
        db.add(event)
        db.commit()

        mock_llm.invoke.return_value = Mock(content="[]")

        service = PredictiveAnalysisService()
        service.predict_next_moves(competitor_id=test_competitor.id, db=db)

        mock_embedding_service.search_similar_insights.assert_called_once()

    def test_no_historical_events_returns_empty(
        self, db, test_competitor, mock_llm, mock_embedding_service
    ):
        """
        GIVEN: Competitor with no strategic events
        WHEN: predict_next_moves is called
        THEN: Returns empty list (nothing to predict from)
        """
        service = PredictiveAnalysisService()
        predictions = service.predict_next_moves(
            competitor_id=test_competitor.id,
            db=db
        )

        assert predictions == []

    def test_llm_failure_returns_empty_gracefully(
        self, db, test_competitor, mock_llm, mock_embedding_service
    ):
        """
        GIVEN: LLM call raises an exception
        WHEN: predict_next_moves is called
        THEN: Returns empty list without raising
        """
        event = StrategicEvent(
            competitor_id=test_competitor.id,
            event_category="funding",
            title="Series B",
            description="Raised $50M",
            confidence=0.95,
            event_date=datetime.utcnow() - timedelta(days=7),
            strategic_implications="Well-funded competitor",
            entities_involved={},
            source_insights={}
        )
        db.add(event)
        db.commit()

        mock_llm.invoke.side_effect = Exception("LLM API error")

        service = PredictiveAnalysisService()
        predictions = service.predict_next_moves(
            competitor_id=test_competitor.id,
            db=db
        )

        assert predictions == []

    def test_update_prediction_outcome(
        self, db, test_competitor, mock_llm, mock_embedding_service
    ):
        """
        GIVEN: An existing pending prediction
        WHEN: update_prediction_outcome is called with 'correct'
        THEN: Prediction outcome is updated and resolved_at is set
        """
        prediction = CompetitorPrediction(
            competitor_id=test_competitor.id,
            prediction_type="pricing_change",
            confidence=0.80,
            timeframe="30_days",
            reasoning="Expected based on pattern",
            suggested_action="Monitor pricing",
            outcome="pending",
            predicted_at=datetime.utcnow() - timedelta(days=25)
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        service = PredictiveAnalysisService()
        updated = service.update_prediction_outcome(
            prediction_id=prediction.id,
            outcome="correct",
            db=db
        )

        assert updated.outcome == "correct"
        assert updated.resolved_at is not None

    def test_active_predictions_excludes_expired(
        self, db, test_competitor, mock_llm, mock_embedding_service
    ):
        """
        GIVEN: Mix of pending and resolved predictions
        WHEN: get_active_predictions is called
        THEN: Only pending (unresolved) predictions returned
        """
        pending = CompetitorPrediction(
            competitor_id=test_competitor.id,
            prediction_type="product_launch",
            confidence=0.75,
            timeframe="60_days",
            reasoning="Active prediction",
            suggested_action="Watch releases",
            outcome="pending",
            predicted_at=datetime.utcnow()
        )
        resolved = CompetitorPrediction(
            competitor_id=test_competitor.id,
            prediction_type="acquisition",
            confidence=0.70,
            timeframe="90_days",
            reasoning="Old prediction",
            suggested_action="N/A",
            outcome="correct",
            predicted_at=datetime.utcnow() - timedelta(days=60),
            resolved_at=datetime.utcnow() - timedelta(days=10)
        )
        db.add(pending)
        db.add(resolved)
        db.commit()

        service = PredictiveAnalysisService()
        active = service.get_active_predictions(
            competitor_id=test_competitor.id,
            db=db
        )

        assert len(active) == 1
        assert active[0].outcome == "pending"
