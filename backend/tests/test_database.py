import pytest
from sqlalchemy import text


def test_database_connection():
    """Test database connection is working"""
    from app.core.database import engine
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1


def test_database_url_configuration():
    """Test database URL is properly configured"""
    from app.core.config import settings
    
    assert settings.database_url is not None
    assert "postgresql" in settings.database_url
    assert "competitive_intel" in settings.database_url