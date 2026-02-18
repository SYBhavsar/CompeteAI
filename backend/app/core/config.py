from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/competitive_intel"
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    secret_key: str = "your-secret-key-change-in-production"

    # AI Model Configuration (global defaults)
    openai_api_key: str = ""  # Required in production
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 500

    # API Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    retry_backoff: float = 2.0  # exponential backoff multiplier

    # Pinecone Configuration
    pinecone_region: str = "us-east-1"
    pinecone_cloud: str = "aws"

    # Additional AI provider API keys
    anthropic_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # Per-service provider overrides (env vars read directly by AIConfig)
    # Format: {SERVICE}_PROVIDER and {SERVICE}_MODEL
    # e.g. ENTITY_EXTRACTION_PROVIDER=anthropic
    #      ENTITY_EXTRACTION_MODEL=claude-3-haiku-20240307

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()