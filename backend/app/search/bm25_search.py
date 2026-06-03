from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import re

class BM25SearchEngine:
    def __init__(self):
        """Initialize BM25 search engine."""
        self.bm25 = None
        self.corpus = []  # Original texts for reference
        self.chunks = []  # Full chunk metadata
        self.tokenized_corpus = []  # Tokenized texts for BM25

    def build_index(self, texts: List[str], chunks: List[Dict[str, Any]] = None):
        """Build BM25 index from texts.

        Args:
            texts: List of text documents/chunks
            chunks: Optional list of full chunk dicts with metadata
        """
        self.corpus = texts
        self.chunks = chunks or [{'text': text} for text in texts]
        self.tokenized_corpus = [self._tokenize(text) for text in texts]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"BM25 index built with {len(texts)} documents")

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split on whitespace, remove punctuation.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        text = text.lower()
        # Remove special characters but keep alphanumeric and hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        tokens = text.split()
        return tokens

    def search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Search using BM25.

        Args:
            query: Query string
            top_k: Number of top results to return

        Returns:
            List of results with text, score, and rank
        """
        if self.bm25 is None:
            raise ValueError("BM25 index not built. Call build_index first.")

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # Create list of (index, score) and sort by score descending
        indexed_scores = [(idx, score) for idx, score in enumerate(scores)]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (idx, score) in enumerate(indexed_scores[:top_k]):
            chunk = self.chunks[idx] if idx < len(self.chunks) else {}
            result = {
                'chunk_id': chunk.get('chunk_id', f'chunk_{idx}'),
                'text': self.corpus[idx],
                'doc_id': chunk.get('doc_id', ''),
                'filename': chunk.get('filename', ''),
                'section': chunk.get('section', ''),
                'page': chunk.get('page', 0),
                'department': chunk.get('department', ''),
                'category': chunk.get('category', ''),
                'score': float(score),
                'rank': rank
            }
            results.append(result)

        return results

    def get_corpus_size(self) -> int:
        """Get number of documents in index."""
        return len(self.corpus)
