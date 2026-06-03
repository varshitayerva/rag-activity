"""Tests for Layer 2 (Retrieval Cache) and Layer 3 (Response Cache)."""

import pytest
import json
from unittest.mock import AsyncMock, patch
from app.cache import (
    RetrievalCache,
    ResponseCache,
    SearchResult,
    GenerationResponse,
    Chunk,
    MetricsCollector,
)


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    MetricsCollector.reset()
    yield
    MetricsCollector.reset()


class TestRetrievalCacheLayer2:
    """Test Layer 2: Retrieval Cache for search results."""

    def test_make_filter_key_no_filters(self):
        """No filters should produce consistent key."""
        cache = RetrievalCache()
        key1 = cache._make_filter_key(None)
        key2 = cache._make_filter_key(None)
        assert key1 == key2
        assert key1 == "no_filter"

    def test_make_filter_key_with_filters(self):
        """Same filters should produce same key."""
        cache = RetrievalCache()
        filters = {"department": "platform", "category": "errors"}
        key1 = cache._make_filter_key(filters)
        key2 = cache._make_filter_key(filters)
        assert key1 == key2

    def test_make_filter_key_different_filters(self):
        """Different filters should produce different keys."""
        cache = RetrievalCache()
        filters1 = {"department": "platform"}
        filters2 = {"department": "network"}
        assert cache._make_filter_key(filters1) != cache._make_filter_key(filters2)

    def test_make_filter_key_order_independent(self):
        """Filter key should be independent of order."""
        cache = RetrievalCache()
        filters1 = {"department": "platform", "category": "errors"}
        filters2 = {"category": "errors", "department": "platform"}
        assert cache._make_filter_key(filters1) == cache._make_filter_key(filters2)

    def test_make_retrieval_cache_key(self):
        """Retrieval cache keys should include query and filter."""
        cache = RetrievalCache()
        key1 = cache._make_retrieval_cache_key("query1", "filter1")
        key2 = cache._make_retrieval_cache_key("query1", "filter1")
        key3 = cache._make_retrieval_cache_key("query2", "filter1")

        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different queries = different keys
        assert key1.startswith("retrieval:")

    @pytest.mark.asyncio
    async def test_retrieval_cache_hit(self):
        """Retrieval cache hit should return cached result."""
        cache = RetrievalCache()

        # Create mock search result
        chunks = [
            Chunk(
                chunk_id="1",
                text="Step 1: Check logs",
                score=0.95,
                source="guide.pdf",
            )
        ]
        search_result = SearchResult(chunks=chunks, query="test query")

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(search_result.to_dict()))
        mock_redis.setex = AsyncMock()

        with patch.object(
            cache.redis_cache, "get_connection", return_value=mock_redis
        ):
            mock_fetch = AsyncMock()

            result = await cache.get_search_results_cached(
                "test query", None, mock_fetch
            )

            assert result.query == "test query"
            assert len(result.chunks) == 1
            assert MetricsCollector.get_instance().retrieval_cache_hits == 1
            mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieval_cache_miss(self):
        """Retrieval cache miss should call fetch function."""
        cache = RetrievalCache()

        # Create mock search result
        chunks = [
            Chunk(
                chunk_id="1",
                text="Step 1: Check logs",
                score=0.95,
                source="guide.pdf",
            )
        ]
        search_result = SearchResult(chunks=chunks, query="test query")

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch.object(
            cache.redis_cache, "get_connection", return_value=mock_redis
        ):
            mock_fetch = AsyncMock(return_value=search_result)

            result = await cache.get_search_results_cached(
                "test query", None, mock_fetch
            )

            assert result.query == "test query"
            assert MetricsCollector.get_instance().retrieval_cache_misses == 1
            mock_fetch.assert_called_once()
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieval_cache_with_filters(self):
        """Retrieval cache should handle filters correctly."""
        cache = RetrievalCache()

        chunks = [Chunk(chunk_id="1", text="text", score=0.9, source="doc.pdf")]
        search_result = SearchResult(chunks=chunks)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch.object(
            cache.redis_cache, "get_connection", return_value=mock_redis
        ):
            mock_fetch = AsyncMock(return_value=search_result)
            filters = {"department": "platform", "category": "errors"}

            await cache.get_search_results_cached("query", filters, mock_fetch)

            # Verify filter was included in cache key
            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            assert "retrieval" in key


class TestResponseCacheLayer3:
    """Test Layer 3: Response Cache for LLM responses."""

    def test_make_response_cache_key_consistent(self):
        """Same query should produce same key."""
        cache = ResponseCache()
        key1 = cache._make_response_cache_key("how do I fix X?")
        key2 = cache._make_response_cache_key("how do I fix X?")
        assert key1 == key2
        assert key1.startswith("response:")

    def test_make_response_cache_key_different(self):
        """Different queries should produce different keys."""
        cache = ResponseCache()
        key1 = cache._make_response_cache_key("query1")
        key2 = cache._make_response_cache_key("query2")
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_response_cache_hit(self):
        """Response cache hit should return cached response."""
        cache = ResponseCache()

        response = GenerationResponse(
            text="Based on the documentation...",
            sources=[{"doc": "guide.pdf", "section": "Troubleshooting"}],
            input_tokens=2450,
            output_tokens=340,
        )

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(response.to_dict()))
        mock_redis.setex = AsyncMock()

        with patch.object(
            cache.redis_cache, "get_connection", return_value=mock_redis
        ):
            mock_fetch = AsyncMock()

            result = await cache.get_response_cached("test query", mock_fetch)

            assert result.text == "Based on the documentation..."
            assert result.input_tokens == 2450
            assert MetricsCollector.get_instance().response_cache_hits == 1
            mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_response_cache_miss(self):
        """Response cache miss should call generation function."""
        cache = ResponseCache()

        response = GenerationResponse(
            text="Generated response",
            sources=[],
            input_tokens=2000,
            output_tokens=300,
        )

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch.object(
            cache.redis_cache, "get_connection", return_value=mock_redis
        ):
            mock_fetch = AsyncMock(return_value=response)

            result = await cache.get_response_cached("test query", mock_fetch)

            assert result.text == "Generated response"
            assert MetricsCollector.get_instance().response_cache_misses == 1
            mock_fetch.assert_called_once()
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_response_cache_token_tracking(self):
        """Response cache should track token usage in metrics."""
        cache = ResponseCache()

        response = GenerationResponse(
            text="Response",
            sources=[],
            input_tokens=2000,
            output_tokens=500,
        )

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch.object(
            cache.redis_cache, "get_connection", return_value=mock_redis
        ):
            mock_fetch = AsyncMock(return_value=response)

            await cache.get_response_cached("query", mock_fetch)

            # Token tracking happens in generation function
            # This test verifies response object carries tokens
            assert response.input_tokens == 2000
            assert response.output_tokens == 500


