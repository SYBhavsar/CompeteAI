from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "competitive_intel",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Import tasks to register them
from app.tasks import scraping_tasks, scheduling_tasks, alert_tasks

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.scraping_tasks.*": {"queue": "scraping"},
        "app.tasks.scheduling_tasks.*": {"queue": "scheduling"},
        "app.tasks.alert_tasks.*": {"queue": "alerts"}
    },
    beat_schedule={
        "check-due-schedules": {
            "task": "app.tasks.scheduling_tasks.check_and_execute_due_schedules",
            "schedule": 300.0,  # Run every 5 minutes
        },
        "check-active-alerts": {
            "task": "app.tasks.alert_tasks.check_all_active_alerts",
            "schedule": 600.0,  # Run every 10 minutes
        },
    }
)