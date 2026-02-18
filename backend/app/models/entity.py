"""
Entity Model

Purpose: Track named entities extracted from competitor content
Types: Products, people, companies, technologies, partnerships
Follows: Single Responsibility Principle
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Entity(Base):
    """
    Named entities extracted from competitor content.

    Tracks:
    - Products: Product names, features, pricing
    - People: Executives, key hires, departures
    - Companies: Partners, acquisition targets, competitors
    - Technologies: Tech stack, tools, platforms used
    - Partnerships: Strategic alliances, integrations

    Used for knowledge graph construction and entity-based analysis.
    """
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)  # product, person, company, technology, partnership
    name = Column(String, nullable=False, index=True)  # Canonical name
    aliases = Column(JSON, nullable=False, default=[])  # Alternative names/spellings
    first_mentioned = Column(DateTime(timezone=True), nullable=False)  # When first detected
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    entity_metadata = Column(JSON, nullable=False, default={})  # Flexible: role, title, pricing, features, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    competitor = relationship("Competitor", back_populates="entities")

    # Relationships as source
    relationships_from = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.source_entity_id",
        back_populates="source_entity"
    )

    # Relationships as target
    relationships_to = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.target_entity_id",
        back_populates="target_entity"
    )
