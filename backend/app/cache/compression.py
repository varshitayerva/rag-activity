"""Context compression: reduce top-20 chunks → top-5 (10K tokens → 2.5K)."""

from typing import List, Dict, Any
import tiktoken
from app.cache.search_context import Chunk
from app.config import get_settings


class ContextCompressor:
    """Compress search results to reduce LLM prompt size."""

    def __init__(self):
        self.settings = get_settings()
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        try:
            return len(self.tokenizer.encode(text))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return len(text) // 4

    def compress_chunks(
        self,
        chunks: List[Chunk],
        max_chunks: int = None,
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """
        Compress chunks by selecting top N and limiting total tokens.

        Strategy:
        1. Sort by relevance score (highest first)
        2. Take top max_chunks
        3. Keep only until total tokens < max_tokens
        4. Return: compressed chunks, token counts, reduction %

        Args:
            chunks: List of chunks from search results
            max_chunks: Max number of chunks to keep (default: from config)
            max_tokens: Max total tokens allowed (default: from config)

        Returns:
            {
                "chunks": List[Chunk],
                "original_token_count": int,
                "compressed_token_count": int,
                "reduction_percent": float,
                "chunks_kept": int,
                "chunks_removed": int,
            }
        """
        if max_chunks is None:
            max_chunks = self.settings.context_compression_max_chunks
        if max_tokens is None:
            max_tokens = self.settings.context_compression_max_tokens

        # Calculate original token count
        original_text = "\n\n".join([c.text for c in chunks])
        original_tokens = self.count_tokens(original_text)

        # Sort by score (highest relevance first)
        sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)

        # Select chunks until we hit limits
        compressed_chunks = []
        compressed_tokens = 0

        for chunk in sorted_chunks:
            chunk_tokens = self.count_tokens(chunk.text)

            # Check if adding this chunk exceeds limits
            if len(compressed_chunks) >= max_chunks:
                break
            if compressed_tokens + chunk_tokens > max_tokens:
                break

            compressed_chunks.append(chunk)
            compressed_tokens += chunk_tokens

        # Calculate statistics
        reduction_percent = (
            (original_tokens - compressed_tokens) / original_tokens * 100
            if original_tokens > 0
            else 0
        )

        return {
            "chunks": compressed_chunks,
            "original_token_count": original_tokens,
            "compressed_token_count": compressed_tokens,
            "reduction_percent": round(reduction_percent, 1),
            "chunks_kept": len(compressed_chunks),
            "chunks_removed": len(chunks) - len(compressed_chunks),
        }

    def get_compression_metrics(
        self,
        original_chunks: List[Chunk],
        compressed_chunks: List[Chunk],
    ) -> Dict[str, Any]:
        """Get detailed compression metrics."""
        original_text = "\n\n".join([c.text for c in original_chunks])
        compressed_text = "\n\n".join([c.text for c in compressed_chunks])

        original_tokens = self.count_tokens(original_text)
        compressed_tokens = self.count_tokens(compressed_text)

        return {
            "original_chunks": len(original_chunks),
            "compressed_chunks": len(compressed_chunks),
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "reduction_tokens": original_tokens - compressed_tokens,
            "reduction_percent": (
                (original_tokens - compressed_tokens) / original_tokens * 100
                if original_tokens > 0
                else 0
            ),
            "avg_tokens_per_chunk_before": (
                original_tokens // len(original_chunks)
                if original_chunks
                else 0
            ),
            "avg_tokens_per_chunk_after": (
                compressed_tokens // len(compressed_chunks)
                if compressed_chunks
                else 0
            ),
        }

    def format_chunks_for_prompt(
        self,
        chunks: List[Chunk],
        include_metadata: bool = True,
    ) -> str:
        """
        Format chunks for inclusion in LLM prompt.

        Args:
            chunks: List of chunks to format
            include_metadata: Include source/section in output

        Returns:
            Formatted string for LLM context
        """
        formatted = []

        for i, chunk in enumerate(chunks, 1):
            if include_metadata:
                metadata_str = (
                    f"\n[Source: {chunk.source} | "
                    f"Section: {chunk.metadata.get('section', 'N/A')} | "
                    f"Score: {chunk.score:.2f}]"
                )
            else:
                metadata_str = ""

            formatted.append(f"Chunk {i}:\n{chunk.text}{metadata_str}")

        return "\n\n".join(formatted)


# Singleton instance
_compressor: ContextCompressor = None


def get_compressor() -> ContextCompressor:
    """Get or create context compressor singleton."""
    global _compressor
    if _compressor is None:
        _compressor = ContextCompressor()
    return _compressor
