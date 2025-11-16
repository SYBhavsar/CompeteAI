from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


from app.core.database import SessionLocal
from app.models import User, Competitor, DataSource, RawContent, ProcessedInsights
from app.schemas.insights import ProcessedInsightsResponse
from app.services.content_processing_service import ContentProcessingService
from app.utils.dependencies import get_current_user
from app.tasks.alert_tasks import process_insight_alerts

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
    logger.info(f"Fetching insights for competitor {competitor_id}, user {current_user.id}. Filters: sentiment={sentiment}, limit={limit}, offset={offset}")
    
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    
    try:
        query = db.query(ProcessedInsights).join(
            RawContent, ProcessedInsights.raw_content_id == RawContent.id
        ).join(
            DataSource, RawContent.data_source_id == DataSource.id
        ).filter(
            DataSource.competitor_id == competitor_id
        )
        
        if sentiment:
            query = query.filter(ProcessedInsights.sentiment == sentiment)
        
        insights = query.order_by(ProcessedInsights.created_at.desc()).offset(offset).limit(limit).all()
        logger.info(f"Found {len(insights)} insights for competitor {competitor_id}.")
        return insights
    except Exception as e:
        logger.error(f"Error fetching insights for competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/insights/{insight_id}", response_model=ProcessedInsightsResponse)
def get_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific insight by ID"""
    logger.debug(f"Fetching insight {insight_id} for user {current_user.id}.")
    
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
        logger.warning(f"Insight {insight_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    
    logger.info(f"Successfully fetched insight {insight_id} for user {current_user.id}.")
    return insight


@router.post("/insights/process/{raw_content_id}", response_model=ProcessedInsightsResponse, status_code=201)
def process_raw_content_endpoint(
    raw_content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process raw content to generate insights"""
    logger.info(f"User {current_user.id} initiated processing for raw_content_id: {raw_content_id}")
    
    raw_content = db.query(RawContent).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).join(
        Competitor, DataSource.competitor_id == Competitor.id
    ).filter(
        RawContent.id == raw_content_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not raw_content:
        logger.warning(f"Raw content {raw_content_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw content not found")
    
    try:
        service = ContentProcessingService()
        result = service.process_raw_content(raw_content_id, db)

        if not result:
            logger.error(f"Content processing failed for raw_content_id: {raw_content_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process content")

        # Trigger alert processing asynchronously
        competitor_id = raw_content.data_source.competitor_id
        process_insight_alerts.delay(result.id, competitor_id)
        logger.info(f"Queued alert processing for new insight {result.id}.")

        logger.info(f"Successfully processed raw_content_id: {raw_content_id}, created insight {result.id}.")
        return result
    except HTTPException as he:
        # Re-raise HTTP exceptions to let FastAPI handle them
        raise he
    except Exception as e:
        logger.critical(f"An unexpected error occurred during content processing for {raw_content_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")