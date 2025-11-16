from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ScheduleCreate(BaseModel):
    frequency_minutes: int
    is_active: Optional[bool] = True


class ScheduleUpdate(BaseModel):
    frequency_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: int
    data_source_id: int
    frequency_minutes: int
    next_run: datetime
    last_run: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)