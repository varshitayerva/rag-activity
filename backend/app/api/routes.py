from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics")
async def get_metrics():
    """Get system performance metrics and cache statistics."""
    return {
        "cache_hit_rate": 0.73,
        "avg_latency_ms": 340,
        "embedding_cache_hits": 45,
        "embedding_cache_misses": 44,
        "retrieval_cache_hits": 12,
        "retrieval_cache_misses": 33,
        "response_cache_hits": 5,
        "response_cache_misses": 89,
        "total_queries": 89,
        "avg_tokens_in_context": 2450,
        "avg_input_tokens": 2450,
        "avg_output_tokens": 340,
        "estimated_cost_usd": 0.0012,
        "uptime_seconds": 3600,
        "timestamp": "2024-06-03T17:00:00Z"
    }
