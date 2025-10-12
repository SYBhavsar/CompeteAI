from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import DataSource, ScrapingSchedule


@celery_app.task
def check_and_execute_due_schedules() -> Dict[str, Any]:
    """Check for due schedules and execute scraping tasks"""
    db = SessionLocal()
    
    try:
        # Find all schedules that are due and active
        current_time = datetime.now(timezone.utc)
        
        due_schedules = db.query(ScrapingSchedule).join(DataSource).filter(
            ScrapingSchedule.next_run <= current_time,
            ScrapingSchedule.is_active == True,
            DataSource.is_active == True  # Only active data sources
        ).all()
        
        task_ids = []
        
        for schedule in due_schedules:
            # Trigger scraping task using task name to avoid circular import
            task = celery_app.send_task(
                'app.tasks.scraping_tasks.scrape_data_source',
                args=[schedule.data_source_id]
            )
            task_ids.append(task.id)
            
            # Update schedule for next run
            schedule.last_run = current_time
            schedule.next_run = current_time + timedelta(minutes=schedule.frequency_minutes)
        
        db.commit()
        
        return {
            "scheduled_count": len(due_schedules),
            "task_ids": task_ids,
            "executed_at": current_time.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        return {
            "scheduled_count": 0,
            "task_ids": [],
            "error": str(e)
        }
    
    finally:
        db.close()


@celery_app.task
def update_schedule_after_scraping(data_source_id: int) -> Dict[str, Any]:
    """Update schedule after successful scraping (alternative approach)"""
    db = SessionLocal()
    
    try:
        schedule = db.query(ScrapingSchedule).filter(
            ScrapingSchedule.data_source_id == data_source_id
        ).first()
        
        if not schedule:
            return {
                "status": "error",
                "message": f"Schedule for data source {data_source_id} not found"
            }
        
        current_time = datetime.now(timezone.utc)
        
        # Update schedule
        schedule.last_run = current_time
        schedule.next_run = current_time + timedelta(minutes=schedule.frequency_minutes)
        
        db.commit()
        
        return {
            "status": "success",
            "data_source_id": data_source_id,
            "next_run": schedule.next_run.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    
    finally:
        db.close()