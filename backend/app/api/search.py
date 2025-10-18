from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import SessionLocal
from app.models import User, ProcessedInsights, RawContent, DataSource, Competitor
from app.models.search import SavedSearch, SearchHistory
from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResult,
    TraditionalSearchResponse,
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchResponse,
    SearchHistoryResponse
)
from app.services.embedding_service import EmbeddingService
from app.utils.dependencies import get_current_user
from typing import List
from fastapi import status, HTTPException

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

    # Log search to history
    search_history = SearchHistory(
        user_id=current_user.id,
        search_type="traditional",
        query=keyword,
        filters={"competitor_id": competitor_id, "sentiment": sentiment},
        results_count=total
    )
    db.add(search_history)
    db.commit()

    return TraditionalSearchResponse(
        keyword=keyword,
        results=formatted_results,
        total=total
    )


@router.post("/search/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
def create_saved_search(
    search_data: SavedSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new saved search"""
    saved_search = SavedSearch(
        user_id=current_user.id,
        name=search_data.name,
        search_type=search_data.search_type,
        query=search_data.query,
        filters=search_data.filters
    )

    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)

    return saved_search


@router.get("/search/saved", response_model=List[SavedSearchResponse])
def get_saved_searches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all saved searches for the current user"""
    saved_searches = db.query(SavedSearch).filter(
        SavedSearch.user_id == current_user.id
    ).order_by(SavedSearch.created_at.desc()).all()

    return saved_searches


@router.get("/search/saved/{search_id}", response_model=SavedSearchResponse)
def get_saved_search(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific saved search"""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()

    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")

    return saved_search


@router.put("/search/saved/{search_id}", response_model=SavedSearchResponse)
def update_saved_search(
    search_id: int,
    search_data: SavedSearchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a saved search"""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()

    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")

    # Update fields
    update_data = search_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(saved_search, field, value)

    db.commit()
    db.refresh(saved_search)

    return saved_search


@router.delete("/search/saved/{search_id}")
def delete_saved_search(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a saved search"""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()

    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")

    db.delete(saved_search)
    db.commit()

    return {"message": "Saved search deleted successfully"}


@router.get("/search/history", response_model=List[SearchHistoryResponse])
def get_search_history(
    limit: int = Query(50, ge=1, le=100, description="Number of history entries"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get search history for the current user"""
    history = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(SearchHistory.executed_at.desc()).offset(offset).limit(limit).all()

    return history


@router.delete("/search/history")
def clear_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all search history for the current user"""
    db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).delete()
    db.commit()

    return {"message": "Search history cleared successfully"}