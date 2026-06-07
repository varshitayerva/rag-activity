import time
from typing import Dict
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CacheMetrics:
    """Track cache performance metrics across all layers."""

    # Cache layer hit/miss counters
    embedding_cache_hits: int = 0
    embedding_cache_misses: int = 0
    retrieval_cache_hits: int = 0
    retrieval_cache_misses: int = 0
    response_cache_hits: int = 0
    response_cache_misses: int = 0

    # Latency tracking
    total_latency_ms: float = 0.0
    query_count: int = 0

    # Token tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # Timestamp
    start_time: float = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()

    @property
    def total_queries(self) -> int:
        """Total number of queries processed."""
        return (
            self.embedding_cache_hits +
            self.embedding_cache_misses
        )

    @property
    def cache_hit_rate(self) -> float:
        """Overall cache hit rate (0.0 to 1.0)."""
        if self.total_queries == 0:
            return 0.0

        total_hits = (
            self.embedding_cache_hits +
            self.retrieval_cache_hits +
            self.response_cache_hits
        )
        total_attempts = (
            self.embedding_cache_hits + self.embedding_cache_misses +
            self.retrieval_cache_hits + self.retrieval_cache_misses +
            self.response_cache_hits + self.response_cache_misses
        )

        return total_hits / total_attempts if total_attempts > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if self.query_count == 0:
            return 0.0
        return self.total_latency_ms / self.query_count

    @property
    def avg_input_tokens(self) -> float:
        """Average input tokens per query."""
        if self.query_count == 0:
            return 0.0
        return self.total_input_tokens / self.query_count

    @property
    def avg_output_tokens(self) -> float:
        """Average output tokens per query."""
        if self.query_count == 0:
            return 0.0
        return self.total_output_tokens / self.query_count

    @property
    def avg_tokens_in_context(self) -> float:
        """Average total tokens (input + output)."""
        return self.avg_input_tokens + self.avg_output_tokens

    @property
    def uptime_seconds(self) -> int:
        """Uptime in seconds."""
        return int(time.time() - self.start_time)

    @property
    def estimated_cost_usd(self) -> float:
        """Estimated cost (rough estimate for Claude Sonnet)."""
        # Claude Sonnet pricing: ~$3/M input, ~$15/M output
        input_cost = (self.total_input_tokens / 1_000_000) * 3.0
        output_cost = (self.total_output_tokens / 1_000_000) * 15.0
        return round(input_cost + output_cost, 2)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "cache_hit_rate": round(self.cache_hit_rate, 3),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "embedding_cache_hits": self.embedding_cache_hits,
            "embedding_cache_misses": self.embedding_cache_misses,
            "retrieval_cache_hits": self.retrieval_cache_hits,
            "retrieval_cache_misses": self.retrieval_cache_misses,
            "response_cache_hits": self.response_cache_hits,
            "response_cache_misses": self.response_cache_misses,
            "total_queries": self.total_queries,
            "avg_tokens_in_context": round(self.avg_tokens_in_context, 1),
            "avg_input_tokens": round(self.avg_input_tokens, 1),
            "avg_output_tokens": round(self.avg_output_tokens, 1),
            "estimated_cost_usd": self.estimated_cost_usd,
            "uptime_seconds": self.uptime_seconds,
        }


class MetricsCollector:
    """Singleton metrics collector for the application."""

    _instance: CacheMetrics = None

    @classmethod
    def get_instance(cls) -> CacheMetrics:
        """Get or create the singleton metrics instance."""
        if cls._instance is None:
            cls._instance = CacheMetrics()
            cls._load_from_db()
        return cls._instance

    @classmethod
    def _load_from_db(cls):
        """Load persisted metrics from database on startup."""
        try:
            from backend.app.database.postgres import db_client
            with db_client.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT metric_type, SUM(value::BIGINT) as total
                    FROM metrics
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                    GROUP BY metric_type
                """)
                for row in cursor.fetchall():
                    metric_type, total = row[0], row[1] or 0
                    if metric_type == 'query_count':
                        cls._instance.query_count = int(total)
                    elif metric_type == 'total_latency_ms':
                        cls._instance.total_latency_ms = float(total)
        except Exception as e:
            print(f"Warning: Could not load metrics from DB: {e}")

    @classmethod
    def _persist_to_db(cls):
        """Persist metrics to database."""
        try:
            from backend.app.database.postgres import db_client
            metrics = cls.get_instance()
            with db_client.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO metrics (metric_type, value)
                    VALUES (%s, %s)
                """, ('query_count', metrics.query_count))
                cursor.execute("""
                    INSERT INTO metrics (metric_type, value)
                    VALUES (%s, %s)
                """, ('total_latency_ms', metrics.total_latency_ms))
        except Exception as e:
            print(f"Warning: Could not persist metrics to DB: {e}")

    @classmethod
    def reset(cls):
        """Reset metrics (for testing)."""
        cls._instance = CacheMetrics()

    @classmethod
    def record_embedding_hit(cls):
        """Record a cache hit for embedding cache."""
        metrics = cls.get_instance()
        metrics.embedding_cache_hits += 1

    @classmethod
    def record_embedding_miss(cls):
        """Record a cache miss for embedding cache."""
        metrics = cls.get_instance()
        metrics.embedding_cache_misses += 1

    @classmethod
    def record_retrieval_hit(cls):
        """Record a cache hit for retrieval cache."""
        metrics = cls.get_instance()
        metrics.retrieval_cache_hits += 1

    @classmethod
    def record_retrieval_miss(cls):
        """Record a cache miss for retrieval cache."""
        metrics = cls.get_instance()
        metrics.retrieval_cache_misses += 1

    @classmethod
    def record_response_hit(cls):
        """Record a cache hit for response cache."""
        metrics = cls.get_instance()
        metrics.response_cache_hits += 1

    @classmethod
    def record_response_miss(cls):
        """Record a cache miss for response cache."""
        metrics = cls.get_instance()
        metrics.response_cache_misses += 1

    @classmethod
    def record_latency(cls, latency_ms: float):
        """Record query latency."""
        metrics = cls.get_instance()
        metrics.total_latency_ms += latency_ms
        metrics.query_count += 1
        cls._persist_to_db()

    @classmethod
    def record_tokens(cls, input_tokens: int, output_tokens: int):
        """Record token usage."""
        metrics = cls.get_instance()
        metrics.total_input_tokens += input_tokens
        metrics.total_output_tokens += output_tokens

    @classmethod
    def get_metrics(cls) -> Dict:
        """Get all metrics as a dictionary."""
        return cls.get_instance().to_dict()
