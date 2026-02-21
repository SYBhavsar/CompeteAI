"""
Strategic Intelligence Schemas

Pydantic models for strategic events, entities, and relationships API.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime


class StrategicEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    name: str
    aliases: List[str]
    first_mentioned: datetime
    competitor_id: int
    entity_metadata: Dict[str, Any]
    created_at: datetime


class EntityRelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_entity_id: int
    target_entity_id: int
    relationship_type: str
    confidence: float
    created_at: datetime


class KnowledgeGraphNode(BaseModel):
    id: int
    entity_type: str
    name: str


class KnowledgeGraphEdge(BaseModel):
    source: int
    target: int
    relationship_type: str
    confidence: float


class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]


class EventSummaryResponse(BaseModel):
    market_entry: int = 0
    acquisition: int = 0
    partnership: int = 0
    product_launch: int = 0
    pricing_change: int = 0
    leadership_change: int = 0
    funding: int = 0


class EntitySummaryResponse(BaseModel):
    product: int = 0
    person: int = 0
    company: int = 0
    technology: int = 0
    partnership: int = 0


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_category: str
    event_date: datetime
    title: str
    confidence: float
