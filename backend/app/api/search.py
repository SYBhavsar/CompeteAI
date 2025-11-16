from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search on insights using vector similarity
    """
    logger.info(f"User {current_user.id} performing semantic search with query: '{request.query}'")
    try:
        embedding_service = EmbeddingService()
        results = embedding_service.search_similar_insights(
            query_text=request.query,
            top_k=request.top_k,
            competitor_id=request.competitor_id
        )
        
        search_results = [SearchResult(id=r["id"], score=r["score"], metadata=r["metadata"]) for r in results]
        
        # Log search to history
        search_history = SearchHistory(
            user_id=current_user.id,
            search_type="semantic",
            query=request.query,
            filters={"competitor_id": request.competitor_id, "top_k": request.top_k},
            results_count=len(search_results)
        )
        db.add(search_history)
        db.commit()
        
        logger.info(f"Semantic search by user {current_user.id} returned {len(search_results)} results.")
        return SemanticSearchResponse(query=request.query, results=search_results, total=len(search_results))
    except Exception as e:
        logger.error(f"Error during semantic search for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


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
    """
    logger.info(f"User {current_user.id} performing traditional search with keyword: '{keyword}'")
    try:
        query = db.query(ProcessedInsights).join(RawContent).join(DataSource).join(Competitor).filter(
            Competitor.user_id == current_user.id
        )

        keyword_filter = (
            ProcessedInsights.summary.ilike(f"%{keyword}%") |
            ProcessedInsights.insights.ilike(f"%{keyword}%")
        )
        query = query.filter(keyword_filter)

        if competitor_id:
            query = query.filter(Competitor.id == competitor_id)
        if sentiment:
            query = query.filter(ProcessedInsights.sentiment == sentiment)

        total = query.count()
        results = query.order_by(ProcessedInsights.created_at.desc()).offset(offset).limit(limit).all()
        
        logger.info(f"Traditional search by user {current_user.id} found {total} results.")

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

        return TraditionalSearchResponse(keyword=keyword, results=results, total=total)
    except Exception as e:
        logger.error(f"Error during traditional search for user {current_user.id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/search/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
def create_saved_search(
    search_data: SavedSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new saved search"""
    logger.info(f"User {current_user.id} creating saved search: '{search_data.name}'")
    try:
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
        logger.info(f"Successfully created saved search {saved_search.id} for user {current_user.id}.")
        return saved_search
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating saved search for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/search/saved", response_model=List[SavedSearchResponse])
def get_saved_searches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all saved searches for the current user"""
    logger.debug(f"Fetching all saved searches for user {current_user.id}.")
    try:
        saved_searches = db.query(SavedSearch).filter_by(user_id=current_user.id).order_by(SavedSearch.created_at.desc()).all()
        logger.info(f"Found {len(saved_searches)} saved searches for user {current_user.id}.")
        return saved_searches
    except Exception as e:
        logger.error(f"Error fetching saved searches for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/search/saved/{search_id}", response_model=SavedSearchResponse)
def get_saved_search(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific saved search"""
    logger.debug(f"Fetching saved search {search_id} for user {current_user.id}.")
    saved_search = db.query(SavedSearch).filter_by(id=search_id, user_id=current_user.id).first()

    if not saved_search:
        logger.warning(f"Saved search {search_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    
    logger.info(f"Successfully fetched saved search {search_id}.")
    return saved_search


@router.put("/search/saved/{search_id}", response_model=SavedSearchResponse)
def update_saved_search(
    search_id: int,
    search_data: SavedSearchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a saved search"""
    logger.info(f"User {current_user.id} updating saved search {search_id}.")
    saved_search = db.query(SavedSearch).filter_by(id=search_id, user_id=current_user.id).first()

    if not saved_search:
        logger.warning(f"Saved search {search_id} not found for user {current_user.id} during update.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    try:
        update_data = search_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(saved_search, field, value)
        db.commit()
        db.refresh(saved_search)
        logger.info(f"Successfully updated saved search {search_id}.")
        return saved_search
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating saved search {search_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/search/saved/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_search(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a saved search"""
    logger.info(f"User {current_user.id} deleting saved search {search_id}.")
    saved_search = db.query(SavedSearch).filter_by(id=search_id, user_id=current_user.id).first()

    if not saved_search:
        logger.warning(f"Saved search {search_id} not found for user {current_user.id} during deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    try:
        db.delete(saved_search)
        db.commit()
        logger.info(f"Successfully deleted saved search {search_id}.")
        return {"message": "Saved search deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting saved search {search_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/search/history", response_model=List[SearchHistoryResponse])
def get_search_history(
    limit: int = Query(50, ge=1, le=100, description="Number of history entries"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get search history for the current user"""
    logger.debug(f"Fetching search history for user {current_user.id}.")
    try:
        history = db.query(SearchHistory).filter_by(user_id=current_user.id).order_by(SearchHistory.executed_at.desc()).offset(offset).limit(limit).all()
        logger.info(f"Found {len(history)} search history entries for user {current_user.id}.")
        return history
    except Exception as e:
        logger.error(f"Error fetching search history for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/search/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all search history for the current user"""
    logger.info(f"User {current_user.id} clearing their search history.")
    try:
        deleted_count = db.query(SearchHistory).filter_by(user_id=current_user.id).delete()
        db.commit()
        logger.info(f"Cleared {deleted_count} history entries for user {current_user.id}.")
        return {"message": "Search history cleared successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing search history for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")