"""
Change Detection Model

Purpose: Track detected changes between competitor snapshots
Follows: Single Responsibility Principle (change event storage only)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ChangeEvent(Base):
    """
    Detected changes between competitor snapshots.

    Tracks what changed, severity, and strategic impact.
    Used for alerting and trend analysis.
    """
    __tablename__ = "change_events"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    change_type = Column(String, nullable=False, index=True)  # pricing, messaging, positioning, partnership, leadership
    severity = Column(String, nullable=False, index=True)  # minor, moderate, major, critical
    before_snapshot_id = Column(Integer, ForeignKey("competitive_snapshots.id"), nullable=False)
    after_snapshot_id = Column(Integer, ForeignKey("competitive_snapshots.id"), nullable=False)
    change_summary = Column(Text, nullable=False)
    strategic_impact = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    competitor = relationship("Competitor")
    before_snapshot = relationship("CompetitiveSnapshot", foreign_keys=[before_snapshot_id])
    after_snapshot = relationship("CompetitiveSnapshot", foreign_keys=[after_snapshot_id])
