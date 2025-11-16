from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

logger = logging.getLogger(__name__)


from app.models.competitor import Competitor
from app.models.data_source import DataSource
from app.models.user import User
from app.utils.dependencies import get_db, get_current_user
from app.tasks.scraping_tasks import scrape_data_source

router = APIRouter()


@router.post("/competitors/{competitor_id}/scrape", status_code=status.HTTP_202_ACCEPTED)
async def trigger_competitor_scraping(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger scraping for all active data sources of a competitor"""
    logger.info(f"User {current_user.id} triggering scraping for competitor {competitor_id}.")
    
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    
    try:
        data_sources = db.query(DataSource).filter(
            DataSource.competitor_id == competitor_id,
            DataSource.is_active == True
        ).all()
        
        if not data_sources:
            logger.info(f"No active data sources found for competitor {competitor_id}.")
            return {"message": "No active data sources to scrape.", "competitor_id": competitor_id, "task_ids": [], "sources_count": 0}

        task_ids = []
        for source in data_sources:
            task = scrape_data_source.delay(source.id)
            task_ids.append(task.id)
        
        logger.info(f"Queued {len(task_ids)} scraping tasks for competitor {competitor_id}.")
        return {
            "message": "Scraping tasks started",
            "competitor_id": competitor_id,
            "task_ids": task_ids,
            "sources_count": len(data_sources)
        }
    except Exception as e:
        logger.error(f"Error triggering scraping for competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/sources/{source_id}/scrape", status_code=status.HTTP_202_ACCEPTED)
async def trigger_source_scraping(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger scraping for a single data source"""
    logger.info(f"User {current_user.id} triggering scraping for source {source_id}.")
    
    data_source = db.query(DataSource).join(Competitor).filter(
        DataSource.id == source_id,
        Competitor.user_id == current_user.id
    ).first()
    
    if not data_source:
        logger.warning(f"Data source {source_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
    
    if not data_source.is_active:
        logger.warning(f"Data source {source_id} is inactive, not starting scrape.")
        return {"message": "Data source is inactive.", "source_id": source_id, "task_id": None}

    try:
        task = scrape_data_source.delay(source_id)
        logger.info(f"Queued scraping task {task.id} for source {source_id}.")
        return {
            "message": "Scraping task started",
            "source_id": source_id,
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error triggering scraping for source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a background task"""
    logger.debug(f"User {current_user.id} checking status for task {task_id}.")
    from app.core.celery_app import celery_app
    
    try:
        task = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None
        }
        
        if task.failed():
            logger.warning(f"Task {task_id} failed with result: {task.result}")
        
        return response
    except Exception as e:
        logger.error(f"Error fetching status for task {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")