import pytest
from app.core.ai_config import AIConfig
from app.core.prompt_loader import PromptLoader


@pytest.fixture(autouse=True)
def clear_cache():
    PromptLoader._cache.clear()
    yield
    PromptLoader._cache.clear()


def test_default_config_reads_from_frontmatter():
    entity = AIConfig.for_service("entity_extraction")
    assert entity.provider == "openai"
    assert entity.model == "gpt-3.5-turbo"
    assert entity.temperature == 0.0

    strategic = AIConfig.for_service("strategic_detection")
    assert strategic.model == "gpt-4"
    assert strategic.temperature == 0.2


def test_env_var_overrides_frontmatter(monkeypatch):
    monkeypatch.setenv("ENTITY_EXTRACTION_PROVIDER", "anthropic")
    monkeypatch.setenv("ENTITY_EXTRACTION_MODEL", "claude-3-haiku-20240307")

    config = AIConfig.for_service("entity_extraction")

    assert config.provider == "anthropic"
    assert config.model == "claude-3-haiku-20240307"
