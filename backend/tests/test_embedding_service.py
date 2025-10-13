import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights
from app.services.embedding_service import EmbeddingService


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
def test_processed_insights(db_session: Session):
    """Create test processed insights"""
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
        content="Test Company announces new AI product with advanced features",
        content_type="text/html",
        url="https://testcompany.com/blog/ai-product"
    )
    db_session.add(raw_content)
    db_session.commit()

    processed_insights = ProcessedInsights(
        raw_content_id=raw_content.id,
        summary="Company announces new AI product with advanced machine learning capabilities",
        key_points=["AI product launch", "Advanced features", "Market expansion"],
        sentiment="positive",
        insights="Strategic move into AI market"
    )
    db_session.add(processed_insights)
    db_session.commit()

    db_session.refresh(processed_insights)
    return processed_insights


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for embeddings"""
    mock_client = Mock()
    mock_client.client = Mock()
    mock_embedding = Mock()
    mock_embedding.embedding = [0.1] * 1536  # 1536-dimensional vector
    mock_response = Mock()
    mock_response.data = [mock_embedding]
    mock_client.client.embeddings.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_pinecone_client():
    """Mock Pinecone client"""
    mock_client = Mock()
    mock_client.upsert_embedding.return_value = True
    return mock_client


@pytest.fixture
def embedding_service(mock_openai_client, mock_pinecone_client):
    """Create embedding service with mocked clients"""
    return EmbeddingService(
        openai_client=mock_openai_client,
        pinecone_client=mock_pinecone_client
    )


def test_generate_embedding_from_text(embedding_service):
    """Test generating embedding from text"""
    text = "This is test content for embedding generation"

    embedding = embedding_service.generate_embedding(text)

    assert embedding is not None
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)


def test_generate_embedding_error_handling(mock_pinecone_client):
    """Test embedding generation error handling"""
    mock_openai = Mock()
    mock_openai.embeddings.create.side_effect = Exception("API Error")

    service = EmbeddingService(
        openai_client=mock_openai,
        pinecone_client=mock_pinecone_client
    )

    embedding = service.generate_embedding("test text")

    assert embedding is None


def test_store_insight_embedding(embedding_service, test_processed_insights, db_session):
    """Test storing insight embedding in vector database"""
    result = embedding_service.store_insight_embedding(
        test_processed_insights.id,
        db_session
    )

    assert result is True
    embedding_service.pinecone_client.upsert_embedding.assert_called_once()


def test_store_insight_embedding_with_metadata(embedding_service, test_processed_insights, db_session):
    """Test that metadata is properly stored with embedding"""
    embedding_service.store_insight_embedding(
        test_processed_insights.id,
        db_session
    )

    # Verify upsert was called with correct metadata structure
    call_args = embedding_service.pinecone_client.upsert_embedding.call_args

    assert call_args is not None
    vector_id = call_args[0][0]
    embedding = call_args[0][1]
    metadata = call_args[0][2]

    assert vector_id.startswith("insight_")
    assert len(embedding) == 1536
    assert metadata["insight_id"] == test_processed_insights.id
    assert metadata["summary"] == test_processed_insights.summary
    assert metadata["sentiment"] == test_processed_insights.sentiment


def test_store_insight_embedding_invalid_id(embedding_service, db_session):
    """Test storing embedding with invalid insight ID"""
    result = embedding_service.store_insight_embedding(99999, db_session)

    assert result is False


def test_search_similar_insights(embedding_service):
    """Test searching for similar insights"""
    query_text = "AI product launch announcement"

    # Mock Pinecone response
    embedding_service.pinecone_client.query_similar.return_value = [
        {
            "id": "insight_1",
            "score": 0.95,
            "metadata": {
                "insight_id": 1,
                "summary": "AI product announcement",
                "sentiment": "positive"
            }
        }
    ]

    results = embedding_service.search_similar_insights(query_text, top_k=5)

    assert len(results) == 1
    assert results[0]["score"] == 0.95
    assert results[0]["metadata"]["sentiment"] == "positive"


def test_search_similar_insights_with_filter(embedding_service):
    """Test searching with competitor filter"""
    query_text = "product update"
    competitor_id = 1

    embedding_service.pinecone_client.query_similar.return_value = []

    results = embedding_service.search_similar_insights(
        query_text,
        top_k=10,
        competitor_id=competitor_id
    )

    # Verify filter was passed to Pinecone
    call_args = embedding_service.pinecone_client.query_similar.call_args
    assert call_args[1].get("filter") == {"competitor_id": competitor_id}


def test_batch_store_insights(embedding_service, test_processed_insights, db_session):
    """Test batch storing multiple insights"""
    insight_ids = [test_processed_insights.id]

    results = embedding_service.batch_store_insights(insight_ids, db_session)

    assert results["success"] == 1
    assert results["failed"] == 0


def test_delete_insight_embedding(embedding_service):
    """Test deleting insight embedding from vector database"""
    insight_id = 123

    embedding_service.pinecone_client.delete_vectors.return_value = True

    result = embedding_service.delete_insight_embedding(insight_id)

    assert result is True
    embedding_service.pinecone_client.delete_vectors.assert_called_once_with(["insight_123"])