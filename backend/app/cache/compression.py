"""Context compression for M4: reduce top-20 chunks to top-5."""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContextCompressor:
    """Compress context chunks to reduce token usage (75% reduction target)."""

    @staticmethod
    def count_tokens_approx(text: str) -> int:
        """Approximate token count (roughly 4 chars = 1 token)."""
        return len(text) // 4

    @staticmethod
    def compress_chunks(
        chunks: List[Dict[str, Any]],
        max_chunks: int = 5,
        preserve_top_k: bool = True
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Compress chunks by selecting top-K by score (simple strategy).

        Args:
            chunks: List of search result chunks
            max_chunks: Maximum chunks to keep (default 5)
            preserve_top_k: If True, keep top K by score

        Returns:
            (compressed_chunks, compression_stats)
        """
        if len(chunks) <= max_chunks:
            return chunks, {
                "original_chunks": len(chunks),
                "compressed_chunks": len(chunks),
                "reduction_percent": 0,
                "original_tokens": sum(ContextCompressor.count_tokens_approx(c.get("text", "")) for c in chunks),
                "compressed_tokens": sum(ContextCompressor.count_tokens_approx(c.get("text", "")) for c in chunks),
            }

        # Sort by score (descending) and take top K
        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
        compressed = sorted_chunks[:max_chunks]

        original_tokens = sum(ContextCompressor.count_tokens_approx(c.get("text", "")) for c in chunks)
        compressed_tokens = sum(ContextCompressor.count_tokens_approx(c.get("text", "")) for c in compressed)

        reduction_percent = round((1 - compressed_tokens / original_tokens) * 100, 1)

        logger.info(
            f"🗜️ Context compressed: {len(chunks)} → {len(compressed)} chunks | "
            f"{original_tokens} → {compressed_tokens} tokens ({reduction_percent}% reduction)"
        )

        return compressed, {
            "original_chunks": len(chunks),
            "compressed_chunks": len(compressed),
            "reduction_percent": reduction_percent,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
        }

    @staticmethod
    def compress_for_generation(
        chunks: List[Dict[str, Any]],
        target_tokens: int = 2500
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Intelligently compress chunks to fit within target token budget.

        Strategy:
        1. Keep highest-scoring chunks first
        2. Add more chunks until target token count reached
        3. Stop when adding next chunk would exceed budget
        """
        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)

        selected = []
        token_count = 0

        for chunk in sorted_chunks:
            chunk_tokens = ContextCompressor.count_tokens_approx(chunk.get("text", ""))
            if token_count + chunk_tokens <= target_tokens:
                selected.append(chunk)
                token_count += chunk_tokens
            else:
                break

        # Fallback: if no chunks selected, at least include top-1
        if not selected:
            selected = [sorted_chunks[0]]
            token_count = ContextCompressor.count_tokens_approx(sorted_chunks[0].get("text", ""))

        original_tokens = sum(ContextCompressor.count_tokens_approx(c.get("text", "")) for c in chunks)
        reduction_percent = round((1 - token_count / original_tokens) * 100, 1) if original_tokens > 0 else 0

        logger.info(
            f"🎯 Generation context: {len(chunks)} → {len(selected)} chunks | "
            f"{original_tokens} → {token_count} tokens ({reduction_percent}% reduction, target: {target_tokens})"
        )

        return selected, {
            "original_chunks": len(chunks),
            "selected_chunks": len(selected),
            "reduction_percent": reduction_percent,
            "original_tokens": original_tokens,
            "selected_tokens": token_count,
            "target_tokens": target_tokens,
        }
