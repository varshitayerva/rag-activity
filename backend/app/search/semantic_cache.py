"""Semantic Cache for embeddings - improves latency for repeated/similar queries"""

import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class SemanticCache:
    """Cache embeddings and search results for improved latency"""

    def __init__(self, max_size: int = 1000, ttl_minutes: int = 10):
        """
        Initialize semantic cache.

        Args:
            max_size: Maximum number of cached items
            ttl_minutes: Time-to-live in minutes (default 10)
        """
        self.cache = {}  # {query_hash: {embedding, timestamp, query}}
        self.max_size = max_size
        self.ttl_seconds = ttl_minutes * 60
        self.hits = 0
        self.misses = 0

    def get_query_hash(self, query: str) -> str:
        """Generate deterministic hash for query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    def is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > self.ttl_seconds

    def get_embedding(self, query: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding for query.

        Args:
            query: Query string

        Returns:
            Cached embedding if found and not expired, else None
        """
        query_hash = self.get_query_hash(query)

        if query_hash not in self.cache:
            self.misses += 1
            return None

        cache_entry = self.cache[query_hash]

        # Check if expired
        if self.is_expired(cache_entry["timestamp"]):
            del self.cache[query_hash]
            self.misses += 1
            return None

        self.hits += 1
        logger.debug(f"Cache HIT for query: '{query}'")
        return cache_entry["embedding"]

    def put_embedding(self, query: str, embedding: List[float]):
        """
        Cache an embedding.

        Args:
            query: Query string
            embedding: Embedding vector
        """
        # Enforce LRU eviction if at max size
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_query = min(
                self.cache.items(),
                key=lambda x: x[1]["timestamp"]
            )[0]
            del self.cache[oldest_query]
            logger.debug(f"Cache evicted oldest entry, size now: {len(self.cache)}")

        query_hash = self.get_query_hash(query)
        self.cache[query_hash] = {
            "embedding": embedding,
            "timestamp": time.time(),
            "query": query,  # Store original for debugging
        }
        logger.debug(f"Cache PUT for query: '{query}'")

    def get_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.get_hit_rate(),
            "ttl_minutes": self.ttl_seconds / 60,
        }

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        logger.info("Semantic cache cleared")

    def cleanup_expired(self):
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self.is_expired(entry["timestamp"])
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)


class ResultCache:
    """Cache search results for repeated queries"""

    def __init__(self, max_size: int = 500, ttl_minutes: int = 15):
        """
        Initialize result cache.

        Args:
            max_size: Maximum number of cached result sets
            ttl_minutes: Time-to-live in minutes (default 15)
        """
        self.cache = {}  # {cache_key: {results, timestamp, query, params}}
        self.max_size = max_size
        self.ttl_seconds = ttl_minutes * 60
        self.hits = 0
        self.misses = 0

    def get_cache_key(self, query: str, filters: Dict[str, Any] = None, top_k: int = 10) -> str:
        """
        Generate cache key for query + filters combo.

        Args:
            query: Query string
            filters: Optional filter dict
            top_k: Number of results requested

        Returns:
            Cache key hash
        """
        # Create a deterministic key from query + filters
        key_data = {
            "query": query.lower().strip(),
            "filters": filters or {},
            "top_k": top_k,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_results(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached search results.

        Args:
            query: Query string
            filters: Optional filters
            top_k: Number of results

        Returns:
            Cached results if found and not expired, else None
        """
        cache_key = self.get_cache_key(query, filters, top_k)

        if cache_key not in self.cache:
            self.misses += 1
            return None

        cache_entry = self.cache[cache_key]

        # Check if expired
        if time.time() - cache_entry["timestamp"] > self.ttl_seconds:
            del self.cache[cache_key]
            self.misses += 1
            return None

        self.hits += 1
        logger.debug(f"Result cache HIT for query: '{query}'")
        return cache_entry["results"]

    def put_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any] = None,
        top_k: int = 10
    ):
        """
        Cache search results.

        Args:
            query: Query string
            results: Search results
            filters: Optional filters
            top_k: Number of results
        """
        # Enforce LRU eviction
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.items(),
                key=lambda x: x[1]["timestamp"]
            )[0]
            del self.cache[oldest_key]
            logger.debug(f"Result cache evicted oldest entry, size now: {len(self.cache)}")

        cache_key = self.get_cache_key(query, filters, top_k)
        self.cache[cache_key] = {
            "results": results,
            "timestamp": time.time(),
            "query": query,
            "filters": filters,
            "top_k": top_k,
        }
        logger.debug(f"Result cache PUT for query: '{query}'")

    def get_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.get_hit_rate(),
            "ttl_minutes": self.ttl_seconds / 60,
        }

    def clear(self):
        """Clear all cached results."""
        self.cache.clear()
        logger.info("Result cache cleared")

    def cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if time.time() - entry["timestamp"] > self.ttl_seconds
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired result cache entries")

        return len(expired_keys)
