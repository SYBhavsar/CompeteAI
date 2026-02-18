import re
import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models import RawContent, ProcessedInsights
from app.services.openai_client import OpenAIClient
from app.services.quality_scoring_service import QualityScoringService
from app.services.entity_extraction_service import EntityExtractionService
from app.services.strategic_detection_service import StrategicDetectionService

logger = logging.getLogger(__name__)


class ContentProcessingService:
    """Service for processing raw content into insights using AI"""

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        try:
            self.openai_client = openai_client or OpenAIClient()
            self.quality_scorer = QualityScoringService()
            self.entity_extractor = EntityExtractionService()
            self.strategic_detector = StrategicDetectionService()
            logger.info("ContentProcessingService initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize ContentProcessingService: {e}", exc_info=True)
            raise
    
    def process_raw_content(self, raw_content_id: int, db: Session) -> Optional[ProcessedInsights]:
        """Process raw content and create insights"""
        logger.info(f"Starting processing for raw_content_id: {raw_content_id}")
        try:
            # Get raw content
            raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
            if not raw_content:
                logger.warning(f"Raw content with id {raw_content_id} not found.")
                return None
            
            # Check if already processed
            existing_insights = db.query(ProcessedInsights).filter(
                ProcessedInsights.raw_content_id == raw_content_id
            ).first()
            if existing_insights:
                logger.info(f"Content {raw_content_id} has already been processed. Skipping.")
                return existing_insights
            
            logger.debug(f"Processing content for URL: {raw_content.url}")
            
            # Process content with OpenAI
            summary = self.openai_client.summarize_content(raw_content.content)
            insights = self.openai_client.extract_insights(raw_content.content)
            sentiment = self.openai_client.analyze_sentiment(raw_content.content)
            
            if not summary or not sentiment:
                logger.error(f"Failed to get summary or sentiment from OpenAI for content {raw_content_id}.")
                raw_content.status = 'failed'
                db.commit()
                return None
            
            # Ensure insights is not None (can be empty string)
            if insights is None:
                insights = ""
                logger.warning(f"No insights were extracted for content {raw_content_id}.")
            
            # Extract key points
            key_points = self._extract_key_points(raw_content.content)
            
            # Create processed insights
            logger.debug(f"Creating ProcessedInsights object for content {raw_content_id}.")
            processed_insights = ProcessedInsights(
                raw_content_id=raw_content_id,
                summary=summary,
                key_points=key_points,
                sentiment=sentiment,
                insights=insights
            )

            db.add(processed_insights)
            db.commit()
            db.refresh(processed_insights)
            logger.info(f"Saved new ProcessedInsights {processed_insights.id} for content {raw_content_id}.")

            # Calculate and store quality score
            logger.debug(f"Calculating quality score for insight {processed_insights.id}.")
            quality_score = self.quality_scorer.calculate_quality_score(processed_insights)
            processed_insights.quality_score = quality_score
            
            # Update raw content status
            raw_content.status = 'processed'
            
            db.commit()
            db.refresh(processed_insights)

            logger.info(f"Successfully processed content {raw_content_id}. Insight ID: {processed_insights.id}, Quality Score: {quality_score}")

            # Run strategic intelligence pipeline
            self._run_strategic_pipeline(raw_content, processed_insights, db)

            return processed_insights

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing content {raw_content_id}: {e}", exc_info=True)
            db.rollback()
            # Mark as failed if possible
            raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
            if raw_content:
                raw_content.status = 'failed'
                db.commit()
            return None
    
    def _run_strategic_pipeline(self, raw_content: RawContent, insight: ProcessedInsights, db: Session) -> None:
        """
        Run entity extraction and strategic detection after insight creation.

        Errors in this pipeline do NOT affect the main insight - logged only.
        competitor_id is resolved via raw_content → data_source → competitor_id
        """
        competitor_id = raw_content.data_source.competitor_id
        content = raw_content.content

        # Step 1: Extract entities (graceful on failure)
        entities = []
        try:
            entities = self.entity_extractor.extract_entities(
                content=content,
                competitor_id=competitor_id,
                db=db
            )
            logger.info(f"Extracted {len(entities)} entities for competitor {competitor_id}")
        except Exception as e:
            logger.error(f"Entity extraction failed for content {raw_content.id}: {e}", exc_info=True)

        # Step 2: Detect strategic moves (graceful on failure)
        try:
            events = self.strategic_detector.detect_strategic_moves(
                content=content,
                competitor_id=competitor_id,
                entities=entities,
                db=db
            )
            logger.info(f"Detected {len(events)} strategic events for competitor {competitor_id}")
        except Exception as e:
            logger.error(f"Strategic detection failed for content {raw_content.id}: {e}", exc_info=True)

    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content using simple text processing"""
        logger.debug("Extracting key points from content.")
        try:
            # Split content into sentences
            sentences = re.split(r'[.!?]+', content)
            
            # Filter sentences and extract key points
            key_points = []
            for sentence in sentences:
                sentence = sentence.strip()
                if 20 < len(sentence) < 200:  # Reasonable length
                    # Look for sentences with important keywords
                    important_words = ['announces', 'launches', 'features', 'available', 'new', 'product', 'service', 'partnership', 'release']
                    if any(word in sentence.lower() for word in important_words):
                        key_points.append(sentence)
            
            if not key_points:
                logger.warning("No specific key points found, using a default message.")
                # Fallback to a generic message if no key points are extracted
                return ["Content processed and summarized."]

            logger.info(f"Extracted {len(key_points)} potential key points.")
            return key_points[:5]
        except Exception as e:
            logger.error(f"Failed to extract key points. Error: {e}", exc_info=True)
            return ["Error during key point extraction."]