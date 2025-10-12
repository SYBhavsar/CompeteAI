from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "competitive_intel",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.scraping_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.scraping_tasks.*": {"queue": "scraping"}
    }
)