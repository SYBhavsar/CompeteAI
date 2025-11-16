"""
WebSocket endpoint for real-time notifications
Follows SOLID principles and clean code practices
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Set
import asyncio
import json
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models import User
from app.models.alert import Notification
from app.utils.jwt import decode_token
from app.services.notification_delivery_service import NotificationDeliveryService


router = APIRouter()

# Global notification delivery service instance
notification_delivery_service = NotificationDeliveryService()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications
    Single Responsibility: Handle WebSocket connection lifecycle
    """

    def __init__(self):
        # Map user_id to set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_notification(self, user_id: int, notification_data: dict):
        """Send notification to all connections for a specific user"""
        if user_id in self.active_connections:
            # Create a copy to avoid modification during iteration
            connections = self.active_connections[user_id].copy()
            for connection in connections:
                try:
                    await connection.send_json(notification_data)
                except Exception:
                    # Remove dead connections
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
    Returns User object if valid, raises HTTPException otherwise
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )

    try:
        # Decode JWT token
        payload = decode_token(token)
        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        # Get user from database
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.websocket("/ws/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notifications

    Query Parameters:
        token: JWT authentication token

    Message Types Sent:
        - notification: New notification created
        - notification_update: Notification status changed
        - ping: Heartbeat to keep connection alive
    """
    try:
        # Authenticate user
        user = await authenticate_websocket(token)
        user_id = user.id

        # Connect WebSocket
        await manager.connect(websocket, user_id)

        # Start heartbeat task
        async def send_heartbeat():
            """Send periodic heartbeat to keep connection alive"""
            while True:
                try:
                    await asyncio.sleep(30)  # Heartbeat every 30 seconds
                    await websocket.send_json({"type": "ping", "timestamp": datetime.now(timezone.utc).isoformat()})
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(send_heartbeat())

        try:
            # Listen for messages (keep connection alive)
            while True:
                # Wait for any message from client (could be pong, etc.)
                data = await websocket.receive_text()

                # Optional: Handle client messages here
                # For now, we just keep the connection alive

        except WebSocketDisconnect:
            # Client disconnected
            pass
        finally:
            # Clean up
            heartbeat_task.cancel()
            manager.disconnect(websocket, user_id)

    except HTTPException as e:
        # Authentication failed
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
    except Exception as e:
        # Unexpected error
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))


# Export functions for use in other modules
async def notify_user(notification: Notification):
    """Send notification to user via WebSocket"""
    await notification_delivery_service.send_websocket_notification(notification)


async def notify_notification_update(notification: Notification):
    """Send notification update to user via WebSocket"""
    await notification_delivery_service.send_websocket_update(notification)


async def broadcast_scraping_progress(user_id: int, progress_data: dict):
    """
    Broadcast scraping progress to user via WebSocket

    Args:
        user_id: User ID to send progress to
        progress_data: Progress data containing task_id, status, progress, etc.
    """
    await manager.send_notification(user_id, {
        "type": "scraping_progress",
        **progress_data
    })


async def broadcast_data_update(user_id: int, update_data: dict):
    """
    Broadcast data update to user via WebSocket

    Args:
        user_id: User ID to send update to
        update_data: Update data (new content, insights, etc.)
    """
    await manager.send_notification(user_id, {
        "type": "data_update",
        **update_data
    })
