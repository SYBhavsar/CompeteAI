"""
LLM Factory

Purpose: Creates LangChain chat model instances based on provider configuration.
Supports: openai, anthropic, google, ollama
"""
import logging

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.ai_config import AIConfig, ServiceAIConfig

logger = logging.getLogger(__name__)


class LLMFactory:
    @staticmethod
    def create(service_name: str) -> BaseChatModel:
        """
        Create a LangChain chat model for the given service.

        Reads provider + model from env vars (via AIConfig), falls back to
        prompt file frontmatter defaults.

        Args:
            service_name: Registered service name (e.g. 'entity_extraction')

        Returns:
            A LangChain BaseChatModel instance
        """
        config = AIConfig.for_service(service_name)
        return LLMFactory.create_from_config(config)

    @staticmethod
    def create_from_config(config: ServiceAIConfig) -> BaseChatModel:
        """
        Create a LangChain chat model from an explicit ServiceAIConfig.

        Args:
            config: Service AI configuration

        Returns:
            A LangChain BaseChatModel instance
        """
        provider = config.provider.lower()

        if provider == "openai":
            return LLMFactory._create_openai(config)
        if provider == "anthropic":
            return LLMFactory._create_anthropic(config)
        if provider == "google":
            return LLMFactory._create_google(config)
        if provider == "ollama":
            return LLMFactory._create_ollama(config)

        logger.warning("Unknown provider '%s', falling back to OpenAI", provider)
        return LLMFactory._create_openai(config)

    # ------------------------------------------------------------------
    # Provider-specific constructors
    # ------------------------------------------------------------------

    @staticmethod
    def _create_openai(config: ServiceAIConfig) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        from app.core.config import settings

        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            openai_api_key=settings.openai_api_key,
        )

    @staticmethod
    def _create_anthropic(config: ServiceAIConfig) -> BaseChatModel:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise ImportError(
                "langchain-anthropic is required for the Anthropic provider. "
                "Install with: pip install langchain-anthropic"
            ) from exc

        from app.core.config import settings

        return ChatAnthropic(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            anthropic_api_key=settings.anthropic_api_key,
        )

    @staticmethod
    def _create_google(config: ServiceAIConfig) -> BaseChatModel:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise ImportError(
                "langchain-google-genai is required for the Google provider. "
                "Install with: pip install langchain-google-genai"
            ) from exc

        from app.core.config import settings

        return ChatGoogleGenerativeAI(
            model=config.model,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
            google_api_key=settings.google_api_key,
        )

    @staticmethod
    def _create_ollama(config: ServiceAIConfig) -> BaseChatModel:
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            try:
                from langchain_community.chat_models import ChatOllama  # type: ignore[no-redef]
            except ImportError as exc:
                raise ImportError(
                    "langchain-ollama is required for the Ollama provider. "
                    "Install with: pip install langchain-ollama"
                ) from exc

        from app.core.config import settings

        return ChatOllama(
            model=config.model,
            temperature=config.temperature,
            num_predict=config.max_tokens,
            base_url=settings.ollama_base_url,
        )
