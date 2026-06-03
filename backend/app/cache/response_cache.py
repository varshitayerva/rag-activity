"""Layer 3: Response Cache for full LLM responses."""

import json
import hashlib
from typing import Optional, Dict, Any, Callable, Awaitable
from backend.app.cache.search_context import GenerationResponse
from backend.app.cache.redis_cache import RedisCache
from backend.app.cache.metrics import MetricsCollector
from backend.app.config import get_settings


class ResponseCache:
    """
    Cache full LLM-generated responses.

    This layer caches the complete response (text + sources + tokens) to avoid
    re-generation for identical or very similar queries. Has the shortest TTL (2h)
    since responses are the most volatile (may need updates if docs change).
    """

    def __init__(self):
        self.redis_cache = RedisCache()

    async def get_response_cached(
        self,
        query: str,
        fetch_generation_fn: Callable[[str], Awaitable[GenerationResponse]],
    ) -> GenerationResponse:
        """
        Get LLM response with caching (Layer 3).

        Args:
            query: Original user query
            fetch_generation_fn: Async function to generate response if not cached

        Returns:
            GenerationResponse with text, sources, and token counts

        Example:
            >>> response = await cache.get_response_cached(
            ...     query="How do I restart a pod?",
            ...     fetch_generation_fn=generate_response
            ... )
        """
        settings = get_settings()
        cache_key = self._make_response_cache_key(query)

        # Try cache hit
        cached = await self._get_cached_response(cache_key)
        if cached is not None:
            MetricsCollector.record_response_hit()
            return cached

        # Cache miss: generate response
        MetricsCollector.record_response_miss()
        response = await fetch_generation_fn(query)

        # Store in cache
        await self._store_cached_response(
            cache_key,
            response,
            settings.response_cache_ttl
        )

        return response

    async def _get_cached_response(self, key: str) -> Optional[GenerationResponse]:
        """Retrieve cached response."""
        redis = await self.redis_cache.get_connection()
        cached = await redis.get(key)
        if cached:
            try:
                data = json.loads(cached)
                return GenerationResponse.from_dict(data)
            except Exception:
                return None
        return None

    async def _store_cached_response(
        self,
        key: str,
        response: GenerationResponse,
        ttl: int
    ) -> None:
        """Store response in cache."""
        redis = await self.redis_cache.get_connection()
        try:
            await redis.setex(
                key,
                ttl,
                json.dumps(response.to_dict()),
            )
        except Exception:
            pass  # Non-critical: cache write failure doesn't break generation

    @staticmethod
    def _make_response_cache_key(query: str) -> str:
        """Create response cache key."""
        hash_suffix = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"response:{hash_suffix}"

    async def invalidate_response(self, query: str) -> None:
        """
        Invalidate cached response for a query.

        Useful when documents are updated and cached responses become stale.
        """
        redis = await self.redis_cache.get_connection()
        key = self._make_response_cache_key(query)
        await redis.delete(key)

    async def clear_cache(self) -> None:
        """Clear all response cache entries."""
        redis = await self.redis_cache.get_connection()
        keys = await redis.keys("response:*")
        if keys:
            await redis.delete(*keys)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get response cache statistics."""
        redis = await self.redis_cache.get_connection()
        keys = await redis.keys("response:*")

        return {
            "response_cache_entries": len(keys or []),
            "ttl_seconds": get_settings().response_cache_ttl,
        }


# Singleton instance
_response_cache: Optional[ResponseCache] = None


def get_response_cache() -> ResponseCache:
    """Get or create response cache singleton."""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache
