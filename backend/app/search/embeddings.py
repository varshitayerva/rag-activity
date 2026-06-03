import os
from openai import OpenAI
from typing import List, Union

class EmbeddingsClient:
    def __init__(self, model: str = "text-embedding-3-small", api_key: str = None):
        """Initialize OpenAI embeddings client.

        Args:
            model: OpenAI embedding model (default: text-embedding-3-small, 1536 dims)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
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
        response = self.client.embeddings.create(
            input=query,
            model=self.model
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )

        # Sort by index to ensure correct order
        embeddings = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in embeddings]

    def embed_chunks(self, chunks: List[dict]) -> List[List[float]]:
        """Embed chunk texts from chunk dicts.

        Args:
            chunks: List of chunk dicts with 'text' field

        Returns:
            List of embedding vectors
        """
        texts = [chunk['text'] for chunk in chunks]
        return self.embed_batch(texts)
