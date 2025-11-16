from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

logger = logging.getLogger(__name__)


from app.core.database import SessionLocal
from app.models import User
from app.models.alert import Alert, Notification
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, NotificationResponse
from app.utils.dependencies import get_current_user
from app.api.websocket import notify_notification_update

router = APIRouter()


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert"""
    logger.info(f"User {current_user.id} creating new alert of type: {alert_data.alert_type}")
    try:
        alert = Alert(
            user_id=current_user.id,
            name=alert_data.name,
            competitor_id=alert_data.competitor_id,
            alert_type=alert_data.alert_type,
            conditions=alert_data.conditions,
            is_active=alert_data.is_active
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.info(f"Successfully created alert {alert.id} for user {current_user.id}.")
        return alert
    except Exception as e:
        logger.error(f"Error creating alert for user {current_user.id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all alerts for current user"""
    logger.debug(f"Fetching all alerts for user {current_user.id}.")
    try:
        alerts = db.query(Alert).filter(Alert.user_id == current_user.id).all()
        logger.info(f"Found {len(alerts)} alerts for user {current_user.id}.")
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific alert"""
    logger.debug(f"Fetching alert {alert_id} for user {current_user.id}.")
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        logger.warning(f"Alert {alert_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    logger.info(f"Successfully fetched alert {alert_id} for user {current_user.id}.")
    return alert


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an alert"""
    logger.info(f"User {current_user.id} updating alert {alert_id}.")
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        logger.warning(f"Alert {alert_id} not found for user {current_user.id} during update.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    try:
        update_data = alert_data.model_dump(exclude_unset=True)
        logger.debug(f"Update data for alert {alert_id}: {update_data}")
        for field, value in update_data.items():
            setattr(alert, field, value)

        db.commit()
        db.refresh(alert)
        logger.info(f"Successfully updated alert {alert_id} for user {current_user.id}.")
        return alert
    except Exception as e:
        logger.error(f"Error updating alert {alert_id} for user {current_user.id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an alert"""
    logger.info(f"User {current_user.id} deleting alert {alert_id}.")
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        logger.warning(f"Alert {alert_id} not found for user {current_user.id} during deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    try:
        db.delete(alert)
        db.commit()
        logger.info(f"Successfully deleted alert {alert_id} for user {current_user.id}.")
        return {"message": "Alert deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id} for user {current_user.id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notifications for current user"""
    logger.debug(f"Fetching all notifications for user {current_user.id}.")
    try:
        notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).order_by(Notification.created_at.desc()).all()
        logger.info(f"Found {len(notifications)} notifications for user {current_user.id}.")
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    logger.info(f"User {current_user.id} marking notification {notification_id} as read.")
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        logger.warning(f"Notification {notification_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    if notification.is_read:
        logger.debug(f"Notification {notification_id} is already marked as read.")
        return {"message": "Notification was already marked as read"}

    try:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        logger.info(f"Successfully marked notification {notification_id} as read for user {current_user.id}.")

        # Send WebSocket update
        await notify_notification_update(notification)
        
        return {"message": "Notification marked as read"}
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")