from typing import Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


from app.models.alert import Alert, Notification
from app.models.processed_insights import ProcessedInsights
from app.models.raw_content import RawContent


class AlertTriggerService:
    """Service for checking and triggering alerts based on conditions"""

    def check_sentiment_alert(
        self,
        alert: Alert,
        insight: ProcessedInsights,
        db: Session
    ) -> bool:
        """
        Check if sentiment change alert should be triggered

        Args:
            alert: Alert configuration
            insight: Processed insight to check
            db: Database session

        Returns:
            True if alert should be triggered
        """
        if alert.alert_type != "sentiment_change" or not alert.is_active:
            return False

        conditions = alert.conditions or {}
        threshold = conditions.get("threshold", "negative")
        
        triggered = insight.sentiment == threshold
        if triggered:
            logger.info(f"Sentiment alert '{alert.name}' (ID: {alert.id}) triggered for insight {insight.id}.")
        return triggered

    def check_new_content_alert(
        self,
        alert: Alert,
        raw_content: RawContent,
        db: Session
    ) -> bool:
        """
        Check if new content alert should be triggered

        Args:
            alert: Alert configuration
            raw_content: New raw content
            db: Database session

        Returns:
            True if alert should be triggered
        """
        if alert.alert_type != "new_content" or not alert.is_active:
            return False
        
        logger.info(f"New content alert '{alert.name}' (ID: {alert.id}) triggered for raw content {raw_content.id}.")
        return True

    def check_keyword_alert(
        self,
        alert: Alert,
        insight: ProcessedInsights,
        db: Session
    ) -> bool:
        """
        Check if keyword match alert should be triggered

        Args:
            alert: Alert configuration
            insight: Processed insight to check
            db: Database session

        Returns:
            True if alert should be triggered
        """
        if alert.alert_type != "keyword_match" or not alert.is_active:
            return False

        conditions = alert.conditions or {}
        keywords = conditions.get("keywords", [])

        if not keywords:
            logger.warning(f"Keyword alert '{alert.name}' (ID: {alert.id}) has no keywords configured.")
            return False

        content_to_check = f"{insight.summary} {insight.insights or ''}".lower()

        for keyword in keywords:
            if keyword.lower() in content_to_check:
                logger.info(f"Keyword alert '{alert.name}' (ID: {alert.id}) triggered for insight {insight.id} with keyword '{keyword}'.")
                return True

        return False

    def create_notification(
        self,
        alert_id: int,
        user_id: int,
        message: str,
        db: Session
    ) -> Optional[Notification]:
        """
        Create a notification for a triggered alert

        Args:
            alert_id: ID of the triggered alert
            user_id: User to notify
            message: Notification message
            db: Database session

        Returns:
            Created notification or None on error
        """
        logger.debug(f"Creating notification for alert_id: {alert_id}, user_id: {user_id}")
        try:
            notification = Notification(
                user_id=user_id,
                alert_id=alert_id,
                message=message,
                is_read=False
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            logger.info(f"Successfully created notification {notification.id} for alert {alert_id}.")
            return notification
        except Exception as e:
            logger.error(f"Failed to create notification for alert {alert_id}. Error: {e}", exc_info=True)
            db.rollback()
            return None

    def process_alerts_for_insight(
        self,
        insight_id: int,
        db: Session
    ) -> int:
        """
        Process all active alerts for a new insight

        Args:
            insight_id: ID of the new insight
            db: Database session

        Returns:
            Number of alerts triggered
        """
        logger.info(f"Processing alerts for insight_id: {insight_id}")
        
        insight = db.query(ProcessedInsights).filter(ProcessedInsights.id == insight_id).first()
        if not insight:
            logger.warning(f"Insight with id {insight_id} not found for alert processing.")
            return 0

        raw_content = db.query(RawContent).filter(RawContent.id == insight.raw_content_id).first()
        if not raw_content:
            logger.warning(f"RawContent not found for insight {insight_id}.")
            return 0
        
        competitor_id = raw_content.data_source.competitor_id
        
        # Query active alerts for the specific competitor or global alerts
        alerts = db.query(Alert).filter(
            Alert.is_active == True,
            (Alert.competitor_id == competitor_id) | (Alert.competitor_id == None)
        ).all()

        logger.info(f"Found {len(alerts)} active alerts for competitor {competitor_id} and global.")
        triggered_count = 0

        for alert in alerts:
            try:
                triggered = False
                message = ""

                if alert.alert_type == "sentiment_change":
                    if self.check_sentiment_alert(alert, insight, db):
                        triggered = True
                        message = f"Sentiment change to '{insight.sentiment}' detected for {raw_content.data_source.competitor.name}: {insight.summary}"

                elif alert.alert_type == "keyword_match":
                    if self.check_keyword_alert(alert, insight, db):
                        triggered = True
                        keywords = alert.conditions.get("keywords", [])
                        message = f"Keyword match on '{', '.join(keywords)}' for {raw_content.data_source.competitor.name}: {insight.summary}"
                
                elif alert.alert_type == "new_content":
                    # This alert type is better handled when new raw_content is created,
                    # but processing here for completeness.
                    if self.check_new_content_alert(alert, raw_content, db):
                        triggered = True
                        message = f"New content from {raw_content.data_source.competitor.name}: {insight.summary}"

                if triggered:
                    self.create_notification(
                        alert_id=alert.id,
                        user_id=alert.user_id,
                        message=message,
                        db=db
                    )
                    triggered_count += 1
            except Exception as e:
                logger.error(f"Error processing alert {alert.id} for insight {insight.id}. Error: {e}", exc_info=True)

        logger.info(f"Finished processing alerts for insight {insight.id}. Triggered {triggered_count} alerts.")
        return triggered_count
