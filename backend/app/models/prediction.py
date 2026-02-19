"""
Competitor Prediction Model

Purpose: Track AI-generated predictions about future competitor moves.
Supports outcome validation for accuracy tracking.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CompetitorPrediction(Base):
    """
    AI-generated prediction of a future competitor strategic move.

    Predictions are generated from historical StrategicEvent patterns + RAG context.
    Outcomes can be validated (correct/incorrect) to track model accuracy.
    """
    __tablename__ = "competitor_predictions"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    prediction_type = Column(String, nullable=False, index=True)  # pricing_change, product_launch, etc.
    confidence = Column(Float, nullable=False)                    # 0.0 - 1.0
    timeframe = Column(String, nullable=False)                    # 30_days, 60_days, 90_days, 180_days
    reasoning = Column(Text, nullable=False)                      # LLM reasoning behind prediction
    suggested_action = Column(Text, nullable=True)                # Recommended response for our team
    outcome = Column(String, nullable=False, default="pending")   # pending | correct | incorrect
    predicted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # Set when outcome validated

    # Relationships
    competitor = relationship("Competitor", back_populates="predictions")
