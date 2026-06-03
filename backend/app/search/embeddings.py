import os
import hashlib
import numpy as np
from openai import OpenAI
from typing import List, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class EmbeddingsClient:
    def __init__(self, model: str = "text-embedding-3-small", api_key: str = None):
        """Initialize OpenAI embeddings client.

        Args:
            model: OpenAI embedding model (default: text-embedding-3-small, 1536 dims)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var or .env file)
        """
        self.model = model
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.embedding_dim = 1536 if model == "text-embedding-3-small" else 3072

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string.

        Args:
            query: Query text

        Returns:
            Embedding vector (list of floats)
        """
        try:
            response = self.client.embeddings.create(
                input=query,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding failed: {e}. Using mock embedding.")
            return self._mock_embedding(query)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in embeddings]
        except Exception as e:
            print(f"OpenAI batch embedding failed: {e}. Using mock embeddings.")
            return [self._mock_embedding(text) for text in texts]

    def embed_chunks(self, chunks: List[dict]) -> List[List[float]]:
        """Embed chunk texts from chunk dicts.

        Args:
            chunks: List of chunk dicts with 'text' field

        Returns:
            List of embedding vectors
        """
        texts = [chunk['text'] for chunk in chunks]
        return self.embed_batch(texts)

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate deterministic mock embedding based on text hash."""
        text_hash = hashlib.md5(text.encode()).digest()
        np.random.seed(int.from_bytes(text_hash[:4], 'big'))
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()
