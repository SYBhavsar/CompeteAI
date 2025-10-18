from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import SessionLocal
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights
from app.schemas.insights import ProcessedInsightsResponse
from app.services.content_processing_service import ContentProcessingService
from app.utils.dependencies import get_current_user

router = APIRouter()


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/competitors/{competitor_id}/insights", response_model=List[ProcessedInsightsResponse])
def get_competitor_insights(
    competitor_id: int,
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: positive, negative, neutral"),
    limit: int = Query(50, ge=1, le=100, description="Number of insights to return"),
    offset: int = Query(0, ge=0, description="Number of insights to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all insights for a competitor"""
    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Build query for insights
    query = db.query(ProcessedInsights).join(
        RawContent, ProcessedInsights.raw_content_id == RawContent.id
    ).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).filter(
        DataSource.competitor_id == competitor_id
    )
    
    # Apply sentiment filter if provided
    if sentiment:
        query = query.filter(ProcessedInsights.sentiment == sentiment)
    
    # Apply pagination
    insights = query.offset(offset).limit(limit).all()
    
    return insights


@router.get("/insights/{insight_id}", response_model=ProcessedInsightsResponse)
def get_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific insight by ID"""
    insight = db.query(ProcessedInsights).join(
        RawContent, ProcessedInsights.raw_content_id == RawContent.id
    ).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).join(
        Competitor, DataSource.competitor_id == Competitor.id
    ).filter(
        ProcessedInsights.id == insight_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return insight


@router.post("/insights/process/{raw_content_id}", response_model=ProcessedInsightsResponse, status_code=201)
def process_raw_content(
    raw_content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process raw content to generate insights"""
    # Verify raw content belongs to user
    raw_content = db.query(RawContent).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).join(
        Competitor, DataSource.competitor_id == Competitor.id
    ).filter(
        RawContent.id == raw_content_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not raw_content:
        raise HTTPException(status_code=404, detail="Raw content not found")
    
    # Process content
    service = ContentProcessingService()
    result = service.process_raw_content(raw_content_id, db)
    
    if not result:
        raise HTTPException(status_code=404, detail="Failed to process content")
    
    return result