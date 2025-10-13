import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec


class PineconeClient:
    """Pinecone vector database client for semantic search"""

    def __init__(self):
        """Initialize Pinecone client and index"""
        api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "competitive-intel")

        # Initialize Pinecone
        self.pc = Pinecone(api_key=api_key)

        # Create index if it doesn't exist
        self._ensure_index_exists()

        # Connect to index
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            existing_indexes = self.pc.list_indexes().names()

            if self.index_name not in existing_indexes:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
        except Exception:
            # Index might already exist or creation failed
            pass

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
            return True
        except Exception:
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
            for match in results.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })

            return matches
        except Exception:
            return []

    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors by IDs

        Args:
            ids: List of vector IDs to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.index.delete(ids=ids)
            return True
        except Exception:
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics

        Returns:
            Dictionary with index stats
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count
            }
        except Exception:
            return {"total_vectors": 0}