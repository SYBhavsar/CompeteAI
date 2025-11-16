from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CompetitorCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None


class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None


class CompetitorResponse(BaseModel):
    id: int
    name: str
    domain: Optional[str]
    industry: Optional[str]
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)