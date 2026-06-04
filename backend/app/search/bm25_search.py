from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import re
import pickle
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BM25SearchEngine:
    # Persistence directory
    PERSISTENCE_DIR = Path(__file__).parent.parent.parent / "data" / "bm25_indexes"
    INDEX_PATH = PERSISTENCE_DIR / "bm25_index.pkl"
    CORPUS_PATH = PERSISTENCE_DIR / "bm25_corpus.pkl"
    CHUNKS_PATH = PERSISTENCE_DIR / "bm25_chunks.pkl"

    def __init__(self):
        """Initialize BM25 search engine."""
        self.bm25 = None
        self.corpus = []  # Original texts for reference
        self.chunks = []  # Full chunk metadata
        self.tokenized_corpus = []  # Tokenized texts for BM25

        # Ensure persistence directory exists
        self.PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)

    def build_index(self, texts: List[str], chunks: List[Dict[str, Any]] = None):
        """Build BM25 index from texts and persist to disk.

        Args:
            texts: List of text documents/chunks
            chunks: Optional list of full chunk dicts with metadata
        """
        self.corpus = texts
        self.chunks = chunks or [{'text': text} for text in texts]
        self.tokenized_corpus = [self._tokenize(text) for text in texts]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        # Persist to disk
        try:
            self.save_index()
            logger.info(f"BM25 index built and persisted with {len(texts)} documents")
        except Exception as e:
            logger.warning(f"Failed to persist BM25 index: {e}. Index will be rebuilt on restart.")
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

    def save_index(self):
        """Save BM25 index to disk."""
        try:
            with open(self.INDEX_PATH, 'wb') as f:
                pickle.dump(self.bm25, f)
            with open(self.CORPUS_PATH, 'wb') as f:
                pickle.dump(self.corpus, f)
            with open(self.CHUNKS_PATH, 'wb') as f:
                pickle.dump(self.chunks, f)
            logger.info(f"BM25 index persisted to {self.INDEX_PATH}")
        except Exception as e:
            logger.error(f"Failed to save BM25 index: {e}")
            raise

    def load_index(self) -> bool:
        """
        Load BM25 index from disk if it exists.

        Returns:
            True if loaded successfully, False if not found or corrupted
        """
        try:
            if not self.INDEX_PATH.exists():
                logger.info("No persisted BM25 index found")
                return False

            with open(self.INDEX_PATH, 'rb') as f:
                self.bm25 = pickle.load(f)
            with open(self.CORPUS_PATH, 'rb') as f:
                self.corpus = pickle.load(f)
            with open(self.CHUNKS_PATH, 'rb') as f:
                self.chunks = pickle.load(f)

            logger.info(f"Loaded persisted BM25 index with {len(self.corpus)} documents")
            return True

        except Exception as e:
            logger.warning(f"Failed to load BM25 index from disk: {e}. Will rebuild on next ingest.")
            # Clean up corrupted files
            self._cleanup_index_files()
            return False

    def _cleanup_index_files(self):
        """Remove corrupted index files."""
        for path in [self.INDEX_PATH, self.CORPUS_PATH, self.CHUNKS_PATH]:
            try:
                if path.exists():
                    path.unlink()
                    logger.info(f"Removed corrupted index file: {path}")
            except Exception as e:
                logger.warning(f"Failed to remove {path}: {e}")

    def get_corpus_size(self) -> int:
        """Get number of documents in index."""
        return len(self.corpus)
