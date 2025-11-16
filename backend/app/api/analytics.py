from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import csv
import io
import json
import logging

logger = logging.getLogger(__name__)


from app.core.database import SessionLocal
from app.models import User, Competitor, ProcessedInsights, RawContent, DataSource
from app.schemas.analytics import (
    TrendsResponse,
    TrendPoint,
    CompetitorSummary,
    SentimentDistribution,
    ComparisonResponse,
    CompetitorComparison,
    QualityDistribution
)
from app.utils.dependencies import get_current_user

router = APIRouter()


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/analytics/trends", response_model=TrendsResponse)
def get_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    competitor_id: Optional[int] = Query(None, description="Filter by competitor"),
    metric: str = Query("count", description="Metric to analyze: count or sentiment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trend analysis over time"""
    logger.info(f"User {current_user.id} requesting trends for {days} days. Competitor: {competitor_id}, Metric: {metric}")
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        query = db.query(
            func.date(ProcessedInsights.created_at),
            func.count(ProcessedInsights.id),
            func.avg(
                case(
                    (ProcessedInsights.sentiment == 'positive', 1),
                    (ProcessedInsights.sentiment == 'negative', -1),
                    else_=0
                )
            )
        ).join(RawContent).join(DataSource).join(Competitor).filter(
            Competitor.user_id == current_user.id,
            ProcessedInsights.created_at >= start_date
        )

        if competitor_id:
            query = query.filter(Competitor.id == competitor_id)

        query = query.group_by(func.date(ProcessedInsights.created_at)).order_by(func.date(ProcessedInsights.created_at))
        
        results = query.all()
        
        trends = [
            TrendPoint(date=r[0].isoformat(), count=r[1], sentiment_avg=r[2] if metric == 'sentiment' else None)
            for r in results
        ]
        
        total_insights = sum(t.count for t in trends)
        logger.info(f"Successfully generated trends for user {current_user.id}. Total insights: {total_insights}")

        return TrendsResponse(trends=trends, period=f"{days} days", total_insights=total_insights)
    except Exception as e:
        logger.error(f"Error getting trends for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/analytics/summary/{competitor_id}", response_model=CompetitorSummary)
def get_competitor_summary(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics for a competitor"""
    logger.info(f"User {current_user.id} requesting summary for competitor {competitor_id}.")
    
    competitor = db.query(Competitor).filter_by(id=competitor_id, user_id=current_user.id).first()
    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    try:
        insights_query = db.query(ProcessedInsights).join(RawContent).join(DataSource).filter(
            DataSource.competitor_id == competitor_id
        )
        
        total_insights = insights_query.count()
        
        sentiment_dist = insights_query.group_by(ProcessedInsights.sentiment).with_entities(
            ProcessedInsights.sentiment, func.count(ProcessedInsights.id)
        ).all()
        sentiment_counts = {s: c for s, c in sentiment_dist}

        avg_quality = insights_query.with_entities(func.avg(ProcessedInsights.quality_score)).scalar()

        recent_insights = insights_query.order_by(ProcessedInsights.created_at.desc()).limit(10).all()
        recent_activity = [
            {
                "summary": insight.summary,
                "sentiment": insight.sentiment,
                "created_at": insight.created_at.isoformat()
            }
            for insight in recent_insights
        ]

        logger.info(f"Successfully generated summary for competitor {competitor_id}.")
        return CompetitorSummary(
            competitor_id=competitor_id,
            competitor_name=competitor.name,
            total_insights=total_insights,
            sentiment_distribution=SentimentDistribution(
                positive=sentiment_counts.get('positive', 0),
                negative=sentiment_counts.get('negative', 0),
                neutral=sentiment_counts.get('neutral', 0)
            ),
            average_quality_score=avg_quality,
            recent_activity=recent_activity
        )
    except Exception as e:
        logger.error(f"Error generating summary for competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/analytics/comparison", response_model=ComparisonResponse)
def compare_competitors(
    competitor_ids: str = Query(..., description="Comma-separated competitor IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare multiple competitors"""
    logger.info(f"User {current_user.id} comparing competitors: {competitor_ids}")
    try:
        ids = [int(id.strip()) for id in competitor_ids.split(",")]
        
        # Verify all competitors belong to the user
        user_competitors = db.query(Competitor.id).filter(
            Competitor.user_id == current_user.id,
            Competitor.id.in_(ids)
        ).all()
        
        valid_ids = {c[0] for c in user_competitors}
        if len(valid_ids) != len(ids):
            logger.warning(f"User {current_user.id} attempted to compare unauthorized or non-existent competitors.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="One or more competitors not found or not authorized.")

        results = db.query(
            DataSource.competitor_id,
            func.count(ProcessedInsights.id),
            func.avg(case((ProcessedInsights.sentiment == 'positive', 1.0), else_=0.0)),
            func.avg(ProcessedInsights.quality_score)
        ).select_from(Competitor).join(DataSource).join(RawContent).join(ProcessedInsights).filter(
            Competitor.id.in_(valid_ids)
        ).group_by(DataSource.competitor_id).all()

        competitor_map = {c.id: c.name for c in db.query(Competitor).filter(Competitor.id.in_(valid_ids)).all()}

        comparisons = [
            CompetitorComparison(
                competitor_id=r[0],
                competitor_name=competitor_map.get(r[0]),
                total_insights=r[1],
                positive_ratio=round(r[2], 2) if r[2] is not None else 0.0,
                average_quality=round(r[3], 2) if r[3] is not None else 0.0
            ) for r in results
        ]
        
        logger.info(f"Successfully compared {len(comparisons)} competitors for user {current_user.id}.")
        return ComparisonResponse(comparisons=comparisons)
    except Exception as e:
        logger.error(f"Error comparing competitors for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/analytics/export")
def export_insights(
    competitor_id: Optional[int] = Query(None, description="Filter by competitor"),
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export insights data"""
    logger.info(f"User {current_user.id} exporting insights. Competitor: {competitor_id}, Format: {format}")
    try:
        query = db.query(ProcessedInsights).join(RawContent).join(DataSource).join(Competitor).filter(
            Competitor.user_id == current_user.id
        )

        if competitor_id:
            query = query.filter(Competitor.id == competitor_id)

        insights = query.all()
        logger.info(f"Exporting {len(insights)} insights for user {current_user.id}.")

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Summary", "Sentiment", "Quality Score", "URL", "Created At"])
            for i in insights:
                writer.writerow([i.id, i.summary, i.sentiment, i.quality_score, i.raw_content.url, i.created_at.isoformat()])
            output.seek(0)
            return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=insights_{datetime.now().strftime('%Y%m%d')}.csv"})
        else:
            data = [{"id": i.id, "summary": i.summary, "sentiment": i.sentiment, "insights": i.insights, "quality_score": i.quality_score, "url": i.raw_content.url, "created_at": i.created_at.isoformat()} for i in insights]
            return data
    except Exception as e:
        logger.error(f"Error exporting insights for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/analytics/quality-distribution", response_model=QualityDistribution)
def get_quality_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality score distribution for the user's insights"""
    logger.debug(f"User {current_user.id} requesting quality distribution.")
    try:
        # Efficiently calculate distribution in the database
        high_quality = func.count(case((ProcessedInsights.quality_score >= 0.7, 1))).label("high")
        medium_quality = func.count(case(((ProcessedInsights.quality_score >= 0.4) & (ProcessedInsights.quality_score < 0.7), 1))).label("medium")
        low_quality = func.count(case((ProcessedInsights.quality_score < 0.4, 1))).label("low")

        distribution = db.query(high_quality, medium_quality, low_quality).join(RawContent).join(DataSource).join(Competitor).filter(
            Competitor.user_id == current_user.id
        ).first()
        
        dist_dict = {"high": distribution[0], "medium": distribution[1], "low": distribution[2]}
        logger.info(f"Quality distribution for user {current_user.id}: {dist_dict}")
        
        return QualityDistribution(**dist_dict)
    except Exception as e:
        logger.error(f"Error getting quality distribution for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")