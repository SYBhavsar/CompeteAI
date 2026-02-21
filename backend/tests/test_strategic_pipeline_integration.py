"""
Test suite for Strategic Intelligence Pipeline Integration

Tests the integration of entity extraction and strategic detection
into the main content processing pipeline.

Following TDD - these tests will FAIL initially.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.core.database import SessionLocal, Base, engine
from app.models import User, Competitor
from app.models.data_source import DataSource
from app.models.raw_content import RawContent
from app.models.processed_insights import ProcessedInsights
from app.models.entity import Entity
from app.models.strategic_event import StrategicEvent
from app.schemas.ai_responses import SummaryResult, InsightsResult, SentimentResult
from app.services.content_processing_service import ContentProcessingService


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
def test_data_source(db, test_competitor):
    source = DataSource(
        competitor_id=test_competitor.id,
        source_type="blog",
        url="https://competitor.com/blog"
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@pytest.fixture
def test_raw_content(db, test_data_source):
    content = RawContent(
        data_source_id=test_data_source.id,
        url="https://competitor.com/blog/announcement",
        content_type="blog",
        content="We're excited to announce our Series B funding of $50M led by Sequoia Capital.",
        content_hash="test_hash_123"
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


def _make_llm_mock():
    """Return a mock LLM that returns valid structured outputs for all 3 pipeline calls."""
    mock_runnable = Mock()
    mock_runnable.invoke.side_effect = [
        SummaryResult(summary="Funding announcement"),
        InsightsResult(insights="$50M Series B"),
        SentimentResult(sentiment="positive"),
    ]
    mock_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_runnable
    return mock_llm


class TestStrategicPipelineIntegration:
    """Test strategic intelligence pipeline integration"""

    @patch('app.services.content_processing_service.QualityScoringService')
    @patch('app.services.content_processing_service.EntityExtractionService')
    @patch('app.services.content_processing_service.StrategicDetectionService')
    @patch('app.core.llm_factory.LLMFactory.create')
    def test_process_content_extracts_entities(
        self, mock_llm_create, mock_strategic_cls, mock_entity_cls, mock_qs_cls,
        db, test_raw_content, test_competitor
    ):
        """
        GIVEN: Raw content with entities
        WHEN: Processing content through pipeline
        THEN: Entity extraction service is called
        """
        mock_llm_create.return_value = _make_llm_mock()

        mock_qs_cls.return_value.calculate_quality_score.return_value = 75.0

        mock_entity = Mock()
        mock_entity.extract_entities.return_value = []
        mock_entity_cls.return_value = mock_entity

        mock_strategic = Mock()
        mock_strategic.detect_strategic_moves.return_value = []
        mock_strategic_cls.return_value = mock_strategic

        service = ContentProcessingService()
        service.process_raw_content(test_raw_content.id, db)

        mock_entity.extract_entities.assert_called_once()

    @patch('app.services.content_processing_service.QualityScoringService')
    @patch('app.services.content_processing_service.EntityExtractionService')
    @patch('app.services.content_processing_service.StrategicDetectionService')
    @patch('app.core.llm_factory.LLMFactory.create')
    def test_process_content_detects_strategic_moves(
        self, mock_llm_create, mock_strategic_cls, mock_entity_cls, mock_qs_cls,
        db, test_raw_content, test_competitor
    ):
        """
        GIVEN: Raw content with strategic move
        WHEN: Processing content through pipeline
        THEN: Strategic detection service is called
        """
        mock_llm_create.return_value = _make_llm_mock()

        mock_qs_cls.return_value.calculate_quality_score.return_value = 75.0

        mock_entity = Mock()
        mock_entity.extract_entities.return_value = []
        mock_entity_cls.return_value = mock_entity

        mock_strategic = Mock()
        mock_strategic.detect_strategic_moves.return_value = []
        mock_strategic_cls.return_value = mock_strategic

        service = ContentProcessingService()
        service.process_raw_content(test_raw_content.id, db)

        mock_strategic.detect_strategic_moves.assert_called_once()

    @patch('app.services.content_processing_service.QualityScoringService')
    @patch('app.services.content_processing_service.EntityExtractionService')
    @patch('app.services.content_processing_service.StrategicDetectionService')
    @patch('app.core.llm_factory.LLMFactory.create')
    def test_entities_passed_to_strategic_detection(
        self, mock_llm_create, mock_strategic_cls, mock_entity_cls, mock_qs_cls,
        db, test_raw_content, test_competitor
    ):
        """
        GIVEN: Entity extraction returns entities
        WHEN: Strategic detection runs
        THEN: Extracted entities are passed to strategic detection
        """
        mock_llm_create.return_value = _make_llm_mock()

        mock_qs_cls.return_value.calculate_quality_score.return_value = 75.0

        microsoft = Entity(
            id=1,
            entity_type="company",
            name="Microsoft",
            aliases=[],
            first_mentioned=datetime.now(timezone.utc),
            competitor_id=test_competitor.id,
            entity_metadata={}
        )
        mock_entity = Mock()
        mock_entity.extract_entities.return_value = [microsoft]
        mock_entity_cls.return_value = mock_entity

        mock_strategic = Mock()
        mock_strategic.detect_strategic_moves.return_value = []
        mock_strategic_cls.return_value = mock_strategic

        service = ContentProcessingService()
        service.process_raw_content(test_raw_content.id, db)

        call_kwargs = mock_strategic.detect_strategic_moves.call_args.kwargs
        assert len(call_kwargs.get('entities', [])) >= 1

    @patch('app.services.content_processing_service.QualityScoringService')
    @patch('app.services.content_processing_service.EntityExtractionService')
    @patch('app.services.content_processing_service.StrategicDetectionService')
    @patch('app.core.llm_factory.LLMFactory.create')
    def test_pipeline_handles_entity_errors_gracefully(
        self, mock_llm_create, mock_strategic_cls, mock_entity_cls, mock_qs_cls,
        db, test_raw_content
    ):
        """
        GIVEN: Entity extraction fails
        WHEN: Processing content
        THEN: Pipeline continues - insight created, strategic detection still runs
        """
        mock_llm_create.return_value = _make_llm_mock()

        mock_qs_cls.return_value.calculate_quality_score.return_value = 75.0

        mock_entity = Mock()
        mock_entity.extract_entities.side_effect = Exception("Entity extraction failed")
        mock_entity_cls.return_value = mock_entity

        mock_strategic = Mock()
        mock_strategic.detect_strategic_moves.return_value = []
        mock_strategic_cls.return_value = mock_strategic

        service = ContentProcessingService()
        insight = service.process_raw_content(test_raw_content.id, db)

        # Insight still created
        assert insight is not None
        # Strategic detection still ran (with empty entities list)
        mock_strategic.detect_strategic_moves.assert_called_once()

    @patch('app.services.content_processing_service.QualityScoringService')
    @patch('app.services.content_processing_service.EntityExtractionService')
    @patch('app.services.content_processing_service.StrategicDetectionService')
    @patch('app.core.llm_factory.LLMFactory.create')
    def test_pipeline_handles_strategic_errors_gracefully(
        self, mock_llm_create, mock_strategic_cls, mock_entity_cls, mock_qs_cls,
        db, test_raw_content
    ):
        """
        GIVEN: Strategic detection fails
        WHEN: Processing content
        THEN: Insight is still returned successfully
        """
        mock_llm_create.return_value = _make_llm_mock()

        mock_qs_cls.return_value.calculate_quality_score.return_value = 75.0

        mock_entity = Mock()
        mock_entity.extract_entities.return_value = []
        mock_entity_cls.return_value = mock_entity

        mock_strategic = Mock()
        mock_strategic.detect_strategic_moves.side_effect = Exception("Detection failed")
        mock_strategic_cls.return_value = mock_strategic

        service = ContentProcessingService()
        insight = service.process_raw_content(test_raw_content.id, db)

        # Insight still returned despite strategic detection failure
        assert insight is not None

    @patch('app.services.content_processing_service.QualityScoringService')
    @patch('app.services.content_processing_service.EntityExtractionService')
    @patch('app.services.content_processing_service.StrategicDetectionService')
    @patch('app.core.llm_factory.LLMFactory.create')
    def test_strategic_detection_receives_competitor_id(
        self, mock_llm_create, mock_strategic_cls, mock_entity_cls, mock_qs_cls,
        db, test_raw_content, test_data_source
    ):
        """
        GIVEN: Raw content linked to a competitor via data source
        WHEN: Pipeline runs
        THEN: Correct competitor_id is passed to both services
        """
        mock_llm_create.return_value = _make_llm_mock()

        mock_qs_cls.return_value.calculate_quality_score.return_value = 75.0

        mock_entity = Mock()
        mock_entity.extract_entities.return_value = []
        mock_entity_cls.return_value = mock_entity

        mock_strategic = Mock()
        mock_strategic.detect_strategic_moves.return_value = []
        mock_strategic_cls.return_value = mock_strategic

        service = ContentProcessingService()
        service.process_raw_content(test_raw_content.id, db)

        # Verify competitor_id passed correctly
        entity_call_kwargs = mock_entity.extract_entities.call_args.kwargs
        strategic_call_kwargs = mock_strategic.detect_strategic_moves.call_args.kwargs

        assert entity_call_kwargs.get('competitor_id') == test_data_source.competitor_id
        assert strategic_call_kwargs.get('competitor_id') == test_data_source.competitor_id
