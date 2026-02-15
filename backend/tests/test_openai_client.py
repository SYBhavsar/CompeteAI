import pytest
from unittest.mock import Mock, patch
import os

from app.services.openai_client import OpenAIClient


@patch('app.services.openai_client.settings')
@patch('app.services.openai_client.OpenAI')
def test_openai_client_initialization(mock_openai, mock_settings):
    """Test OpenAI client initializes correctly"""
    mock_settings.openai_api_key = "test-api-key"
    mock_settings.openai_model = "gpt-3.5-turbo"
    mock_settings.openai_temperature = 0.3
    mock_settings.openai_max_tokens = 500

    client = OpenAIClient()
    assert client is not None
    assert hasattr(client, 'client')


@patch('app.services.openai_client.settings')
@patch('app.services.openai_client.OpenAI')
def test_summarize_content_success(mock_openai, mock_settings):
    """Test successful content summarization"""
    mock_settings.openai_api_key = "test-api-key"
    mock_settings.openai_model = "gpt-3.5-turbo"
    mock_settings.openai_temperature = 0.3
    mock_settings.openai_max_tokens = 500

    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test summary of the content"

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = OpenAIClient()
    result = client.summarize_content("This is test content to summarize")

    assert result == "Test summary of the content"
    mock_client.chat.completions.create.assert_called_once()


@patch('app.services.openai_client.settings')
@patch('app.services.openai_client.OpenAI')
def test_extract_insights_success(mock_openai, mock_settings):
    """Test successful insight extraction"""
    mock_settings.openai_api_key = "test-api-key"
    mock_settings.openai_model = "gpt-3.5-turbo"
    mock_settings.openai_temperature = 0.3
    mock_settings.openai_max_tokens = 500

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Key business insights extracted"

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = OpenAIClient()
    result = client.extract_insights("Business content for insight extraction")

    assert result == "Key business insights extracted"


@patch('app.services.openai_client.settings')
@patch('app.services.openai_client.OpenAI')
def test_analyze_sentiment_success(mock_openai, mock_settings):
    """Test successful sentiment analysis"""
    mock_settings.openai_api_key = "test-api-key"
    mock_settings.openai_model = "gpt-3.5-turbo"
    mock_settings.openai_temperature = 0.3
    mock_settings.openai_max_tokens = 500

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "positive"

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    client = OpenAIClient()
    result = client.analyze_sentiment("This is great news for the company")

    assert result == "positive"


@patch('app.services.openai_client.settings')
@patch('app.services.openai_client.OpenAI')
def test_openai_api_error_handling(mock_openai, mock_settings):
    """Test OpenAI API error handling"""
    mock_settings.openai_api_key = "test-api-key"
    mock_settings.openai_model = "gpt-3.5-turbo"
    mock_settings.openai_temperature = 0.3
    mock_settings.openai_max_tokens = 500

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    client = OpenAIClient()
    result = client.summarize_content("Test content")

    assert result is None