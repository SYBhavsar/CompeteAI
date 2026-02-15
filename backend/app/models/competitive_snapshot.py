"""
Competitive Snapshot Model

Purpose: Store point-in-time snapshots of competitor state for historical analysis
Follows: Single Responsibility Principle (data storage only)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CompetitiveSnapshot(Base):
    """
    Point-in-time snapshot of competitor state.

    Used for temporal analysis and change detection.
    Stores flexible metadata in JSON for various competitor attributes.
    """
    __tablename__ = "competitive_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)
    data_hash = Column(String, nullable=False, index=True)  # Content-addressable hash
    snapshot_data = Column(JSON, nullable=False, default={})  # Flexible schema for competitor attributes
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    competitor = relationship("Competitor")
