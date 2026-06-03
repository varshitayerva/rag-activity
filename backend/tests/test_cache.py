import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from redis import asyncio as aioredis
from app.cache import RedisCache, MetricsCollector
from app.cache.metrics import CacheMetrics


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    MetricsCollector.reset()
    yield
    MetricsCollector.reset()


class TestMetricsCollector:
    """Test metrics collection and calculation."""

    def test_initial_metrics_zero(self):
        """Initial metrics should be zero."""
        metrics = MetricsCollector.get_instance()
        assert metrics.embedding_cache_hits == 0
        assert metrics.embedding_cache_misses == 0
        assert metrics.total_queries == 0
        assert metrics.cache_hit_rate == 0.0

    def test_record_embedding_hit(self):
        """Recording embedding hits should increment counter."""
        MetricsCollector.record_embedding_hit()
        MetricsCollector.record_embedding_hit()

        metrics = MetricsCollector.get_instance()
        assert metrics.embedding_cache_hits == 2

    def test_record_embedding_miss(self):
        """Recording embedding misses should increment counter."""
        MetricsCollector.record_embedding_miss()

        metrics = MetricsCollector.get_instance()
        assert metrics.embedding_cache_misses == 1

    def test_cache_hit_rate_calculation(self):
        """Cache hit rate should be calculated correctly."""
        # 2 hits, 3 misses = 2/5 = 0.4
        MetricsCollector.record_embedding_hit()
        MetricsCollector.record_embedding_hit()
        MetricsCollector.record_embedding_miss()
        MetricsCollector.record_embedding_miss()
        MetricsCollector.record_embedding_miss()

        metrics = MetricsCollector.get_instance()
        assert metrics.cache_hit_rate == pytest.approx(0.4)

    def test_average_latency(self):
        """Average latency should be calculated correctly."""
        MetricsCollector.record_latency(100.0)
        MetricsCollector.record_latency(200.0)
        MetricsCollector.record_latency(300.0)

        metrics = MetricsCollector.get_instance()
        assert metrics.avg_latency_ms == pytest.approx(200.0)

    def test_token_tracking(self):
        """Token usage should be tracked correctly."""
        MetricsCollector.record_tokens(1000, 500)
        MetricsCollector.record_tokens(2000, 750)

        metrics = MetricsCollector.get_instance()
        assert metrics.total_input_tokens == 3000
        assert metrics.total_output_tokens == 1250

    def test_avg_tokens_in_context(self):
        """Average tokens in context should be sum of input and output."""
        MetricsCollector.record_tokens(1000, 500)
        MetricsCollector.record_tokens(2000, 750)

        metrics = MetricsCollector.get_instance()
        # (3000 + 1250) / 2 = 2125
        assert metrics.avg_tokens_in_context == pytest.approx(2125.0)

    def test_estimated_cost_calculation(self):
        """Estimated cost should be calculated based on token count."""
        # Input: $3/M, Output: $15/M
        MetricsCollector.record_tokens(1_000_000, 1_000_000)

        metrics = MetricsCollector.get_instance()
        expected_cost = 3.0 + 15.0  # 1M input + 1M output
        assert metrics.estimated_cost_usd == pytest.approx(expected_cost, abs=0.01)

    def test_metrics_to_dict(self):
        """Metrics should be serializable to dictionary."""
        MetricsCollector.record_embedding_hit()
        MetricsCollector.record_embedding_miss()
        MetricsCollector.record_latency(150.0)
        MetricsCollector.record_tokens(2000, 500)

        metrics_dict = MetricsCollector.get_metrics()

        assert "cache_hit_rate" in metrics_dict
        assert "avg_latency_ms" in metrics_dict
        assert "embedding_cache_hits" in metrics_dict
        assert "total_queries" in metrics_dict
        assert "avg_tokens_in_context" in metrics_dict
        assert "estimated_cost_usd" in metrics_dict
        assert "uptime_seconds" in metrics_dict

    def test_all_cache_layers(self):
        """All cache layers should be tracked independently."""
        # Embedding layer
        MetricsCollector.record_embedding_hit()
        MetricsCollector.record_embedding_miss()

        # Retrieval layer
        MetricsCollector.record_retrieval_hit()
        MetricsCollector.record_retrieval_hit()
        MetricsCollector.record_retrieval_miss()

        # Response layer
        MetricsCollector.record_response_hit()

        metrics = MetricsCollector.get_instance()
        assert metrics.embedding_cache_hits == 1
        assert metrics.retrieval_cache_hits == 2
        assert metrics.response_cache_hits == 1


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def test_make_key_consistent(self):
        """Same input should produce same key."""
        cache = RedisCache()
        key1 = cache._make_key("embedding", "hello world")
        key2 = cache._make_key("embedding", "hello world")

        assert key1 == key2

    def test_make_key_different_inputs(self):
        """Different inputs should produce different keys."""
        cache = RedisCache()
        key1 = cache._make_key("embedding", "hello")
        key2 = cache._make_key("embedding", "world")

        assert key1 != key2

    def test_make_key_different_prefixes(self):
        """Different prefixes should produce different keys."""
        cache = RedisCache()
        key1 = cache._make_key("embedding", "hello")
        key2 = cache._make_key("retrieval", "hello")

        assert key1 != key2


