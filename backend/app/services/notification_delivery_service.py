import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.models.alert import Notification
from app.models import User

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send email notification (placeholder for actual email service)

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body

    Returns:
        True if email sent successfully
    """
    # TODO: Implement actual email sending (SMTP, SendGrid, etc.)
    # For now, just log the email
    logger.info(f"Email sent to {to_email}: {subject}")
    return True


class NotificationDeliveryService:
    """Service for delivering notifications to users"""

    def __init__(self):
        self._websocket_manager = None

    def set_websocket_manager(self, manager):
        """Set the WebSocket connection manager for real-time notifications"""
        self._websocket_manager = manager

    async def send_websocket_notification(self, notification: Notification):
        """
        Send notification via WebSocket to connected clients

        Args:
            notification: Notification object to send
        """
        if self._websocket_manager is None:
            return

        notification_data = {
            "type": "notification",
            "id": notification.id,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
            "alert_id": notification.alert_id
        }
        await self._websocket_manager.send_notification(notification.user_id, notification_data)

    async def send_websocket_update(self, notification: Notification):
        """
        Send notification update via WebSocket to connected clients

        Args:
            notification: Updated notification object
        """
        if self._websocket_manager is None:
            return

        from datetime import datetime, timezone
        update_data = {
            "type": "notification_update",
            "id": notification.id,
            "is_read": notification.is_read,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self._websocket_manager.send_update(notification.user_id, update_data)

    def get_unread_notifications(
        self,
        user_id: int,
        db: Session
    ) -> List[Notification]:
        """
        Get all unread notifications for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of unread notifications
        """
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).all()

        return notifications

    def send_email_notification(
        self,
        user_email: str,
        subject: str,
        message: str
    ) -> bool:
        """
        Send email notification to user

        Args:
            user_email: User's email address
            subject: Email subject
            message: Email message

        Returns:
            True if email sent successfully
        """
        try:
            return send_email(
                to_email=user_email,
                subject=subject,
                body=message
            )
        except Exception as e:
            logger.error(f"Failed to send email to {user_email}: {str(e)}")
            return False

    def format_notification_email(
        self,
        notification: Notification
    ) -> str:
        """
        Format notification message for email

        Args:
            notification: Notification object

        Returns:
            Formatted email body
        """
        email_body = f"""
        Alert Notification

        {notification.message}

        ---
        This is an automated notification from the AI Competitive Intelligence Platform.
        """
        return email_body.strip()

    def deliver_notification(
        self,
        notification_id: int,
        db: Session
    ) -> bool:
        """
        Deliver a notification to user via email

        Args:
            notification_id: Notification ID
            db: Database session

        Returns:
            True if delivered successfully
        """
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            logger.warning(f"Notification {notification_id} not found")
            return False

        # Get user email
        user = db.query(User).filter(User.id == notification.user_id).first()
        if not user:
            logger.warning(f"User {notification.user_id} not found")
            return False

        # Format and send email
        email_body = self.format_notification_email(notification)
        success = self.send_email_notification(
            user_email=user.email,
            subject="Alert Notification",
            message=email_body
        )

        return success

    def batch_deliver_notifications(
        self,
        user_id: int,
        db: Session
    ) -> int:
        """
        Deliver all unread notifications for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Number of notifications delivered
        """
        unread_notifications = self.get_unread_notifications(user_id, db)
        delivered_count = 0

        # Get user email once
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0

        for notification in unread_notifications:
            email_body = self.format_notification_email(notification)
            success = self.send_email_notification(
                user_email=user.email,
                subject="Alert Notification",
                message=email_body
            )

            if success:
                delivered_count += 1

        return delivered_count

    def mark_as_delivered(
        self,
        notification_id: int,
        db: Session
    ) -> bool:
        """
        Mark notification as delivered (read)

        Args:
            notification_id: Notification ID
            db: Database session

        Returns:
            True if marked successfully
        """
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            return False

        notification.is_read = True
        db.commit()

        return True

    def get_notification_summary(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, int]:
        """
        Get notification summary for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with notification counts
        """
        all_notifications = db.query(Notification).filter(
            Notification.user_id == user_id
        ).all()

        unread_count = sum(1 for n in all_notifications if not n.is_read)
        read_count = sum(1 for n in all_notifications if n.is_read)

        return {
            "total": len(all_notifications),
            "unread": unread_count,
            "read": read_count
        }
