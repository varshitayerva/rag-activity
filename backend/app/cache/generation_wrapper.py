"""Wrapper to add M4 caching to generation service."""

from typing import Optional, List, Dict, Any, AsyncGenerator
from app.cache.cache_manager import CacheManager
from app.cache.compression import ContextCompressor
import logging

logger = logging.getLogger(__name__)


class CachedGenerationWrapper:
    """Wraps a GenerationService with M4 Layer 3 caching and compression."""

    def __init__(self, generation_service, cache_manager: Optional[CacheManager] = None):
        self.service = generation_service
        self.cache_manager = cache_manager

    async def generate(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        compress: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response with Layer 3 caching and compression.

        Args:
            query: User query
            chunks: Search result chunks
            compress: If True, compress chunks to 2500 tokens before generation

        Returns:
            Generated response (cached if available)
        """
        # M4: Check Layer 3 cache
        if self.cache_manager:
            cached_response = await self.cache_manager.get_response(query, chunks)
            if cached_response:
                logger.info(f"✅ Layer 3 HIT: Returning cached response for query: '{query[:50]}...'")
                return cached_response

        logger.debug(f"❌ Layer 3 MISS: Generating new response for query: '{query[:50]}...'")

        # M4: Compress chunks before generation (75% token reduction)
        original_chunks = chunks
        if compress and len(chunks) > 5:
            chunks, compression_stats = ContextCompressor.compress_for_generation(
                chunks,
                target_tokens=2500
            )
            logger.info(
                f"🗜️ Compression: {compression_stats['original_chunks']} → "
                f"{compression_stats['selected_chunks']} chunks | "
                f"{compression_stats['original_tokens']} → {compression_stats['selected_tokens']} tokens "
                f"({compression_stats['reduction_percent']}% reduction)"
            )

        # Generate response
        response = await self.service.generate(query, chunks)

        # M4: Cache the response
        if self.cache_manager and response:
            await self.cache_manager.cache_response(
                query,
                original_chunks,  # Cache with original chunks for consistency
                response
            )
            logger.info(f"💾 Layer 3 CACHED: Response cached for 2h")

        # Update metrics
        if self.cache_manager:
            input_tokens = response.get("tokens", {}).get("input_tokens", 0)
            output_tokens = response.get("tokens", {}).get("output_tokens", 0)
            self.cache_manager.update_metrics(input_tokens + output_tokens)

        return response

    async def generate_streaming(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        compress: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming SSE.

        Note: Streaming responses are NOT cached (too complex to cache streams).
        But we compress context before generation.

        Args:
            query: User query
            chunks: Search result chunks
            compress: If True, compress chunks to 2500 tokens before generation

        Yields:
            SSE events (metadata, tokens, done)
        """
        # M4: Compress chunks before streaming generation
        original_chunks = chunks
        if compress and len(chunks) > 5:
            chunks, compression_stats = ContextCompressor.compress_for_generation(
                chunks,
                target_tokens=2500
            )
            logger.info(
                f"🗜️ Compression (streaming): {compression_stats['original_chunks']} → "
                f"{compression_stats['selected_chunks']} chunks | "
                f"{compression_stats['reduction_percent']}% reduction"
            )

        # Stream response (not cached due to SSE complexity)
        async for event in self.service.generate_streaming(query, chunks):
            yield event

        # Update metrics for streaming
        if self.cache_manager:
            # For streaming, estimate tokens (rough approximation)
            estimated_tokens = len(query) // 4 + 500  # Estimate output tokens
            self.cache_manager.update_metrics(estimated_tokens)
