from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


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
    logger.info(f"User {current_user.id} creating competitor: {competitor_data.name}")
    try:
        competitor = Competitor(
            name=competitor_data.name,
            domain=competitor_data.domain,
            industry=competitor_data.industry,
            user_id=current_user.id
        )
        
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
        logger.info(f"Successfully created competitor {competitor.id} for user {current_user.id}.")
        return competitor
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating competitor for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=List[CompetitorResponse])
async def get_competitors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all competitors for current user"""
    logger.debug(f"Fetching all competitors for user {current_user.id}.")
    try:
        competitors = db.query(Competitor).filter(Competitor.user_id == current_user.id).all()
        logger.info(f"Found {len(competitors)} competitors for user {current_user.id}.")
        return competitors
    except Exception as e:
        logger.error(f"Error fetching competitors for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get individual competitor details"""
    logger.debug(f"Fetching competitor {competitor_id} for user {current_user.id}.")
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    logger.info(f"Successfully fetched competitor {competitor_id} for user {current_user.id}.")
    return competitor


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: int,
    competitor_data: CompetitorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update competitor information"""
    logger.info(f"User {current_user.id} updating competitor {competitor_id}.")
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id} during update.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    try:
        update_data = competitor_data.model_dump(exclude_unset=True)
        logger.debug(f"Update data for competitor {competitor_id}: {update_data}")
        for field, value in update_data.items():
            setattr(competitor, field, value)

        db.commit()
        db.refresh(competitor)
        logger.info(f"Successfully updated competitor {competitor_id}.")
        return competitor
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete competitor and all associated data"""
    logger.info(f"User {current_user.id} deleting competitor {competitor_id}.")
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id} during deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    try:
        db.delete(competitor)
        db.commit()
        logger.info(f"Successfully deleted competitor {competitor_id}.")
        return {"message": "Competitor deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{competitor_id}/data", response_model=Dict[str, Any])
async def get_competitor_data(
    competitor_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scraped data for a competitor"""
    logger.debug(f"Fetching data for competitor {competitor_id}, user {current_user.id}.")
    
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id} when fetching data.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    try:
        query = db.query(RawContent).join(
            DataSource, RawContent.data_source_id == DataSource.id
        ).filter(
            DataSource.competitor_id == competitor_id
        ).order_by(RawContent.scraped_at.desc())

        total = query.count()
        raw_contents = query.offset(offset).limit(limit).all()
        logger.info(f"Found {len(raw_contents)} raw content items for competitor {competitor_id} (total: {total}).")

        formatted_contents = [
            {
                "id": content.id,
                "content": content.content[:500] + "..." if content.content and len(content.content) > 500 else content.content,
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
    except Exception as e:
        logger.error(f"Error fetching data for competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")