from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.competitor import Competitor
from app.models.user import User
from app.models import DataSource, RawContent
from app.schemas.competitor import CompetitorCreate, CompetitorResponse, CompetitorUpdate
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


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get individual competitor details"""
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    return competitor


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: int,
    competitor_data: CompetitorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update competitor information"""
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Update only provided fields
    update_data = competitor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(competitor, field, value)

    db.commit()
    db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete competitor and all associated data"""
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    db.delete(competitor)
    db.commit()

    return {"message": "Competitor deleted successfully"}


@router.get("/{competitor_id}/data")
async def get_competitor_data(
    competitor_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scraped data for a competitor"""
    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Get raw contents through data sources
    query = db.query(RawContent).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).filter(
        DataSource.competitor_id == competitor_id
    )

    total = query.count()
    raw_contents = query.offset(offset).limit(limit).all()

    # Format response
    formatted_contents = [
        {
            "id": content.id,
            "content": content.content[:500] + "..." if len(content.content) > 500 else content.content,
            "content_type": content.content_type,
            "url": content.url,
            "scraped_at": content.scraped_at.isoformat() if content.scraped_at else None,
            "created_at": content.created_at.isoformat()
        }
        for content in raw_contents
    ]

    return {
        "raw_contents": formatted_contents,
        "total": total,
        "limit": limit,
        "offset": offset
    }