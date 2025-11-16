from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class AlertCreate(BaseModel):
    """Schema for creating an alert"""
    competitor_id: Optional[int] = None
    alert_type: str
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool = True


class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    alert_type: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: int
    user_id: int
    competitor_id: Optional[int]
    alert_type: str
    conditions: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: int
    user_id: int
    alert_id: Optional[int]
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)