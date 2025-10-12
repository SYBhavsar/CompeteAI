from datetime import datetime
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.data_source import DataSource
from app.models.raw_content import RawContent
from app.services.scraping_service import ScrapingService


@celery_app.task
def scrape_data_source(data_source_id: int) -> Dict[str, Any]:
    """Scrape content from a data source"""
    db = SessionLocal()
    
    try:
        # Get data source
        data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
        
        if not data_source:
            return {
                "status": "failed",
                "error": "Data source not found",
                "content_saved": False
            }
        
        # Check if data source is active
        if not data_source.is_active:
            return {
                "status": "skipped",
                "reason": "Data source is inactive",
                "content_saved": False
            }
        
        # Scrape the URL
        scraping_service = ScrapingService()
        scraped_data = scraping_service.scrape_url(data_source.url)
        
        if not scraped_data:
            return {
                "status": "failed",
                "error": "Failed to scrape URL",
                "content_saved": False
            }
        
        # Check for duplicate content
        existing_content = db.query(RawContent).filter(
            RawContent.data_source_id == data_source_id,
            RawContent.content_hash == scraped_data["content_hash"]
        ).first()
        
        if existing_content:
            return {
                "status": "success",
                "message": "Content already exists (duplicate)",
                "content_saved": False
            }
        
        # Save raw content
        raw_content = RawContent(
            data_source_id=data_source_id,
            content=scraped_data["content"],
            content_type=scraped_data["content_type"],
            url=scraped_data["url"],
            content_hash=scraped_data["content_hash"],
            scraped_at=datetime.utcnow()
        )
        
        db.add(raw_content)
        
        # Update last_scraped timestamp
        data_source.last_scraped = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "success",
            "content_saved": True,
            "content_id": raw_content.id,
            "content_hash": scraped_data["content_hash"]
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "failed",
            "error": str(e),
            "content_saved": False
        }
    
    finally:
        db.close()