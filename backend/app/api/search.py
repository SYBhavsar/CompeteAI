from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import SessionLocal
from app.models import User, ProcessedInsights, RawContent, DataSource, Competitor
from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResult,
    TraditionalSearchResponse
)
from app.services.embedding_service import EmbeddingService
from app.utils.dependencies import get_current_user

router = APIRouter()


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/search/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform semantic search on insights using vector similarity

    Args:
        request: Search request with query and filters
        current_user: Authenticated user

    Returns:
        Similar insights ranked by relevance
    """
    # Initialize embedding service
    embedding_service = EmbeddingService()

    # Perform semantic search
    results = embedding_service.search_similar_insights(
        query_text=request.query,
        top_k=request.top_k,
        competitor_id=request.competitor_id
    )

    # Format results
    search_results = [
        SearchResult(
            id=result["id"],
            score=result["score"],
            metadata=result["metadata"]
        )
        for result in results
    ]

    return SemanticSearchResponse(
        query=request.query,
        results=search_results,
        total=len(search_results)
    )


@router.get("/search/traditional", response_model=TraditionalSearchResponse)
def traditional_search(
    keyword: str = Query(..., min_length=1, description="Search keyword"),
    competitor_id: Optional[int] = Query(None, description="Filter by competitor ID"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform traditional keyword-based search on insights

    Args:
        keyword: Search keyword
        competitor_id: Optional competitor filter
        sentiment: Optional sentiment filter
        limit: Maximum results to return
        offset: Pagination offset
        db: Database session
        current_user: Authenticated user

    Returns:
        Matching insights based on keyword search
    """
    # Build query
    query = db.query(ProcessedInsights).join(
        RawContent, ProcessedInsights.raw_content_id == RawContent.id
    ).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).join(
        Competitor, DataSource.competitor_id == Competitor.id
    ).filter(
        Competitor.user_id == current_user.id
    )

    # Apply keyword filter on summary and insights
    keyword_filter = (
        ProcessedInsights.summary.ilike(f"%{keyword}%") |
        ProcessedInsights.insights.ilike(f"%{keyword}%")
    )
    query = query.filter(keyword_filter)

    # Apply optional filters
    if competitor_id:
        query = query.filter(Competitor.id == competitor_id)

    if sentiment:
        query = query.filter(ProcessedInsights.sentiment == sentiment)

    # Get total count
    total = query.count()

    # Apply pagination
    results = query.offset(offset).limit(limit).all()

    # Format results
    formatted_results = [
        {
            "id": insight.id,
            "summary": insight.summary,
            "sentiment": insight.sentiment,
            "insights": insight.insights,
            "key_points": insight.key_points,
            "competitor_id": insight.raw_content.data_source.competitor_id,
            "created_at": insight.created_at.isoformat()
        }
        for insight in results
    ]

    return TraditionalSearchResponse(
        keyword=keyword,
        results=formatted_results,
        total=total
    )