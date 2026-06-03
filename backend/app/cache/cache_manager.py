"""M4 Three-Layer Caching System."""

from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime, timedelta
import logging
from app.cache.redis_client import RedisClient

logger = logging.getLogger(__name__)

# Cache TTLs (in seconds)
EMBEDDING_CACHE_TTL = 86400  # 24 hours
RETRIEVAL_CACHE_TTL = 14400  # 4 hours
RESPONSE_CACHE_TTL = 7200  # 2 hours


class CacheManager:
    """Manages three-layer caching for RAG pipeline."""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        # Metrics tracking
        self.metrics = {
            "layer1_hits": 0,
            "layer1_misses": 0,
            "layer2_hits": 0,
            "layer2_misses": 0,
            "layer3_hits": 0,
            "layer3_misses": 0,
            "total_queries": 0,
            "total_tokens": 0,
            "start_time": datetime.now(),
        }

    # ============ LAYER 1: EMBEDDING CACHE ============
    # TTL: 24h | Hit Rate Target: 50-70%
    # Caches query embeddings to avoid re-computing

    def _embedding_cache_key(self, query: str) -> str:
        """Generate cache key for query embedding."""
        query_hash = RedisClient.hash_key(query.lower().strip())
        return f"embed:{query_hash}"

    async def get_embedding(self, query: str) -> Optional[List[float]]:
        """Get cached embedding for query."""
        key = self._embedding_cache_key(query)
        cached = await self.redis.get(key)
        if cached:
            self.metrics["layer1_hits"] += 1
            logger.debug(f"✅ Layer 1 HIT: {key[:20]}...")
            return cached.get("embedding")
        self.metrics["layer1_misses"] += 1
        logger.debug(f"❌ Layer 1 MISS: {key[:20]}...")
        return None

    async def cache_embedding(self, query: str, embedding: List[float]) -> bool:
        """Cache query embedding."""
        key = self._embedding_cache_key(query)
        success = await self.redis.set(
            key,
            {"embedding": embedding, "cached_at": datetime.now().isoformat()},
            EMBEDDING_CACHE_TTL
        )
        if success:
            logger.debug(f"💾 Layer 1 CACHED: {key[:20]}... (24h TTL)")
        return success

    # ============ LAYER 2: RETRIEVAL CACHE ============
    # TTL: 4h | Hit Rate Target: 30-50%
    # Caches search results per query+filter combo

    def _retrieval_cache_key(self, query: str, top_k: int, metadata_filter: Optional[Dict] = None) -> str:
        """Generate cache key for search results."""
        filter_str = json.dumps(metadata_filter, sort_keys=True) if metadata_filter else ""
        cache_input = f"{query}|{top_k}|{filter_str}".lower().strip()
        result_hash = RedisClient.hash_key(cache_input)
        return f"retrieval:{result_hash}"

    async def get_search_results(
        self,
        query: str,
        top_k: int,
        metadata_filter: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached search results."""
        key = self._retrieval_cache_key(query, top_k, metadata_filter)
        cached = await self.redis.get(key)
        if cached:
            self.metrics["layer2_hits"] += 1
            logger.debug(f"✅ Layer 2 HIT: {key[:20]}...")
            return cached.get("results")
        self.metrics["layer2_misses"] += 1
        logger.debug(f"❌ Layer 2 MISS: {key[:20]}...")
        return None

    async def cache_search_results(
        self,
        query: str,
        top_k: int,
        results: Dict[str, Any],
        metadata_filter: Optional[Dict] = None
    ) -> bool:
        """Cache search results."""
        key = self._retrieval_cache_key(query, top_k, metadata_filter)
        success = await self.redis.set(
            key,
            {"results": results, "cached_at": datetime.now().isoformat()},
            RETRIEVAL_CACHE_TTL
        )
        if success:
            logger.debug(f"💾 Layer 2 CACHED: {key[:20]}... (4h TTL)")
        return success

    # ============ LAYER 3: RESPONSE CACHE ============
    # TTL: 2h | Hit Rate Target: 10-20%
    # Caches full LLM responses

    def _response_cache_key(self, query: str, chunks_hash: str) -> str:
        """Generate cache key for LLM response."""
        cache_input = f"{query}|{chunks_hash}".lower().strip()
        result_hash = RedisClient.hash_key(cache_input)
        return f"response:{result_hash}"

    @staticmethod
    def _hash_chunks(chunks: List[Dict[str, Any]]) -> str:
        """Create hash of chunks for cache key."""
        chunk_ids = [c.get("chunk_id", "") for c in chunks]
        return RedisClient.hash_key("|".join(chunk_ids))

    async def get_response(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get cached LLM response."""
        chunks_hash = self._hash_chunks(chunks)
        key = self._response_cache_key(query, chunks_hash)
        cached = await self.redis.get(key)
        if cached:
            self.metrics["layer3_hits"] += 1
            logger.debug(f"✅ Layer 3 HIT: {key[:20]}...")
            return cached.get("response")
        self.metrics["layer3_misses"] += 1
        logger.debug(f"❌ Layer 3 MISS: {key[:20]}...")
        return None

    async def cache_response(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        response: Dict[str, Any]
    ) -> bool:
        """Cache LLM response."""
        chunks_hash = self._hash_chunks(chunks)
        key = self._response_cache_key(query, chunks_hash)
        success = await self.redis.set(
            key,
            {"response": response, "cached_at": datetime.now().isoformat()},
            RESPONSE_CACHE_TTL
        )
        if success:
            logger.debug(f"💾 Layer 3 CACHED: {key[:20]}... (2h TTL)")
        return success

    # ============ METRICS ============

    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics and KPIs."""
        layer1_total = self.metrics["layer1_hits"] + self.metrics["layer1_misses"]
        layer2_total = self.metrics["layer2_hits"] + self.metrics["layer2_misses"]
        layer3_total = self.metrics["layer3_hits"] + self.metrics["layer3_misses"]

        uptime = datetime.now() - self.metrics["start_time"]

        return {
            "cache_hit_rates": {
                "layer1_embedding": round(
                    (self.metrics["layer1_hits"] / layer1_total * 100) if layer1_total > 0 else 0, 2
                ),
                "layer2_retrieval": round(
                    (self.metrics["layer2_hits"] / layer2_total * 100) if layer2_total > 0 else 0, 2
                ),
                "layer3_response": round(
                    (self.metrics["layer3_hits"] / layer3_total * 100) if layer3_total > 0 else 0, 2
                ),
            },
            "total_queries": layer1_total + layer2_total + layer3_total,
            "average_tokens_in_context": round(
                self.metrics["total_tokens"] / max(self.metrics["total_queries"], 1), 2
            ),
            "uptime_seconds": int(uptime.total_seconds()),
            "redis_status": await self.redis.get_stats(),
        }

    def update_metrics(self, tokens: int):
        """Update metrics after query."""
        self.metrics["total_queries"] += 1
        self.metrics["total_tokens"] += tokens
