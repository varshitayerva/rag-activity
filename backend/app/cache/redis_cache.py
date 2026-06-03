import json
import hashlib
from redis import asyncio as aioredis
from typing import Optional, Any, Dict, List
from backend.app.config import get_settings
from backend.app.cache.metrics import MetricsCollector


class RedisCache:
    """Three-layer Redis cache for embeddings, retrieval results, and responses."""

    _instance: Optional[aioredis.Redis] = None

    @classmethod
    async def get_connection(cls) -> aioredis.Redis:
        """Get or create Redis connection."""
        if cls._instance is None:
            settings = get_settings()
            cls._instance = await aioredis.from_url(settings.redis_url)
        return cls._instance

    @classmethod
    async def close(cls):
        """Close Redis connection."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

    @staticmethod
    def _make_key(prefix: str, value: str) -> str:
        """Create a cache key with prefix and hash."""
        hash_suffix = hashlib.md5(value.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_suffix}"

    # ─── LAYER 1: EMBEDDING CACHE ───
    async def get_embedding_cached(
        self, query: str, fetch_fn
    ) -> List[float]:
        """
        Cache embedding lookups (Layer 1).

        Args:
            query: Query string to embed
            fetch_fn: Async function to fetch embedding if not cached

        Returns:
            List of embedding values
        """
        redis = await self.get_connection()
        settings = get_settings()

        key = self._make_key("embedding", query)

        # Try cache hit
        cached = await redis.get(key)
        if cached:
            MetricsCollector.record_embedding_hit()
            return json.loads(cached)

        # Cache miss: fetch embedding
        MetricsCollector.record_embedding_miss()
        embedding = await fetch_fn(query)

        # Store in cache
        await redis.setex(
            key,
            settings.embedding_cache_ttl,
            json.dumps(embedding),
        )

        return embedding

    # ─── LAYER 2: RETRIEVAL CACHE ───
    async def get_retrieval_cached(
        self,
        query: str,
        filter_key: Optional[str],
        fetch_fn,
    ) -> Dict[str, Any]:
        """
        Cache search results (Layer 2).

        Args:
            query: Search query
            filter_key: Metadata filter key (department, category, etc.)
            fetch_fn: Async function to fetch search results if not cached

        Returns:
            Search result dictionary
        """
        redis = await self.get_connection()
        settings = get_settings()

        # Include filter in cache key
        key_suffix = f"{query}:{filter_key or 'no-filter'}"
        key = self._make_key("retrieval", key_suffix)

        # Try cache hit
        cached = await redis.get(key)
        if cached:
            MetricsCollector.record_retrieval_hit()
            return json.loads(cached)

        # Cache miss: fetch results
        MetricsCollector.record_retrieval_miss()
        results = await fetch_fn(query, filter_key)

        # Store in cache
        await redis.setex(
            key,
            settings.retrieval_cache_ttl,
            json.dumps(results),
        )

        return results

    # ─── LAYER 3: RESPONSE CACHE ───
    async def get_response_cached(
        self,
        query: str,
        fetch_fn,
    ) -> Dict[str, Any]:
        """
        Cache full LLM responses (Layer 3).

        Args:
            query: Original query
            fetch_fn: Async function to generate response if not cached

        Returns:
            Response dictionary with sources and text
        """
        redis = await self.get_connection()
        settings = get_settings()

        key = self._make_key("response", query)

        # Try cache hit
        cached = await redis.get(key)
        if cached:
            MetricsCollector.record_response_hit()
            return json.loads(cached)

        # Cache miss: generate response
        MetricsCollector.record_response_miss()
        response = await fetch_fn(query)

        # Store in cache
        await redis.setex(
            key,
            settings.response_cache_ttl,
            json.dumps(response),
        )

        return response

    # ─── CACHE CONTROL ───
    async def clear_embedding_cache(self):
        """Clear all embedding cache entries."""
        redis = await self.get_connection()
        keys = await redis.keys("embedding:*")
        if keys:
            await redis.delete(*keys)

    async def clear_retrieval_cache(self):
        """Clear all retrieval cache entries."""
        redis = await self.get_connection()
        keys = await redis.keys("retrieval:*")
        if keys:
            await redis.delete(*keys)

    async def clear_response_cache(self):
        """Clear all response cache entries."""
        redis = await self.get_connection()
        keys = await redis.keys("response:*")
        if keys:
            await redis.delete(*keys)

    async def clear_all(self):
        """Clear all cache layers."""
        await self.clear_embedding_cache()
        await self.clear_retrieval_cache()
        await self.clear_response_cache()

    async def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        redis = await self.get_connection()

        embedding_keys = await redis.keys("embedding:*")
        retrieval_keys = await redis.keys("retrieval:*")
        response_keys = await redis.keys("response:*")

        return {
            "embedding_cache_entries": len(embedding_keys or []),
            "retrieval_cache_entries": len(retrieval_keys or []),
            "response_cache_entries": len(response_keys or []),
        }
