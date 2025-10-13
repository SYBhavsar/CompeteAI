from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import ProcessedInsights, RawContent, DataSource
from app.services.openai_client import OpenAIClient
from app.services.pinecone_client import PineconeClient


class EmbeddingService:
    """Service for generating and managing embeddings for semantic search"""

    def __init__(
        self,
        openai_client: Optional[OpenAIClient] = None,
        pinecone_client: Optional[PineconeClient] = None
    ):
        self.openai_client = openai_client or OpenAIClient()
        self.pinecone_client = pinecone_client or PineconeClient()

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector from text using OpenAI

        Args:
            text: Text to generate embedding for

        Returns:
            1536-dimensional embedding vector or None on error
        """
        try:
            response = self.openai_client.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception:
            return None

    def store_insight_embedding(
        self,
        insight_id: int,
        db: Session
    ) -> bool:
        """
        Generate and store embedding for a processed insight

        Args:
            insight_id: ID of the processed insight
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get insight with related data
            insight = db.query(ProcessedInsights).join(
                RawContent, ProcessedInsights.raw_content_id == RawContent.id
            ).join(
                DataSource, RawContent.data_source_id == DataSource.id
            ).filter(
                ProcessedInsights.id == insight_id
            ).first()

            if not insight:
                return False

            # Combine summary and insights for embedding
            text_for_embedding = f"{insight.summary}. {insight.insights or ''}"

            # Generate embedding
            embedding = self.generate_embedding(text_for_embedding)
            if not embedding:
                return False

            # Prepare metadata
            metadata = {
                "insight_id": insight.id,
                "competitor_id": insight.raw_content.data_source.competitor_id,
                "summary": insight.summary,
                "sentiment": insight.sentiment,
                "url": insight.raw_content.url,
                "created_at": insight.created_at.isoformat()
            }

            # Store in Pinecone
            vector_id = f"insight_{insight.id}"
            return self.pinecone_client.upsert_embedding(
                vector_id,
                embedding,
                metadata
            )

        except Exception:
            return False

    def search_similar_insights(
        self,
        query_text: str,
        top_k: int = 10,
        competitor_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar insights using semantic search

        Args:
            query_text: Query text to search for
            top_k: Number of results to return
            competitor_id: Optional filter by competitor ID

        Returns:
            List of similar insights with metadata
        """
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query_text)
            if not query_embedding:
                return []

            # Build filter if competitor_id provided
            filter_dict = None
            if competitor_id:
                filter_dict = {"competitor_id": competitor_id}

            # Query Pinecone
            results = self.pinecone_client.query_similar(
                query_embedding,
                top_k=top_k,
                filter=filter_dict
            )

            return results

        except Exception:
            return []

    def batch_store_insights(
        self,
        insight_ids: List[int],
        db: Session
    ) -> Dict[str, int]:
        """
        Store embeddings for multiple insights in batch

        Args:
            insight_ids: List of insight IDs to process
            db: Database session

        Returns:
            Dictionary with success and failed counts
        """
        success_count = 0
        failed_count = 0

        for insight_id in insight_ids:
            if self.store_insight_embedding(insight_id, db):
                success_count += 1
            else:
                failed_count += 1

        return {
            "success": success_count,
            "failed": failed_count
        }

    def delete_insight_embedding(self, insight_id: int) -> bool:
        """
        Delete embedding for an insight from vector database

        Args:
            insight_id: ID of the insight

        Returns:
            True if successful, False otherwise
        """
        try:
            vector_id = f"insight_{insight_id}"
            return self.pinecone_client.delete_vectors([vector_id])
        except Exception:
            return False