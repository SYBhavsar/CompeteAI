from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.models.competitor import Competitor
from app.models.user import User
from app.schemas.competitor import CompetitorCreate, CompetitorResponse
from app.utils.dependencies import get_db, get_current_user

router = APIRouter()


@router.post("/", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def create_competitor(
    competitor_data: CompetitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new competitor"""
    competitor = Competitor(
        name=competitor_data.name,
        domain=competitor_data.domain,
        industry=competitor_data.industry,
        user_id=current_user.id
    )
    
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@router.get("/", response_model=List[CompetitorResponse])
async def get_competitors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all competitors for current user"""
    competitors = db.query(Competitor).filter(Competitor.user_id == current_user.id).all()
    return competitors