import json
import hashlib
from typing import Optional, List
import redis
from app.config import get_settings

settings = get_settings()


class CacheMetrics:
    def __init__(self):
        self.embedding_hits = 0
        self.embedding_misses = 0
        self.retrieval_hits = 0
        self.retrieval_misses = 0
        self.response_hits = 0
        self.response_misses = 0
        self.total_queries = 0
        self.total_tokens_in_context = 0

    def get_hit_rate(self) -> float:
        total_checks = (
            self.embedding_hits + self.embedding_misses +
            self.retrieval_hits + self.retrieval_misses +
            self.response_hits + self.response_misses
        )
        if total_checks == 0:
            return 0.0
        total_hits = self.embedding_hits + self.retrieval_hits + self.response_hits
        return total_hits / total_checks

    def to_dict(self) -> dict:
        return {
            "embedding_hits": self.embedding_hits,
            "embedding_misses": self.embedding_misses,
            "retrieval_hits": self.retrieval_hits,
            "retrieval_misses": self.retrieval_misses,
            "response_hits": self.response_hits,
            "response_misses": self.response_misses,
            "total_queries": self.total_queries,
            "cache_hit_rate": self.get_hit_rate(),
            "avg_tokens_in_context": (
                self.total_tokens_in_context / self.total_queries
                if self.total_queries > 0 else 0
            ),
        }


metrics = CacheMetrics()


class RedisCache:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            self.available = True
        except Exception:
            self.available = False

    def _hash_key(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()

    async def get_embedding_cached(self, query: str) -> Optional[List[float]]:
        """Get cached embedding for query."""
        if not self.available:
            metrics.embedding_misses += 1
            return None

        try:
            key = f"embedding:{self._hash_key(query)}"
            cached = self.redis_client.get(key)

            if cached:
                metrics.embedding_hits += 1
                return json.loads(cached)
            else:
                metrics.embedding_misses += 1
                return None
        except Exception:
            metrics.embedding_misses += 1
            return None

    async def set_embedding_cached(self, query: str, embedding: List[float]) -> None:
        """Cache embedding for query (24h TTL)."""
        if not self.available:
            return

        try:
            key = f"embedding:{self._hash_key(query)}"
            self.redis_client.setex(key, 86400, json.dumps(embedding))
        except Exception:
            pass

    async def get_retrieval_cached(self, query: str, filter_key: str = "") -> Optional[dict]:
        """Get cached search results."""
        if not self.available:
            metrics.retrieval_misses += 1
            return None

        try:
            key = f"retrieval:{self._hash_key(query)}:{filter_key}"
            cached = self.redis_client.get(key)

            if cached:
                metrics.retrieval_hits += 1
                return json.loads(cached)
            else:
                metrics.retrieval_misses += 1
                return None
        except Exception:
            metrics.retrieval_misses += 1
            return None

    async def set_retrieval_cached(self, query: str, results: dict, filter_key: str = "") -> None:
        """Cache search results (4h TTL)."""
        if not self.available:
            return

        try:
            key = f"retrieval:{self._hash_key(query)}:{filter_key}"
            self.redis_client.setex(key, 14400, json.dumps(results))
        except Exception:
            pass

    async def get_response_cached(self, query: str, filter_key: str = "") -> Optional[str]:
        """Get cached LLM response."""
        if not self.available:
            metrics.response_misses += 1
            return None

        try:
            key = f"response:{self._hash_key(query)}:{filter_key}"
            cached = self.redis_client.get(key)

            if cached:
                metrics.response_hits += 1
                return cached
            else:
                metrics.response_misses += 1
                return None
        except Exception:
            metrics.response_misses += 1
            return None

    async def set_response_cached(self, query: str, response: str, filter_key: str = "") -> None:
        """Cache LLM response (2h TTL)."""
        if not self.available:
            return

        try:
            key = f"response:{self._hash_key(query)}:{filter_key}"
            self.redis_client.setex(key, 7200, response)
        except Exception:
            pass

    def clear_all(self) -> None:
        """Clear all cache entries."""
        if not self.available:
            return

        try:
            self.redis_client.flushdb()
        except Exception:
            pass


cache = RedisCache()
