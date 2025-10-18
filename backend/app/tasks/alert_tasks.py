from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.alert_trigger_service import AlertTriggerService
from app.services.notification_delivery_service import NotificationDeliveryService


class DatabaseTask(Task):
    """Base task with database session management"""
    _db = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def process_insight_alerts(self, insight_id: int, competitor_id: int = None):
    """
    Process alerts for a newly created insight

    Args:
        insight_id: ID of the processed insight
        competitor_id: Optional competitor ID
    """
    db = self.db
    alert_service = AlertTriggerService()

    try:
        triggered_count = alert_service.process_alerts_for_insight(
            insight_id=insight_id,
            competitor_id=competitor_id,
            db=db
        )

        return {
            "insight_id": insight_id,
            "alerts_triggered": triggered_count
        }
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(base=DatabaseTask, bind=True)
def deliver_user_notifications(self, user_id: int):
    """
    Deliver all unread notifications for a user

    Args:
        user_id: User ID
    """
    db = self.db
    notification_service = NotificationDeliveryService()

    try:
        delivered_count = notification_service.batch_deliver_notifications(
            user_id=user_id,
            db=db
        )

        # Mark notifications as delivered
        unread = notification_service.get_unread_notifications(user_id, db)
        for notification in unread:
            notification_service.mark_as_delivered(notification.id, db)

        return {
            "user_id": user_id,
            "delivered": delivered_count
        }
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(base=DatabaseTask, bind=True)
def deliver_single_notification(self, notification_id: int):
    """
    Deliver a single notification

    Args:
        notification_id: Notification ID
    """
    db = self.db
    notification_service = NotificationDeliveryService()

    try:
        success = notification_service.deliver_notification(
            notification_id=notification_id,
            db=db
        )

        if success:
            notification_service.mark_as_delivered(notification_id, db)

        return {
            "notification_id": notification_id,
            "delivered": success
        }
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(base=DatabaseTask, bind=True)
def check_all_active_alerts(self):
    """
    Periodic task to check all active alerts and process new insights
    """
    db = self.db
    from app.models.processed_insights import ProcessedInsights
    from datetime import datetime, timedelta

    try:
        # Get insights created in the last 10 minutes that haven't been checked
        recent_time = datetime.utcnow() - timedelta(minutes=10)
        recent_insights = db.query(ProcessedInsights).filter(
            ProcessedInsights.created_at >= recent_time
        ).all()

        processed_count = 0
        for insight in recent_insights:
            # Get competitor_id from raw_content -> data_source
            if insight.raw_content and insight.raw_content.data_source:
                competitor_id = insight.raw_content.data_source.competitor_id
                process_insight_alerts.delay(insight.id, competitor_id)
                processed_count += 1

        return {
            "insights_processed": processed_count
        }
    except Exception as e:
        self.retry(exc=e, countdown=300, max_retries=3)
