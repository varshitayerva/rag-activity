import time
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from .postgres_client import PostgresVectorDB
from .embeddings import EmbeddingsClient
from .bm25_search import BM25SearchEngine
from .rrf_fusion import RRFFusion

load_dotenv()
logger = logging.getLogger(__name__)

class HybridSearchService:
    """Hybrid search combining vector (PostgreSQL+pgvector) + sparse (BM25) search with RRF fusion."""

    def __init__(self, postgres_host: str = None, postgres_user: str = None,
                 postgres_password: str = None, postgres_db: str = None,
                 openai_api_key: str = None):
        # Use environment variables if not provided
        postgres_host = postgres_host or os.getenv("DB_HOST", "localhost")
        postgres_user = postgres_user or os.getenv("DB_USER", "postgres")
        postgres_password = postgres_password or os.getenv("DB_PASSWORD", "postgres")
        postgres_db = postgres_db or os.getenv("DB_NAME", "fde_rag")

        self.vector_db = PostgresVectorDB(
            host=postgres_host,
            user=postgres_user,
            password=postgres_password,
            database=postgres_db
        )
        self.embeddings = EmbeddingsClient(api_key=openai_api_key)
        self.bm25 = BM25SearchEngine()
        self.rrf = RRFFusion()

        # Try to load persisted BM25 index
        if not self.bm25.load_index():
            logger.info("No persisted BM25 index found, initializing from PostgreSQL...")
            self._initialize_bm25_index()

    def _initialize_bm25_index(self):
        """Load existing chunks from PostgreSQL into BM25 index."""
        try:
            chunks = self.vector_db.get_all_chunks()
            if chunks:
                texts = [chunk['text'] for chunk in chunks]
                self.bm25.build_index(texts, chunks)
                logger.info(f"Initialized BM25 with {len(chunks)} existing chunks")
            else:
                logger.info("No chunks found in database for BM25 initialization")
        except Exception as e:
            logger.error(f"Failed to initialize BM25 from database: {e}")

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Index chunks in both PostgreSQL+pgvector (vector) and BM25 (sparse).

        Args:
            chunks: List of chunk dicts with 'chunk_id', 'text', 'doc_id', etc.
        """
        print(f"Indexing {len(chunks)} chunks...")

        # Embed chunks and add to PostgreSQL with pgvector
        embeddings = self.embeddings.embed_chunks(chunks)
        self.vector_db.add_points(chunks, embeddings)

        # Build BM25 index for full-text search
        texts = [chunk['text'] for chunk in chunks]
        self.bm25.build_index(texts, chunks)

        print("Indexing complete (PostgreSQL pgvector + BM25)")

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

        # Stage 2: Vector search in PostgreSQL with pgvector
        vector_start = time.time()
        vector_results = self.vector_db.search(query_embedding, top_k=50)
        latency['vector_search_ms'] = int((time.time() - vector_start) * 1000)

        # Stage 3: BM25 search
        bm25_start = time.time()
        bm25_results = self.bm25.search(query, top_k=50)
        latency['bm25_search_ms'] = int((time.time() - bm25_start) * 1000)

        # Stage 4: RRF fusion with adaptive k
        fusion_start = time.time()
        corpus_size = self.vector_db.get_count()
        fused_results = self.rrf.fuse(vector_results, bm25_results, corpus_size=corpus_size)
        latency['rrf_fusion_ms'] = int((time.time() - fusion_start) * 1000)

        # Stage 5: Apply metadata filter
        filter_start = time.time()
        if metadata_filter and 'document_ids' not in metadata_filter:
            # Note: Need to map fused results back to full payload for filtering
            filtered_results = self.rrf.apply_metadata_filter(fused_results, metadata_filter)
        else:
            filtered_results = fused_results
        latency['metadata_filter_ms'] = int((time.time() - filter_start) * 1000)

        # Truncate to top_k
        final_results = filtered_results[:top_k]

        # Calculate confidence scores from actual vector similarity (cosine similarity 0-1)
        # Use the top vector search result's similarity score (not RRF score)
        confidence_score = 0.5
        if vector_results and len(vector_results) > 0:
            # vector_results[0]['score'] is the actual cosine similarity from postgres (0-1 range)
            # This is the real relevance score, not the RRF-fused score
            top_vector_similarity = float(vector_results[0].get('score', 0.5))
            confidence_score = max(0.0, min(1.0, top_vector_similarity))
            logger.info(f"Query confidence: {confidence_score:.3f} (from vector similarity)")

        # Add confidence score and level to results
        for result in final_results:
            result['confidence_score'] = confidence_score
            # Determine confidence level
            if confidence_score >= 0.7:
                result['confidence_level'] = 'high'
            elif confidence_score >= 0.4:
                result['confidence_level'] = 'medium'
            else:
                result['confidence_level'] = 'low'

        # Return empty if no results found
        if not final_results:
            logger.warning(f"No results found for query: {query}")
            return {
                'query': query,
                'chunks': [],
                'search_type': 'hybrid',
                'num_results': 0,
                'latency_ms': latency,
                'error': 'No relevant documents found. Please refine your search query.'
            }

        latency['total_ms'] = int((time.time() - start_time) * 1000)

        return {
            'query': query,
            'chunks': final_results,
            'search_type': 'hybrid',
            'num_results': len(final_results),
            'confidence_score': round(confidence_score, 3),
            'latency_ms': latency,
        }

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed data."""
        corpus_size = self.vector_db.get_count()
        optimal_k = self.rrf.get_optimal_k(corpus_size)

        return {
            'postgres_vectors': corpus_size,
            'bm25_documents': self.bm25.get_corpus_size(),
            'vector_dimension': self.vector_db.vector_size,
            'embedding_model': self.embeddings.model,
            'rrf_k': optimal_k,
            'corpus_size_category': 'small' if corpus_size < 1_000 else 'medium' if corpus_size < 10_000 else 'large',
        }
