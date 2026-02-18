"""
AI Configuration per Service

Purpose: Reads per-service AI provider + model config from environment variables,
         falling back to prompt file frontmatter defaults.
"""
import logging
import os
from dataclasses import dataclass

from app.core.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

# Maps service name → environment variable prefix
SERVICE_ENV_PREFIXES: dict[str, str] = {
    "summarization": "SUMMARIZATION",
    "insight_extraction": "INSIGHT_EXTRACTION",
    "sentiment_analysis": "SENTIMENT_ANALYSIS",
    "entity_extraction": "ENTITY_EXTRACTION",
    "strategic_detection": "STRATEGIC_DETECTION",
    "historical_analysis": "HISTORICAL_ANALYSIS",
    "competitive_analysis": "COMPETITIVE_ANALYSIS",
}


@dataclass
class ServiceAIConfig:
    provider: str   # openai | anthropic | google | ollama
    model: str
    temperature: float
    max_tokens: int


class AIConfig:
    @staticmethod
    def for_service(service_name: str) -> ServiceAIConfig:
        """
        Return AI config for the given service.

        Reads env vars: {PREFIX}_PROVIDER, {PREFIX}_MODEL,
                        {PREFIX}_TEMPERATURE, {PREFIX}_MAX_TOKENS.
        Falls back to prompt file frontmatter defaults.

        Args:
            service_name: Registered service name (e.g. 'entity_extraction')
        """
        prefix = SERVICE_ENV_PREFIXES.get(service_name, service_name.upper())

        try:
            defaults = PromptLoader.get_default_config(service_name)
            default_provider: str = defaults.get("default_provider", "openai")
            default_model: str = defaults.get("default_model", "gpt-3.5-turbo")
            default_temperature: float = float(defaults.get("temperature", 0.3))
            default_max_tokens: int = int(defaults.get("max_tokens", 500))
        except FileNotFoundError:
            logger.warning(
                "No prompt file found for service '%s', using hardcoded defaults",
                service_name,
            )
            default_provider = "openai"
            default_model = "gpt-3.5-turbo"
            default_temperature = 0.3
            default_max_tokens = 500

        provider = os.environ.get(f"{prefix}_PROVIDER", default_provider)
        model = os.environ.get(f"{prefix}_MODEL", default_model)
        temperature = float(os.environ.get(f"{prefix}_TEMPERATURE", str(default_temperature)))
        max_tokens = int(os.environ.get(f"{prefix}_MAX_TOKENS", str(default_max_tokens)))

        config = ServiceAIConfig(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.debug(
            "AI config for '%s': provider=%s, model=%s",
            service_name,
            provider,
            model,
        )
        return config
