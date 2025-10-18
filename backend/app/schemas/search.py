from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


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