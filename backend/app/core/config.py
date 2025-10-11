from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/competitive_intel"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"


settings = Settings()