import pytest
from unittest.mock import Mock
from langchain_openai import ChatOpenAI

from app.core.llm_factory import LLMFactory
from app.core.prompt_loader import PromptLoader


@pytest.fixture(autouse=True)
def clear_cache():
    PromptLoader._cache.clear()
    yield
    PromptLoader._cache.clear()


def _model_name(llm) -> str:
    """Retrieve model name regardless of langchain-openai attribute naming."""
    return getattr(llm, "model_name", None) or getattr(llm, "model", None)


def _mock_settings():
    m = Mock()
    m.openai_api_key = "test-key"
    m.anthropic_api_key = ""
    m.google_api_key = ""
    m.ollama_base_url = "http://localhost:11434"
    return m


def test_default_provider_creates_chat_openai(monkeypatch):
    monkeypatch.setattr("app.core.config.settings", _mock_settings())

    llm = LLMFactory.create("entity_extraction")

    assert isinstance(llm, ChatOpenAI)
    assert _model_name(llm) == "gpt-3.5-turbo"


def test_strategic_detection_uses_gpt4(monkeypatch):
    monkeypatch.setattr("app.core.config.settings", _mock_settings())

    llm = LLMFactory.create("strategic_detection")

    assert isinstance(llm, ChatOpenAI)
    assert _model_name(llm) == "gpt-4"


def test_unknown_provider_falls_back_to_openai(monkeypatch):
    monkeypatch.setattr("app.core.config.settings", _mock_settings())
    monkeypatch.setenv("ENTITY_EXTRACTION_PROVIDER", "unknown_xyz")

    llm = LLMFactory.create("entity_extraction")

    assert isinstance(llm, ChatOpenAI)
