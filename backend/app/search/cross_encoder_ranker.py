"""Cross-Encoder Re-ranking using HuggingFace Inference API"""

import logging
import os
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Use HuggingFace Inference API for cross-encoder re-ranking"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize cross-encoder reranker using Inference API.

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.api_url = os.getenv("HF_API_URL", "https://api-inference.huggingface.co/models")
        self.hf_token = os.getenv("HF_TOKEN")
        self.available = False

        if self.hf_token:
            self.available = True
            logger.info(f"Cross-Encoder Inference API initialized: {model_name}")
        else:
            logger.warning("HF_TOKEN not set - cross-encoder reranking disabled")
            self.available = False

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results using cross-encoder via Inference API.

        Args:
            query: Original query string
            results: Search results to re-rank
            top_k: Only re-rank top-k results (cost optimization)

        Returns:
            Re-ranked results with reranked_score field
        """
        if not self.available or not results:
            return results

        try:
            # Only re-rank top_k results (cost optimization)
            results_to_rank = results[:top_k]
            remaining_results = results[top_k:]

            # Prepare pairs: [query, document_text]
            pairs = [[query, result.get('text', '')] for result in results_to_rank]

            url = f"{self.api_url}/{self.model_name}"
            headers = {"Authorization": f"Bearer {self.hf_token}"}

            # Call Inference API
            response = requests.post(
                url,
                headers=headers,
                json={"inputs": pairs},
                timeout=60
            )
            response.raise_for_status()

            scores = response.json()

            # Add scores to results
            for result, score in zip(results_to_rank, scores):
                result['reranked_score'] = float(score)

            # Sort by reranked score (descending)
            results_to_rank.sort(key=lambda x: x['reranked_score'], reverse=True)

            # Combine with remaining results
            reranked_results = results_to_rank + remaining_results

            # Update rank field
            for idx, result in enumerate(reranked_results):
                result['rank'] = idx

            if scores:
                top_score = max(scores) if isinstance(scores, list) else scores[0]
                logger.info(f"Cross-encoder reranked {len(results_to_rank)} results, top score: {top_score:.3f}")

            return reranked_results

        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}. Returning original results.")
            return results

    def batch_rerank(
        self,
        queries: List[str],
        results_per_query: List[List[Dict[str, Any]]],
        top_k: int = 20
    ) -> List[List[Dict[str, Any]]]:
        """
        Re-rank multiple queries in batch.

        Args:
            queries: List of query strings
            results_per_query: List of result lists (one per query)
            top_k: Only re-rank top-k per query

        Returns:
            List of re-ranked result lists
        """
        return [
            self.rerank(query, results, top_k=top_k)
            for query, results in zip(queries, results_per_query)
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get reranker statistics and status"""
        return {
            "available": self.available,
            "model": self.model_name if self.available else None,
            "type": "cross-encoder-inference-api"
        }
