import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from typing import List, Optional, Dict, Any

class QdrantVectorDB:
    def __init__(self, collection_name: str = "technical-support-chunks",
                 storage_path: str = "./qdrant_storage"):
        self.client = QdrantClient(":memory:")
        print("Using in-memory Qdrant database")
        self.collection_name = collection_name
        self.vector_size = 1536  # OpenAI text-embedding-3-small dimension
        self.ensure_collection_exists()

    def ensure_collection_exists(self):
        """Create Qdrant collection with HNSW index if it doesn't exist."""
        try:
            self.client.get_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' already exists")
        except Exception:
            print(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                ),
                # HNSW index configuration for fast approximate search
                hnsw_config={
                    "m": 16,  # number of connections per point
                    "ef_construct": 100,  # construction parameter
                    "ef": 100,  # search parameter
                    "max_m": 16,
                    "max_m_0": 32,
                    "ef_construct_threshold": 10000,
                }
            )
            print(f"Collection '{self.collection_name}' created with HNSW index")

    def add_points(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add chunks with embeddings to Qdrant collection.

        Args:
            chunks: List of chunk dicts with 'chunk_id', 'text', 'doc_id', 'section', 'page', etc.
            embeddings: List of embedding vectors (same length as chunks)
        """
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=hash(chunk['chunk_id']) & 0x7fffffff,  # ensure positive int
                vector=embedding,
                payload={
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'doc_id': chunk.get('doc_id', ''),
                    'filename': chunk.get('filename', ''),
                    'section': chunk.get('section', ''),
                    'page': chunk.get('page', 0),
                    'department': chunk.get('department', ''),
                    'category': chunk.get('category', ''),
                    'uploaded_at': chunk.get('uploaded_at', ''),
                }
            )
            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Added {len(points)} points to Qdrant collection")

    def search(self, query_vector: List[float], top_k: int = 50) -> List[Dict[str, Any]]:
        """Search for similar vectors in Qdrant.

        Args:
            query_vector: Query embedding vector
            top_k: Number of top results to return

        Returns:
            List of search results with scores and payload
        """
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )

        return [
            {
                'chunk_id': result.payload.get('chunk_id'),
                'text': result.payload.get('text'),
                'doc_id': result.payload.get('doc_id'),
                'filename': result.payload.get('filename'),
                'section': result.payload.get('section'),
                'page': result.payload.get('page'),
                'department': result.payload.get('department'),
                'category': result.payload.get('category'),
                'score': result.score,  # cosine similarity [0, 1]
                'rank': idx
            }
            for idx, result in enumerate(results)
        ]

    def get_all_texts(self) -> List[str]:
        """Retrieve all chunk texts for BM25 indexing."""
        try:
            # Scroll through all points to get texts
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True
            )
            return [point.payload.get('text', '') for point in points]
        except Exception as e:
            print(f"Error retrieving texts from Qdrant: {e}")
            return []

    def delete_collection(self):
        """Delete the collection (for testing/reset)."""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' deleted")
        except Exception as e:
            print(f"Error deleting collection: {e}")
