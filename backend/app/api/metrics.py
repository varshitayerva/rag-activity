from fastapi import APIRouter
from backend.app.cache import MetricsCollector, Demo3Scenario

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics")
async def get_metrics():
    """
    Get performance metrics and cache statistics.

    Returns:
        {
            "cache_hit_rate": float (0.0-1.0),
            "avg_latency_ms": float,
            "embedding_cache_hits": int,
            "embedding_cache_misses": int,
            "retrieval_cache_hits": int,
            "retrieval_cache_misses": int,
            "response_cache_hits": int,
            "response_cache_misses": int,
            "total_queries": int,
            "avg_tokens_in_context": float,
            "avg_input_tokens": float,
            "avg_output_tokens": float,
            "estimated_cost_usd": float,
            "uptime_seconds": int
        }
    """
    metrics = MetricsCollector.get_metrics()
    return metrics


@router.get("/demo3/speedup")
async def get_demo3_speedup():
    """
    Get Demo 3 speedup report (450× latency improvement).

    Shows cold cache (2,300ms) vs warm cache (5ms) with token compression.

    Returns:
        {
            "query": str,
            "cold_cache": {...},
            "warm_cache": {...},
            "speedup": {...},
            "compression": {...},
            "metrics_snapshot": {...}
        }
    """
    return Demo3Scenario.get_speedup_report()
