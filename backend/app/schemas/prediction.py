"""
Prediction Schemas

Pydantic models for predictive analytics API.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PredictionResponse(BaseModel):
    id: int
    competitor_id: int
    prediction_type: str
    confidence: float
    timeframe: str
    reasoning: str
    suggested_action: Optional[str]
    outcome: str
    predicted_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class ValidateOutcomeRequest(BaseModel):
    outcome: str  # correct | incorrect


class AccuracyReportResponse(BaseModel):
    competitor_id: int
    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
    pending_predictions: int
    accuracy_rate: float  # correct / (correct + incorrect), 0.0 if no resolved predictions
