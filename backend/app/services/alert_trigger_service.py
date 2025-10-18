from typing import Optional
from sqlalchemy.orm import Session

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
        if alert.alert_type != "sentiment_change":
            return False

        if not alert.is_active:
            return False

        conditions = alert.conditions or {}
        threshold = conditions.get("threshold", "negative")

        return insight.sentiment == threshold

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
        if alert.alert_type != "new_content":
            return False

        if not alert.is_active:
            return False

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
        if alert.alert_type != "keyword_match":
            return False

        if not alert.is_active:
            return False

        conditions = alert.conditions or {}
        keywords = conditions.get("keywords", [])

        if not keywords:
            return False

        # Check if any keyword is in summary or insights
        content_to_check = f"{insight.summary} {insight.insights or ''}".lower()

        for keyword in keywords:
            if keyword.lower() in content_to_check:
                return True

        return False

    def create_notification(
        self,
        alert_id: int,
        user_id: int,
        message: str,
        db: Session
    ) -> Notification:
        """
        Create a notification for triggered alert

        Args:
            alert_id: ID of the triggered alert
            user_id: User to notify
            message: Notification message
            db: Database session

        Returns:
            Created notification
        """
        notification = Notification(
            user_id=user_id,
            alert_id=alert_id,
            message=message,
            is_read=False
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    def process_alerts_for_insight(
        self,
        insight_id: int,
        competitor_id: Optional[int],
        db: Session
    ) -> int:
        """
        Process all active alerts for a new insight

        Args:
            insight_id: ID of the new insight
            competitor_id: Competitor ID (optional)
            db: Database session

        Returns:
            Number of alerts triggered
        """
        insight = db.query(ProcessedInsights).filter(
            ProcessedInsights.id == insight_id
        ).first()

        if not insight:
            return 0

        # Get raw content to access competitor info
        raw_content = db.query(RawContent).filter(
            RawContent.id == insight.raw_content_id
        ).first()

        if not raw_content:
            return 0

        # Query active alerts
        query = db.query(Alert).filter(Alert.is_active == True)

        if competitor_id:
            query = query.filter(
                (Alert.competitor_id == competitor_id) |
                (Alert.competitor_id == None)
            )

        alerts = query.all()
        triggered_count = 0

        for alert in alerts:
            triggered = False
            message = ""

            if alert.alert_type == "sentiment_change":
                triggered = self.check_sentiment_alert(alert, insight, db)
                if triggered:
                    message = f"Sentiment change detected: {insight.sentiment} - {insight.summary}"

            elif alert.alert_type == "keyword_match":
                triggered = self.check_keyword_alert(alert, insight, db)
                if triggered:
                    keywords = alert.conditions.get("keywords", [])
                    message = f"Keyword match found ({', '.join(keywords)}): {insight.summary}"

            elif alert.alert_type == "new_content":
                triggered = self.check_new_content_alert(alert, raw_content, db)
                if triggered:
                    message = f"New content detected: {insight.summary}"

            if triggered:
                self.create_notification(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    message=message,
                    db=db
                )
                triggered_count += 1

        return triggered_count
