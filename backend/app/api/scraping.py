from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.competitor import Competitor
from app.models.data_source import DataSource
from app.models.user import User
from app.utils.dependencies import get_db, get_current_user
from app.tasks.scraping_tasks import scrape_data_source

router = APIRouter()


@router.post("/competitors/{competitor_id}/scrape")
async def trigger_competitor_scraping(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger scraping for all data sources of a competitor"""
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
    
    # Get all active data sources for this competitor
    data_sources = db.query(DataSource).filter(
        DataSource.competitor_id == competitor_id,
        DataSource.is_active == True
    ).all()
    
    # Start scraping tasks for each source
    task_ids = []
    for source in data_sources:
        task = scrape_data_source.delay(source.id)
        task_ids.append(task.id)
    
    return {
        "message": "Scraping tasks started",
        "competitor_id": competitor_id,
        "task_ids": task_ids,
        "sources_count": len(data_sources)
    }


@router.post("/sources/{source_id}/scrape")
async def trigger_source_scraping(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger scraping for a single data source"""
    # Get data source and verify it belongs to user
    data_source = db.query(DataSource).join(Competitor).filter(
        DataSource.id == source_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Start scraping task
    task = scrape_data_source.delay(source_id)
    
    return {
        "message": "Scraping task started",
        "source_id": source_id,
        "task_id": task.id
    }


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a scraping task"""
    from app.core.celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }