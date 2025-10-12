import pytest
import redis
from app.core.config import settings
from app.core.celery_app import celery_app


def test_redis_connection():
    """Test Redis connection is working"""
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        assert True
    except redis.ConnectionError:
        pytest.fail("Redis connection failed")


def test_celery_app_configuration():
    """Test Celery app is properly configured"""
    assert celery_app.conf.broker_url == settings.redis_url
    assert celery_app.conf.result_backend == settings.redis_url
    assert celery_app.conf.task_serializer == "json"


def test_celery_task_registration():
    """Test that our scraping task is registered"""
    registered_tasks = list(celery_app.tasks.keys())
    # Check if scrape_data_source task is registered (with any namespace)
    scraping_tasks = [task for task in registered_tasks if "scrape_data_source" in task]
    assert len(scraping_tasks) > 0, f"scrape_data_source task not found in: {registered_tasks}"


def test_celery_task_signature():
    """Test creating task signature without executing"""
    from app.tasks.scraping_tasks import scrape_data_source
    
    # Create task signature (doesn't execute)
    signature = scrape_data_source.s(123)
    
    assert signature.task == "app.tasks.scraping_tasks.scrape_data_source"
    assert signature.args == (123,)