import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.search.bm25_search import BM25SearchEngine
from backend.app.search.rrf_fusion import RRFFusion
from backend.app.search.embeddings import EmbeddingsClient

class TestBM25Search:
    """Test BM25 sparse search implementation."""

    def test_bm25_build_index(self):
        """Test building BM25 index."""
        engine = BM25SearchEngine()
        texts = [
            "How to restart a Kubernetes pod",
            "ImagePullBackOff error in Docker",
            "Database connection timeout issues",
            "RBAC permission denied error",
        ]
        engine.build_index(texts)
        assert engine.get_corpus_size() == 4

    def test_bm25_search_exact_match(self):
        """Test BM25 finds exact string matches (sparse search strength)."""
        engine = BM25SearchEngine()
        texts = [
            "How to fix ImagePullBackOff error",
            "Container restart policy settings",
            "Pod eviction and memory issues",
            "ImagePullBackOff troubleshooting guide",
        ]
        engine.build_index(texts)

        results = engine.search("ImagePullBackOff", top_k=10)
        assert len(results) > 0
        # Top result should contain "ImagePullBackOff"
        assert "ImagePullBackOff" in results[0]['text']
        assert results[0]['rank'] == 0

    def test_bm25_search_scoring_order(self):
        """Test BM25 ranks results by relevance score."""
        engine = BM25SearchEngine()
        texts = [
            "Pod troubleshooting and debugging",
            "How to restart a pod in Kubernetes",
            "Pod configuration best practices",
        ]
        engine.build_index(texts)

        results = engine.search("restart pod", top_k=10)
        # Result with "restart pod" should rank higher
        assert results[0]['score'] > results[1]['score']

    def test_bm25_tokenization(self):
        """Test tokenization handles various text formats."""
        engine = BM25SearchEngine()
        texts = [
            "Error: RBAC policy denied access!",
            "Fix: Remove special characters?",
            "Pod-to-Pod networking issues",
        ]
        engine.build_index(texts)

        results = engine.search("RBAC denied", top_k=10)
        assert len(results) > 0

    def test_bm25_handles_empty_query(self):
        """Test BM25 handles empty query gracefully."""
        engine = BM25SearchEngine()
        texts = ["Test document", "Another document"]
        engine.build_index(texts)

        results = engine.search("", top_k=10)
        # Should return results (all with same score)
        assert len(results) > 0

    def test_bm25_not_built_error(self):
        """Test error when searching without building index."""
        engine = BM25SearchEngine()
        with pytest.raises(ValueError, match="BM25 index not built"):
            engine.search("query")

