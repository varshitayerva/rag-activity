"""Layer 2: Retrieval Cache for hybrid search results."""

import json
import hashlib
from typing import Optional, Dict, Any, Callable, Awaitable
from backend.app.cache.search_context import SearchResult
from backend.app.cache.redis_cache import RedisCache
from backend.app.cache.metrics import MetricsCollector
from backend.app.config import get_settings


class RetrievalCache:
    """
    Cache search results from hybrid search (vector + BM25).

    Stores results per (query + filter combination) to support different
    metadata filter scenarios (department, category, date ranges, etc.).
    """

    def __init__(self):
        self.redis_cache = RedisCache()

    @staticmethod
    def _make_filter_key(filters: Optional[Dict[str, Any]]) -> str:
        """Create a deterministic key from filters."""
        if not filters:
            return "no_filter"

        # Sort keys for consistency
        sorted_items = sorted(filters.items())
        filter_str = json.dumps(sorted_items)
        return hashlib.md5(filter_str.encode()).hexdigest()[:8]

    async def get_search_results_cached(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        fetch_search_fn: Callable[[str, Optional[Dict[str, Any]]], Awaitable[SearchResult]],
    ) -> SearchResult:
        """
        Get search results with caching (Layer 2).

        Args:
            query: Search query
            filters: Optional metadata filters (department, category, date_from, date_to)
            fetch_search_fn: Async function to execute hybrid search if not cached

        Returns:
            SearchResult with chunks and latency breakdown

        Example:
            >>> result = await cache.get_search_results_cached(
            ...     query="How do I fix ImagePullBackOff?",
            ...     filters={"department": "platform", "category": "errors"},
            ...     fetch_search_fn=hybrid_search
            ... )
        """
        settings = get_settings()
        filter_key = self._make_filter_key(filters)
        cache_key = self._make_retrieval_cache_key(query, filter_key)

        # Try cache hit
        cached = await self._get_cached_result(cache_key)
        if cached is not None:
            MetricsCollector.record_retrieval_hit()
            return cached

        # Cache miss: execute hybrid search
        MetricsCollector.record_retrieval_miss()
        search_result = await fetch_search_fn(query, filters)

        # Store in cache
        await self._store_cached_result(
            cache_key,
            search_result,
            settings.retrieval_cache_ttl
        )

        return search_result

    async def _get_cached_result(self, key: str) -> Optional[SearchResult]:
        """Retrieve cached search result."""
        redis = await self.redis_cache.get_connection()
        cached = await redis.get(key)
        if cached:
            try:
                data = json.loads(cached)
                return SearchResult.from_dict(data)
            except Exception:
                return None
        return None

    async def _store_cached_result(
        self,
        key: str,
        result: SearchResult,
        ttl: int
    ) -> None:
        """Store search result in cache."""
        redis = await self.redis_cache.get_connection()
        try:
            await redis.setex(
                key,
                ttl,
                json.dumps(result.to_dict()),
            )
        except Exception:
            pass  # Non-critical: cache write failure doesn't break search

    @staticmethod
    def _make_retrieval_cache_key(query: str, filter_key: str) -> str:
        """Create retrieval cache key."""
        key_suffix = f"{query}:{filter_key}"
        hash_suffix = hashlib.md5(key_suffix.encode()).hexdigest()[:8]
        return f"retrieval:{hash_suffix}"

    async def clear_cache(self) -> None:
        """Clear all retrieval cache entries."""
        redis = await self.redis_cache.get_connection()
        keys = await redis.keys("retrieval:*")
        if keys:
            await redis.delete(*keys)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get retrieval cache statistics."""
        redis = await self.redis_cache.get_connection()
        keys = await redis.keys("retrieval:*")

        return {
            "retrieval_cache_entries": len(keys or []),
            "ttl_seconds": get_settings().retrieval_cache_ttl,
        }


# Singleton instance
_retrieval_cache: Optional[RetrievalCache] = None


def get_retrieval_cache() -> RetrievalCache:
    """Get or create retrieval cache singleton."""
    global _retrieval_cache
    if _retrieval_cache is None:
        _retrieval_cache = RetrievalCache()
    return _retrieval_cache
