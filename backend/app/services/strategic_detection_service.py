"""
Strategic Detection Service

Purpose: Detect high-value strategic moves from competitor content
Uses: GPT-4 for complex strategic reasoning
Categories: Market entries, M&A, partnerships, product launches, pricing, leadership, funding
Follows: Single Responsibility Principle - focused on strategic event detection only
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from app.core.llm_factory import LLMFactory
from app.core.prompt_loader import PromptLoader
from app.models.strategic_event import StrategicEvent
from app.models.entity import Entity

logger = logging.getLogger(__name__)


class StrategicEventSchema(BaseModel):
    """
    Pydantic schema for strategic event detection.

    Used by LangChain to enforce structured output from GPT-4.
    """
    event_category: str = Field(
        description="Category: market_entry, acquisition, partnership, product_launch, pricing_change, leadership_change, funding"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0"
    )
    title: str = Field(
        description="Short title summarizing the strategic move (max 100 chars)"
    )
    description: str = Field(
        description="Detailed description of the strategic move"
    )
    strategic_implications: str = Field(
        description="Analysis of strategic implications and competitive impact"
    )
    entities: List[str] = Field(
        description="List of key entities involved (companies, products, people, technologies)"
    )


class StrategicDetectionService:
    """
    Service for detecting strategic moves from competitor content.

    Uses GPT-4 for complex strategic reasoning to identify high-value
    competitive intelligence:
    - Market entries (geographic/vertical expansion)
    - Acquisitions and M&A activity
    - Strategic partnerships and alliances
    - Major product launches
    - Significant pricing changes
    - Leadership hires/departures
    - Funding rounds

    Returns StrategicEvent objects with confidence scores and implications.
    """

    def __init__(self):
        """Initialize with LangChain LLM via LLMFactory (provider/model configurable)."""
        try:
            self.llm = LLMFactory.create("strategic_detection")
            logger.info("StrategicDetectionService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize StrategicDetectionService: {e}", exc_info=True)
            raise

    def detect_strategic_moves(
        self,
        content: str,
        competitor_id: int,
        entities: List[Entity],
        db: Session
    ) -> List[StrategicEvent]:
        """
        Detect strategic moves from content using GPT-4 reasoning.

        Args:
            content: Text content to analyze
            competitor_id: ID of competitor
            entities: Pre-extracted entities (optional, enhances detection)
            db: Database session

        Returns:
            List of StrategicEvent objects (saved to database)

        Follows: Open/Closed Principle - extensible event categories
        """
        if not content or len(content.strip()) == 0:
            logger.debug("Empty content provided, skipping detection")
            return []

        try:
            logger.info(f"Detecting strategic moves for competitor {competitor_id}")

            # Build entity context
            entity_context = self._build_entity_context(entities)

            # Analyze content with LLM
            detected_events = self._analyze_with_llm(content, entity_context)

            if not detected_events:
                logger.info("No strategic moves detected")
                return []

            logger.info(f"Detected {len(detected_events)} strategic events")

            # Create StrategicEvent objects
            events = self._create_strategic_events(
                detected_events=detected_events,
                competitor_id=competitor_id,
                db=db
            )

            logger.info(f"Created {len(events)} strategic events for competitor {competitor_id}")
            return events

        except Exception as e:
            logger.error(f"Error detecting strategic moves: {e}", exc_info=True)
            return []

    def _build_entity_context(self, entities: List[Entity]) -> str:
        """
        Build context string from pre-extracted entities.

        Args:
            entities: List of Entity objects

        Returns:
            Formatted entity context string

        Follows: Clean Code - single-purpose helper
        """
        if not entities:
            return "No pre-extracted entities available."

        context_parts = []
        for entity in entities:
            context_parts.append(
                f"- {entity.entity_type.title()}: {entity.name}"
            )

        return "Known entities:\n" + "\n".join(context_parts)

    def _analyze_with_llm(
        self,
        content: str,
        entity_context: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze content with LLM to detect strategic moves.

        Args:
            content: Text content
            entity_context: Pre-extracted entities context

        Returns:
            List of detected event dictionaries
        """
        try:
            prompt_config = PromptLoader.load("strategic_detection")
            system = prompt_config.system_prompt.format(entity_context=entity_context)

            prompt = ChatPromptTemplate.from_messages([
                ("system", system),
                ("human", "{content}"),
            ])

            logger.debug("Invoking LLM for strategic detection")
            response = self.llm.invoke(
                prompt.format_messages(content=content)
            )

            # Parse response
            response_text = response.content.strip()

            # Handle both single object and array responses
            if response_text.startswith('['):
                events = json.loads(response_text)
            elif response_text.startswith('{'):
                events = [json.loads(response_text)]
            else:
                logger.warning(f"Unexpected GPT-4 response format: {response_text[:100]}")
                return []

            logger.debug(f"LLM detected {len(events)} events")
            return events

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in GPT-4 analysis: {e}", exc_info=True)
            return []

    def _create_strategic_events(
        self,
        detected_events: List[Dict[str, Any]],
        competitor_id: int,
        db: Session
    ) -> List[StrategicEvent]:
        """
        Create StrategicEvent objects from detection results.

        Args:
            detected_events: List of detected event dictionaries
            competitor_id: ID of competitor
            db: Database session

        Returns:
            List of StrategicEvent objects

        Follows: Single Responsibility - event creation logic
        """
        events = []

        for event_data in detected_events:
            try:
                # Validate category
                event_category = event_data.get("event_category", "").lower()
                valid_categories = [
                    "market_entry", "acquisition", "partnership",
                    "product_launch", "pricing_change", "leadership_change", "funding"
                ]

                if event_category not in valid_categories:
                    logger.warning(f"Invalid event category '{event_category}', skipping")
                    continue

                # Validate confidence
                confidence = float(event_data.get("confidence", 0.0))
                if confidence < 0.5:  # Only save high-confidence events
                    logger.debug(f"Low confidence event ({confidence}), skipping")
                    continue

                # Extract fields
                title = event_data.get("title", "")[:200]  # Limit length
                description = event_data.get("description", "")
                strategic_implications = event_data.get("strategic_implications", "")
                entities_list = event_data.get("entities", [])

                # Create event
                event = StrategicEvent(
                    competitor_id=competitor_id,
                    event_category=event_category,
                    confidence=confidence,
                    event_date=datetime.now(timezone.utc),  # Detection time
                    title=title,
                    description=description,
                    entities_involved={"entities": entities_list},
                    strategic_implications=strategic_implications,
                    source_insights={}
                )

                db.add(event)
                events.append(event)

                logger.debug(
                    f"Created strategic event: {event_category} - {title} "
                    f"(confidence: {confidence:.2f})"
                )

            except Exception as e:
                logger.error(f"Error creating strategic event: {e}", exc_info=True)
                continue

        # Commit all events
        try:
            db.commit()
            logger.info(f"Committed {len(events)} strategic events to database")
        except Exception as e:
            logger.error(f"Error committing strategic events: {e}", exc_info=True)
            db.rollback()
            return []

        return events