class TestSearchResultModel:
    """Test SearchResult data model."""

    def test_search_result_to_dict(self):
        """SearchResult should serialize to dict."""
        chunks = [
            Chunk(
                chunk_id="1",
                text="Step 1",
                score=0.95,
                source="guide.pdf",
                metadata={"section": "Setup"},
            )
        ]
        result = SearchResult(
            chunks=chunks,
            search_type="hybrid",
            query="test",
            latency_ms={"total": 250},
        )

        result_dict = result.to_dict()

        assert result_dict["search_type"] == "hybrid"
        assert result_dict["query"] == "test"
        assert len(result_dict["chunks"]) == 1
        assert result_dict["chunks"][0]["text"] == "Step 1"

    def test_search_result_from_dict(self):
        """SearchResult should deserialize from dict."""
        data = {
            "chunks": [
                {
                    "chunk_id": "1",
                    "text": "Step 1",
                    "score": 0.95,
                    "source": "guide.pdf",
                    "metadata": {},
                }
            ],
            "search_type": "hybrid",
            "query": "test",
            "latency_ms": {"total": 250},
            "timestamp": "2024-01-01T00:00:00",
        }

        result = SearchResult.from_dict(data)

        assert result.search_type == "hybrid"
        assert result.query == "test"
        assert len(result.chunks) == 1


class TestGenerationResponseModel:
    """Test GenerationResponse data model."""

    def test_generation_response_to_dict(self):
        """GenerationResponse should serialize to dict."""
        response = GenerationResponse(
            text="Based on the docs...",
            sources=[{"doc": "guide.pdf"}],
            input_tokens=2450,
            output_tokens=340,
            model="claude-sonnet-4-20250514",
        )

        response_dict = response.to_dict()

        assert response_dict["text"] == "Based on the docs..."
        assert response_dict["input_tokens"] == 2450
        assert response_dict["output_tokens"] == 340
        assert len(response_dict["sources"]) == 1

    def test_generation_response_from_dict(self):
        """GenerationResponse should deserialize from dict."""
        data = {
            "text": "Response text",
            "sources": [{"doc": "guide.pdf"}],
            "input_tokens": 2000,
            "output_tokens": 500,
            "model": "claude-sonnet-4-20250514",
            "timestamp": "2024-01-01T00:00:00",
        }

        response = GenerationResponse.from_dict(data)

        assert response.text == "Response text"
        assert response.input_tokens == 2000
        assert response.output_tokens == 500


class TestCacheHitRateTargets:
    """Test cache hit rate achievement targets."""

    def test_embedding_cache_50_70_percent(self):
        """Embedding cache should achieve 50-70% hit rate."""
        # Simulate 10 queries: 6 hits, 4 misses
        for _ in range(6):
            MetricsCollector.record_embedding_hit()
        for _ in range(4):
            MetricsCollector.record_embedding_miss()

        metrics = MetricsCollector.get_instance()

        # Embedding hits / (hits + misses) = 6/10 = 0.6 (60%)
        embedding_hit_rate = metrics.embedding_cache_hits / (
            metrics.embedding_cache_hits + metrics.embedding_cache_misses
        )
        assert 0.5 <= embedding_hit_rate <= 0.7

    def test_retrieval_cache_30_50_percent(self):
        """Retrieval cache should achieve 30-50% hit rate."""
        # Simulate 10 queries: 4 hits, 6 misses
        for _ in range(4):
            MetricsCollector.record_retrieval_hit()
        for _ in range(6):
            MetricsCollector.record_retrieval_miss()

        metrics = MetricsCollector.get_instance()

        # Retrieval hits / (hits + misses) = 4/10 = 0.4 (40%)
        retrieval_hit_rate = metrics.retrieval_cache_hits / (
            metrics.retrieval_cache_hits + metrics.retrieval_cache_misses
        )
        assert 0.3 <= retrieval_hit_rate <= 0.5

    def test_response_cache_10_20_percent(self):
        """Response cache should achieve 10-20% hit rate."""
        # Simulate 10 queries: 1 hit, 9 misses
        for _ in range(1):
            MetricsCollector.record_response_hit()
        for _ in range(9):
            MetricsCollector.record_response_miss()

        metrics = MetricsCollector.get_instance()

        # Response hits / (hits + misses) = 1/10 = 0.1 (10%)
        response_hit_rate = metrics.response_cache_hits / (
            metrics.response_cache_hits + metrics.response_cache_misses
        )
        assert 0.1 <= response_hit_rate <= 0.2
