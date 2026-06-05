"""Cache embeddings by text hash to avoid redundant API calls."""

import hashlib
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """File-based embedding cache with text hash keys."""

    def __init__(self, cache_dir: str = None):
        """
        Initialize embedding cache.

        Args:
            cache_dir: Directory to store cache (default: backend/data/embeddings_cache)
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "embeddings_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _hash_text(text: str) -> str:
        """Generate SHA256 hash of text."""
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache by text."""
        text_hash = self._hash_text(text)
        cache_file = self.cache_dir / f"{text_hash}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.hits += 1
                    logger.debug(f"Cache hit for {text_hash[:8]}")
                    return data['embedding']
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
                return None

        self.misses += 1
        return None

    def set(self, text: str, embedding: List[float]) -> bool:
        """Store embedding in cache."""
        text_hash = self._hash_text(text)
        cache_file = self.cache_dir / f"{text_hash}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'text': text[:200],  # Store snippet for debugging
                    'embedding': embedding,
                    'hash': text_hash
                }, f)
            logger.debug(f"Cached embedding for {text_hash[:8]}")
            return True
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': len(list(self.cache_dir.glob('*.json'))),
        }
