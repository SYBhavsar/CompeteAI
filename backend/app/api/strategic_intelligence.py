"""
Strategic Intelligence API

Endpoints for strategic events, entities, and knowledge graph.
Provides competitive intelligence on high-value strategic moves.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import SessionLocal
from app.utils.dependencies import get_current_user
from app.models import User, Competitor
from app.models.strategic_event import StrategicEvent
from app.models.entity import Entity
from app.models.entity_relationship import EntityRelationship
from app.schemas.strategic_intelligence import (
    StrategicEventResponse,
    EntityResponse,
    EntityRelationshipResponse,
    KnowledgeGraphResponse,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    EventSummaryResponse,
    EntitySummaryResponse,
    TimelineEventResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategic", tags=["Strategic Intelligence"])


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Strategic Events Endpoints
@router.get(
    "/competitors/{competitor_id}/events",
    response_model=List[StrategicEventResponse]
)
def get_strategic_events(
    competitor_id: int,
    category: Optional[str] = Query(None, description="Filter by event category"),
    days: Optional[int] = Query(None, description="Filter events from last N days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get strategic events for a competitor.

    Filters:
    - category: market_entry, acquisition, partnership, product_launch,
                pricing_change, leadership_change, funding
    - days: Only return events from last N days
    """
    logger.info(
        f"User {current_user.id} fetching strategic events for competitor {competitor_id}"
    )

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Build query
    query = db.query(StrategicEvent).filter(
        StrategicEvent.competitor_id == competitor_id
    )

    # Apply category filter
    if category:
        query = query.filter(StrategicEvent.event_category == category)

    # Apply date filter
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(StrategicEvent.event_date >= cutoff_date)

    # Order by date (newest first)
    events = query.order_by(StrategicEvent.event_date.desc()).all()

    logger.info(f"Found {len(events)} strategic events")
    return events


# Entities Endpoints
@router.get(
    "/competitors/{competitor_id}/entities",
    response_model=List[EntityResponse]
)
def get_entities(
    competitor_id: int,
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get entities for a competitor.

    Filters:
    - entity_type: product, person, company, technology, partnership
    """
    logger.info(
        f"User {current_user.id} fetching entities for competitor {competitor_id}"
    )

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"Competitor {competitor_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Build query
    query = db.query(Entity).filter(Entity.competitor_id == competitor_id)

    # Apply type filter
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)

    # Order by first mentioned (newest first)
    entities = query.order_by(Entity.first_mentioned.desc()).all()

    logger.info(f"Found {len(entities)} entities")
    return entities


@router.get(
    "/entities/{entity_id}",
    response_model=EntityResponse
)
def get_entity(
    entity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get entity details by ID.
    """
    logger.info(f"User {current_user.id} fetching entity {entity_id}")

    # Get entity
    entity = db.query(Entity).filter(Entity.id == entity_id).first()

    if not entity:
        logger.warning(f"Entity {entity_id} not found")
        raise HTTPException(status_code=404, detail="Entity not found")

    # Verify entity's competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == entity.competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        logger.warning(f"User {current_user.id} unauthorized for entity {entity_id}")
        raise HTTPException(status_code=403, detail="Unauthorized")

    return entity


# Entity Relationships Endpoints
@router.get(
    "/entities/{entity_id}/relationships",
    response_model=List[EntityRelationshipResponse]
)
def get_entity_relationships(
    entity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get relationships for an entity.

    Returns both outgoing and incoming relationships.
    """
    logger.info(f"User {current_user.id} fetching relationships for entity {entity_id}")

    # Verify entity belongs to user's competitor
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    competitor = db.query(Competitor).filter(
        Competitor.id == entity.competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Get relationships (both directions)
    relationships = db.query(EntityRelationship).filter(
        (EntityRelationship.source_entity_id == entity_id) |
        (EntityRelationship.target_entity_id == entity_id)
    ).all()

    logger.info(f"Found {len(relationships)} relationships")
    return relationships


@router.get(
    "/competitors/{competitor_id}/knowledge-graph",
    response_model=KnowledgeGraphResponse
)
def get_knowledge_graph(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get knowledge graph for a competitor.

    Returns nodes (entities) and edges (relationships).
    """
    logger.info(
        f"User {current_user.id} fetching knowledge graph for competitor {competitor_id}"
    )

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Get all entities (nodes)
    entities = db.query(Entity).filter(Entity.competitor_id == competitor_id).all()

    # Get all relationships (edges) for these entities
    entity_ids = [e.id for e in entities]
    relationships = db.query(EntityRelationship).filter(
        (EntityRelationship.source_entity_id.in_(entity_ids)) |
        (EntityRelationship.target_entity_id.in_(entity_ids))
    ).all()

    # Build graph response
    nodes = [
        KnowledgeGraphNode(
            id=e.id,
            entity_type=e.entity_type,
            name=e.name
        )
        for e in entities
    ]

    edges = [
        KnowledgeGraphEdge(
            source=r.source_entity_id,
            target=r.target_entity_id,
            relationship_type=r.relationship_type,
            confidence=r.confidence
        )
        for r in relationships
    ]

    logger.info(f"Knowledge graph: {len(nodes)} nodes, {len(edges)} edges")

    return KnowledgeGraphResponse(nodes=nodes, edges=edges)


# Analytics Endpoints
@router.get(
    "/competitors/{competitor_id}/analytics/event-summary",
    response_model=EventSummaryResponse
)
def get_event_summary(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get event counts by category.
    """
    logger.info(
        f"User {current_user.id} fetching event summary for competitor {competitor_id}"
    )

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Count events by category
    results = db.query(
        StrategicEvent.event_category,
        func.count(StrategicEvent.id).label("count")
    ).filter(
        StrategicEvent.competitor_id == competitor_id
    ).group_by(
        StrategicEvent.event_category
    ).all()

    # Build response
    summary = EventSummaryResponse()
    for category, count in results:
        setattr(summary, category, count)

    logger.info(f"Event summary: {len(results)} categories")
    return summary


@router.get(
    "/competitors/{competitor_id}/analytics/entity-summary",
    response_model=EntitySummaryResponse
)
def get_entity_summary(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get entity counts by type.
    """
    logger.info(
        f"User {current_user.id} fetching entity summary for competitor {competitor_id}"
    )

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Count entities by type
    results = db.query(
        Entity.entity_type,
        func.count(Entity.id).label("count")
    ).filter(
        Entity.competitor_id == competitor_id
    ).group_by(
        Entity.entity_type
    ).all()

    # Build response
    summary = EntitySummaryResponse()
    for entity_type, count in results:
        setattr(summary, entity_type, count)

    logger.info(f"Entity summary: {len(results)} types")
    return summary


@router.get(
    "/competitors/{competitor_id}/analytics/timeline",
    response_model=List[TimelineEventResponse]
)
def get_strategic_timeline(
    competitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chronological timeline of strategic events.

    Returns events sorted by date (newest first).
    """
    logger.info(
        f"User {current_user.id} fetching timeline for competitor {competitor_id}"
    )

    # Verify competitor belongs to user
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.user_id == current_user.id
    ).first()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Get events ordered by date
    events = db.query(StrategicEvent).filter(
        StrategicEvent.competitor_id == competitor_id
    ).order_by(
        StrategicEvent.event_date.desc()
    ).all()

    logger.info(f"Timeline: {len(events)} events")
    return events
