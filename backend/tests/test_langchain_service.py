import pytest
from unittest.mock import Mock, patch

from app.services.langchain_service import LangChainService


@pytest.fixture
def mock_settings():
    """Mock settings for LangChain"""
    with patch('app.services.langchain_service.settings') as mock:
        mock.openai_api_key = "test-api-key"
        mock.openai_model = "gpt-3.5-turbo"
        mock.openai_temperature = 0.3
        mock.openai_max_tokens = 500
        yield mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI for LangChain"""
    with patch('app.services.langchain_service.ChatOpenAI') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def langchain_service(mock_settings, mock_openai):
    """Create LangChain service with mocked OpenAI and settings"""
    return LangChainService()


def test_langchain_service_initialization(mock_settings, mock_openai):
    """Test that the LangChainService can be initialized"""
    service = LangChainService()
    assert service is not None
    assert hasattr(service, 'llm')


def test_analyze_competitive_intelligence(langchain_service, mock_openai):
    """Test competitive intelligence analysis chain"""
    content = "Company X launches new AI product with advanced features targeting enterprise market"

    mock_openai.invoke.return_value = Mock(
        content="Strategic analysis: Company X is expanding into enterprise AI market with competitive product offering"
    )

    result = langchain_service.analyze_competitive_intelligence(content)

    assert result is not None
    assert "strategic" in result.lower() or "analysis" in result.lower()


def test_generate_summary_with_template(langchain_service, mock_openai):
    """Test summary generation with custom prompt template"""
    content = "Tech company announces Q4 earnings beat with 25% revenue growth"

    mock_openai.invoke.return_value = Mock(
        content="Q4 earnings exceeded expectations with strong 25% revenue growth"
    )

    result = langchain_service.generate_summary(content)

    assert result is not None
    assert len(result) > 0


def test_extract_strategic_insights(langchain_service, mock_openai):
    """Test strategic insights extraction with chain"""
    content = "Competitor launches new pricing model reducing costs by 30% for customers"

    mock_openai.invoke.return_value = Mock(
        content="Pricing strategy: Aggressive 30% cost reduction indicates market share acquisition focus"
    )

    result = langchain_service.extract_strategic_insights(content)

    assert result is not None
    assert isinstance(result, str)


def test_analyze_sentiment_with_reasoning(langchain_service, mock_openai):
    """Test sentiment analysis with reasoning"""
    content = "Product launch delayed due to quality issues, disappointing investors"

    mock_openai.invoke.return_value = Mock(
        content="negative|Delay and quality concerns create negative market sentiment"
    )

    result = langchain_service.analyze_sentiment_with_reasoning(content)

    assert result is not None
    assert "sentiment" in result
    assert "reasoning" in result


def test_chain_orchestration(langchain_service, mock_openai):
    """Test orchestrated chain for complete analysis"""
    content = "Major competitor announces partnership with industry leader"

    # Mock sequential responses for chain
    mock_openai.invoke.side_effect = [
        Mock(content="Partnership strengthens market position"),
        Mock(content="Strategic alliance indicates expansion strategy"),
        Mock(content="positive")
    ]

    result = langchain_service.full_content_analysis(content)

    assert result is not None
    assert "summary" in result
    assert "insights" in result
    assert "sentiment" in result


def test_custom_prompt_template_formatting(langchain_service):
    """Test custom prompt template creates properly formatted prompts"""
    content = "Test content for analysis"

    prompt = langchain_service._create_competitive_analysis_prompt(content)

    assert prompt is not None
    assert "competitive intelligence" in prompt.lower()
    assert content in prompt


def test_error_handling_in_chain(mock_settings, mock_openai):
    """Test error handling when LLM fails"""
    mock_openai.invoke.side_effect = Exception("API Error")

    service = LangChainService()
    result = service.analyze_competitive_intelligence("test content")

    assert result is None or result == ""


def test_retry_logic_on_failure(langchain_service, mock_openai):
    """Test retry logic when chain fails"""
    # First call fails, second succeeds
    mock_openai.invoke.side_effect = [
        Exception("Temporary error"),
        Mock(content="Success on retry")
    ]

    result = langchain_service.analyze_competitive_intelligence("test content")

    # Should succeed on retry
    assert result == "Success on retry"