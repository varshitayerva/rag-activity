"""Tests for context compression and latency instrumentation."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.cache import Chunk
from app.cache.compression import ContextCompressor, get_compressor
from app.cache.latency import (
    LatencyTimer,
    LatencyBreakdown,
    PerformanceAnalyzer,
    measure_latency,
    DEMO_3_COLD_LATENCY,
    DEMO_3_WARM_LATENCY,
    DEMO_3_SPEEDUP,
)


class TestContextCompressor:
    """Test context compression for token reduction."""

    def test_compressor_singleton(self):
        """get_compressor() should return singleton."""
        c1 = get_compressor()
        c2 = get_compressor()
        assert c1 is c2

    def test_count_tokens_simple(self):
        """Token counting should work for simple text."""
        compressor = ContextCompressor()
        text = "Hello world this is a test"
        tokens = compressor.count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_count_tokens_scaling(self):
        """Longer text should have more tokens."""
        compressor = ContextCompressor()
        short = "Hello"
        long = "Hello world " * 100
        assert compressor.count_tokens(long) > compressor.count_tokens(short)

    def test_compress_chunks_sorting(self):
        """Compression should sort by score (highest first)."""
        compressor = ContextCompressor()

        # Create chunks with different scores
        chunks = [
            Chunk(
                chunk_id="1",
                text="Low relevance chunk",
                score=0.3,
                source="doc.pdf",
            ),
            Chunk(
                chunk_id="2",
                text="High relevance chunk",
                score=0.9,
                source="doc.pdf",
            ),
            Chunk(
                chunk_id="3",
                text="Medium relevance chunk",
                score=0.6,
                source="doc.pdf",
            ),
        ]

        result = compressor.compress_chunks(chunks, max_chunks=2)

        compressed = result["chunks"]
        # Should keep high (0.9) and medium (0.6), drop low (0.3)
        assert len(compressed) == 2
        assert compressed[0].score == 0.9
        assert compressed[1].score == 0.6

    def test_compress_chunks_max_chunks(self):
        """Compression should respect max_chunks limit."""
        compressor = ContextCompressor()

        chunks = [
            Chunk(chunk_id=str(i), text=f"Chunk {i}", score=1.0 - i*0.1, source="doc.pdf")
            for i in range(10)
        ]

        result = compressor.compress_chunks(chunks, max_chunks=5)

        assert result["chunks_kept"] == 5
        assert result["chunks_removed"] == 5

    def test_compress_chunks_max_tokens(self):
        """Compression should respect max_tokens limit."""
        compressor = ContextCompressor()

        # Create chunks with known token counts
        chunks = [
            Chunk(
                chunk_id="1",
                text="This is a test chunk with some content. " * 10,  # ~80 tokens
                score=0.9,
                source="doc.pdf",
            ),
            Chunk(
                chunk_id="2",
                text="Another test chunk. " * 10,  # ~40 tokens
                score=0.8,
                source="doc.pdf",
            ),
            Chunk(
                chunk_id="3",
                text="Third chunk. " * 10,  # ~30 tokens
                score=0.7,
                source="doc.pdf",
            ),
        ]

        result = compressor.compress_chunks(chunks, max_chunks=10, max_tokens=100)

        # Should keep high-score chunks until total tokens <= 100
        assert result["compressed_token_count"] <= 100

    def test_compression_reduction_percent(self):
        """Compression should calculate reduction percentage."""
        compressor = ContextCompressor()

        chunks = [
            Chunk(
                chunk_id=str(i),
                text="This is a test chunk with some content. " * 20,
                score=1.0,
                source="doc.pdf",
            )
            for i in range(10)
        ]

        result = compressor.compress_chunks(chunks, max_chunks=2)

        assert "reduction_percent" in result
        assert result["reduction_percent"] > 0
        assert result["reduction_percent"] < 100

    def test_get_compression_metrics(self):
        """get_compression_metrics should return detailed stats."""
        compressor = ContextCompressor()

        original = [
            Chunk(chunk_id="1", text="Long text " * 50, score=0.9, source="doc.pdf"),
            Chunk(chunk_id="2", text="Long text " * 50, score=0.8, source="doc.pdf"),
        ]
        compressed = [original[0]]

        metrics = compressor.get_compression_metrics(original, compressed)

        assert "original_chunks" in metrics
        assert "compressed_chunks" in metrics
        assert "original_tokens" in metrics
        assert "compressed_tokens" in metrics
        assert "reduction_percent" in metrics
        assert metrics["original_chunks"] == 2
        assert metrics["compressed_chunks"] == 1

    def test_format_chunks_for_prompt(self):
        """Chunks should be formatted for LLM prompt."""
        compressor = ContextCompressor()

        chunks = [
            Chunk(
                chunk_id="1",
                text="Step 1: Check logs",
                score=0.95,
                source="guide.pdf",
                metadata={"section": "Troubleshooting"},
            ),
            Chunk(
                chunk_id="2",
                text="Step 2: Restart service",
                score=0.90,
                source="guide.pdf",
                metadata={"section": "Troubleshooting"},
            ),
        ]

        formatted = compressor.format_chunks_for_prompt(chunks, include_metadata=True)

        assert "Chunk 1:" in formatted
        assert "Chunk 2:" in formatted
        assert "Step 1: Check logs" in formatted
        assert "[Source: guide.pdf" in formatted

    def test_format_chunks_without_metadata(self):
        """Chunks should be formattable without metadata."""
        compressor = ContextCompressor()

        chunks = [
            Chunk(chunk_id="1", text="Content 1", score=0.9, source="doc.pdf"),
            Chunk(chunk_id="2", text="Content 2", score=0.8, source="doc.pdf"),
        ]

        formatted = compressor.format_chunks_for_prompt(chunks, include_metadata=False)

        assert "Content 1" in formatted
        assert "Content 2" in formatted
        assert "[Source:" not in formatted


class TestLatencyInstrumentation:
    """Test latency tracking and analysis."""

    def test_latency_timer_context_manager(self):
        """LatencyTimer should measure elapsed time."""
        with LatencyTimer("test") as timer:
            import time
            time.sleep(0.01)  # 10ms

        assert timer.elapsed_ms >= 10

    def test_latency_breakdown_initialization(self):
        """LatencyBreakdown should initialize to zero."""
        breakdown = LatencyBreakdown()
        assert breakdown.embedding_ms == 0.0
        assert breakdown.search_ms == 0.0
        assert breakdown.total_ms == 0.0

    def test_latency_breakdown_add_stage(self):
        """add_stage should accumulate times and update total."""
        breakdown = LatencyBreakdown()
        breakdown.add_stage("embedding", 100.0)
        breakdown.add_stage("search", 350.0)
        breakdown.add_stage("generation", 1800.0)

        assert breakdown.embedding_ms == 100.0
        assert breakdown.search_ms == 350.0
        assert breakdown.generation_ms == 1800.0
        assert breakdown.total_ms == 2250.0

    def test_latency_breakdown_to_dict(self):
        """to_dict should return proper structure."""
        breakdown = LatencyBreakdown(
            embedding_ms=100.0,
            search_ms=350.0,
            generation_ms=1800.0,
        )

        d = breakdown.to_dict()

        assert isinstance(d, dict)
        assert "embedding_ms" in d
        assert "total_ms" in d
        assert isinstance(d["embedding_ms"], float)

    def test_measure_latency_decorator_sync(self):
        """measure_latency decorator should work with sync functions."""
        from app.cache.metrics import MetricsCollector
        MetricsCollector.reset()

        @measure_latency("test_stage")
        def slow_function():
            import time
            time.sleep(0.01)
            return "result"

        result = slow_function()

        assert result == "result"
        metrics = MetricsCollector.get_instance()
        assert metrics.query_count > 0

    @pytest.mark.asyncio
    async def test_measure_latency_decorator_async(self):
        """measure_latency decorator should work with async functions."""
        from app.cache.metrics import MetricsCollector
        MetricsCollector.reset()

        @measure_latency("async_stage")
        async def slow_async_function():
            await asyncio.sleep(0.01)
            return "result"

        result = await slow_async_function()

        assert result == "result"
        metrics = MetricsCollector.get_instance()
        assert metrics.query_count > 0


class TestPerformanceAnalyzer:
    """Test performance analysis utilities."""

    def test_speedup_factor_calculation(self):
        """Speedup factor should be cold / warm."""
        speedup = PerformanceAnalyzer.get_speedup_factor(2250.0, 5.0)
        assert speedup == pytest.approx(450.0)

    def test_speedup_factor_infinite(self):
        """Speedup should be infinite if warm = 0."""
        speedup = PerformanceAnalyzer.get_speedup_factor(1000.0, 0.0)
        assert speedup == float("inf")

    def test_latency_breakdown_analysis(self):
        """Analyze latency breakdown percentages."""
        breakdown = LatencyBreakdown()
        breakdown.add_stage("embedding", 100.0)
        breakdown.add_stage("search", 350.0)
        breakdown.add_stage("compression", 50.0)
        breakdown.add_stage("generation", 1800.0)

        analysis = PerformanceAnalyzer.get_latency_breakdown(breakdown)

        assert "embedding_percent" in analysis
        assert "search_percent" in analysis
        assert "generation_percent" in analysis
        assert "bottleneck" in analysis
        # Generation is the biggest: 1800 / 2300 = 78%
        assert analysis["bottleneck"] == "generation"

    def test_cost_reduction_estimation(self):
        """Cost reduction should be calculated correctly."""
        cost = PerformanceAnalyzer.estimate_cost_reduction(
            original_tokens=10_000,
            compressed_tokens=2_500,
            cost_per_m_input=3.0,
        )

        assert "original_cost_usd" in cost
        assert "compressed_cost_usd" in cost
        assert "savings_usd" in cost
        assert "savings_percent" in cost
        # 75% token reduction = 75% cost reduction
        assert cost["savings_percent"] == pytest.approx(75.0, abs=1)

    def test_cost_reduction_zero_savings(self):
        """Cost reduction with no compression should be zero."""
        cost = PerformanceAnalyzer.estimate_cost_reduction(
            original_tokens=5_000,
            compressed_tokens=5_000,
            cost_per_m_input=3.0,
        )

        assert cost["savings_usd"] == pytest.approx(0.0)
        assert cost["savings_percent"] == pytest.approx(0.0)


class TestDemo3Scenario:
    """Test Demo 3: Cold vs Warm Latency (450× speedup)."""

    def test_demo3_cold_latency(self):
        """Demo 3 cold cache should be ~2300ms."""
        cold_total = DEMO_3_COLD_LATENCY["total_ms"]
        assert 2200 <= cold_total <= 2400

    def test_demo3_warm_latency(self):
        """Demo 3 warm cache should be <=5ms."""
        warm_total = DEMO_3_WARM_LATENCY["total_ms"]
        assert warm_total <= 5

    def test_demo3_speedup(self):
        """Demo 3 speedup should be ~450×."""
        assert 400 < DEMO_3_SPEEDUP < 500

    def test_demo3_breakdown(self):
        """Demo 3 should show latency breakdown."""
        breakdown = LatencyBreakdown()
        breakdown.add_stage("embedding", DEMO_3_COLD_LATENCY["embedding_ms"])
        breakdown.add_stage("search", DEMO_3_COLD_LATENCY["search_ms"])
        breakdown.add_stage("compression", DEMO_3_COLD_LATENCY["compression_ms"])
        breakdown.add_stage("generation", DEMO_3_COLD_LATENCY["generation_ms"])

        analysis = PerformanceAnalyzer.get_latency_breakdown(breakdown)

        # Generation should be bottleneck (~78%)
        assert analysis["bottleneck"] == "generation"
        assert analysis["generation_percent"] > 70

    def test_demo3_token_reduction(self):
        """Demo 3 token reduction: 10K → 2.5K."""
        cost = PerformanceAnalyzer.estimate_cost_reduction(
            original_tokens=10_000,
            compressed_tokens=2_500,
        )

        # 75% token reduction
        assert cost["savings_percent"] == pytest.approx(75.0)


class TestCompressionIntegration:
    """Test compression integration with cache manager."""

    def test_cache_manager_compress_chunks(self):
        """CacheManager should support compression."""
        from app.cache import get_cache_manager

        manager = get_cache_manager()

        chunks = [
            Chunk(
                chunk_id=str(i),
                text="Test chunk with content. " * 20,
                score=1.0 - i*0.1,
                source="doc.pdf",
            )
            for i in range(10)
        ]

        result = manager.compress_chunks(chunks, max_chunks=5)

        assert result["chunks_kept"] == 5
        assert result["chunks_removed"] == 5
        assert result["reduction_percent"] > 0

    def test_cache_manager_format_chunks(self):
        """CacheManager should format chunks for prompt."""
        from app.cache import get_cache_manager

        manager = get_cache_manager()

        chunks = [
            Chunk(
                chunk_id="1",
                text="Content",
                score=0.9,
                source="doc.pdf",
                metadata={"section": "Test"},
            ),
        ]

        formatted = manager.format_chunks_for_prompt(chunks)

        assert "Chunk 1:" in formatted
        assert "Content" in formatted
