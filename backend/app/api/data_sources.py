from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

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
    """Create a new data source for competitor"""
    # Verify competitor exists and belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )
    
    # Create data source
    data_source = DataSource(
        competitor_id=competitor_id,
        source_type=source_data.source_type,
        url=source_data.url,
        is_active=source_data.is_active
    )
    
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.get("/{competitor_id}/sources", response_model=List[DataSourceResponse])
async def get_competitor_sources(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all data sources for a competitor"""
    # Verify competitor exists and belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )
    
    sources = db.query(DataSource).filter(DataSource.competitor_id == competitor_id).all()
    return sources