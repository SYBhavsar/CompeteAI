from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


class SemanticSearchRequest(BaseModel):
    """Request schema for semantic search"""
    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    competitor_id: Optional[int] = Field(None, description="Filter by competitor ID")


class SearchResult(BaseModel):
    """Individual search result"""
    id: str
    score: float
    metadata: Dict[str, Any]


class SemanticSearchResponse(BaseModel):
    """Response schema for semantic search"""
    query: str
    results: List[SearchResult]
    total: int


class TraditionalSearchResponse(BaseModel):
    """Response schema for traditional search"""
    keyword: str
    results: List[Dict[str, Any]]
    total: int


class SavedSearchCreate(BaseModel):
    """Schema for creating a saved search"""
    name: str
    search_type: str  # semantic or traditional
    query: str
    filters: Optional[Dict[str, Any]] = None


class SavedSearchUpdate(BaseModel):
    """Schema for updating a saved search"""
    name: Optional[str] = None
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class SavedSearchResponse(BaseModel):
    """Schema for saved search response"""
    id: int
    user_id: int
    name: str
    search_type: str
    query: str
    filters: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SearchHistoryCreate(BaseModel):
    """Schema for creating search history entry"""
    search_type: str
    query: str
    filters: Optional[Dict[str, Any]] = None
    results_count: Optional[int] = None


class SearchHistoryResponse(BaseModel):
    """Schema for search history response"""
    id: int
    user_id: int
    search_type: str
    query: str
    filters: Optional[Dict[str, Any]]
    results_count: Optional[int]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)