class TestRedisCacheMocking:
    """Test Redis cache with mocked Redis connection."""

    @pytest.mark.asyncio
    async def test_embedding_cache_hit(self):
        """Embedding cache hit should return cached value."""
        cache = RedisCache()

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps([0.1, 0.2, 0.3]))
        mock_redis.setex = AsyncMock()

        with patch.object(RedisCache, "get_connection", return_value=mock_redis):
            mock_fetch = AsyncMock()

            result = await cache.get_embedding_cached("test query", mock_fetch)

            assert result == [0.1, 0.2, 0.3]
            assert MetricsCollector.get_instance().embedding_cache_hits == 1
            assert MetricsCollector.get_instance().embedding_cache_misses == 0
            # Fetch should not be called
            mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_embedding_cache_miss(self):
        """Embedding cache miss should call fetch function."""
        cache = RedisCache()

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch.object(RedisCache, "get_connection", return_value=mock_redis):
            mock_fetch = AsyncMock(return_value=[0.4, 0.5, 0.6])

            result = await cache.get_embedding_cached("test query", mock_fetch)

            assert result == [0.4, 0.5, 0.6]
            assert MetricsCollector.get_instance().embedding_cache_hits == 0
            assert MetricsCollector.get_instance().embedding_cache_misses == 1
            # Fetch should be called
            mock_fetch.assert_called_once()
            # Cache should be updated
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieval_cache_with_filter(self):
        """Retrieval cache should include filter in key."""
        cache = RedisCache()

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch.object(RedisCache, "get_connection", return_value=mock_redis):
            mock_fetch = AsyncMock(return_value={"chunks": []})

            await cache.get_retrieval_cached(
                "test query",
                "department=platform",
                mock_fetch
            )

            # Verify filter is included in key
            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            assert "retrieval" in key

    @pytest.mark.asyncio
    async def test_response_cache(self):
        """Response cache should cache full responses."""
        cache = RedisCache()

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch.object(RedisCache, "get_connection", return_value=mock_redis):
            mock_fetch = AsyncMock(return_value={"text": "answer", "sources": []})

            result = await cache.get_response_cached("test query", mock_fetch)

            assert result == {"text": "answer", "sources": []}
            assert MetricsCollector.get_instance().response_cache_misses == 1


class TestCacheClearance:
    """Test cache clearing operations."""

    @pytest.mark.asyncio
    async def test_clear_embedding_cache(self):
        """Clearing embedding cache should remove all embedding keys."""
        cache = RedisCache()

        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=["embedding:abc", "embedding:def"])
        mock_redis.delete = AsyncMock()

        with patch.object(RedisCache, "get_connection", return_value=mock_redis):
            await cache.clear_embedding_cache()

            mock_redis.keys.assert_called_once_with("embedding:*")
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Clearing all caches should clear all layers."""
        cache = RedisCache()

        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.delete = AsyncMock()

        with patch.object(RedisCache, "get_connection", return_value=mock_redis):
            await cache.clear_all()

            # Should call keys for each layer
            assert mock_redis.keys.call_count == 3
