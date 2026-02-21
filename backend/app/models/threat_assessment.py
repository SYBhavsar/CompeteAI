"""
Threat Assessment Model

Purpose: Store competitive threat scoring per competitor.
threat_score is a weighted 0-100 aggregate.
threat_categories breaks it down by dimension.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ThreatAssessment(Base):
    __tablename__ = "threat_assessments"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    threat_score = Column(Float, nullable=False)           # 0-100 weighted aggregate
    threat_categories = Column(JSON, nullable=False)       # {pricing, innovation, market_share, resource_strength, partnerships}
    assessment_text = Column(Text, nullable=False, default="")
    mitigation_recommendations = Column(JSON, nullable=False, default=[])
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    competitor = relationship("Competitor", back_populates="threat_assessments")
