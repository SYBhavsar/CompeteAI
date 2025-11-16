from celery import Task
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


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
    logger.info(f"Starting task 'process_insight_alerts' for insight_id: {insight_id}")

    try:
        triggered_count = alert_service.process_alerts_for_insight(
            insight_id=insight_id,
            db=db
        )
        logger.info(f"Task 'process_insight_alerts' completed for insight {insight_id}. Triggered {triggered_count} alerts.")
        return {
            "insight_id": insight_id,
            "alerts_triggered": triggered_count
        }
    except Exception as e:
        logger.error(f"Error in task 'process_insight_alerts' for insight {insight_id}: {e}", exc_info=True)
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
    logger.info(f"Starting task 'deliver_user_notifications' for user_id: {user_id}")

    try:
        delivered_count = notification_service.batch_deliver_notifications(
            user_id=user_id,
            db=db
        )
        logger.info(f"Delivered {delivered_count} notifications to user {user_id}.")

        # Mark notifications as delivered
        unread = notification_service.get_unread_notifications(user_id, db)
        for notification in unread:
            notification_service.mark_as_delivered(notification.id, db)
        logger.info(f"Marked {len(unread)} notifications as delivered for user {user_id}.")

        return {
            "user_id": user_id,
            "delivered": delivered_count
        }
    except Exception as e:
        logger.error(f"Error in task 'deliver_user_notifications' for user {user_id}: {e}", exc_info=True)
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
    logger.info(f"Starting task 'deliver_single_notification' for notification_id: {notification_id}")

    try:
        success = notification_service.deliver_notification(
            notification_id=notification_id,
            db=db
        )

        if success:
            notification_service.mark_as_delivered(notification_id, db)
            logger.info(f"Successfully delivered and marked notification {notification_id} as delivered.")
        else:
            logger.warning(f"Failed to deliver notification {notification_id}.")

        return {
            "notification_id": notification_id,
            "delivered": success
        }
    except Exception as e:
        logger.error(f"Error in task 'deliver_single_notification' for notification {notification_id}: {e}", exc_info=True)
        self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(base=DatabaseTask, bind=True)
def check_all_active_alerts(self):
    """
    Periodic task to check all active alerts and process new insights
    """
    db = self.db
    from app.models.processed_insights import ProcessedInsights
    from datetime import datetime, timedelta, timezone
    logger.info("Starting periodic task 'check_all_active_alerts'.")

    try:
        # Get insights created in the last 10 minutes that haven't been checked
        # This logic might need refinement to avoid reprocessing. A 'checked' flag could be useful.
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        recent_insights = db.query(ProcessedInsights).filter(
            ProcessedInsights.created_at >= recent_time
        ).all()
        
        logger.info(f"Found {len(recent_insights)} recent insights to process for alerts.")
        processed_count = 0
        for insight in recent_insights:
            # Get competitor_id from raw_content -> data_source
            if insight.raw_content and insight.raw_content.data_source:
                competitor_id = insight.raw_content.data_source.competitor_id
                logger.debug(f"Queueing alert processing for insight {insight.id}, competitor {competitor_id}.")
                process_insight_alerts.delay(insight.id, competitor_id)
                processed_count += 1
        
        logger.info(f"Periodic task 'check_all_active_alerts' finished. Queued {processed_count} insights for processing.")
        return {
            "insights_processed": processed_count
        }
    except Exception as e:
        logger.error(f"Error in periodic task 'check_all_active_alerts': {e}", exc_info=True)
        self.retry(exc=e, countdown=300, max_retries=3)
