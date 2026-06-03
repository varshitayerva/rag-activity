"""Latency instrumentation and performance tracking."""

import time
from typing import Dict, Any, Callable, TypeVar, Optional
from functools import wraps
from dataclasses import dataclass, field
from app.cache.metrics import MetricsCollector

T = TypeVar("T")


@dataclass
class LatencyBreakdown:
    """Detailed latency breakdown across pipeline stages."""

    embedding_ms: float = 0.0
    search_ms: float = 0.0
    compression_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0

    cache_hits: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "embedding_ms": round(self.embedding_ms, 2),
            "search_ms": round(self.search_ms, 2),
            "compression_ms": round(self.compression_ms, 2),
            "generation_ms": round(self.generation_ms, 2),
            "total_ms": round(self.total_ms, 2),
            "cache_hits": self.cache_hits,
        }

    def add_stage(self, stage_name: str, duration_ms: float) -> None:
        """Add duration for a stage."""
        if stage_name == "embedding":
            self.embedding_ms += duration_ms
        elif stage_name == "search":
            self.search_ms += duration_ms
        elif stage_name == "compression":
            self.compression_ms += duration_ms
        elif stage_name == "generation":
            self.generation_ms += duration_ms
        self.total_ms = (
            self.embedding_ms +
            self.search_ms +
            self.compression_ms +
            self.generation_ms
        )


class LatencyTimer:
    """Context manager for timing code blocks."""

    def __init__(self, stage_name: str = "unknown"):
        self.stage_name = stage_name
        self.start_time = None
        self.elapsed_ms = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        return False

    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed_ms


def measure_latency(stage_name: str = None):
    """
    Decorator to measure function latency and record in metrics.

    Args:
        stage_name: Name of the stage for metrics (default: function name)

    Example:
        @measure_latency("embedding")
        async def embed_query(query: str) -> List[float]:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = stage_name or func.__name__
            with LatencyTimer(name) as timer:
                result = await func(*args, **kwargs)
            MetricsCollector.record_latency(timer.elapsed_ms)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = stage_name or func.__name__
            with LatencyTimer(name) as timer:
                result = func(*args, **kwargs)
            MetricsCollector.record_latency(timer.elapsed_ms)
            return result

        # Return appropriate wrapper
        if hasattr(func, "__await__"):
            return async_wrapper
        return sync_wrapper

    return decorator


class PerformanceAnalyzer:
    """Analyze performance metrics and identify bottlenecks."""

    @staticmethod
    def get_speedup_factor(cold_ms: float, warm_ms: float) -> float:
        """Calculate speedup factor (cold / warm)."""
        if warm_ms == 0:
            return float("inf")
        return cold_ms / warm_ms

    @staticmethod
    def get_latency_breakdown(breakdown: LatencyBreakdown) -> Dict[str, Any]:
        """Analyze latency breakdown."""
        total = breakdown.total_ms
        if total == 0:
            return {}

        return {
            "embedding_percent": round((breakdown.embedding_ms / total) * 100, 1),
            "search_percent": round((breakdown.search_ms / total) * 100, 1),
            "compression_percent": round((breakdown.compression_ms / total) * 100, 1),
            "generation_percent": round((breakdown.generation_ms / total) * 100, 1),
            "bottleneck": max(
                ("embedding", breakdown.embedding_ms),
                ("search", breakdown.search_ms),
                ("compression", breakdown.compression_ms),
                ("generation", breakdown.generation_ms),
                key=lambda x: x[1],
            )[0],
        }

    @staticmethod
    def estimate_cost_reduction(
        original_tokens: int,
        compressed_tokens: int,
        cost_per_m_input: float = 3.0,
    ) -> Dict[str, float]:
        """
        Estimate cost reduction from token compression.

        Args:
            original_tokens: Token count before compression
            compressed_tokens: Token count after compression
            cost_per_m_input: Cost per million input tokens

        Returns:
            {
                "original_cost": float,
                "compressed_cost": float,
                "savings": float,
                "savings_percent": float,
            }
        """
        original_cost = (original_tokens / 1_000_000) * cost_per_m_input
        compressed_cost = (compressed_tokens / 1_000_000) * cost_per_m_input
        savings = original_cost - compressed_cost
        savings_percent = (savings / original_cost * 100) if original_cost > 0 else 0

        return {
            "original_cost_usd": round(original_cost, 4),
            "compressed_cost_usd": round(compressed_cost, 4),
            "savings_usd": round(savings, 4),
            "savings_percent": round(savings_percent, 1),
        }


# Example usage for Demo 3
DEMO_3_COLD_LATENCY = {
    "embedding_ms": 100,
    "search_ms": 350,
    "compression_ms": 50,
    "generation_ms": 1800,
    "total_ms": 2300,
}

DEMO_3_WARM_LATENCY = {
    "embedding_ms": 0,
    "search_ms": 0,
    "compression_ms": 0,
    "generation_ms": 0,
    "total_ms": 5,
}

DEMO_3_SPEEDUP = PerformanceAnalyzer.get_speedup_factor(
    DEMO_3_COLD_LATENCY["total_ms"],
    DEMO_3_WARM_LATENCY["total_ms"],
)
