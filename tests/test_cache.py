import pytest
import asyncio
from app.cache import RedisCache, CacheMetrics


@pytest.fixture
def cache():
    return RedisCache()


@pytest.fixture
def metrics():
    return CacheMetrics()


def test_cache_metrics_init(metrics):
    assert metrics.embedding_hits == 0
    assert metrics.embedding_misses == 0
    assert metrics.get_hit_rate() == 0.0


def test_cache_metrics_hit_rate(metrics):
    metrics.embedding_hits = 7
    metrics.embedding_misses = 3
    hit_rate = metrics.get_hit_rate()

    assert hit_rate == 0.7


def test_cache_metrics_to_dict(metrics):
    metrics.embedding_hits = 5
    metrics.embedding_misses = 5
    metrics.total_queries = 10
    metrics.total_tokens_in_context = 5000

    result = metrics.to_dict()

    assert result["embedding_hits"] == 5
    assert result["embedding_misses"] == 5
    assert result["cache_hit_rate"] == 0.0
    assert result["avg_tokens_in_context"] == 500


@pytest.mark.asyncio
async def test_embedding_cache_miss(cache):
    result = await cache.get_embedding_cached("non-existent-query")
    assert result is None


@pytest.mark.asyncio
async def test_embedding_cache_set_get(cache):
    if not cache.available:
        pytest.skip("Redis not available")

    query = "test query"
    embedding = [0.1] * 1536

    await cache.set_embedding_cached(query, embedding)
    result = await cache.get_embedding_cached(query)

    assert result == embedding


def test_cache_key_hashing(cache):
    key1 = cache._hash_key("test")
    key2 = cache._hash_key("test")
    key3 = cache._hash_key("different")

    assert key1 == key2
    assert key1 != key3
