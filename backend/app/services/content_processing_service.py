import re
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models import RawContent, ProcessedInsights
from app.services.openai_client import OpenAIClient
from app.services.quality_scoring_service import QualityScoringService


class ContentProcessingService:
    """Service for processing raw content into insights using AI"""

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        self.openai_client = openai_client or OpenAIClient()
        self.quality_scorer = QualityScoringService()
    
    def process_raw_content(self, raw_content_id: int, db: Session) -> Optional[ProcessedInsights]:
        """Process raw content and create insights"""
        try:
            # Get raw content
            raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
            if not raw_content:
                return None
            
            # Check if already processed
            existing_insights = db.query(ProcessedInsights).filter(
                ProcessedInsights.raw_content_id == raw_content_id
            ).first()
            if existing_insights:
                return existing_insights
            
            # Process content with OpenAI
            summary = self.openai_client.summarize_content(raw_content.content)
            insights = self.openai_client.extract_insights(raw_content.content)
            sentiment = self.openai_client.analyze_sentiment(raw_content.content)
            
            if not summary or not sentiment:
                return None
            
            # Ensure insights is not None (can be empty string)
            if insights is None:
                insights = ""
            
            # Extract key points
            key_points = self._extract_key_points(raw_content.content)
            
            # Create processed insights
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

            # Calculate and store quality score
            quality_score = self.quality_scorer.calculate_quality_score(processed_insights)
            processed_insights.quality_score = quality_score
            db.commit()
            db.refresh(processed_insights)

            return processed_insights
            
        except Exception:
            return None
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content using simple text processing"""
        # Split content into sentences
        sentences = re.split(r'[.!?]+', content)
        
        # Filter sentences and extract key points
        key_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                # Look for sentences with important keywords
                important_words = ['announces', 'launches', 'features', 'available', 'new', 'product', 'service']
                if any(word in sentence.lower() for word in important_words):
                    key_points.append(sentence)
        
        # Return first 5 key points
        return key_points[:5] if key_points else ["Content processed"]