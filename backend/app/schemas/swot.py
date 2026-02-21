"""Pydantic schemas for SWOT & Threat Assessment API."""

from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime


class SWOTAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    analysis_date: datetime
    strengths: List[Dict[str, Any]]
    weaknesses: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    overall_assessment: str
    confidence_score: float


class ThreatAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    threat_score: float
    threat_categories: Dict[str, Any]
    assessment_text: str
    mitigation_recommendations: List[str]
    updated_at: datetime


class ThreatLandscapeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    competitor_id: int
    competitor_name: str
    threat_score: float
    threat_categories: Dict[str, Any]
