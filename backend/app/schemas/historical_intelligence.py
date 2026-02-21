"""
Pydantic schemas for Historical Intelligence API

Request/Response models for historical analysis endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class TimelineEventResponse(BaseModel):
    """Response model for timeline events"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    event_type: str
    event_date: datetime
    title: str
    description: str
    source_urls: List[str]
    created_at: datetime


class ChangeEventResponse(BaseModel):
    """Response model for change events"""
    model_config = ConfigDict(from_attributes=True)

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


class SnapshotCreateRequest(BaseModel):
    """Request model for creating snapshots"""
    snapshot_data: Dict[str, Any] = Field(
        ...,
        description="Competitor data to snapshot (pricing, features, etc.)",
        json_schema_extra={
            "example": {
                "pricing": "$199/month",
                "features": ["Feature A", "Feature B"],
                "target_market": "Enterprise"
            }
        }
    )


class SnapshotResponse(BaseModel):
    """Response model for snapshots"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    snapshot_date: datetime
    data_hash: str
    snapshot_data: Dict[str, Any]
    created_at: datetime


class ChangeVelocityResponse(BaseModel):
    """Response model for change velocity analytics"""
    model_config = ConfigDict(from_attributes=True)

    competitor_id: int
    competitor_name: str
    competitor_domain: Optional[str] = None
    change_count: int = Field(..., description="Number of changes in timeframe")
    average_severity: str = Field(..., description="Average severity: minor, moderate, major, critical")
    timeframe_days: int = Field(..., description="Analysis timeframe in days")
