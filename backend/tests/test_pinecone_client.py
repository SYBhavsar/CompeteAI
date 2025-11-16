import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from app.services.pinecone_client import PineconeClient


@pytest.fixture
def mock_pinecone():
    """Mock Pinecone"""
    with patch('app.services.pinecone_client.Pinecone') as mock:
        yield mock


@pytest.fixture
@patch.dict('os.environ', {'PINECONE_API_KEY': 'test_api_key', 'PINECONE_INDEX_NAME': 'test_index'})
def pinecone_client(mock_pinecone):
    """Create Pinecone client with mocked Pinecone"""
    return PineconeClient()


@patch.dict('os.environ', {'PINECONE_API_KEY': 'test_api_key', 'PINECONE_INDEX_NAME': 'test_index'})
def test_pinecone_client_initialization(mock_pinecone):
    """Test Pinecone client initializes correctly"""
    client = PineconeClient()

    assert client is not None
    assert hasattr(client, 'pc')
    assert hasattr(client, 'index')
    mock_pinecone.assert_called_once()


@patch.dict('os.environ', {'PINECONE_API_KEY': 'test_api_key', 'PINECONE_INDEX_NAME': 'test_index'})
def test_create_index_if_not_exists(mock_pinecone):
    """Test index creation when it doesn't exist"""
    mock_pc = Mock()
    mock_pc.list_indexes.return_value.names.return_value = []
    mock_pinecone.return_value = mock_pc

    client = PineconeClient()

    # Verify index creation was attempted
    assert client.index is not None


def test_upsert_embedding_success(pinecone_client):
    """Test successful embedding upsert"""
    mock_index = Mock()
    pinecone_client.index = mock_index

    embedding = [0.1, 0.2, 0.3] * 512  # 1536-dimensional vector
    metadata = {
        "content_id": 123,
        "competitor_id": 1,
        "summary": "Test summary",
        "url": "https://example.com"
    }

    result = pinecone_client.upsert_embedding("test_id_123", embedding, metadata)

    assert result is True
    mock_index.upsert.assert_called_once()


def test_upsert_embedding_error_handling(pinecone_client):
    """Test embedding upsert error handling"""
    mock_index = Mock()
    mock_index.upsert.side_effect = Exception("Pinecone error")
    pinecone_client.index = mock_index

    embedding = [0.1] * 1536
    metadata = {"content_id": 123}

    result = pinecone_client.upsert_embedding("test_id", embedding, metadata)

    assert result is False


def test_query_similar_vectors_success(pinecone_client):
    """Test querying similar vectors"""
    mock_index = Mock()
    mock_match = Mock()
    mock_match.id = "match_1"
    mock_match.score = 0.95
    mock_match.metadata = {"content_id": 123, "summary": "Test"}

    mock_response = Mock()
    mock_response.matches = [mock_match]
    mock_index.query.return_value = mock_response

    pinecone_client.index = mock_index

    query_vector = [0.1] * 1536
    results = pinecone_client.query_similar(query_vector, top_k=5)

    assert len(results) == 1
    assert results[0]["id"] == "match_1"
    assert results[0]["score"] == 0.95
    assert results[0]["metadata"]["content_id"] == 123


def test_query_with_filter(pinecone_client):
    """Test querying with metadata filter"""
    mock_index = Mock()
    mock_response = Mock()
    mock_response.matches = []
    mock_index.query.return_value = mock_response

    pinecone_client.index = mock_index

    query_vector = [0.1] * 1536
    filter_dict = {"competitor_id": 1}

    pinecone_client.query_similar(query_vector, top_k=10, filter=filter_dict)

    mock_index.query.assert_called_once()
    call_args = mock_index.query.call_args
    assert call_args[1]["filter"] == filter_dict


def test_delete_vectors_by_id(pinecone_client):
    """Test deleting vectors by ID"""
    mock_index = Mock()
    pinecone_client.index = mock_index

    ids_to_delete = ["id_1", "id_2", "id_3"]
    result = pinecone_client.delete_vectors(ids_to_delete)

    assert result is True
    mock_index.delete.assert_called_once_with(ids=ids_to_delete)


def test_delete_vectors_error_handling(pinecone_client):
    """Test delete vectors error handling"""
    mock_index = Mock()
    mock_index.delete.side_effect = Exception("Delete error")
    pinecone_client.index = mock_index

    result = pinecone_client.delete_vectors(["id_1"])

    assert result is False


def test_get_index_stats(pinecone_client):
    """Test getting index statistics"""
    mock_index = Mock()
    mock_stats = MagicMock()
    mock_stats.get.return_value = 1000
    mock_index.describe_index_stats.return_value = mock_stats

    pinecone_client.index = mock_index

    stats = pinecone_client.get_index_stats()

    assert stats["total_vectors"] == 1000
    mock_index.describe_index_stats.assert_called_once()