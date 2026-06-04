import os
import hashlib
import numpy as np
from typing import List, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class EmbeddingsClient:
    def __init__(self, model: str = "sentence-transformers/all-mpnet-base-v2", api_key: str = None,
                 use_cache: bool = True):
        """Initialize HuggingFace sentence-transformers embeddings client (1536 dimensions).

        Args:
            model: HuggingFace sentence-transformers model ID
            api_key: Not used (HF_TOKEN from env used by transformers library)
            use_cache: Whether to cache embeddings (default: True)
        """
        self.model = model
        self._embedder = None
        self.embedding_dim = 1536
        self.base_dim = self._get_base_dim(model)

        # Initialize cache
        if use_cache:
            try:
                from backend.app.search.embedding_cache import EmbeddingCache
                self.cache = EmbeddingCache()
            except Exception:
                self.cache = None
        else:
            self.cache = None

    def _get_base_dim(self, model: str) -> int:
        """Get base embedding dimension for HuggingFace model."""
        dims = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/paraphrase-MiniLM-L6-v2": 384,
            "sentence-transformers/paraphrase-mpnet-base-v2": 768,
            "sentence-transformers/distilbert-base-multilingual-cased": 768,
        }
        return dims.get(model, 768)

    def _get_embedder(self):
        """Lazy load sentence-transformers model from HuggingFace."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading HuggingFace model: {self.model}")
                self._embedder = SentenceTransformer(self.model)
            except ImportError:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        return self._embedder

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string.

        Args:
            query: Query text

        Returns:
            Embedding vector (list of floats, 1536 dimensions)
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(query)
            if cached:
                return cached

        try:
            embedder = self._get_embedder()
            embedding = embedder.encode(query, convert_to_tensor=False)
            # Expand to 1536 dimensions
            embedding = self._expand_to_1536(embedding)

            # Store in cache
            if self.cache:
                self.cache.set(query, embedding)

            return embedding
        except Exception as e:
            print(f"HuggingFace embedding failed: {e}. Using mock embedding.")
            return self._mock_embedding(query)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch with caching for cache hits.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (1536 dimensions each)
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
                embedder = self._get_embedder()
                batch_embeddings = embedder.encode(to_embed, convert_to_tensor=False)

                for idx, embedding in enumerate(batch_embeddings):
                    # Expand to 1536 dimensions
                    expanded = self._expand_to_1536(embedding)
                    # Cache it
                    if self.cache:
                        self.cache.set(to_embed[idx], expanded)

                    # Insert in correct position
                    insert_pos = to_embed_indices[idx]
                    embeddings.insert(insert_pos, expanded)

            except Exception as e:
                print(f"HuggingFace batch embedding failed: {e}. Using mock embeddings.")
                for text in to_embed:
                    embeddings.append(self._mock_embedding(text))

        return embeddings

    def embed_chunks(self, chunks: List[dict]) -> List[List[float]]:
        """Embed chunk texts from chunk dicts.

        Args:
            chunks: List of chunk dicts with 'text' field

        Returns:
            List of embedding vectors (1536 dimensions each)
        """
        texts = [chunk['text'] for chunk in chunks]
        return self.embed_batch(texts)

    def _expand_to_1536(self, embedding: np.ndarray) -> List[float]:
        """Expand embedding to 1536 dimensions by concatenating duplicates and padding."""
        if len(embedding) >= 1536:
            return embedding[:1536].tolist()

        # Duplicate and pad to 1536 dimensions
        embedding = np.array(embedding, dtype=np.float32)
        repeats = (1536 // len(embedding)) + 1
        expanded = np.tile(embedding, repeats)[:1536]

        # Normalize
        expanded = expanded / np.linalg.norm(expanded)
        return expanded.tolist()

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate deterministic mock embedding based on text hash."""
        text_hash = hashlib.md5(text.encode()).digest()
        np.random.seed(int.from_bytes(text_hash[:4], 'big'))
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()
