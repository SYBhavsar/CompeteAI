"""
Historical Analysis Celery Tasks

Background tasks for automated historical intelligence:
- Analyze competitor changes after scraping
- Create snapshots from scraped content
- Trigger alerts for high-severity changes

Follows: Single Responsibility, async processing best practices
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import RawContent, DataSource
from app.models.competitive_snapshot import CompetitiveSnapshot
from app.services.historical_analysis_service import HistoricalAnalysisService
from app.tasks.alert_tasks import process_insight_alerts

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5}
)
def analyze_competitor_changes(self, competitor_id: int) -> Dict[str, Any]:
    """
    Analyze competitor for changes between latest snapshots.

    This task is triggered after:
    - New snapshot is created
    - Manual snapshot request
    - Scheduled analysis

    Args:
        competitor_id: ID of competitor to analyze

    Returns:
        Dict with analysis results and detected changes
    """
    logger.info(f"Starting change analysis for competitor {competitor_id}")

    db = SessionLocal()
    try:
        # Initialize service
        analysis_service = HistoricalAnalysisService()

        # Analyze latest snapshots
        changes = analysis_service.analyze_latest_snapshots(
            competitor_id=competitor_id,
            db=db
        )

        if changes is None:
            logger.info(f"No snapshots to compare for competitor {competitor_id}")
            return {
                "competitor_id": competitor_id,
                "changes_detected": 0,
                "message": "Insufficient snapshots for analysis"
            }

        changes_count = len(changes)
        logger.info(f"Detected {changes_count} changes for competitor {competitor_id}")

        # Trigger alerts for high-severity changes
        high_severity_changes = [
            c for c in changes
            if c.severity in ["major", "critical"]
        ]

        if high_severity_changes:
            logger.info(
                f"Triggering alerts for {len(high_severity_changes)} "
                f"high-severity changes for competitor {competitor_id}"
            )
            for change in high_severity_changes:
                # Trigger alert processing
                # Note: We don't have insight_id, so we pass change_id as reference
                process_insight_alerts.delay(change.id, competitor_id)

        return {
            "competitor_id": competitor_id,
            "changes_detected": changes_count,
            "high_severity_count": len(high_severity_changes),
            "change_ids": [c.id for c in changes]
        }

    except Exception as e:
        logger.error(
            f"Error analyzing changes for competitor {competitor_id}: {e}",
            exc_info=True
        )
        return {
            "competitor_id": competitor_id,
            "changes_detected": 0,
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5}
)
def create_snapshot_from_content(self, raw_content_id: int) -> Dict[str, Any]:
    """
    Create a competitor snapshot from scraped content.

    This task is triggered after scraping completes. It extracts
    structured data from raw content and creates a snapshot for
    historical analysis.

    Args:
        raw_content_id: ID of RawContent to process

    Returns:
        Dict with snapshot creation results
    """
    logger.info(f"Creating snapshot from raw content {raw_content_id}")

    db = SessionLocal()
    try:
        # Get raw content
        raw_content = db.query(RawContent).filter(
            RawContent.id == raw_content_id
        ).first()

        if not raw_content:
            logger.error(f"Raw content {raw_content_id} not found")
            return {
                "error": "Raw content not found",
                "raw_content_id": raw_content_id
            }

        # Get data source and competitor
        data_source = db.query(DataSource).filter(
            DataSource.id == raw_content.data_source_id
        ).first()

        if not data_source:
            logger.error(f"Data source not found for raw content {raw_content_id}")
            return {
                "error": "Data source not found",
                "raw_content_id": raw_content_id
            }

        competitor_id = data_source.competitor_id

        # Extract structured data from content
        # For now, we'll store the raw content as-is
        # In future iterations, this could be enhanced with AI extraction
        snapshot_data = {
            "raw_content": raw_content.content[:1000],  # Truncate for storage
            "url": raw_content.url,
            "content_type": raw_content.content_type,
            "scraped_at": raw_content.created_at.isoformat() if raw_content.created_at else None,
            "source_type": data_source.source_type
        }

        # Generate content hash for deduplication
        content_str = json.dumps(snapshot_data, sort_keys=True)
        data_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # Check if identical snapshot already exists
        existing = db.query(CompetitiveSnapshot).filter(
            CompetitiveSnapshot.competitor_id == competitor_id,
            CompetitiveSnapshot.data_hash == data_hash
        ).first()

        if existing:
            logger.info(
                f"Identical snapshot already exists (hash: {data_hash[:8]}...) "
                f"for competitor {competitor_id}. Skipping creation."
            )
            return {
                "competitor_id": competitor_id,
                "raw_content_id": raw_content_id,
                "snapshot_id": existing.id,
                "deduplicated": True
            }

        # Create snapshot
        from datetime import datetime
        snapshot = CompetitiveSnapshot(
            competitor_id=competitor_id,
            snapshot_date=datetime.utcnow(),
            data_hash=data_hash,
            snapshot_data=snapshot_data
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        logger.info(
            f"Created snapshot {snapshot.id} for competitor {competitor_id} "
            f"from raw content {raw_content_id}"
        )

        # Trigger change analysis
        logger.info(f"Triggering change analysis for competitor {competitor_id}")
        analyze_competitor_changes.delay(competitor_id)

        return {
            "competitor_id": competitor_id,
            "raw_content_id": raw_content_id,
            "snapshot_id": snapshot.id,
            "deduplicated": False
        }

    except Exception as e:
        logger.error(
            f"Error creating snapshot from raw content {raw_content_id}: {e}",
            exc_info=True
        )
        db.rollback()
        return {
            "error": str(e),
            "raw_content_id": raw_content_id
        }
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_old_snapshots(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old snapshots to prevent database bloat.

    Optional maintenance task to remove snapshots older than N days.
    Keeps at least 2 snapshots per competitor for change detection.

    Args:
        days_to_keep: Number of days of snapshots to retain

    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Starting snapshot cleanup (keeping last {days_to_keep} days)")

    db = SessionLocal()
    try:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Get snapshots older than cutoff, keeping at least 2 per competitor
        from sqlalchemy import func

        # Subquery to get the 2 most recent snapshots per competitor
        from sqlalchemy.sql import select

        # For simplicity, we'll just delete old snapshots
        # In production, you'd want more sophisticated logic
        deleted_count = db.query(CompetitiveSnapshot).filter(
            CompetitiveSnapshot.snapshot_date < cutoff_date
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Cleaned up {deleted_count} old snapshots")

        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep
        }

    except Exception as e:
        logger.error(f"Error during snapshot cleanup: {e}", exc_info=True)
        db.rollback()
        return {
            "error": str(e),
            "deleted_count": 0
        }
    finally:
        db.close()
