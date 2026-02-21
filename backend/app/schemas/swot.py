"""Pydantic schemas for SWOT & Threat Assessment API."""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class SWOTAnalysisResponse(BaseModel):
    id: int
    competitor_id: int
    analysis_date: datetime
    strengths: List[Dict[str, Any]]
    weaknesses: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    overall_assessment: str
    confidence_score: float

    class Config:
        from_attributes = True


class ThreatAssessmentResponse(BaseModel):
    id: int
    competitor_id: int
    threat_score: float
    threat_categories: Dict[str, Any]
    assessment_text: str
    mitigation_recommendations: List[str]
    updated_at: datetime

    class Config:
        from_attributes = True


class ThreatLandscapeItem(BaseModel):
    competitor_id: int
    competitor_name: str
    threat_score: float
    threat_categories: Dict[str, Any]

    class Config:
        from_attributes = True
