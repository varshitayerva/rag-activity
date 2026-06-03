"""Unified cache manager integrating all 3 layers."""

import time
from typing import Optional, Dict, Any, Callable, Awaitable, List
from app.cache.redis_cache import RedisCache
from app.cache.retrieval_cache import RetrievalCache, get_retrieval_cache
from app.cache.response_cache import ResponseCache, get_response_cache
from app.cache.compression import ContextCompressor, get_compressor
from app.cache.latency import LatencyBreakdown, PerformanceAnalyzer
from app.cache.search_context import SearchResult, GenerationResponse, Chunk
from app.cache.metrics import MetricsCollector
from app.config import get_settings


class CacheManager:
    """
    Unified interface for all 3 cache layers.

    Orchestrates caching across:
    - Layer 1: Embedding cache (24h TTL, 50-70% target hit rate)
    - Layer 2: Retrieval cache (4h TTL, 30-50% target hit rate)
    - Layer 3: Response cache (2h TTL, 10-20% target hit rate)
    """

    def __init__(self):
        self.redis_cache = RedisCache()
        self.retrieval_cache = get_retrieval_cache()
        self.response_cache = get_response_cache()
        self.compressor = get_compressor()

    # ─── LAYER 1: EMBEDDING CACHE ───
    async def get_embedding(
        self,
        query: str,
        fetch_embedding_fn: Callable[[str], Awaitable[List[float]]],
    ) -> List[float]:
        """
        Get embedding vector with caching (Layer 1).

        Args:
            query: Text to embed
            fetch_embedding_fn: Async function to generate embedding if not cached

        Returns:
            Embedding vector (list of floats)
        """
        return await self.redis_cache.get_embedding_cached(query, fetch_embedding_fn)

    # ─── LAYER 2: RETRIEVAL CACHE ───
    async def get_search_results(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        fetch_search_fn: Callable[[str, Optional[Dict[str, Any]]], Awaitable[SearchResult]],
    ) -> SearchResult:
        """
        Get search results with caching (Layer 2).

        Combines vector search and BM25 via hybrid search, with results cached
        per (query, filter) combination.

        Args:
            query: Search query
            filters: Optional metadata filters
            fetch_search_fn: Async function to execute hybrid search

        Returns:
            SearchResult with ranked chunks
        """
        return await self.retrieval_cache.get_search_results_cached(
            query, filters, fetch_search_fn
        )

    # ─── LAYER 3: RESPONSE CACHE ───
    async def get_response(
        self,
        query: str,
        fetch_generation_fn: Callable[[str], Awaitable[GenerationResponse]],
    ) -> GenerationResponse:
        """
        Get LLM response with caching (Layer 3).

        Args:
            query: Original user query
            fetch_generation_fn: Async function to generate response

        Returns:
            GenerationResponse with text, sources, and token counts
        """
        return await self.response_cache.get_response_cached(
            query, fetch_generation_fn
        )

    # ─── FULL PIPELINE WITH INSTRUMENTATION ───
    async def full_pipeline(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        embed_fn: Callable[[str], Awaitable[List[float]]],
        search_fn: Callable[[str, Optional[Dict[str, Any]]], Awaitable[SearchResult]],
        generate_fn: Callable[[str], Awaitable[GenerationResponse]],
    ) -> Dict[str, Any]:
        """
        Execute full RAG pipeline with caching and latency tracking.

        Flow:
        1. Embed query (Layer 1) → 100ms cold / 0ms warm
        2. Hybrid search (Layer 2) → 350ms cold / 0ms warm
        3. Generate response (Layer 3) → 1800ms cold / 0ms warm
        Total: 2250ms cold, <5ms warm (all cache hits)

        Args:
            query: User query
            filters: Metadata filters
            embed_fn: Embedding function
            search_fn: Hybrid search function
            generate_fn: Response generation function

        Returns:
            {
                "response": GenerationResponse,
                "search_results": SearchResult,
                "latency_breakdown": {
                    "embedding_ms": float,
                    "search_ms": float,
                    "generation_ms": float,
                    "total_ms": float
                },
                "cache_hits": {
                    "embedding": bool,
                    "search": bool,
                    "response": bool
                }
            }
        """
        start_time = time.time()
        latency_breakdown = {}
        cache_hits = {}

        # Step 1: Get embedding (Layer 1)
        embedding_start = time.time()
        embedding_metrics_before = {
            "hits": MetricsCollector.get_instance().embedding_cache_hits,
            "misses": MetricsCollector.get_instance().embedding_cache_misses,
        }

        embedding = await self.get_embedding(query, embed_fn)
        embedding_time = (time.time() - embedding_start) * 1000

        embedding_metrics_after = {
            "hits": MetricsCollector.get_instance().embedding_cache_hits,
            "misses": MetricsCollector.get_instance().embedding_cache_misses,
        }
        cache_hits["embedding"] = (
            embedding_metrics_after["hits"] > embedding_metrics_before["hits"]
        )
        latency_breakdown["embedding_ms"] = embedding_time

        # Step 2: Hybrid search (Layer 2)
        search_start = time.time()
        search_metrics_before = {
            "hits": MetricsCollector.get_instance().retrieval_cache_hits,
            "misses": MetricsCollector.get_instance().retrieval_cache_misses,
        }

        search_results = await self.get_search_results(query, filters, search_fn)
        search_time = (time.time() - search_start) * 1000

        search_metrics_after = {
            "hits": MetricsCollector.get_instance().retrieval_cache_hits,
            "misses": MetricsCollector.get_instance().retrieval_cache_misses,
        }
        cache_hits["search"] = (
            search_metrics_after["hits"] > search_metrics_before["hits"]
        )
        latency_breakdown["search_ms"] = search_time

        # Step 3: Generate response (Layer 3)
        generation_start = time.time()
        response_metrics_before = {
            "hits": MetricsCollector.get_instance().response_cache_hits,
            "misses": MetricsCollector.get_instance().response_cache_misses,
        }

        response = await self.get_response(query, generate_fn)
        generation_time = (time.time() - generation_start) * 1000

        response_metrics_after = {
            "hits": MetricsCollector.get_instance().response_cache_hits,
            "misses": MetricsCollector.get_instance().response_cache_misses,
        }
        cache_hits["response"] = (
            response_metrics_after["hits"] > response_metrics_before["hits"]
        )
        latency_breakdown["generation_ms"] = generation_time

        # Total latency
        total_time = (time.time() - start_time) * 1000
        latency_breakdown["total_ms"] = total_time

        # Record latency in metrics
        MetricsCollector.record_latency(total_time)
        MetricsCollector.record_tokens(response.input_tokens, response.output_tokens)

        return {
            "response": response,
            "search_results": search_results,
            "embedding": embedding,
            "latency_breakdown": latency_breakdown,
            "cache_hits": cache_hits,
        }

    # ─── CONTEXT COMPRESSION ───
    def compress_chunks(
        self,
        chunks: List[Chunk],
        max_chunks: int = None,
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """
        Compress search results (top-20 → top-5, 10K → 2.5K tokens).

        Returns:
            {
                "chunks": List[Chunk],
                "original_token_count": int,
                "compressed_token_count": int,
                "reduction_percent": float,
                "chunks_kept": int,
                "chunks_removed": int,
            }
        """
        return self.compressor.compress_chunks(chunks, max_chunks, max_tokens)

    def get_compression_metrics(
        self,
        original_chunks: List[Chunk],
        compressed_chunks: List[Chunk],
    ) -> Dict[str, Any]:
        """Get detailed compression metrics."""
        return self.compressor.get_compression_metrics(
            original_chunks, compressed_chunks
        )

    def format_chunks_for_prompt(
        self,
        chunks: List[Chunk],
        include_metadata: bool = True,
    ) -> str:
        """Format chunks for LLM prompt."""
        return self.compressor.format_chunks_for_prompt(chunks, include_metadata)

    # ─── CACHE MANAGEMENT ───
    async def clear_embedding_cache(self) -> None:
        """Clear Layer 1 cache."""
        await self.redis_cache.clear_embedding_cache()

    async def clear_retrieval_cache(self) -> None:
        """Clear Layer 2 cache."""
        await self.retrieval_cache.clear_cache()

    async def clear_response_cache(self) -> None:
        """Clear Layer 3 cache."""
        await self.response_cache.clear_cache()

    async def clear_all_caches(self) -> None:
        """Clear all cache layers."""
        await self.clear_embedding_cache()
        await self.clear_retrieval_cache()
        await self.clear_response_cache()

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get statistics for all cache layers."""
        redis_stats = await self.redis_cache.get_cache_stats()
        retrieval_stats = await self.retrieval_cache.get_cache_stats()
        response_stats = await self.response_cache.get_cache_stats()

        return {
            "embedding": redis_stats,
            "retrieval": retrieval_stats,
            "response": response_stats,
        }

    async def invalidate_response_for_query(self, query: str) -> None:
        """Invalidate cached response when documents are updated."""
        await self.response_cache.invalidate_response(query)


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager singleton."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
