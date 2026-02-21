"""
SWOT Analysis Model

Purpose: Store AI-generated SWOT analysis for a competitor.
Each quadrant is a JSON array of {description, evidence, impact_score} items.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SWOTAnalysis(Base):
    __tablename__ = "swot_analyses"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    analysis_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    strengths = Column(JSON, nullable=False, default=[])
    weaknesses = Column(JSON, nullable=False, default=[])
    opportunities = Column(JSON, nullable=False, default=[])
    threats = Column(JSON, nullable=False, default=[])
    overall_assessment = Column(Text, nullable=False, default="")
    confidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    competitor = relationship("Competitor", back_populates="swot_analyses")
