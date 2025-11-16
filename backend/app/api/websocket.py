import logging
import asyncio
from typing import Dict, Set
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import User
from app.models.alert import Notification
from app.services.notification_delivery_service import NotificationDeliveryService
from app.utils.jwt import decode_token

logger = logging.getLogger(__name__)

router = APIRouter()

# Global notification delivery service instance
notification_delivery_service = NotificationDeliveryService()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications
    """

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections for user: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}.")
        else:
            logger.warning(f"Attempted to disconnect a non-existent user: {user_id}")

    async def send_notification(self, user_id: int, notification_data: dict):
        """Send notification to all connections for a specific user"""
        if user_id in self.active_connections:
            connections = self.active_connections[user_id].copy()
            logger.debug(f"Sending notification to {len(connections)} connections for user {user_id}.")
            for connection in connections:
                try:
                    await connection.send_json(notification_data)
                except WebSocketDisconnect:
                    logger.warning(f"WebSocket disconnected during send for user {user_id}.")
                    self.disconnect(connection, user_id)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket for user {user_id}: {e}", exc_info=True)
                    self.disconnect(connection, user_id)

    async def send_update(self, user_id: int, update_data: dict):
        """Send update to all connections for a specific user"""
        await self.send_notification(user_id, update_data)

    async def broadcast_to_user(self, user_id: int, message: dict):
        """Broadcast message to all connections for a user"""
        await self.send_notification(user_id, message)


# Global connection manager instance
manager = ConnectionManager()

# Register manager with notification delivery service
notification_delivery_service.set_websocket_manager(manager)


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def authenticate_websocket(token: str) -> User:
    """
    Authenticate WebSocket connection using JWT token
    """
    if not token:
        logger.warning("WebSocket connection attempt with no token.")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")

    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if not email:
            logger.warning("Invalid token: 'sub' claim missing.")
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token claims")

        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()

        if not user:
            logger.warning(f"User not found for email: {email}")
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        
        logger.info(f"Successfully authenticated WebSocket for user {user.id} ({user.email}).")
        return user

    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}", exc_info=True)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=f"Authentication failed: {e}")


@router.websocket("/ws/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notifications
    """
    user = None
    try:
        user = await authenticate_websocket(token)
        await manager.connect(websocket, user.id)

        async def send_heartbeat():
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send_json({"type": "ping", "timestamp": datetime.now(timezone.utc).isoformat()})
                except (WebSocketDisconnect, asyncio.CancelledError):
                    break
        
        heartbeat_task = asyncio.create_task(send_heartbeat())

        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(f"Received message from user {user.id}: {data}")
                # Handle client messages if needed, e.g., pong responses

        except WebSocketDisconnect:
            logger.info(f"Client for user {user.id} disconnected gracefully.")
        finally:
            heartbeat_task.cancel()
            if user:
                manager.disconnect(websocket, user.id)

    except WebSocketException as e:
        logger.error(f"WebSocket connection closed due to policy violation: {e.reason}")
        await websocket.close(code=e.code, reason=e.reason)
    except Exception as e:
        reason = f"An unexpected error occurred: {e}"
        logger.critical(reason, exc_info=True)
        if user:
            manager.disconnect(websocket, user.id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=reason)


# Custom exception for WebSocket handling
class WebSocketException(Exception):
    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason


# Export functions for use in other modules
async def notify_user(notification: Notification):
    """Send notification to user via WebSocket"""
    logger.debug(f"Queueing WebSocket notification {notification.id} for user {notification.user_id}.")
    await notification_delivery_service.send_websocket_notification(notification)


async def notify_notification_update(notification: Notification):
    """Send notification update to user via WebSocket"""
    logger.debug(f"Queueing WebSocket update for notification {notification.id} for user {notification.user_id}.")
    await notification_delivery_service.send_websocket_update(notification)


async def broadcast_scraping_progress(user_id: int, progress_data: dict):
    """
    Broadcast scraping progress to user via WebSocket
    """
    logger.debug(f"Broadcasting scraping progress to user {user_id}.")
    await manager.broadcast_to_user(user_id, {
        "type": "scraping_progress",
        **progress_data
    })


async def broadcast_data_update(user_id: int, update_data: dict):
    """
    Broadcast data update to user via WebSocket
    """
    logger.debug(f"Broadcasting data update to user {user_id}.")
    await manager.broadcast_to_user(user_id, {
        "type": "data_update",
        **update_data
    })
