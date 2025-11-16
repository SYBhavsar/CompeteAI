from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import DataSource, ScrapingSchedule


@celery_app.task(name="app.tasks.scheduling_tasks.check_and_execute_due_schedules")
def check_and_execute_due_schedules() -> Dict[str, Any]:
    """Check for due schedules and execute scraping tasks"""
    db = SessionLocal()
    logger.info("Starting task 'check_and_execute_due_schedules'.")
    
    try:
        current_time = datetime.now(timezone.utc)
        
        due_schedules = db.query(ScrapingSchedule).join(DataSource).filter(
            ScrapingSchedule.next_run <= current_time,
            ScrapingSchedule.is_active == True,
            DataSource.is_active == True
        ).all()
        
        if not due_schedules:
            logger.info("No due schedules found.")
            return {"scheduled_count": 0, "task_ids": []}

        logger.info(f"Found {len(due_schedules)} due schedules to execute.")
        task_ids = []
        
        for schedule in due_schedules:
            logger.info(f"Executing schedule {schedule.id} for data_source_id: {schedule.data_source_id}")
            try:
                task = celery_app.send_task(
                    'app.tasks.scraping_tasks.scrape_data_source',
                    args=[schedule.data_source_id]
                )
                task_ids.append(task.id)
                
                # Update schedule for next run
                schedule.last_run = current_time
                schedule.next_run = current_time + timedelta(minutes=schedule.frequency_minutes)
                logger.debug(f"Updated schedule {schedule.id}. Next run at: {schedule.next_run}")

            except Exception as e:
                logger.error(f"Failed to queue scraping task for schedule {schedule.id}. Error: {e}", exc_info=True)
        
        db.commit()
        logger.info(f"Successfully queued {len(task_ids)} scraping tasks.")
        
        return {
            "scheduled_count": len(task_ids),
            "task_ids": task_ids,
            "executed_at": current_time.isoformat()
        }
        
    except Exception as e:
        logger.critical(f"An unexpected error occurred in 'check_and_execute_due_schedules': {e}", exc_info=True)
        db.rollback()
        # Re-raise the exception to let Celery know the task failed
        raise
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduling_tasks.update_schedule_after_scraping")
def update_schedule_after_scraping(data_source_id: int) -> Dict[str, Any]:
    """Update schedule after successful scraping (alternative approach)"""
    db = SessionLocal()
    logger.info(f"Starting task 'update_schedule_after_scraping' for data_source_id: {data_source_id}")
    
    try:
        schedule = db.query(ScrapingSchedule).filter(
            ScrapingSchedule.data_source_id == data_source_id
        ).first()
        
        if not schedule:
            logger.warning(f"Schedule for data_source_id {data_source_id} not found.")
            return {
                "status": "error",
                "message": f"Schedule for data source {data_source_id} not found"
            }
        
        current_time = datetime.now(timezone.utc)
        
        # Update schedule
        schedule.last_run = current_time
        schedule.next_run = current_time + timedelta(minutes=schedule.frequency_minutes)
        
        db.commit()
        logger.info(f"Successfully updated schedule for data_source_id {data_source_id}. Next run: {schedule.next_run.isoformat()}")
        
        return {
            "status": "success",
            "data_source_id": data_source_id,
            "next_run": schedule.next_run.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update schedule for data_source_id {data_source_id}. Error: {e}", exc_info=True)
        db.rollback()
        raise
    
    finally:
        db.close()