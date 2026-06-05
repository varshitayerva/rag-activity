"""Advanced caching strategies with Redis."""

import os
import json
import hashlib
from typing import Any, Optional, Dict
import logging
import time

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced cache manager with multiple strategies."""

    def __init__(self):
        self.enable_redis = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        self.local_cache: Dict[str, tuple] = {}  # (value, expiry_time)
        self.redis_client = self._init_redis()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
        }

    def _init_redis(self):
        """Initialize Redis if available."""
        if not self.enable_redis:
            logger.info("Redis disabled - using in-memory cache")
            return None

        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            client = redis.from_url(redis_url)
            client.ping()
            logger.info("Redis cache initialized")
            return client
        except Exception as e:
            logger.warning(f"Redis unavailable: {e} - falling back to local cache")
            return None

    def _generate_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate cache key from data."""
        key_str = json.dumps(data, sort_keys=True)
        hash_val = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{hash_val}"

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache value."""
        expiry_time = time.time() + ttl

        # Set in Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

        # Always set in local cache as fallback
        self.local_cache[key] = (value, expiry_time)

    def get(self, key: str) -> Optional[Any]:
        """Get cache value."""
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats['hits'] += 1
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # Try local cache
        if key in self.local_cache:
            value, expiry_time = self.local_cache[key]
            if time.time() < expiry_time:
                self.cache_stats['hits'] += 1
                return value
            else:
                del self.local_cache[key]
                self.cache_stats['evictions'] += 1

        self.cache_stats['misses'] += 1
        return None

    def delete(self, key: str):
        """Delete cache entry."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        if key in self.local_cache:
            del self.local_cache[key]

    def clear(self):
        """Clear all cache."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        self.local_cache.clear()
        logger.info("Cache cleared")

    def cache_search_result(self, query: str, filters: Dict, result: Any):
        """Cache search result."""
        key = self._generate_key("search", {'query': query, **filters})
        self.set(key, result, ttl=3600)  # 1 hour TTL

    def get_cached_search(self, query: str, filters: Dict) -> Optional[Any]:
        """Get cached search result."""
        key = self._generate_key("search", {'query': query, **filters})
        return self.get(key)

    def cache_generation(self, query: str, result: str):
        """Cache generation result."""
        key = self._generate_key("generation", {'query': query})
        self.set(key, result, ttl=7200)  # 2 hour TTL

    def get_cached_generation(self, query: str) -> Optional[str]:
        """Get cached generation result."""
        key = self._generate_key("generation", {'query': query})
        return self.get(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0

        return {
            'total_requests': total,
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'evictions': self.cache_stats['evictions'],
            'local_cache_size': len(self.local_cache),
            'redis_enabled': bool(self.redis_client),
        }


# Global instance
cache_manager = CacheManager()
