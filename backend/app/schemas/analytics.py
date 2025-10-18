from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class TrendPoint(BaseModel):
    """Single data point in a trend"""
    date: str
    count: int
    sentiment_avg: Optional[float] = None


class TrendsResponse(BaseModel):
    """Response for trends analysis"""
    trends: List[TrendPoint]
    period: str
    total_insights: int


class SentimentDistribution(BaseModel):
    """Sentiment distribution stats"""
    positive: int
    negative: int
    neutral: int


class CompetitorSummary(BaseModel):
    """Summary statistics for a competitor"""
    competitor_id: int
    competitor_name: str
    total_insights: int
    sentiment_distribution: SentimentDistribution
    average_quality_score: Optional[float]
    recent_activity: List[Dict[str, Any]]


class CompetitorComparison(BaseModel):
    """Comparison data for a competitor"""
    competitor_id: int
    competitor_name: str
    total_insights: int
    positive_ratio: float
    average_quality: float


class ComparisonResponse(BaseModel):
    """Response for competitor comparison"""
    comparisons: List[CompetitorComparison]


class QualityDistribution(BaseModel):
    """Quality score distribution"""
    high: int
    medium: int
    low: int