import pytest
from app.core.prompt_loader import PromptLoader


@pytest.fixture(autouse=True)
def clear_cache():
    PromptLoader._cache.clear()
    yield
    PromptLoader._cache.clear()


@pytest.mark.parametrize("name,expected_provider,expected_model", [
    ("summarization",       "openai", "gpt-3.5-turbo"),
    ("insight_extraction",  "openai", "gpt-3.5-turbo"),
    ("sentiment_analysis",  "openai", "gpt-3.5-turbo"),
    ("entity_extraction",   "openai", "gpt-3.5-turbo"),
    ("strategic_detection", "openai", "gpt-4"),
    ("historical_analysis", "openai", "gpt-3.5-turbo"),
    ("competitive_analysis","openai", "gpt-3.5-turbo"),
])
def test_all_prompts_load_with_correct_config(name, expected_provider, expected_model):
    config = PromptLoader.load(name)

    assert config.default_provider == expected_provider
    assert config.default_model == expected_model
    assert config.system_prompt, f"{name}: system_prompt must not be empty"
    assert "{" in config.user_prompt, f"{name}: user_prompt must contain a placeholder"


def test_missing_prompt_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        PromptLoader.load("nonexistent_prompt")


def test_repeated_load_returns_cached_instance():
    first = PromptLoader.load("summarization")
    second = PromptLoader.load("summarization")
    assert first is second
