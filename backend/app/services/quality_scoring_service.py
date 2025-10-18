from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models import ProcessedInsights


class QualityScoringService:
    """Service for scoring the quality of processed insights"""

    def calculate_quality_score(self, insight: ProcessedInsights) -> float:
        """
        Calculate overall quality score for an insight

        Args:
            insight: ProcessedInsights object

        Returns:
            Quality score between 0.0 and 1.0
        """
        # Individual quality factors
        summary_score = self._score_summary_length(insight.summary)
        key_points_score = self._score_key_points_count(insight.key_points or [])
        insights_score = self._score_insights_depth(insight.insights or "")
        sentiment_score = self._score_sentiment_confidence(insight.sentiment)

        # Weighted average of quality factors
        weights = {
            "summary": 0.3,
            "key_points": 0.25,
            "insights": 0.35,
            "sentiment": 0.1
        }

        total_score = (
            summary_score * weights["summary"] +
            key_points_score * weights["key_points"] +
            insights_score * weights["insights"] +
            sentiment_score * weights["sentiment"]
        )

        return round(total_score, 2)

    def _score_summary_length(self, summary: str) -> float:
        """
        Score based on summary length and quality

        Args:
            summary: Summary text

        Returns:
            Score between 0.0 and 1.0
        """
        if not summary:
            return 0.0

        length = len(summary)

        # Optimal range: 50-200 characters
        if length < 20:
            return 0.2
        elif length < 50:
            return 0.5
        elif length <= 200:
            return 1.0
        elif length <= 300:
            return 0.8
        else:
            return 0.6  # Too long

    def _score_key_points_count(self, key_points: List[str]) -> float:
        """
        Score based on number of key points

        Args:
            key_points: List of key points

        Returns:
            Score between 0.0 and 1.0
        """
        if not key_points:
            return 0.0

        count = len(key_points)

        # Optimal range: 3-5 key points
        if count == 0:
            return 0.0
        elif count == 1:
            return 0.3
        elif count == 2:
            return 0.6
        elif count in [3, 4, 5]:
            return 1.0
        elif count <= 7:
            return 0.8
        else:
            return 0.5  # Too many

    def _score_insights_depth(self, insights: str) -> float:
        """
        Score based on insights depth and detail

        Args:
            insights: Insights text

        Returns:
            Score between 0.0 and 1.0
        """
        if not insights:
            return 0.0

        length = len(insights)

        # Check for strategic keywords that indicate depth
        strategic_keywords = [
            "strategic", "competitive", "market", "positioning",
            "innovation", "trend", "opportunity", "advantage",
            "leadership", "growth", "expansion", "transformation"
        ]

        keyword_count = sum(1 for keyword in strategic_keywords if keyword.lower() in insights.lower())

        # Base score on length
        if length < 20:
            length_score = 0.2
        elif length < 50:
            length_score = 0.4
        elif length <= 150:
            length_score = 0.8
        elif length <= 300:
            length_score = 1.0
        else:
            length_score = 0.9

        # Boost score based on strategic keywords
        keyword_boost = min(keyword_count * 0.1, 0.3)

        return min(length_score + keyword_boost, 1.0)

    def _score_sentiment_confidence(self, sentiment: str) -> float:
        """
        Score based on sentiment clarity

        Args:
            sentiment: Sentiment value (positive, negative, neutral)

        Returns:
            Score between 0.0 and 1.0
        """
        # Clear sentiment (positive/negative) is more valuable than neutral
        sentiment_scores = {
            "positive": 1.0,
            "negative": 1.0,
            "neutral": 0.7
        }

        return sentiment_scores.get(sentiment.lower(), 0.5)

    def update_quality_scores(
        self,
        insight_ids: List[int],
        db: Session
    ) -> Dict[str, int]:
        """
        Update quality scores for multiple insights

        Args:
            insight_ids: List of insight IDs to update
            db: Database session

        Returns:
            Dictionary with updated and failed counts
        """
        updated_count = 0
        failed_count = 0

        for insight_id in insight_ids:
            try:
                insight = db.query(ProcessedInsights).filter(
                    ProcessedInsights.id == insight_id
                ).first()

                if insight:
                    quality_score = self.calculate_quality_score(insight)
                    insight.quality_score = quality_score
                    db.commit()
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
                db.rollback()

        return {
            "updated": updated_count,
            "failed": failed_count
        }

    def get_quality_distribution(self, db: Session) -> Dict[str, int]:
        """
        Get distribution of quality scores

        Args:
            db: Database session

        Returns:
            Dictionary with counts for high, medium, low quality
        """
        insights = db.query(ProcessedInsights).filter(
            ProcessedInsights.quality_score.isnot(None)
        ).all()

        distribution = {
            "high": 0,    # >= 0.7
            "medium": 0,  # 0.4 - 0.69
            "low": 0      # < 0.4
        }

        for insight in insights:
            score = insight.quality_score
            if score >= 0.7:
                distribution["high"] += 1
            elif score >= 0.4:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution