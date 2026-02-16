"""
Pydantic schemas for Historical Intelligence API

Request/Response models for historical analysis endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class TimelineEventResponse(BaseModel):
    """Response model for timeline events"""
    id: int
    competitor_id: int
    event_type: str
    event_date: datetime
    title: str
    description: str
    source_urls: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChangeEventResponse(BaseModel):
    """Response model for change events"""
    id: int
    competitor_id: int
    change_type: str
    severity: str
    before_snapshot_id: int
    after_snapshot_id: int
    change_summary: str
    strategic_impact: str
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotCreateRequest(BaseModel):
    """Request model for creating snapshots"""
    snapshot_data: Dict[str, Any] = Field(
        ...,
        description="Competitor data to snapshot (pricing, features, etc.)",
        example={
            "pricing": "$199/month",
            "features": ["Feature A", "Feature B"],
            "target_market": "Enterprise"
        }
    )


class SnapshotResponse(BaseModel):
    """Response model for snapshots"""
    id: int
    competitor_id: int
    snapshot_date: datetime
    data_hash: str
    snapshot_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ChangeVelocityResponse(BaseModel):
    """Response model for change velocity analytics"""
    competitor_id: int
    competitor_name: str
    competitor_domain: Optional[str] = None
    change_count: int = Field(..., description="Number of changes in timeframe")
    average_severity: str = Field(..., description="Average severity: minor, moderate, major, critical")
    timeframe_days: int = Field(..., description="Analysis timeframe in days")

    class Config:
        from_attributes = True
