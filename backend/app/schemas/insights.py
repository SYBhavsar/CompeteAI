from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class ProcessedInsightsResponse(BaseModel):
    """Response schema for processed insights"""
    id: int
    raw_content_id: int
    summary: str
    key_points: Optional[List[str]]
    sentiment: str
    insights: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightSummary(BaseModel):
    """Summary schema for insights"""
    id: int
    summary: str
    sentiment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)