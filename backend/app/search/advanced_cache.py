"""Advanced caching with semantic similarity and tiered storage"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import time
import json
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    timestamp: float
    ttl: int
    hits: int = 0
    query_embedding: Optional[List[float]] = None
    score: float = 0.0


class SemanticCacheTier:
    """Multi-tier caching with semantic similarity matching"""

    def __init__(
        self,
        max_size: int = 2000,
        ttl_minutes: int = 30,
        semantic_threshold: float = 0.95
    ):
        """
        Initialize semantic cache tier.

        Args:
            max_size: Maximum cache size
            ttl_minutes: Default TTL in minutes
            semantic_threshold: Similarity threshold for semantic matches (0-1)
        """
        self.cache = {}  # {key: CacheEntry}
        self.max_size = max_size
        self.ttl_seconds = ttl_minutes * 60
        self.semantic_threshold = semantic_threshold
        self.stats = {
            'hits': 0,
            'misses': 0,
            'semantic_hits': 0,
            'evictions': 0
        }

    def get(
        self,
        query: str,
        embedding: Optional[List[float]] = None
    ) -> Optional[Any]:
        """
        Get cached value with exact or semantic match.

        Args:
            query: Query string
            embedding: Optional query embedding for semantic matching

        Returns:
            Cached value or None
        """
        key = self._hash_key(query)

        # Exact match
        if key in self.cache:
            entry = self.cache[key]
            if not self._is_expired(entry):
                entry.hits += 1
                self.stats['hits'] += 1
                return entry.value
            else:
                del self.cache[key]

        # Semantic match (if embedding provided)
        if embedding:
            for cached_key, entry in list(self.cache.items()):
                if not self._is_expired(entry) and entry.query_embedding:
                    similarity = self._cosine_similarity(embedding, entry.query_embedding)
                    if similarity >= self.semantic_threshold:
                        entry.hits += 1
                        self.stats['semantic_hits'] += 1
                        logger.debug(f"Semantic cache hit (similarity: {similarity:.3f})")
                        return entry.value

        self.stats['misses'] += 1
        return None

    def put(
        self,
        query: str,
        value: Any,
        embedding: Optional[List[float]] = None,
        ttl: Optional[int] = None
    ):
        """
        Store value in cache.

        Args:
            query: Query string
            value: Value to cache
            embedding: Optional query embedding for semantic matching
            ttl: Optional custom TTL in seconds
        """
        # LRU eviction
        if len(self.cache) >= self.max_size:
            lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[lru_key]
            self.stats['evictions'] += 1

        key = self._hash_key(query)
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl or self.ttl_seconds,
            query_embedding=embedding
        )
        self.cache[key] = entry
        logger.debug(f"Cached query: {query[:50]}... (size: {len(self.cache)}/{self.max_size})")

    def _hash_key(self, query: str) -> str:
        """Generate cache key"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if entry is expired"""
        return time.time() - entry.timestamp > entry.ttl

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
        magnitude2 = sum(b ** 2 for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0.0

        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'semantic_hits': self.stats['semantic_hits'],
            'hit_rate': hit_rate,
            'evictions': self.stats['evictions'],
            'ttl_minutes': self.ttl_seconds / 60
        }

    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        logger.info("Advanced cache cleared")

    def cleanup_expired(self):
        """Remove expired entries"""
        expired = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        for key in expired:
            del self.cache[key]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired entries")
        return len(expired)


class QueryCompressionCache:
    """Compress and store normalized queries for better cache hits"""

    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Normalize query for better cache hits.

        Args:
            query: Original query

        Returns:
            Normalized query
        """
        # Remove extra whitespace
        query = ' '.join(query.split())

        # Lowercase
        query = query.lower()

        # Remove common stopwords that don't affect meaning
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'please', 'thank', 'you'}
        words = query.split()
        words = [w for w in words if w not in stopwords]
        query = ' '.join(words)

        return query

    @staticmethod
    def get_query_hash(query: str) -> str:
        """Get normalized query hash for caching"""
        normalized = QueryCompressionCache.normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()
