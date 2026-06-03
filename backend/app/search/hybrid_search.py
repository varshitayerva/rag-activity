import time
from typing import List, Dict, Any, Optional
from .qdrant_client import QdrantVectorDB
from .embeddings import EmbeddingsClient
from .bm25_search import BM25SearchEngine
from .rrf_fusion import RRFFusion

class HybridSearchService:
    """Hybrid search combining vector (Qdrant) + sparse (BM25) search with RRF fusion."""

    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333,
                 openai_api_key: str = None):
        self.vector_db = QdrantVectorDB(host=qdrant_host, port=qdrant_port)
        self.embeddings = EmbeddingsClient(api_key=openai_api_key)
        self.bm25 = BM25SearchEngine()
        self.rrf = RRFFusion()

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Index chunks in both Qdrant (vector) and BM25 (sparse).

        Args:
            chunks: List of chunk dicts with 'chunk_id', 'text', 'doc_id', etc.
        """
        print(f"Indexing {len(chunks)} chunks...")

        # Embed chunks and add to Qdrant
        embeddings = self.embeddings.embed_chunks(chunks)
        self.vector_db.add_points(chunks, embeddings)

        # Build BM25 index
        texts = [chunk['text'] for chunk in chunks]
        self.bm25.build_index(texts)

        print("Indexing complete (Qdrant + BM25)")

    async def search(self, query: str, top_k: int = 20,
                    metadata_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform hybrid search using vector + BM25 with RRF fusion.

        Args:
            query: User query string
            top_k: Number of final results to return
            metadata_filter: Optional metadata filters (department, category, date range)

        Returns:
            Dict with search results and latency breakdown
        """
        latency = {}
        start_time = time.time()

        # Stage 1: Embed query
        embed_start = time.time()
        query_embedding = self.embeddings.embed_query(query)
        latency['embedding_ms'] = int((time.time() - embed_start) * 1000)

        # Stage 2: Vector search in Qdrant
        vector_start = time.time()
        vector_results = self.vector_db.search(query_embedding, top_k=50)
        latency['vector_search_ms'] = int((time.time() - vector_start) * 1000)

        # Stage 3: BM25 search
        bm25_start = time.time()
        bm25_results = self.bm25.search(query, top_k=50)
        latency['bm25_search_ms'] = int((time.time() - bm25_start) * 1000)

        # Stage 4: RRF fusion
        fusion_start = time.time()
        fused_results = self.rrf.fuse(vector_results, bm25_results, k=60)
        latency['rrf_fusion_ms'] = int((time.time() - fusion_start) * 1000)

        # Stage 5: Apply metadata filter
        filter_start = time.time()
        if metadata_filter:
            # Note: Need to map fused results back to full payload for filtering
            filtered_results = self.rrf.apply_metadata_filter(fused_results, metadata_filter)
        else:
            filtered_results = fused_results
        latency['metadata_filter_ms'] = int((time.time() - filter_start) * 1000)

        # Truncate to top_k
        final_results = filtered_results[:top_k]

        latency['total_ms'] = int((time.time() - start_time) * 1000)

        return {
            'query': query,
            'chunks': final_results,
            'search_type': 'hybrid',
            'num_results': len(final_results),
            'latency_ms': latency,
        }

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed data."""
        return {
            'qdrant_documents': self.vector_db.client.count(self.vector_db.collection_name).count,
            'bm25_documents': self.bm25.get_corpus_size(),
            'vector_dimension': self.vector_db.vector_size,
            'embedding_model': self.embeddings.model,
        }
