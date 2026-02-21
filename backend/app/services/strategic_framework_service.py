"""
Strategic Framework Service

Purpose: Generate SWOT analyses and threat assessments for competitors
Architecture: LLM + RAG (EmbeddingService for context retrieval)
- SWOT: single LLM call with competitor context + RAG patterns
- Threat scoring: 5-factor weighted score from LLM + category breakdown
Follows: Single Responsibility Principle
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.llm_factory import LLMFactory
from app.core.prompt_loader import PromptLoader
from app.models import Competitor
from app.models.strategic_event import StrategicEvent
from app.models.swot import SWOTAnalysis
from app.models.threat_assessment import ThreatAssessment
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# Weighted factors for threat score (must sum to 1.0)
THREAT_WEIGHTS = {
    "pricing": 0.30,
    "innovation": 0.25,
    "market_share": 0.20,
    "resource_strength": 0.15,
    "partnerships": 0.10,
}


class StrategicFrameworkService:
    """
    Generates SWOT analyses and threat assessments using LLM + RAG.

    SWOT flow:
      1. Build competitor context from DB
      2. Retrieve RAG context via EmbeddingService
      3. Call LLM with swot_analysis prompt
      4. Parse response → upsert SWOTAnalysis

    Threat scoring flow:
      1. Build context from recent events
      2. Call LLM with threat_scoring prompt
      3. Apply weighted formula → upsert ThreatAssessment
    """

    def __init__(self):
        self.llm = LLMFactory.create("swot_analysis")
        self.embedding_service = EmbeddingService()
        logger.info("StrategicFrameworkService initialized")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def generate_swot(
        self,
        competitor_id: int,
        db: Session
    ) -> Optional[SWOTAnalysis]:
        """
        Generate or regenerate a SWOT analysis for a competitor.

        If a previous SWOTAnalysis exists it is replaced (upsert).

        Returns the saved SWOTAnalysis or None on failure.
        """
        try:
            competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
            competitor_context = self._build_competitor_context(competitor, competitor_id, db)
            rag_context = self._get_rag_context(competitor_id, "SWOT competitive strengths weaknesses")
            strategic_events = self._format_recent_events(competitor_id, db)

            prompt_config = PromptLoader.load("swot_analysis")
            from langchain.schema import SystemMessage, HumanMessage
            user_msg = prompt_config.user_prompt.format(
                competitor_context=competitor_context,
                strategic_events=strategic_events,
                rag_context=rag_context,
            )
            messages = [
                SystemMessage(content=prompt_config.system_prompt),
                HumanMessage(content=user_msg),
            ]

            logger.info(f"Generating SWOT for competitor {competitor_id}")
            response = self.llm.invoke(messages)
            raw = response.content if hasattr(response, "content") else str(response)

            return self._parse_and_upsert_swot(raw, competitor_id, db)

        except Exception as e:
            logger.error(f"SWOT generation failed for competitor {competitor_id}: {e}", exc_info=True)
            return None

    def calculate_threat_score(
        self,
        competitor_id: int,
        db: Session
    ) -> Optional[ThreatAssessment]:
        """
        Calculate and persist a threat assessment for a competitor.

        Returns the saved ThreatAssessment or None on failure.
        """
        try:
            competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
            competitor_context = self._build_competitor_context(competitor, competitor_id, db)
            recent_events = self._format_recent_events(competitor_id, db, limit=10)

            prompt_config = PromptLoader.load("threat_scoring")
            from langchain.schema import SystemMessage, HumanMessage
            user_msg = prompt_config.user_prompt.format(
                competitor_context=competitor_context,
                recent_events=recent_events,
            )
            messages = [
                SystemMessage(content=prompt_config.system_prompt),
                HumanMessage(content=user_msg),
            ]

            logger.info(f"Calculating threat score for competitor {competitor_id}")
            response = self.llm.invoke(messages)
            raw = response.content if hasattr(response, "content") else str(response)

            return self._parse_and_upsert_threat(raw, competitor_id, db)

        except Exception as e:
            logger.error(f"Threat scoring failed for competitor {competitor_id}: {e}", exc_info=True)
            return None

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _build_competitor_context(
        self,
        competitor: Optional[Competitor],
        competitor_id: int,
        db: Session
    ) -> str:
        if not competitor:
            return f"Competitor ID: {competitor_id} (details unavailable)"
        return f"Competitor: {competitor.name}\nDomain: {competitor.domain or 'unknown'}"

    def _get_rag_context(self, competitor_id: int, query: str) -> str:
        try:
            results = self.embedding_service.search_similar_insights(
                query_text=query,
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

    def _format_recent_events(
        self,
        competitor_id: int,
        db: Session,
        limit: int = 15
    ) -> str:
        events = (
            db.query(StrategicEvent)
            .filter(StrategicEvent.competitor_id == competitor_id)
            .order_by(StrategicEvent.event_date.desc())
            .limit(limit)
            .all()
        )
        if not events:
            return "No recent strategic events recorded."
        lines = []
        for e in events:
            date_str = e.event_date.strftime("%Y-%m-%d") if e.event_date else "unknown"
            lines.append(f"- [{date_str}] {e.event_category.upper()}: {e.title}")
        return "\n".join(lines)

    def _parse_and_upsert_swot(
        self,
        raw: str,
        competitor_id: int,
        db: Session
    ) -> Optional[SWOTAnalysis]:
        content = self._strip_code_fences(raw)
        data = json.loads(content)

        # Delete existing (upsert pattern)
        db.query(SWOTAnalysis).filter(
            SWOTAnalysis.competitor_id == competitor_id
        ).delete()

        swot = SWOTAnalysis(
            competitor_id=competitor_id,
            analysis_date=datetime.now(timezone.utc),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            opportunities=data.get("opportunities", []),
            threats=data.get("threats", []),
            overall_assessment=data.get("overall_assessment", ""),
            confidence_score=min(1.0, max(0.0, float(data.get("confidence_score", 0.0)))),
        )
        db.add(swot)
        db.commit()
        db.refresh(swot)
        logger.info(f"SWOT upserted for competitor {competitor_id}")
        return swot

    def _parse_and_upsert_threat(
        self,
        raw: str,
        competitor_id: int,
        db: Session
    ) -> Optional[ThreatAssessment]:
        content = self._strip_code_fences(raw)
        cats = json.loads(content)

        # Clamp all scores to 0-100
        for key in THREAT_WEIGHTS:
            cats[key] = min(100, max(0, int(cats.get(key, 50))))

        # Weighted aggregate
        threat_score = sum(cats[k] * w for k, w in THREAT_WEIGHTS.items())

        # Upsert
        db.query(ThreatAssessment).filter(
            ThreatAssessment.competitor_id == competitor_id
        ).delete()

        assessment = ThreatAssessment(
            competitor_id=competitor_id,
            threat_score=round(threat_score, 2),
            threat_categories=cats,
            assessment_text=self._build_assessment_text(threat_score, cats),
            mitigation_recommendations=self._build_mitigations(cats),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        logger.info(f"ThreatAssessment upserted for competitor {competitor_id}, score={threat_score:.1f}")
        return assessment

    def _build_assessment_text(self, score: float, cats: dict) -> str:
        level = "critical" if score >= 80 else "high" if score >= 60 else "moderate" if score >= 40 else "low"
        top_cat = max(cats, key=lambda k: cats[k])
        return f"{level.capitalize()} threat level ({score:.0f}/100). Strongest dimension: {top_cat} ({cats[top_cat]}/100)."

    def _build_mitigations(self, cats: dict) -> list:
        tips = {
            "pricing": "Consider competitive pricing review and value-based positioning.",
            "innovation": "Accelerate product roadmap to match feature velocity.",
            "market_share": "Strengthen customer retention and loyalty programs.",
            "resource_strength": "Explore strategic partnerships or funding to close resource gap.",
            "partnerships": "Expand integration ecosystem and partner network.",
        }
        # Return mitigations for top-2 scoring categories
        top2 = sorted(cats, key=lambda k: cats[k], reverse=True)[:2]
        return [tips[k] for k in top2 if k in tips]

    @staticmethod
    def _strip_code_fences(raw: str) -> str:
        content = raw.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return content.strip()
