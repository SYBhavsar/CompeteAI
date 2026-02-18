"""
Entity Relationship Model

Purpose: Track relationships between entities for knowledge graph
Types: Competitor, partner, acquired_by, uses_technology, employs
Follows: Single Responsibility Principle
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EntityRelationship(Base):
    """
    Relationships between entities for competitive knowledge graph.

    Relationship types:
    - competitor: Two companies compete in same market
    - partner: Strategic partnership or alliance
    - acquired_by: Acquisition relationship
    - uses_technology: Company uses a technology/platform
    - employs: Company employs a person

    Used for:
    - Network analysis (who partners with whom)
    - Technology stack mapping
    - Competitive landscape visualization
    - M&A activity tracking
    """
    __tablename__ = "entity_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    target_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    relationship_type = Column(String, nullable=False, index=True)  # competitor, partner, acquired_by, etc.
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0 - AI confidence in relationship
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    source_entity = relationship(
        "Entity",
        foreign_keys=[source_entity_id],
        back_populates="relationships_from"
    )
    target_entity = relationship(
        "Entity",
        foreign_keys=[target_entity_id],
        back_populates="relationships_to"
    )
