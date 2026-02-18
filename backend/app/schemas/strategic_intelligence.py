"""
Strategic Intelligence Schemas

Pydantic models for strategic events, entities, and relationships API.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Strategic Event Schemas
class StrategicEventResponse(BaseModel):
    """Response model for strategic event"""
    id: int
    competitor_id: int
    event_category: str
    confidence: float
    event_date: datetime
    title: str
    description: str
    entities_involved: Dict[str, Any]
    strategic_implications: str
    source_insights: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# Entity Schemas
class EntityResponse(BaseModel):
    """Response model for entity"""
    id: int
    entity_type: str
    name: str
    aliases: List[str]
    first_mentioned: datetime
    competitor_id: int
    entity_metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# Entity Relationship Schemas
class EntityRelationshipResponse(BaseModel):
    """Response model for entity relationship"""
    id: int
    source_entity_id: int
    target_entity_id: int
    relationship_type: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


# Knowledge Graph Schemas
class KnowledgeGraphNode(BaseModel):
    """Node in knowledge graph"""
    id: int
    entity_type: str
    name: str


class KnowledgeGraphEdge(BaseModel):
    """Edge in knowledge graph"""
    source: int
    target: int
    relationship_type: str
    confidence: float


class KnowledgeGraphResponse(BaseModel):
    """Response model for knowledge graph"""
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]


# Analytics Schemas
class EventSummaryResponse(BaseModel):
    """Event counts by category"""
    market_entry: int = 0
    acquisition: int = 0
    partnership: int = 0
    product_launch: int = 0
    pricing_change: int = 0
    leadership_change: int = 0
    funding: int = 0


class EntitySummaryResponse(BaseModel):
    """Entity counts by type"""
    product: int = 0
    person: int = 0
    company: int = 0
    technology: int = 0
    partnership: int = 0


class TimelineEventResponse(BaseModel):
    """Simplified event for timeline"""
    id: int
    event_category: str
    event_date: datetime
    title: str
    confidence: float

    class Config:
        from_attributes = True
