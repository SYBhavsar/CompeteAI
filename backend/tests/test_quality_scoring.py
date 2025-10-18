import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights
from app.services.quality_scoring_service import QualityScoringService


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def quality_scoring_service():
    """Create quality scoring service"""
    return QualityScoringService()


@pytest.fixture
def test_insights(db_session: Session):
    """Create test insights with various quality levels"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()

    competitor = Competitor(
        name="Test Company",
        domain="testcompany.com",
        user_id=user.id
    )
    db_session.add(competitor)
    db_session.commit()

    data_source = DataSource(
        competitor_id=competitor.id,
        source_type="website",
        url="https://testcompany.com/blog",
        is_active=True
    )
    db_session.add(data_source)
    db_session.commit()

    raw_content = RawContent(
        data_source_id=data_source.id,
        content="Test Company announces revolutionary AI product",
        content_type="text/html",
        url="https://testcompany.com/blog/ai-product"
    )
    db_session.add(raw_content)
    db_session.commit()

    # High quality insight
    high_quality = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Test Company announces groundbreaking AI product with advanced machine learning capabilities that will transform the industry landscape",
        key_points=["AI product launch", "Advanced ML features", "Industry transformation", "Market leadership"],
        sentiment="positive",
        insights="Strategic move into AI demonstrates strong innovation focus and competitive positioning in emerging technology sector"
    )
    db_session.add(high_quality)
    db_session.commit()

    db_session.refresh(high_quality)
    return high_quality


def test_calculate_quality_score_high_quality(quality_scoring_service, test_insights):
    """Test quality score calculation for high quality insight"""
    score = quality_scoring_service.calculate_quality_score(test_insights)

    assert score is not None
    assert 0.0 <= score <= 1.0
    assert score >= 0.7  # High quality should score above 0.7


def test_calculate_quality_score_low_quality(quality_scoring_service, db_session):
    """Test quality score calculation for low quality insight"""
    user = User(
        email="test2@example.com",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()

    competitor = Competitor(
        name="Test Company",
        domain="testcompany.com",
        user_id=user.id
    )
    db_session.add(competitor)
    db_session.commit()

    data_source = DataSource(
        competitor_id=competitor.id,
        source_type="website",
        url="https://testcompany.com/blog",
        is_active=True
    )
    db_session.add(data_source)
    db_session.commit()

    raw_content = RawContent(
        data_source_id=data_source.id,
        content="Short content",
        content_type="text/html",
        url="https://testcompany.com/blog/post"
    )
    db_session.add(raw_content)
    db_session.commit()

    # Low quality insight
    low_quality = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Short summary",
        key_points=["One point"],
        sentiment="neutral",
        insights="Brief insight"
    )
    db_session.add(low_quality)
    db_session.commit()

    score = quality_scoring_service.calculate_quality_score(low_quality)

    assert score is not None
    assert 0.0 <= score <= 1.0
    assert score < 0.5  # Low quality should score below 0.5


def test_quality_factors_summary_length(quality_scoring_service):
    """Test quality factor: summary length"""
    # Long, detailed summary
    long_summary = "This is a comprehensive and detailed summary that provides substantial information about the topic and demonstrates thorough analysis"
    score_long = quality_scoring_service._score_summary_length(long_summary)

    # Short summary
    short_summary = "Brief summary"
    score_short = quality_scoring_service._score_summary_length(short_summary)

    assert score_long > score_short


def test_quality_factors_key_points_count(quality_scoring_service):
    """Test quality factor: key points count"""
    # Multiple key points
    many_points = ["Point 1", "Point 2", "Point 3", "Point 4"]
    score_many = quality_scoring_service._score_key_points_count(many_points)

    # Few key points
    few_points = ["Point 1"]
    score_few = quality_scoring_service._score_key_points_count(few_points)

    assert score_many > score_few


def test_quality_factors_insights_depth(quality_scoring_service):
    """Test quality factor: insights depth"""
    # Detailed insights
    detailed = "Comprehensive strategic analysis showing competitive positioning, market trends, innovation focus, and business implications for stakeholders"
    score_detailed = quality_scoring_service._score_insights_depth(detailed)

    # Shallow insights
    shallow = "Good news"
    score_shallow = quality_scoring_service._score_insights_depth(shallow)

    assert score_detailed > score_shallow


def test_quality_factors_sentiment_confidence(quality_scoring_service):
    """Test quality factor: sentiment confidence"""
    # Strong positive sentiment
    positive_score = quality_scoring_service._score_sentiment_confidence("positive")

    # Neutral sentiment (less confident)
    neutral_score = quality_scoring_service._score_sentiment_confidence("neutral")

    assert positive_score >= neutral_score


def test_update_quality_scores_batch(quality_scoring_service, test_insights, db_session):
    """Test batch updating quality scores"""
    insight_ids = [test_insights.id]

    results = quality_scoring_service.update_quality_scores(insight_ids, db_session)

    assert results["updated"] == 1
    assert results["failed"] == 0

    # Verify score was stored
    db_session.refresh(test_insights)
    assert test_insights.quality_score is not None
    assert 0.0 <= test_insights.quality_score <= 1.0


def test_get_quality_distribution(quality_scoring_service, test_insights, db_session):
    """Test getting quality score distribution"""
    # First update quality score
    quality_scoring_service.update_quality_scores([test_insights.id], db_session)

    distribution = quality_scoring_service.get_quality_distribution(db_session)

    assert "high" in distribution
    assert "medium" in distribution
    assert "low" in distribution
    assert distribution["high"] >= 0