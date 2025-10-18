from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ProcessedInsights(Base):
    """Processed insights from AI analysis of raw content"""
    __tablename__ = "processed_insights"

    id = Column(Integer, primary_key=True, index=True)
    raw_content_id = Column(Integer, ForeignKey("raw_content.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=True)  # List of key points
    sentiment = Column(String(20), nullable=False)  # positive, negative, neutral
    insights = Column(Text, nullable=True)  # Detailed business insights
    quality_score = Column(Float, nullable=True)  # Quality score 0.0-1.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    raw_content = relationship("RawContent", back_populates="processed_insights")