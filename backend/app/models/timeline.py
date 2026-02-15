"""
Competitor Timeline Model

Purpose: Track temporal events for timeline visualization
Follows: Single Responsibility Principle (event tracking only)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CompetitorTimeline(Base):
    """
    Temporal event tracking for competitor timeline visualization.

    Stores significant events (launches, partnerships, funding, etc.)
    with source attribution and chronological ordering.
    """
    __tablename__ = "competitor_timeline"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # product_launch, pricing_change, partnership, etc.
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    source_urls = Column(JSON, nullable=False, default=[])  # List of source URLs
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    competitor = relationship("Competitor")
