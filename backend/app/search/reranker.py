"""Reranking utilities for search results."""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BM25Reranker:
    """Rerank results using BM25 scores."""

    @staticmethod
    def rerank(chunks: List[Dict[str, Any]], bm25_engine, query: str,
               top_k: int = None) -> List[Dict[str, Any]]:
        """
        Rerank chunks using BM25 scores.

        Args:
            chunks: Initial chunks from vector search
            bm25_engine: BM25SearchEngine instance
            query: Original query
            top_k: Rerank to top-k (if None, rerank all)

        Returns:
            Reranked chunks
        """
        if not chunks or bm25_engine.bm25 is None:
            return chunks

        try:
            # Get BM25 scores for each chunk's text
            bm25_results = bm25_engine.search(query, top_k=len(chunks) * 2)

            # Map text to BM25 score
            bm25_scores = {r['text']: r['score'] for r in bm25_results}

            # Rerank by combining vector + BM25 scores
            reranked = []
            for chunk in chunks:
                chunk_copy = chunk.copy()
                bm25_score = bm25_scores.get(chunk.get('text', ''), 0.0)

                # Combine scores (50/50 weighting)
                original_score = chunk.get('score', 0)
                combined_score = (original_score + bm25_score) / 2
                chunk_copy['score'] = combined_score
                chunk_copy['bm25_score'] = bm25_score
                chunk_copy['reranked'] = True
                reranked.append(chunk_copy)

            # Sort by combined score
            reranked.sort(key=lambda x: x['score'], reverse=True)

            logger.info(f"Reranked {len(reranked)} chunks using BM25")
            return reranked[:top_k] if top_k else reranked

        except Exception as e:
            logger.error(f"BM25 reranking failed: {e}. Returning original order.")
            return chunks
