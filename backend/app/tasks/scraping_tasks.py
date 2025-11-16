from datetime import datetime, timezone
from typing import Dict, Any
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.data_source import DataSource
from app.models.raw_content import RawContent
from app.services.scraping_service import ScrapingService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.scraping_tasks.scrape_data_source", autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def scrape_data_source(data_source_id: int) -> Dict[str, Any]:
    """Scrape content from a data source with retry logic"""
    logger.info(f"Starting task 'scrape_data_source' for data_source_id={data_source_id}")
    db = SessionLocal()

    try:
        data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()

        if not data_source:
            logger.error(f"Data source with id {data_source_id} not found.")
            return {"status": "failed", "error": "Data source not found", "content_saved": False}
        
        if not data_source.is_active:
            logger.warning(f"Data source {data_source_id} is inactive. Skipping scrape.")
            return {"status": "skipped", "reason": "Data source is inactive", "content_saved": False}
        
        logger.debug(f"Scraping URL: {data_source.url}")
        scraping_service = ScrapingService()
        scraped_data = scraping_service.scrape_url(data_source.url)
        
        if not scraped_data:
            logger.error(f"Failed to scrape URL for data source {data_source_id}.")
            return {"status": "failed", "error": "Failed to scrape URL", "content_saved": False}
        
        content_hash = scraped_data["content_hash"]
        logger.debug(f"Scraped content hash: {content_hash}")

        existing_content = db.query(RawContent).filter(
            RawContent.data_source_id == data_source_id,
            RawContent.content_hash == content_hash
        ).first()
        
        if existing_content:
            logger.info(f"Content from data source {data_source_id} with hash {content_hash} already exists. Skipping save.")
            return {"status": "success", "message": "Content already exists (duplicate)", "content_saved": False}
        
        logger.debug(f"Saving new raw content for data source {data_source_id}.")
        raw_content = RawContent(
            data_source_id=data_source_id,
            content=scraped_data["content"],
            content_type=scraped_data["content_type"],
            url=scraped_data["url"],
            content_hash=content_hash,
            scraped_at=datetime.now(timezone.utc),
            status='pending' # Set initial status
        )
        
        db.add(raw_content)
        data_source.last_scraped = datetime.now(timezone.utc)
        db.commit()
        db.refresh(raw_content)
        
        logger.info(f"Successfully saved new raw content {raw_content.id} for data source {data_source_id}.")
        
        # Optional: Trigger content processing task
        # from .processing_tasks import process_raw_content_task
        # process_raw_content_task.delay(raw_content.id)

        return {
            "status": "success",
            "content_saved": True,
            "content_id": raw_content.id,
            "content_hash": content_hash
        }
        
    except Exception as e:
        logger.critical(f"An unexpected error occurred in 'scrape_data_source' for data_source_id {data_source_id}: {e}", exc_info=True)
        db.rollback()
        raise  # Re-raise to trigger Celery retry
    
    finally:
        db.close()