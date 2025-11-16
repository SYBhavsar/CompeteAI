from pydantic import BaseModel, ConfigDict, HttpUrl
from typing import Optional
from datetime import datetime


class DataSourceCreate(BaseModel):
    source_type: str  # website, blog, social_media, news
    url: str
    is_active: Optional[bool] = True


class DataSourceResponse(BaseModel):
    id: int
    competitor_id: int
    source_type: str
    url: str
    is_active: bool
    last_scraped: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)