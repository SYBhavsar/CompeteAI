"""
Entity Extraction Service

Purpose: Extract named entities from content using LangChain
Uses: GPT-3.5 for cost-effective extraction with structured output
Follows: Single Responsibility Principle - focused on entity extraction only
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from langchain.chains import create_extraction_chain

from app.core.llm_factory import LLMFactory
from app.models.entity import Entity

logger = logging.getLogger(__name__)


class EntitySchema(BaseModel):
    """
    Pydantic schema for entity extraction.

    Used by LangChain to enforce structured output from LLM.
    """
    entity_type: str = Field(
        description="Type of entity: product, person, company, technology, partnership"
    )
    name: str = Field(
        description="Canonical name of the entity"
    )
    context: str = Field(
        description="Surrounding context about the entity (role, features, relationship, etc.)"
    )


class EntityExtractionService:
    """
    Service for extracting named entities from competitor content.

    Uses LangChain extraction chains with GPT-3.5 for cost-effective
    structured entity extraction. Extracts products, people, companies,
    and technologies with automatic deduplication.
    """

    def __init__(self):
        """Initialize with LangChain LLM via LLMFactory (provider/model configurable)."""
        try:
            self.llm = LLMFactory.create("entity_extraction")
            logger.info("EntityExtractionService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EntityExtractionService: {e}", exc_info=True)
            raise

    def extract_entities(
        self,
        content: str,
        competitor_id: int,
        db: Session
    ) -> List[Entity]:
        """
        Extract entities from content using LangChain extraction chains.

        Args:
            content: Text content to analyze
            competitor_id: ID of competitor
            db: Database session

        Returns:
            List of Entity objects (saved to database)

        Follows: Open/Closed Principle - extensible without modification
        """
        if not content or len(content.strip()) == 0:
            logger.debug("Empty content provided, skipping extraction")
            return []

        try:
            logger.info(f"Extracting entities from content for competitor {competitor_id}")

            # Create extraction chain with Pydantic schema
            extraction_chain = create_extraction_chain(
                schema=EntitySchema,
                llm=self.llm
            )

            # Run extraction
            logger.debug("Running LangChain extraction")
            extracted_data = extraction_chain.run(content)

            if not extracted_data:
                logger.info("No entities extracted from content")
                return []

            logger.info(f"Extracted {len(extracted_data)} raw entities")

            # Process and deduplicate entities
            entities = self._process_entities(
                extracted_data=extracted_data,
                competitor_id=competitor_id,
                db=db
            )

            logger.info(f"Created {len(entities)} unique entities for competitor {competitor_id}")
            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}", exc_info=True)
            return []

    def _process_entities(
        self,
        extracted_data: List[Dict[str, Any]],
        competitor_id: int,
        db: Session
    ) -> List[Entity]:
        """
        Process extracted entities: deduplicate, resolve aliases, save to DB.

        Args:
            extracted_data: Raw extraction results from LangChain
            competitor_id: ID of competitor
            db: Database session

        Returns:
            List of Entity objects

        Follows: Single Responsibility - entity processing logic
        """
        entities_dict = {}  # name -> entity data (for deduplication)

        for item in extracted_data:
            try:
                entity_type = item.get("entity_type", "").lower()
                name = item.get("name", "").strip()
                context = item.get("context", "")

                if not name or not entity_type:
                    continue

                # Normalize entity type
                if entity_type not in ["product", "person", "company", "technology", "partnership"]:
                    logger.warning(f"Unknown entity type '{entity_type}', skipping")
                    continue

                # Deduplication: merge entities with same name
                if name in entities_dict:
                    # Merge context
                    existing_context = entities_dict[name]["context"]
                    entities_dict[name]["context"] = f"{existing_context}; {context}"
                else:
                    entities_dict[name] = {
                        "entity_type": entity_type,
                        "name": name,
                        "context": context
                    }

            except Exception as e:
                logger.error(f"Error processing entity item: {e}")
                continue

        # Create Entity objects
        entities = []
        for name, data in entities_dict.items():
            try:
                # Check if entity already exists
                existing_entity = db.query(Entity).filter(
                    Entity.competitor_id == competitor_id,
                    Entity.name == name
                ).first()

                if existing_entity:
                    logger.debug(f"Entity '{name}' already exists, skipping")
                    entities.append(existing_entity)
                    continue

                # Extract aliases from context (simple heuristic)
                aliases = self._extract_aliases(name, data["context"])

                # Extract metadata from context
                entity_metadata = self._extract_metadata(
                    data["entity_type"],
                    data["context"]
                )

                # Create new entity
                entity = Entity(
                    entity_type=data["entity_type"],
                    name=name,
                    aliases=aliases,
                    first_mentioned=datetime.now(timezone.utc),
                    competitor_id=competitor_id,
                    entity_metadata=entity_metadata
                )

                db.add(entity)
                entities.append(entity)

                logger.debug(f"Created entity: {entity_type} '{name}'")

            except Exception as e:
                logger.error(f"Error creating entity '{name}': {e}", exc_info=True)
                continue

        # Commit all entities
        try:
            db.commit()
            logger.info(f"Committed {len(entities)} entities to database")
        except Exception as e:
            logger.error(f"Error committing entities: {e}", exc_info=True)
            db.rollback()
            return []

        return entities

    def _extract_aliases(self, name: str, context: str) -> List[str]:
        """
        Extract aliases from context using simple heuristics.

        Args:
            name: Canonical entity name
            context: Context string

        Returns:
            List of detected aliases

        Follows: Clean Code - single-purpose helper function
        """
        aliases = []

        # Common alias patterns
        alias_patterns = [
            "also known as",
            "aka",
            "abbreviated as",
            "(",  # Parenthetical abbreviations
        ]

        context_lower = context.lower()

        # Check for parenthetical abbreviations (e.g., "Enterprise Analytics Platform (EAP)")
        if "(" in context and ")" in context:
            import re
            # Find content in parentheses
            matches = re.findall(r'\(([^)]+)\)', context)
            for match in matches:
                # If it's short (likely an abbreviation), add as alias
                if len(match) <= 10 and match.upper() == match:
                    aliases.append(match)

        # Check for explicit alias indicators
        for pattern in alias_patterns:
            if pattern in context_lower:
                # Extract text after pattern (simple heuristic)
                parts = context_lower.split(pattern)
                if len(parts) > 1:
                    potential_alias = parts[1].split(',')[0].split('.')[0].strip()
                    if potential_alias and len(potential_alias) < 50:
                        aliases.append(potential_alias.title())

        return list(set(aliases))  # Remove duplicates

    def _extract_metadata(self, entity_type: str, context: str) -> Dict[str, Any]:
        """
        Extract structured metadata from context based on entity type.

        Args:
            entity_type: Type of entity (product, person, company, technology)
            context: Context string

        Returns:
            Dict with extracted metadata

        Follows: Strategy Pattern - different extraction per type
        """
        metadata = {"raw_context": context}

        try:
            if entity_type == "person":
                # Extract role/title
                role_keywords = ["ceo", "cto", "cfo", "vp", "chief", "director", "manager", "officer"]
                for keyword in role_keywords:
                    if keyword in context.lower():
                        metadata["role"] = context
                        break

                # Extract previous company
                if "from" in context.lower():
                    metadata["background"] = context

            elif entity_type == "product":
                # Extract pricing
                import re
                price_match = re.search(r'\$\d+(?:,\d{3})*(?:\.\d{2})?(?:/month|/year)?', context)
                if price_match:
                    metadata["pricing"] = price_match.group()

                # Extract features mentioned
                if "feature" in context.lower() or "capabilit" in context.lower():
                    metadata["features"] = context

            elif entity_type == "company":
                # Extract relationship type
                relationship_keywords = ["partner", "acquisition", "competitor", "customer"]
                for keyword in relationship_keywords:
                    if keyword in context.lower():
                        metadata["relationship"] = keyword
                        break

            elif entity_type == "technology":
                # Extract vendor/provider
                if "by" in context or "from" in context:
                    metadata["vendor"] = context

        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata
