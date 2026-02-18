import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights
from app.schemas.ai_responses import InsightsResult, SentimentResult, SummaryResult
from app.services.content_processing_service import ContentProcessingService


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_raw_content(db_session: Session):
    user = User(email="test@example.com", hashed_password="hash", full_name="Test User")
    db_session.add(user)
    db_session.commit()

    competitor = Competitor(name="Test Co", domain="test.com", user_id=user.id)
    db_session.add(competitor)
    db_session.commit()

    data_source = DataSource(
        competitor_id=competitor.id,
        source_type="website",
        url="https://test.com",
        is_active=True,
    )
    db_session.add(data_source)
    db_session.commit()

    raw_content = RawContent(
        data_source_id=data_source.id,
        content="Test Company announces new AI product with advanced features available next quarter.",
        content_type="text/html",
        url="https://test.com/news",
    )
    db_session.add(raw_content)
    db_session.commit()
    db_session.refresh(raw_content)
    return raw_content


@pytest.fixture
def service():
    """ContentProcessingService with all LLM and sub-service calls mocked."""

    def make_llm(service_name: str) -> Mock:
        runnable = Mock()
        if service_name == "summarization":
            runnable.invoke.return_value = SummaryResult(summary="Mock summary")
        elif service_name == "insight_extraction":
            runnable.invoke.return_value = InsightsResult(insights="Mock insights")
        elif service_name == "sentiment_analysis":
            runnable.invoke.return_value = SentimentResult(sentiment="positive")
        else:
            runnable.invoke.return_value = Mock()
        mock_llm = Mock()
        mock_llm.with_structured_output.return_value = runnable
        return mock_llm

    with (
        patch("app.core.llm_factory.LLMFactory.create", side_effect=make_llm),
        patch("app.services.content_processing_service.QualityScoringService") as mock_qs,
        patch("app.services.content_processing_service.EntityExtractionService"),
        patch("app.services.content_processing_service.StrategicDetectionService"),
    ):
        mock_qs.return_value.calculate_quality_score.return_value = 75.0
        yield ContentProcessingService()


def test_process_raw_content_saves_typed_results(service, test_raw_content, db_session):
    result = service.process_raw_content(test_raw_content.id, db_session)

    assert result is not None
    assert result.summary == "Mock summary"
    assert result.insights == "Mock insights"
    assert result.sentiment == "positive"
    assert result.raw_content_id == test_raw_content.id


def test_already_processed_skips_llm(service, test_raw_content, db_session):
    existing = ProcessedInsights(
        raw_content_id=test_raw_content.id,
        summary="Existing summary",
        sentiment="neutral",
        insights="Existing insights",
    )
    db_session.add(existing)
    db_session.commit()

    result = service.process_raw_content(test_raw_content.id, db_session)

    assert result.id == existing.id
    service._summarization_llm.invoke.assert_not_called()


def test_llm_error_returns_none_and_marks_failed(service, test_raw_content, db_session):
    with patch.object(service, "_summarize", side_effect=Exception("LLM error")):
        result = service.process_raw_content(test_raw_content.id, db_session)

    assert result is None
    db_session.refresh(test_raw_content)
    assert test_raw_content.status == "failed"
