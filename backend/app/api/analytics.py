from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List
import csv
import io
import json

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
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Build query
    query = db.query(ProcessedInsights).join(
        RawContent, ProcessedInsights.raw_content_id == RawContent.id
    ).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).join(
        Competitor, DataSource.competitor_id == Competitor.id
    ).filter(
        Competitor.user_id == current_user.id,
        ProcessedInsights.created_at >= start_date
    )

    # Apply competitor filter if provided
    if competitor_id:
        query = query.filter(Competitor.id == competitor_id)

    insights = query.all()

    # Group by date
    trends_by_date = {}
    for insight in insights:
        date_key = insight.created_at.date().isoformat()
        if date_key not in trends_by_date:
            trends_by_date[date_key] = {"count": 0, "sentiments": []}

        trends_by_date[date_key]["count"] += 1
        if metric == "sentiment":
            sentiment_value = 1 if insight.sentiment == "positive" else (-1 if insight.sentiment == "negative" else 0)
            trends_by_date[date_key]["sentiments"].append(sentiment_value)

    # Format response
    trends = []
    for date_str in sorted(trends_by_date.keys()):
        data = trends_by_date[date_str]
        sentiment_avg = None
        if metric == "sentiment" and data["sentiments"]:
            sentiment_avg = sum(data["sentiments"]) / len(data["sentiments"])

        trends.append(TrendPoint(
            date=date_str,
            count=data["count"],
            sentiment_avg=sentiment_avg
        ))

    return TrendsResponse(
        trends=trends,
        period=f"{days} days",
        total_insights=len(insights)
    )


@router.get("/analytics/summary/{competitor_id}", response_model=CompetitorSummary)
def get_competitor_summary(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics for a competitor"""
    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Get insights
    insights = db.query(ProcessedInsights).join(
        RawContent, ProcessedInsights.raw_content_id == RawContent.id
    ).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).filter(
        DataSource.competitor_id == competitor_id
    ).all()

    # Calculate sentiment distribution
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    quality_scores = []

    for insight in insights:
        sentiment_counts[insight.sentiment] = sentiment_counts.get(insight.sentiment, 0) + 1
        if insight.quality_score is not None:
            quality_scores.append(insight.quality_score)

    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

    # Get recent activity (last 5 insights)
    recent = sorted(insights, key=lambda x: x.created_at, reverse=True)[:5]
    recent_activity = [
        {
            "summary": insight.summary,
            "sentiment": insight.sentiment,
            "created_at": insight.created_at.isoformat()
        }
        for insight in recent
    ]

    return CompetitorSummary(
        competitor_id=competitor_id,
        competitor_name=competitor.name,
        total_insights=len(insights),
        sentiment_distribution=SentimentDistribution(**sentiment_counts),
        average_quality_score=avg_quality,
        recent_activity=recent_activity
    )


@router.get("/analytics/comparison", response_model=ComparisonResponse)
def compare_competitors(
    competitor_ids: str = Query(..., description="Comma-separated competitor IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare multiple competitors"""
    # Parse competitor IDs
    ids = [int(id.strip()) for id in competitor_ids.split(",")]

    comparisons = []

    for competitor_id in ids:
        competitor = db.query(Competitor).filter(
            Competitor.id == competitor_id,
            Competitor.user_id == current_user.id
        ).first()

        if not competitor:
            continue

        # Get insights
        insights = db.query(ProcessedInsights).join(
            RawContent, ProcessedInsights.raw_content_id == RawContent.id
        ).join(
            DataSource, RawContent.data_source_id == DataSource.id
        ).filter(
            DataSource.competitor_id == competitor_id
        ).all()

        if not insights:
            comparisons.append(CompetitorComparison(
                competitor_id=competitor_id,
                competitor_name=competitor.name,
                total_insights=0,
                positive_ratio=0.0,
                average_quality=0.0
            ))
            continue

        # Calculate metrics
        positive_count = sum(1 for i in insights if i.sentiment == "positive")
        positive_ratio = positive_count / len(insights) if insights else 0

        quality_scores = [i.quality_score for i in insights if i.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        comparisons.append(CompetitorComparison(
            competitor_id=competitor_id,
            competitor_name=competitor.name,
            total_insights=len(insights),
            positive_ratio=round(positive_ratio, 2),
            average_quality=round(avg_quality, 2)
        ))

    return ComparisonResponse(comparisons=comparisons)


@router.get("/analytics/export")
def export_insights(
    competitor_id: Optional[int] = Query(None, description="Filter by competitor"),
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export insights data"""
    # Build query
    query = db.query(ProcessedInsights).join(
        RawContent, ProcessedInsights.raw_content_id == RawContent.id
    ).join(
        DataSource, RawContent.data_source_id == DataSource.id
    ).join(
        Competitor, DataSource.competitor_id == Competitor.id
    ).filter(
        Competitor.user_id == current_user.id
    )

    if competitor_id:
        query = query.filter(Competitor.id == competitor_id)

    insights = query.all()

    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Summary", "Sentiment", "Quality Score", "Created At"])

        for insight in insights:
            writer.writerow([
                insight.id,
                insight.summary,
                insight.sentiment,
                insight.quality_score or "",
                insight.created_at.isoformat()
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=insights.csv"}
        )
    else:
        # Generate JSON
        data = [
            {
                "id": insight.id,
                "summary": insight.summary,
                "sentiment": insight.sentiment,
                "insights": insight.insights,
                "quality_score": insight.quality_score,
                "created_at": insight.created_at.isoformat()
            }
            for insight in insights
        ]

        return data


@router.get("/analytics/quality-distribution", response_model=QualityDistribution)
def get_quality_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality score distribution"""
    from app.services.quality_scoring_service import QualityScoringService

    quality_service = QualityScoringService()
    distribution = quality_service.get_quality_distribution(db)

    return QualityDistribution(**distribution)