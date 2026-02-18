"""
Strategic Event Model

Purpose: Track high-value strategic moves by competitors
Categories: Market entry, M&A, partnerships, product launches, funding, leadership
Follows: Single Responsibility Principle
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class StrategicEvent(Base):
    """
    High-value strategic moves detected from competitor activity.

    Tracks major competitive events that require strategic response:
    - Market entries (geographic expansion, new verticals)
    - Acquisitions and mergers
    - Strategic partnerships
    - Product launches
    - Pricing changes
    - Leadership changes (C-suite hires)
    - Funding rounds

    Used for strategic planning and competitive response.
    """
    __tablename__ = "strategic_events"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    event_category = Column(String, nullable=False, index=True)  # market_entry, acquisition, partnership, etc.
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0 - AI confidence in detection
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)  # Estimated actual date of event
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    entities_involved = Column(JSON, nullable=False, default={})  # Links to Entity records or raw entity data
    strategic_implications = Column(Text, nullable=False)  # What this means for our business
    source_insights = Column(JSON, nullable=False, default={})  # Links to ProcessedInsights that support this
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    competitor = relationship("Competitor", back_populates="strategic_events")
