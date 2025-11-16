from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/competitive_intel"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "your-secret-key-change-in-production"

    # AI Model Configuration
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

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()