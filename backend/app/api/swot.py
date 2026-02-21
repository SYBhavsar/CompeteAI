"""
SWOT & Threat Assessment API

Endpoints:
- GET  /swot/{competitor_id}/swot
- GET  /swot/{competitor_id}/threat-assessment
- POST /swot/{competitor_id}/regenerate
- GET  /swot/threat-landscape
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.utils.dependencies import get_current_user
from app.models import User, Competitor
from app.models.swot import SWOTAnalysis
from app.models.threat_assessment import ThreatAssessment
from app.schemas.swot import (
    SWOTAnalysisResponse,
    ThreatAssessmentResponse,
    ThreatLandscapeItem,
)
from app.services.strategic_framework_service import StrategicFrameworkService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/swot", tags=["SWOT & Threat Assessment"])


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


@router.get("/threat-landscape", response_model=List[ThreatLandscapeItem])
def get_threat_landscape(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return threat assessments for all competitors owned by the current user."""
    competitors = db.query(Competitor).filter(
        Competitor.user_id == current_user.id
    ).all()

    result = []
    for comp in competitors:
        assessment = db.query(ThreatAssessment).filter(
            ThreatAssessment.competitor_id == comp.id
        ).order_by(ThreatAssessment.updated_at.desc()).first()

        if assessment:
            result.append(ThreatLandscapeItem(
                competitor_id=comp.id,
                competitor_name=comp.name,
                threat_score=assessment.threat_score,
                threat_categories=assessment.threat_categories,
            ))

    return result


@router.get("/{competitor_id}/swot", response_model=SWOTAnalysisResponse)
def get_swot(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the latest SWOT analysis for a competitor."""
    _get_competitor_or_404(competitor_id, current_user, db)

    swot = db.query(SWOTAnalysis).filter(
        SWOTAnalysis.competitor_id == competitor_id
    ).order_by(SWOTAnalysis.analysis_date.desc()).first()

    if not swot:
        raise HTTPException(status_code=404, detail="No SWOT analysis found. Run /regenerate first.")

    return swot


@router.get("/{competitor_id}/threat-assessment", response_model=ThreatAssessmentResponse)
def get_threat_assessment(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the latest threat assessment for a competitor."""
    _get_competitor_or_404(competitor_id, current_user, db)

    assessment = db.query(ThreatAssessment).filter(
        ThreatAssessment.competitor_id == competitor_id
    ).order_by(ThreatAssessment.updated_at.desc()).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="No threat assessment found. Run /regenerate first.")

    return assessment


@router.post("/{competitor_id}/regenerate", response_model=SWOTAnalysisResponse)
def regenerate_swot(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger a fresh SWOT analysis for a competitor (replaces existing)."""
    _get_competitor_or_404(competitor_id, current_user, db)

    service = StrategicFrameworkService()
    swot = service.generate_swot(competitor_id=competitor_id, db=db)

    if not swot:
        raise HTTPException(status_code=500, detail="SWOT generation failed")

    return swot