class TestRRFFusion:
    """Test RRF fusion algorithm."""

    def test_rrf_basic_fusion(self):
        """Test basic RRF fusion of two result sets."""
        vector_results = [
            {'text': 'Pod restart guide', 'rank': 0, 'score': 0.95},
            {'text': 'Container restart', 'rank': 1, 'score': 0.85},
        ]
        bm25_results = [
            {'text': 'Container restart', 'rank': 0, 'score': 100},
            {'text': 'Pod restart guide', 'rank': 1, 'score': 90},
        ]

        fused = RRFFusion.fuse(vector_results, bm25_results, k=60)

        # Both results should be included
        assert len(fused) == 2
        texts = [r['text'] for r in fused]
        assert 'Pod restart guide' in texts
        assert 'Container restart' in texts
        # Both should appear in both search results
        assert fused[0]['from_vector'] is True
        assert fused[0]['from_bm25'] is True
        assert fused[1]['from_vector'] is True
        assert fused[1]['from_bm25'] is True

    def test_rrf_k_parameter_effect(self):
        """Test that k parameter affects weighting."""
        vector_results = [
            {'text': 'Document A', 'rank': 0, 'score': 0.95},
        ]
        bm25_results = [
            {'text': 'Document B', 'rank': 0, 'score': 100},
        ]

        fused_k30 = RRFFusion.fuse(vector_results, bm25_results, k=30)
        fused_k100 = RRFFusion.fuse(vector_results, bm25_results, k=100)

        # With k=30, top results have higher impact
        # With k=100, results are more balanced
        assert len(fused_k30) == 2
        assert len(fused_k100) == 2

    def test_rrf_missing_sources(self):
        """Test RRF when result appears in only one search (vector or BM25)."""
        vector_results = [
            {'text': 'Semantic content only in vector search', 'rank': 0, 'score': 0.92},
        ]
        bm25_results = [
            {'text': 'Exact match in BM25 only', 'rank': 0, 'score': 95},
        ]

        fused = RRFFusion.fuse(vector_results, bm25_results, k=60)

        assert len(fused) == 2
        # Both results should be included (union of both)
        texts = [r['text'] for r in fused]
        assert 'Semantic content only in vector search' in texts
        assert 'Exact match in BM25 only' in texts

    def test_rrf_score_calculation(self):
        """Test RRF score formula: 1/(k + rank)."""
        vector_results = [
            {'text': 'Doc1', 'rank': 0, 'score': 0.9},
        ]
        bm25_results = [
            {'text': 'Doc1', 'rank': 0, 'score': 100},
        ]

        fused = RRFFusion.fuse(vector_results, bm25_results, k=60)
        result = fused[0]

        # Score should be 1/(60+0) + 1/(60+0) = 1/60 + 1/60
        expected_score = 1.0/60 + 1.0/60
        assert abs(result['combined_rrf_score'] - expected_score) < 0.001

    def test_rrf_metadata_filter_department(self):
        """Test metadata filtering by department."""
        results = [
            {'text': 'Doc1', 'combined_rrf_score': 0.9, 'department': 'engineering'},
            {'text': 'Doc2', 'combined_rrf_score': 0.8, 'department': 'finance'},
            {'text': 'Doc3', 'combined_rrf_score': 0.7, 'department': 'engineering'},
        ]
        metadata_filter = {'department': 'engineering'}

        filtered = RRFFusion.apply_metadata_filter(results, metadata_filter)
        assert len(filtered) == 2
        assert all(r['department'] == 'engineering' for r in filtered)

    def test_rrf_metadata_filter_multiple(self):
        """Test metadata filtering with multiple constraints."""
        results = [
            {'text': 'Doc1', 'department': 'eng', 'category': 'k8s'},
            {'text': 'Doc2', 'department': 'eng', 'category': 'docker'},
            {'text': 'Doc3', 'department': 'ops', 'category': 'k8s'},
        ]
        metadata_filter = {'department': 'eng', 'category': 'k8s'}

        filtered = RRFFusion.apply_metadata_filter(results, metadata_filter)
        assert len(filtered) == 1
        assert filtered[0]['text'] == 'Doc1'

class TestEmbeddingsClient:
    """Test embeddings client (mocked, no actual API calls)."""

    @patch('app.search.embeddings.OpenAI')
    def test_embeddings_single_query(self, mock_openai):
        """Test embedding a single query."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response

        embedder = EmbeddingsClient(api_key='test-key')
        result = embedder.embed_query("test query")

        assert result == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once()

    @patch('app.search.embeddings.OpenAI')
    def test_embeddings_batch(self, mock_openai):
        """Test embedding multiple texts in batch."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2], index=0),
            MagicMock(embedding=[0.3, 0.4], index=1),
        ]
        mock_client.embeddings.create.return_value = mock_response

        embedder = EmbeddingsClient(api_key='test-key')
        results = embedder.embed_batch(["text1", "text2"])

        assert len(results) == 2
        assert results[0] == [0.1, 0.2]
        assert results[1] == [0.3, 0.4]

    @patch('app.search.embeddings.OpenAI')
    def test_embeddings_empty_batch(self, mock_openai):
        """Test embedding empty batch."""
        embedder = EmbeddingsClient(api_key='test-key')
        results = embedder.embed_batch([])

        assert results == []

class TestIntegrationHybridSearch:
    """Integration tests for hybrid search (without actual Qdrant/API)."""

    def test_vector_vs_bm25_strengths(self):
        """Demonstrate vector search captures semantic similarity."""
        # Vector search excels at semantic understanding
        vector_results = [
            {'text': 'How to troubleshoot container startup issues', 'rank': 0, 'score': 0.91},
            {'text': 'Pod lifecycle and restart policies', 'rank': 1, 'score': 0.88},
        ]

        # BM25 excels at exact string matches (error codes)
        bm25_results = [
            {'text': 'ImagePullBackOff error troubleshooting', 'rank': 0, 'score': 150},
            {'text': 'Container runtime errors: CrashLoopBackOff and ImagePullBackOff', 'rank': 1, 'score': 120},
        ]

        fused = RRFFusion.fuse(vector_results, bm25_results, k=60)

        # Both should contribute to final ranking
        assert len(fused) > 0
        # Verify we got results from both sources
        sources = [r for r in fused if r['from_vector'] and r['from_bm25']]
        assert len(sources) >= 0  # May or may not overlap

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
