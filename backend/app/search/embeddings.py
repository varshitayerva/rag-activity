import os
import hashlib
import numpy as np
import logging
import requests
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


class EmbeddingsClient:
    def __init__(self, model: str = "sentence-transformers/all-mpnet-base-v2", api_key: str = None,
                 use_cache: bool = True):
        """Initialize HuggingFace Inference API embeddings client.

        Args:
            model: HuggingFace model ID
            api_key: Not used (HF_TOKEN from env)
            use_cache: Whether to cache embeddings (default: True)
        """
        self.model = model
        self.api_url = os.getenv("HF_API_URL", "https://api-inference.huggingface.co/models")
        self.hf_token = os.getenv("HF_TOKEN")
        self.embedding_dim = 1536
        self.base_dim = 768

        if not self.hf_token:
            logger.warning("HF_TOKEN not set - embeddings will use mock fallback")
            self.available = False
        else:
            self.available = True
            logger.info(f"HuggingFace Inference API initialized for {model}")

        # Initialize cache
        if use_cache:
            try:
                from backend.app.search.embedding_cache import EmbeddingCache
                self.cache = EmbeddingCache()
            except Exception:
                self.cache = None
        else:
            self.cache = None

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string via Inference API.

        Args:
            query: Query text

        Returns:
            Embedding vector (list of floats)
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(query)
            if cached:
                return cached

        try:
            if not self.available:
                return self._mock_embedding(query)

            url = f"{self.api_url}/{self.model}"
            headers = {"Authorization": f"Bearer {self.hf_token}"}

            response = requests.post(
                url,
                headers=headers,
                json={"inputs": query},
                timeout=30
            )
            response.raise_for_status()

            embedding = response.json()[0]

            # Expand from 768 to 1536 dimensions
            embedding = self._expand_to_1536(embedding)

            # Store in cache
            if self.cache:
                self.cache.set(query, embedding)

            return embedding

        except Exception as e:
            logger.error(f"Inference API embedding failed: {e}. Using mock embedding.")
            return self._mock_embedding(query)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts via Inference API.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = []
        to_embed = []
        to_embed_indices = []

        # Check cache for each text
        for i, text in enumerate(texts):
            if self.cache:
                cached = self.cache.get(text)
                if cached:
                    embeddings.append(cached)
                else:
                    to_embed.append(text)
                    to_embed_indices.append(i)
            else:
                to_embed.append(text)
                to_embed_indices.append(i)

        # Embed texts not in cache
        if to_embed:
            try:
                if not self.available:
                    for text in to_embed:
                        embeddings.append(self._mock_embedding(text))
                    return embeddings

                url = f"{self.api_url}/{self.model}"
                headers = {"Authorization": f"Bearer {self.hf_token}"}

                response = requests.post(
                    url,
                    headers=headers,
                    json={"inputs": to_embed},
                    timeout=60
                )
                response.raise_for_status()

                batch_embeddings = response.json()

                for idx, embedding in enumerate(batch_embeddings):
                    # Expand from 768 to 1536 dimensions
                    expanded = self._expand_to_1536(embedding)

                    # Cache it
                    if self.cache:
                        self.cache.set(to_embed[idx], expanded)

                    # Insert in correct position
                    insert_pos = to_embed_indices[idx]
                    embeddings.insert(insert_pos, expanded)

            except Exception as e:
                logger.error(f"Inference API batch embedding failed: {e}. Using mock embeddings.")
                for text in to_embed:
                    embeddings.append(self._mock_embedding(text))

        return embeddings

    def embed_chunks(self, chunks: List[dict]) -> List[List[float]]:
        """Embed chunk texts from chunk dicts.

        Args:
            chunks: List of chunk dicts with 'text' field

        Returns:
            List of embedding vectors
        """
        texts = [chunk['text'] for chunk in chunks]
        return self.embed_batch(texts)

    def _expand_to_1536(self, embedding: List[float]) -> List[float]:
        """Expand embedding from 768 to 1536 dimensions by concatenating duplicates and padding."""
        if isinstance(embedding, list):
            embedding = np.array(embedding, dtype=np.float32)

        if len(embedding) >= 1536:
            return embedding[:1536].tolist()

        # Duplicate and pad to 1536 dimensions
        repeats = (1536 // len(embedding)) + 1
        expanded = np.tile(embedding, repeats)[:1536]

        # Normalize
        expanded = expanded / np.linalg.norm(expanded)
        return expanded.tolist()

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate semantic-aware mock embedding based on text content.

        Uses TF-IDF-like approach instead of pure random noise.
        Similar texts will have similar embeddings.
        """
        # Tokenize and get word frequencies
        words = text.lower().split()
        word_freqs = {}
        for word in words:
            # Clean word
            word = ''.join(c for c in word if c.isalnum())
            if len(word) > 2:
                word_freqs[word] = word_freqs.get(word, 0) + 1

        # Initialize embedding with zeros
        embedding = np.zeros(self.embedding_dim, dtype=np.float32)

        if not word_freqs:
            # Fallback for empty text
            text_hash = hashlib.md5(text.encode()).digest()
            np.random.seed(int.from_bytes(text_hash[:4], 'big'))
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        else:
            # Build embedding from word hashes
            total_words = sum(word_freqs.values())
            for word, freq in word_freqs.items():
                # Hash each word to consistent dimensions
                word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)

                # Distribute word's contribution across embedding dimensions
                for i in range(self.embedding_dim):
                    # Use word hash to create deterministic but varied values
                    dimension_seed = (word_hash + i) % 1000000
                    np.random.seed(dimension_seed)
                    # Add word frequency weighted contribution
                    contribution = np.random.randn() * (freq / total_words)
                    embedding[i] += contribution

        # Normalize to unit vector for consistent similarity scores
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        else:
            embedding = np.ones(self.embedding_dim, dtype=np.float32) / np.sqrt(self.embedding_dim)

        return embedding.tolist()
