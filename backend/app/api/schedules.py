from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime, timedelta, timezone

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
    # Verify data source exists and belongs to user
    data_source = db.query(DataSource).join(Competitor).filter(
        DataSource.id == source_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Check if schedule already exists
    existing_schedule = db.query(ScrapingSchedule).filter(
        ScrapingSchedule.data_source_id == source_id
    ).first()
    
    if existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data source already has a schedule"
        )
    
    # Create schedule
    next_run = datetime.now(timezone.utc) + timedelta(minutes=schedule_data.frequency_minutes)
    
    schedule = ScrapingSchedule(
        data_source_id=source_id,
        frequency_minutes=schedule_data.frequency_minutes,
        next_run=next_run,
        is_active=schedule_data.is_active
    )
    
    try:
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create schedule"
        )


@router.get("/sources/{source_id}", response_model=ScheduleResponse)
async def get_schedule_for_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get schedule for a data source"""
    # Verify data source belongs to user and get schedule
    schedule = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
        ScrapingSchedule.data_source_id == source_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return schedule


@router.get("/", response_model=List[ScheduleResponse])
async def get_all_user_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all schedules for current user"""
    schedules = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
        Competitor.user_id == current_user.id
    ).all()
    
    return schedules


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a schedule"""
    # Verify schedule belongs to user
    schedule = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
        ScrapingSchedule.id == schedule_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Update fields
    if schedule_data.frequency_minutes is not None:
        schedule.frequency_minutes = schedule_data.frequency_minutes
        # Recalculate next_run if frequency changed
        if schedule.last_run:
            schedule.next_run = schedule.last_run + timedelta(minutes=schedule_data.frequency_minutes)
        else:
            schedule.next_run = datetime.now(timezone.utc) + timedelta(minutes=schedule_data.frequency_minutes)
    
    if schedule_data.is_active is not None:
        schedule.is_active = schedule_data.is_active
    
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a schedule"""
    # Verify schedule belongs to user
    schedule = db.query(ScrapingSchedule).join(DataSource).join(Competitor).filter(
        ScrapingSchedule.id == schedule_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "Schedule deleted successfully"}