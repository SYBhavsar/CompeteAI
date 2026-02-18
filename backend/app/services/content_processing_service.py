import re
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm_factory import LLMFactory
from app.core.prompt_loader import PromptLoader
from app.models import RawContent, ProcessedInsights
from app.schemas.ai_responses import SummaryResult, InsightsResult, SentimentResult
from app.services.quality_scoring_service import QualityScoringService
from app.services.entity_extraction_service import EntityExtractionService
from app.services.strategic_detection_service import StrategicDetectionService
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ContentProcessingService:
    """Service for processing raw content into insights using AI"""

    def __init__(self):
        try:
            self._summarization_llm = LLMFactory.create("summarization").with_structured_output(SummaryResult)
            self._insight_llm = LLMFactory.create("insight_extraction").with_structured_output(InsightsResult)
            self._sentiment_llm = LLMFactory.create("sentiment_analysis").with_structured_output(SentimentResult)
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
            raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
            if not raw_content:
                logger.warning(f"Raw content with id {raw_content_id} not found.")
                return None

            existing_insights = db.query(ProcessedInsights).filter(
                ProcessedInsights.raw_content_id == raw_content_id
            ).first()
            if existing_insights:
                logger.info(f"Content {raw_content_id} already processed. Skipping.")
                return existing_insights

            logger.debug(f"Processing content for URL: {raw_content.url}")

            summary_result = self._summarize(raw_content.content)
            insights_result = self._extract_insights(raw_content.content)
            sentiment_result = self._analyze_sentiment(raw_content.content)

            key_points = self._extract_key_points(raw_content.content)

            logger.debug(f"Creating ProcessedInsights for content {raw_content_id}.")
            processed_insights = ProcessedInsights(
                raw_content_id=raw_content_id,
                summary=summary_result.summary,
                key_points=key_points,
                sentiment=sentiment_result.sentiment,
                insights=insights_result.insights,
            )

            db.add(processed_insights)
            db.commit()
            db.refresh(processed_insights)
            logger.info(f"Saved ProcessedInsights {processed_insights.id} for content {raw_content_id}.")

            quality_score = self.quality_scorer.calculate_quality_score(processed_insights)
            processed_insights.quality_score = quality_score
            raw_content.status = "processed"

            db.commit()
            db.refresh(processed_insights)
            logger.info(
                f"Successfully processed content {raw_content_id}. "
                f"Insight ID: {processed_insights.id}, Quality Score: {quality_score}"
            )

            self._run_strategic_pipeline(raw_content, processed_insights, db)
            return processed_insights

        except Exception as e:
            logger.error(f"Unexpected error processing content {raw_content_id}: {e}", exc_info=True)
            db.rollback()
            raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
            if raw_content:
                raw_content.status = "failed"
                db.commit()
            return None

    @retry_with_backoff(exceptions=(Exception,))
    def _summarize(self, content: str) -> SummaryResult:
        """Summarize content via structured LLM output."""
        prompt = PromptLoader.load("summarization")
        messages = [
            SystemMessage(content=prompt.system_prompt),
            HumanMessage(content=prompt.user_prompt.format(content=content)),
        ]
        result = self._summarization_llm.invoke(messages)
        logger.debug("Summarization complete.")
        return result

    @retry_with_backoff(exceptions=(Exception,))
    def _extract_insights(self, content: str) -> InsightsResult:
        """Extract insights via structured LLM output."""
        prompt = PromptLoader.load("insight_extraction")
        messages = [
            SystemMessage(content=prompt.system_prompt),
            HumanMessage(content=prompt.user_prompt.format(content=content)),
        ]
        result = self._insight_llm.invoke(messages)
        logger.debug("Insight extraction complete.")
        return result

    @retry_with_backoff(exceptions=(Exception,))
    def _analyze_sentiment(self, content: str) -> SentimentResult:
        """Analyze sentiment via structured LLM output."""
        prompt = PromptLoader.load("sentiment_analysis")
        messages = [
            SystemMessage(content=prompt.system_prompt),
            HumanMessage(content=prompt.user_prompt.format(content=content)),
        ]
        result = self._sentiment_llm.invoke(messages)
        logger.debug(f"Sentiment analysis complete: {result.sentiment}")
        return result

    def _run_strategic_pipeline(
        self, raw_content: RawContent, insight: ProcessedInsights, db: Session
    ) -> None:
        """
        Run entity extraction and strategic detection after insight creation.
        Errors here do NOT affect the saved insight — logged only.
        """
        competitor_id = raw_content.data_source.competitor_id
        content = raw_content.content

        entities = []
        try:
            entities = self.entity_extractor.extract_entities(
                content=content,
                competitor_id=competitor_id,
                db=db,
            )
            logger.info(f"Extracted {len(entities)} entities for competitor {competitor_id}")
        except Exception as e:
            logger.error(f"Entity extraction failed for content {raw_content.id}: {e}", exc_info=True)

        try:
            events = self.strategic_detector.detect_strategic_moves(
                content=content,
                competitor_id=competitor_id,
                entities=entities,
                db=db,
            )
            logger.info(f"Detected {len(events)} strategic events for competitor {competitor_id}")
        except Exception as e:
            logger.error(f"Strategic detection failed for content {raw_content.id}: {e}", exc_info=True)

    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content using simple text processing"""
        logger.debug("Extracting key points from content.")
        try:
            sentences = re.split(r"[.!?]+", content)
            important_words = [
                "announces", "launches", "features", "available", "new",
                "product", "service", "partnership", "release",
            ]
            key_points = [
                s.strip()
                for s in sentences
                if 20 < len(s.strip()) < 200
                and any(w in s.lower() for w in important_words)
            ]
            if not key_points:
                logger.warning("No specific key points found, using fallback.")
                return ["Content processed and summarized."]
            logger.info(f"Extracted {len(key_points)} key points.")
            return key_points[:5]
        except Exception as e:
            logger.error(f"Failed to extract key points. Error: {e}", exc_info=True)
            return ["Error during key point extraction."]
