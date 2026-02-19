"""
Predictive Analytics API

Endpoints for AI-powered predictions of future competitor moves.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.utils.dependencies import get_current_user
from app.models import User, Competitor
from app.models.prediction import CompetitorPrediction
from app.schemas.prediction import (
    PredictionResponse,
    ValidateOutcomeRequest,
    AccuracyReportResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictive", tags=["Predictive Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_competitor_or_404(competitor_id: int, user: User, db: Session) -> Competitor:
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == user.id
    ).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@router.get(
    "/{competitor_id}/predictions",
    response_model=List[PredictionResponse]
)
def get_predictions(
    competitor_id: int,
    status: Optional[str] = Query(None, description="Filter by outcome status (pending/correct/incorrect)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all predictions for a competitor, optionally filtered by status."""
    _get_competitor_or_404(competitor_id, current_user, db)

    query = db.query(CompetitorPrediction).filter(
        CompetitorPrediction.competitor_id == competitor_id
    )

    if status:
        query = query.filter(CompetitorPrediction.outcome == status)

    return query.order_by(CompetitorPrediction.predicted_at.desc()).all()


@router.post(
    "/predictions/{prediction_id}/validate-outcome",
    response_model=PredictionResponse
)
def validate_outcome(
    prediction_id: int,
    body: ValidateOutcomeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate whether a prediction came true (correct/incorrect)."""
    prediction = db.query(CompetitorPrediction).filter(
        CompetitorPrediction.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # Ensure user owns the competitor this prediction belongs to
    _get_competitor_or_404(prediction.competitor_id, current_user, db)

    if body.outcome not in ("correct", "incorrect"):
        raise HTTPException(status_code=400, detail="outcome must be 'correct' or 'incorrect'")

    from datetime import datetime
    prediction.outcome = body.outcome
    prediction.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(prediction)
    return prediction


@router.get(
    "/{competitor_id}/accuracy-report",
    response_model=AccuracyReportResponse
)
def get_accuracy_report(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prediction accuracy statistics for a competitor."""
    _get_competitor_or_404(competitor_id, current_user, db)

    all_preds = db.query(CompetitorPrediction).filter(
        CompetitorPrediction.competitor_id == competitor_id
    ).all()

    total = len(all_preds)
    correct = sum(1 for p in all_preds if p.outcome == "correct")
    incorrect = sum(1 for p in all_preds if p.outcome == "incorrect")
    pending = sum(1 for p in all_preds if p.outcome == "pending")

    resolved = correct + incorrect
    accuracy_rate = correct / resolved if resolved > 0 else 0.0

    return AccuracyReportResponse(
        competitor_id=competitor_id,
        total_predictions=total,
        correct_predictions=correct,
        incorrect_predictions=incorrect,
        pending_predictions=pending,
        accuracy_rate=accuracy_rate
    )
