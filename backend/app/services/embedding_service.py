from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
from openai import OpenAI

from app.core.config import settings
from app.models import ProcessedInsights, RawContent, DataSource
from app.services.pinecone_client import PineconeClient

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings for semantic search"""

    def __init__(self, pinecone_client: Optional[PineconeClient] = None):
        try:
            self._client = OpenAI(api_key=settings.openai_api_key)
            self.pinecone_client = pinecone_client or PineconeClient()
            logger.info("EmbeddingService initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize EmbeddingService: {e}", exc_info=True)
            raise

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector from text using OpenAI

        Args:
            text: Text to generate embedding for

        Returns:
            1536-dimensional embedding vector or None on error
        """
        logger.debug("Generating embedding...")
        try:
            # Truncate text to avoid exceeding token limits, if necessary
            max_tokens = 8191  # Max tokens for text-embedding-ada-002
            if len(text) > max_tokens * 4: # A rough estimation
                text = text[:max_tokens * 4]
                logger.warning("Input text truncated for embedding generation.")

            response = self._client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            logger.info("Successfully generated embedding.")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding. Error: {e}", exc_info=True)
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
        logger.debug(f"Storing embedding for insight_id: {insight_id}")
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
                logger.warning(f"Insight with id {insight_id} not found.")
                return False

            # Combine summary and insights for embedding
            text_for_embedding = f"{insight.summary}. {insight.insights or ''}"
            logger.debug(f"Text for embedding (insight_id: {insight_id}): '{text_for_embedding[:100]}...'")

            # Generate embedding
            embedding = self.generate_embedding(text_for_embedding)
            if not embedding:
                logger.error(f"Failed to generate embedding for insight_id: {insight_id}")
                return False

            # Prepare metadata
            metadata = {
                "insight_id": insight.id,
                "competitor_id": insight.raw_content.data_source.competitor_id,
                "summary": insight.summary[:200],  # Truncate for metadata limits
                "sentiment": insight.sentiment,
                "url": insight.raw_content.url,
                "created_at": insight.created_at.isoformat()
            }

            # Store in Pinecone
            vector_id = f"insight_{insight.id}"
            success = self.pinecone_client.upsert_embedding(
                vector_id,
                embedding,
                metadata
            )
            if success:
                logger.info(f"Successfully stored embedding for insight_id: {insight_id}")
            else:
                logger.error(f"Failed to store embedding for insight_id: {insight_id} in Pinecone.")
            return success

        except Exception as e:
            logger.error(f"An unexpected error occurred while storing insight embedding for id {insight_id}. Error: {e}", exc_info=True)
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
        logger.debug(f"Searching for insights similar to: '{query_text[:100]}...'")
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query_text)
            if not query_embedding:
                logger.error("Failed to generate query embedding. Cannot perform search.")
                return []

            # Build filter if competitor_id provided
            filter_dict = None
            if competitor_id:
                filter_dict = {"competitor_id": competitor_id}
                logger.debug(f"Applying filter: {filter_dict}")

            # Query Pinecone
            results = self.pinecone_client.query_similar(
                query_embedding,
                top_k=top_k,
                filter=filter_dict
            )
            
            logger.info(f"Semantic search returned {len(results)} results.")
            return results

        except Exception as e:
            logger.error(f"Failed to search for similar insights. Error: {e}", exc_info=True)
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
        logger.info(f"Starting batch processing for {len(insight_ids)} insights.")
        success_count = 0
        failed_count = 0

        for insight_id in insight_ids:
            if self.store_insight_embedding(insight_id, db):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Batch processing complete. Success: {success_count}, Failed: {failed_count}")
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
        logger.debug(f"Deleting embedding for insight_id: {insight_id}")
        try:
            vector_id = f"insight_{insight_id}"
            success = self.pinecone_client.delete_vectors([vector_id])
            if success:
                logger.info(f"Successfully deleted embedding for insight_id: {insight_id}")
            else:
                logger.error(f"Failed to delete embedding for insight_id: {insight_id} from Pinecone.")
            return success
        except Exception as e:
            logger.error(f"Failed to delete insight embedding for id {insight_id}. Error: {e}", exc_info=True)
            return False