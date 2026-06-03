"""Redis client wrapper for M4 caching layer."""

import redis.asyncio as redis
from typing import Optional, Any, Dict
import json
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection pooling and error handling."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client: Optional[redis.Redis] = None
        self.is_available = False

    async def connect(self):
        """Connect to Redis with fallback if unavailable."""
        try:
            self.client = await redis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            await self.client.ping()
            self.is_available = True
            logger.info(f"✅ Connected to Redis: {self.host}:{self.port}")
        except Exception as e:
            self.is_available = False
            logger.warning(f"⚠️ Redis unavailable: {e}. Caching disabled. (Graceful degradation)")

    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    @staticmethod
    def hash_key(value: str) -> str:
        """Create SHA256 hash of value for use as cache key."""
        return hashlib.sha256(value.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        if not self.is_available or not self.client:
            return None
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Dict[str, Any], ttl_seconds: int):
        """Set value in cache with TTL."""
        if not self.is_available or not self.client:
            return False
        try:
            await self.client.setex(
                key,
                ttl_seconds,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_available or not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False

    async def clear_all(self) -> bool:
        """Clear all cache (use with caution)."""
        if not self.is_available or not self.client:
            return False
        try:
            await self.client.flushdb()
            logger.info("🗑️ Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache FLUSH error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis server stats."""
        if not self.is_available or not self.client:
            return {"status": "unavailable"}
        try:
            info = await self.client.info()
            return {
                "status": "available",
                "used_memory_mb": info.get("used_memory") / (1024 * 1024) if info.get("used_memory") else 0,
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
