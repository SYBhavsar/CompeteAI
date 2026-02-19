"""
Predictive Analysis Service

Purpose: Generate AI-powered predictions of future competitor moves
Architecture: RAG (Retrieval Augmented Generation) + LLM chain
- Retrieves similar historical patterns via EmbeddingService
- Builds context from recent StrategicEvents
- Uses LLMFactory for configurable provider/model
Follows: Single Responsibility Principle - focused on prediction only
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.llm_factory import LLMFactory
from app.core.prompt_loader import PromptLoader
from app.models.strategic_event import StrategicEvent
from app.models.prediction import CompetitorPrediction
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

VALID_TIMEFRAMES = {"30_days", "60_days", "90_days", "180_days"}
VALID_OUTCOMES = {"pending", "correct", "incorrect"}


class PredictiveAnalysisService:
    """
    Predicts future competitor strategic moves using historical event patterns and RAG context.

    Flow:
      1. Fetch recent StrategicEvents for competitor
      2. Retrieve similar market context via EmbeddingService (RAG)
      3. Pass both to LLM via predictive_analysis prompt
      4. Parse JSON response → CompetitorPrediction records
      5. Persist to DB and return
    """

    def __init__(self):
        self.llm = LLMFactory.create("predictive_analysis")
        self.embedding_service = EmbeddingService()
        logger.info("PredictiveAnalysisService initialized")

    def predict_next_moves(
        self,
        competitor_id: int,
        db: Session,
        lookback_days: int = 90
    ) -> List[CompetitorPrediction]:
        """
        Generate predictions for a competitor's next strategic moves.

        Args:
            competitor_id: Competitor to predict for
            db: Database session
            lookback_days: How many days of history to use

        Returns:
            List of saved CompetitorPrediction records
        """
        try:
            # 1. Fetch recent historical events
            events = (
                db.query(StrategicEvent)
                .filter(StrategicEvent.competitor_id == competitor_id)
                .order_by(StrategicEvent.event_date.desc())
                .limit(20)
                .all()
            )

            if not events:
                logger.info(f"No historical events for competitor {competitor_id}, skipping prediction")
                return []

            # 2. RAG context - retrieve similar insights
            rag_context = self._get_rag_context(competitor_id)

            # 3. Build prompt
            historical_summary = self._format_events(events)
            prompt_config = PromptLoader.load("predictive_analysis")
            user_msg = prompt_config.user_prompt.format(
                historical_events=historical_summary,
                rag_context=rag_context
            )
            from langchain.schema import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=prompt_config.system_prompt),
                HumanMessage(content=user_msg),
            ]

            # 4. Call LLM
            logger.info(f"Running prediction LLM for competitor {competitor_id}")
            response = self.llm.invoke(messages)
            raw = response.content if hasattr(response, "content") else str(response)

            # 5. Parse and persist
            predictions = self._parse_and_save(raw, competitor_id, db)
            logger.info(f"Generated {len(predictions)} predictions for competitor {competitor_id}")
            return predictions

        except Exception as e:
            logger.error(f"Prediction failed for competitor {competitor_id}: {e}", exc_info=True)
            return []

    def get_active_predictions(
        self,
        competitor_id: int,
        db: Session
    ) -> List[CompetitorPrediction]:
        """Return all pending (unresolved) predictions for a competitor."""
        return (
            db.query(CompetitorPrediction)
            .filter(
                CompetitorPrediction.competitor_id == competitor_id,
                CompetitorPrediction.outcome == "pending"
            )
            .order_by(CompetitorPrediction.predicted_at.desc())
            .all()
        )

    def update_prediction_outcome(
        self,
        prediction_id: int,
        outcome: str,
        db: Session
    ) -> Optional[CompetitorPrediction]:
        """
        Validate a prediction outcome.

        Args:
            prediction_id: ID of the prediction to update
            outcome: 'correct' or 'incorrect'
            db: Database session

        Returns:
            Updated prediction, or None if not found
        """
        if outcome not in ("correct", "incorrect"):
            raise ValueError(f"outcome must be 'correct' or 'incorrect', got '{outcome}'")

        prediction = db.query(CompetitorPrediction).filter(
            CompetitorPrediction.id == prediction_id
        ).first()

        if not prediction:
            return None

        prediction.outcome = outcome
        prediction.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(prediction)
        logger.info(f"Prediction {prediction_id} marked as {outcome}")
        return prediction

    # --- Private helpers ---

    def _get_rag_context(self, competitor_id: int) -> str:
        """Retrieve similar historical patterns via semantic search."""
        try:
            query = f"competitor strategic moves patterns competitor_id:{competitor_id}"
            results = self.embedding_service.search_similar_insights(
                query=query,
                competitor_id=competitor_id,
                top_k=5
            )
            if not results:
                return "No similar patterns found."
            return "\n".join(
                f"- {r.get('summary', r.get('content', ''))}" for r in results
            )
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return "Context unavailable."

    def _format_events(self, events: List[StrategicEvent]) -> str:
        """Format StrategicEvent list into a readable summary for the prompt."""
        lines = []
        for event in events:
            date_str = event.event_date.strftime("%Y-%m-%d") if event.event_date else "unknown date"
            lines.append(
                f"- [{date_str}] {event.event_category.upper()}: {event.title} "
                f"(confidence: {event.confidence:.0%})"
            )
        return "\n".join(lines)

    def _parse_and_save(
        self,
        raw_response: str,
        competitor_id: int,
        db: Session
    ) -> List[CompetitorPrediction]:
        """Parse LLM JSON response and persist predictions."""
        try:
            # Strip markdown code fences if present
            content = raw_response.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            data = json.loads(content)

            if not isinstance(data, list):
                logger.warning("LLM returned non-list prediction response")
                return []

            saved = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                timeframe = item.get("timeframe", "90_days")
                if timeframe not in VALID_TIMEFRAMES:
                    timeframe = "90_days"

                prediction = CompetitorPrediction(
                    competitor_id=competitor_id,
                    prediction_type=item.get("prediction_type", "unknown"),
                    confidence=min(1.0, max(0.0, float(item.get("confidence", 0.5)))),
                    timeframe=timeframe,
                    reasoning=item.get("reasoning", ""),
                    suggested_action=item.get("suggested_action", ""),
                    outcome="pending",
                    predicted_at=datetime.utcnow()
                )
                db.add(prediction)
                saved.append(prediction)

            db.commit()
            for p in saved:
                db.refresh(p)

            return saved

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse prediction response: {e}\nRaw: {raw_response[:500]}")
            return []
