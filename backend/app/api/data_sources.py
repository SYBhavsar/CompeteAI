from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

logger = logging.getLogger(__name__)


from app.models.data_source import DataSource
from app.models.competitor import Competitor
from app.models.user import User
from app.schemas.data_source import DataSourceCreate, DataSourceResponse
from app.utils.dependencies import get_db, get_current_user

router = APIRouter()


@router.post("/{competitor_id}/sources", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    competitor_id: int,
    source_data: DataSourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new data source for a competitor"""
    logger.info(f"User {current_user.id} creating data source for competitor {competitor_id} with URL: {source_data.url}")
    
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    
    try:
        data_source = DataSource(
            competitor_id=competitor_id,
            source_type=source_data.source_type,
            url=str(source_data.url), # Ensure URL is a string
            is_active=source_data.is_active
        )
        
        db.add(data_source)
        db.commit()
        db.refresh(data_source)
        logger.info(f"Successfully created data source {data_source.id} for competitor {competitor_id}.")
        return data_source
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating data source for competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{competitor_id}/sources", response_model=List[DataSourceResponse])
async def get_competitor_sources(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all data sources for a competitor"""
    logger.debug(f"Fetching data sources for competitor {competitor_id}, user {current_user.id}.")
    
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id} when fetching sources.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    
    try:
        sources = db.query(DataSource).filter(DataSource.competitor_id == competitor_id).all()
        logger.info(f"Found {len(sources)} data sources for competitor {competitor_id}.")
        return sources
    except Exception as e:
        logger.error(f"Error fetching data sources for competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")