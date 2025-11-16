import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import logging

logger = logging.getLogger(__name__)



class PineconeClient:
    """Pinecone vector database client for semantic search"""

    def __init__(self):
        """Initialize Pinecone client and index"""
        try:
            api_key = os.getenv("PINECONE_API_KEY")
            self.index_name = os.getenv("PINECONE_INDEX_NAME", "competitive-intel")

            if not api_key:
                logger.error("PINECONE_API_KEY not found in environment variables.")
                raise ValueError("PINECONE_API_KEY is required.")

            # Initialize Pinecone
            self.pc = Pinecone(api_key=api_key)
            logger.info("Pinecone client initialized.")

            # Create index if it doesn't exist
            self._ensure_index_exists()

            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")

        except Exception as e:
            logger.critical(f"Failed to initialize PineconeClient: {e}", exc_info=True)
            raise

    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            existing_indexes = self.pc.list_indexes().names()
            if self.index_name not in existing_indexes:
                logger.info(f"Index '{self.index_name}' not found. Creating new index...")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Index '{self.index_name}' created successfully.")
            else:
                logger.info(f"Index '{self.index_name}' already exists.")
        except Exception as e:
            logger.error(f"Error checking or creating index '{self.index_name}': {e}", exc_info=True)
            # If index creation fails, it's a critical issue for the service's operation.
            raise

    def upsert_embedding(
        self,
        vector_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Insert or update a vector embedding

        Args:
            vector_id: Unique ID for the vector
            embedding: Vector embedding (1536 dimensions)
            metadata: Metadata to store with vector

        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Upserting vector_id: {vector_id}")
        try:
            self.index.upsert(
                vectors=[
                    {
                        "id": vector_id,
                        "values": embedding,
                        "metadata": metadata
                    }
                ]
            )
            logger.info(f"Successfully upserted vector_id: {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vector_id: {vector_id}. Error: {e}", exc_info=True)
            return False

    def query_similar(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar vectors

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of similar vectors with metadata
        """
        logger.debug(f"Querying for {top_k} similar vectors.")
        try:
            query_params = {
                "vector": query_vector,
                "top_k": top_k,
                "include_metadata": True
            }

            if filter:
                query_params["filter"] = filter

            results = self.index.query(**query_params)
            
            # Format results
            matches = []
            if results.matches:
                for match in results.matches:
                    matches.append({
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata
                    })
            
            logger.info(f"Query returned {len(matches)} results.")
            return matches
        except Exception as e:
            logger.error(f"Failed to query similar vectors. Error: {e}", exc_info=True)
            return []

    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors by IDs

        Args:
            ids: List of vector IDs to delete

        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Deleting {len(ids)} vectors.")
        try:
            self.index.delete(ids=ids)
            logger.info(f"Successfully deleted {len(ids)} vectors.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vectors. Error: {e}", exc_info=True)
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics

        Returns:
            Dictionary with index stats
        """
        logger.debug("Fetching index stats.")
        try:
            stats = self.index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            logger.info(f"Index stats: total_vectors={total_vectors}")
            return {
                "total_vectors": total_vectors
            }
        except Exception as e:
            logger.error(f"Failed to get index stats. Error: {e}", exc_info=True)
            return {"total_vectors": 0}