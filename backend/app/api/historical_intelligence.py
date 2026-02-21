"""
Historical Intelligence API Router

Provides REST API endpoints for historical analysis features:
- Timeline visualization
- Change detection results
- Manual snapshot creation
- Analytics/velocity tracking

Follows: RESTful principles, proper HTTP status codes
"""

import hashlib
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models import User, Competitor
from app.models.competitive_snapshot import CompetitiveSnapshot
from app.models.change_detection import ChangeEvent
from app.models.timeline import CompetitorTimeline
from app.schemas.historical_intelligence import (
    TimelineEventResponse,
    ChangeEventResponse,
    SnapshotCreateRequest,
    SnapshotResponse,
    ChangeVelocityResponse
)
from app.services.historical_analysis_service import HistoricalAnalysisService
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/historical", tags=["Historical Intelligence"])


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/competitors/{competitor_id}/timeline",
    response_model=List[TimelineEventResponse],
    summary="Get competitor timeline"
)
def get_competitor_timeline(
    competitor_id: int,
    limit: int = Query(50, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get temporal timeline of events for a competitor.

    Returns chronological list of significant events (launches, partnerships, etc.)
    ordered by most recent first.
    """
    logger.info(f"Fetching timeline for competitor {competitor_id}, user {current_user.id}")

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    # Get timeline events
    timeline_events = db.query(CompetitorTimeline).filter(
        CompetitorTimeline.competitor_id == competitor_id
    ).order_by(
        desc(CompetitorTimeline.event_date)
    ).offset(offset).limit(limit).all()

    logger.info(f"Found {len(timeline_events)} timeline events for competitor {competitor_id}")
    return timeline_events


@router.get(
    "/competitors/{competitor_id}/changes",
    response_model=List[ChangeEventResponse],
    summary="Get detected changes"
)
def get_competitor_changes(
    competitor_id: int,
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter by last N days"),
    severity: Optional[str] = Query(None, description="Filter by severity: minor, moderate, major, critical"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get change detection results for a competitor.

    Returns list of detected changes with severity, impact, and confidence scores.
    Optionally filter by timeframe (days) or severity level.
    """
    logger.info(f"Fetching changes for competitor {competitor_id}, filters: days={days}, severity={severity}")

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    # Build query
    query = db.query(ChangeEvent).filter(
        ChangeEvent.competitor_id == competitor_id
    )

    # Apply filters
    if days:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(ChangeEvent.created_at >= cutoff_date)

    if severity:
        query = query.filter(ChangeEvent.severity == severity)

    # Execute query
    changes = query.order_by(
        desc(ChangeEvent.created_at)
    ).offset(offset).limit(limit).all()

    logger.info(f"Found {len(changes)} changes for competitor {competitor_id}")
    return changes


@router.post(
    "/competitors/{competitor_id}/snapshot",
    response_model=SnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create manual snapshot"
)
def create_competitor_snapshot(
    competitor_id: int,
    request: SnapshotCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a manual snapshot of competitor state.

    Useful for on-demand analysis. Automatically triggers change detection
    if previous snapshots exist.
    """
    logger.info(f"Creating snapshot for competitor {competitor_id}, user {current_user.id}")

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    try:
        # Generate content hash for deduplication
        content_str = json.dumps(request.snapshot_data, sort_keys=True)
        data_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # Create snapshot
        snapshot = CompetitiveSnapshot(
            competitor_id=competitor_id,
            snapshot_date=datetime.now(timezone.utc),
            data_hash=data_hash,
            snapshot_data=request.snapshot_data
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        logger.info(f"Created snapshot {snapshot.id} for competitor {competitor_id}")

        # Trigger change detection if previous snapshot exists
        previous_snapshot = db.query(CompetitiveSnapshot).filter(
            CompetitiveSnapshot.competitor_id == competitor_id,
            CompetitiveSnapshot.id != snapshot.id
        ).order_by(
            desc(CompetitiveSnapshot.snapshot_date)
        ).first()

        if previous_snapshot:
            logger.info(f"Triggering change detection between snapshots {previous_snapshot.id} and {snapshot.id}")
            try:
                analysis_service = HistoricalAnalysisService()
                changes = analysis_service.detect_changes(
                    competitor_id=competitor_id,
                    before_snapshot=previous_snapshot,
                    after_snapshot=snapshot,
                    db=db
                )
                logger.info(f"Detected {len(changes)} changes")
            except Exception as e:
                logger.error(f"Change detection failed: {e}", exc_info=True)
                # Don't fail the request if analysis fails

        return snapshot

    except Exception as e:
        logger.error(f"Error creating snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create snapshot"
        )


@router.get(
    "/analytics/change-velocity",
    response_model=List[ChangeVelocityResponse],
    summary="Get change velocity analytics"
)
def get_change_velocity(
    days: int = Query(30, ge=1, le=365, description="Timeframe for analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get rate of change across all competitors.

    Analytics endpoint showing which competitors are changing most frequently
    and with what severity. Useful for dashboard visualization.
    """
    logger.info(f"Fetching change velocity analytics for user {current_user.id}, days={days}")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Query change counts and average severity by competitor
    results = db.query(
        Competitor.id.label("competitor_id"),
        Competitor.name.label("competitor_name"),
        Competitor.domain.label("competitor_domain"),
        func.count(ChangeEvent.id).label("change_count"),
        func.avg(
            case(
                (ChangeEvent.severity == "minor", 1),
                (ChangeEvent.severity == "moderate", 2),
                (ChangeEvent.severity == "major", 3),
                (ChangeEvent.severity == "critical", 4),
                else_=0
            )
        ).label("avg_severity_score")
    ).join(
        ChangeEvent,
        Competitor.id == ChangeEvent.competitor_id
    ).filter(
        Competitor.user_id == current_user.id,
        ChangeEvent.created_at >= cutoff_date
    ).group_by(
        Competitor.id,
        Competitor.name,
        Competitor.domain
    ).all()

    # Format response
    velocity_data = []
    for row in results:
        # Map numeric severity back to string
        avg_severity = "minor"
        if row.avg_severity_score:
            if row.avg_severity_score >= 3.5:
                avg_severity = "critical"
            elif row.avg_severity_score >= 2.5:
                avg_severity = "major"
            elif row.avg_severity_score >= 1.5:
                avg_severity = "moderate"

        velocity_data.append({
            "competitor_id": row.competitor_id,
            "competitor_name": row.competitor_name,
            "competitor_domain": row.competitor_domain,
            "change_count": row.change_count,
            "average_severity": avg_severity,
            "timeframe_days": days
        })

    logger.info(f"Found velocity data for {len(velocity_data)} competitors")
    return velocity_data
