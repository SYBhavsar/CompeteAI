from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


from app.models import DataSource, ScrapingSchedule, Competitor, User
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.utils.dependencies import get_db, get_current_user

router = APIRouter()


@router.post("/sources/{source_id}", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    source_id: int,
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a schedule for a data source"""
    logger.info(f"User {current_user.id} attempting to create schedule for source_id: {source_id}")
    
    data_source = db.query(DataSource).join(Competitor).filter(
        DataSource.id == source_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not data_source:
        logger.warning(f"Data source {source_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
    
    existing_schedule = db.query(ScrapingSchedule).filter_by(data_source_id=source_id).first()
    if existing_schedule:
        logger.warning(f"Schedule already exists for data source {source_id}.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data source already has a schedule")
    
    try:
        next_run = datetime.now(timezone.utc) + timedelta(minutes=schedule_data.frequency_minutes)
        schedule = ScrapingSchedule(
            data_source_id=source_id,
            frequency_minutes=schedule_data.frequency_minutes,
            next_run=next_run,
            is_active=schedule_data.is_active
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        logger.info(f"Successfully created schedule {schedule.id} for source {source_id}.")
        return schedule
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create schedule for source {source_id} due to integrity error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create schedule due to a conflict.")
    except Exception as e:
        db.rollback()
        logger.error(f"An unexpected error occurred creating schedule for source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get("/sources/{source_id}", response_model=ScheduleResponse)
async def get_schedule_for_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get schedule for a data source"""
    logger.debug(f"Fetching schedule for source_id: {source_id}, user: {current_user.id}")
    
    schedule = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
        ScrapingSchedule.data_source_id == source_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not schedule:
        logger.warning(f"Schedule not found for source {source_id} and user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    
    logger.info(f"Successfully fetched schedule {schedule.id} for source {source_id}.")
    return schedule


@router.get("/", response_model=List[ScheduleResponse])
async def get_all_user_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all schedules for current user"""
    logger.debug(f"Fetching all schedules for user {current_user.id}.")
    try:
        schedules = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
            Competitor.user_id == current_user.id
        ).all()
        logger.info(f"Found {len(schedules)} schedules for user {current_user.id}.")
        return schedules
    except Exception as e:
        logger.error(f"Error fetching all schedules for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a schedule"""
    logger.info(f"User {current_user.id} updating schedule {schedule_id}.")
    
    schedule = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
        ScrapingSchedule.id == schedule_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not schedule:
        logger.warning(f"Schedule {schedule_id} not found for user {current_user.id} during update.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    
    try:
        update_data = schedule_data.model_dump(exclude_unset=True)
        logger.debug(f"Update data for schedule {schedule_id}: {update_data}")
        
        if 'frequency_minutes' in update_data:
            schedule.frequency_minutes = update_data['frequency_minutes']
            if schedule.last_run:
                schedule.next_run = schedule.last_run + timedelta(minutes=schedule.frequency_minutes)
            else:
                schedule.next_run = datetime.now(timezone.utc) + timedelta(minutes=schedule.frequency_minutes)
        
        if 'is_active' in update_data:
            schedule.is_active = update_data['is_active']
        
        db.commit()
        db.refresh(schedule)
        logger.info(f"Successfully updated schedule {schedule_id}.")
        return schedule
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating schedule {schedule_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a schedule"""
    logger.info(f"User {current_user.id} deleting schedule {schedule_id}.")
    
    schedule = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
        ScrapingSchedule.id == schedule_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not schedule:
        logger.warning(f"Schedule {schedule_id} not found for user {current_user.id} during deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    
    try:
        db.delete(schedule)
        db.commit()
        logger.info(f"Successfully deleted schedule {schedule_id}.")
        return {"message": "Schedule deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting schedule {schedule_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")