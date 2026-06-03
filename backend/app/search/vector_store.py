"""In-memory vector store using sentence-transformers with offline fallback."""

import os
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class SimpleEmbedding:
    """Simple offline embedding using TF-IDF-like approach."""

    def __init__(self):
        self.vocab = {}
        self.idf = {}

    def encode(self, texts: List[str], convert_to_tensor: bool = False) -> List[List[float]]:
        """Encode texts to 384-dimensional vectors using simple method."""
        embeddings = []

        for text in texts:
            # Simple hash-based embedding
            words = text.lower().split()
            embedding = [0.0] * 384

            for i, word in enumerate(words):
                # Use word hash to determine which dimensions to activate
                word_hash = hash(word) % 384
                embedding[word_hash] += 1.0 / (len(words) + 1)

            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [x / norm for x in embedding]

            embeddings.append(np.array(embedding, dtype=np.float32))

        return embeddings


class VectorStore:
    """In-memory vector store using sentence-transformers with fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with sentence-transformers model or simple fallback."""
        self.model = None
        self.embedding_dim = 384
        self.vectors = []
        self.metadata = []
        self.use_simple = False

        if HAS_TRANSFORMERS:
            try:
                print(f"Loading embedding model: {model_name}...")
                self.model = SentenceTransformer(model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                print(f"Model loaded. Embedding dimension: {self.embedding_dim}")
            except Exception as e:
                print(f"Could not load transformer model: {e}")
                print("Using simple embedding fallback...")
                self.model = SimpleEmbedding()
                self.use_simple = True
        else:
            print("sentence-transformers not available, using simple embedding")
            self.model = SimpleEmbedding()
            self.use_simple = True

    def add(self, texts: List[str], metadata_list: List[Dict[str, Any]]):
        """Add texts with embeddings."""
        if not texts:
            return

        print(f"Embedding {len(texts)} chunks...")

        if self.use_simple or isinstance(self.model, SimpleEmbedding):
            embeddings = self.model.encode(texts)
        else:
            embeddings = self.model.encode(texts, convert_to_tensor=False)

        for emb, meta in zip(embeddings, metadata_list):
            self.vectors.append(emb)
            self.metadata.append(meta)

        print(f"Added {len(texts)} chunks to vector store")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search similar texts."""
        if not self.vectors:
            return []

        if self.use_simple or isinstance(self.model, SimpleEmbedding):
            query_embedding = self.model.encode([query])[0]
        else:
            query_embedding = self.model.encode(query, convert_to_tensor=False)

        # Calculate cosine similarity
        similarities = []
        for vec in self.vectors:
            vec_norm = np.linalg.norm(vec)
            query_norm = np.linalg.norm(query_embedding)

            if vec_norm == 0 or query_norm == 0:
                sim = 0
            else:
                sim = np.dot(query_embedding, vec) / (vec_norm * query_norm)

            similarities.append(sim)

        # Get top results
        similarities = np.array(similarities)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if idx >= 0 and similarities[idx] > 0:
                results.append({
                    "score": float(similarities[idx]),
                    **self.metadata[idx]
                })

        return results

    def search_by_embedding(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search by embedding vector."""
        if not self.vectors:
            return []

        similarities = []
        for vec in self.vectors:
            vec_norm = np.linalg.norm(vec)
            emb_norm = np.linalg.norm(embedding)

            if vec_norm == 0 or emb_norm == 0:
                sim = 0
            else:
                sim = np.dot(embedding, vec) / (vec_norm * emb_norm)

            similarities.append(sim)

        similarities = np.array(similarities)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if idx >= 0:
                results.append({
                    "score": float(similarities[idx]),
                    **self.metadata[idx]
                })

        return results

    def size(self) -> int:
        """Return number of vectors in store."""
        return len(self.vectors)

    def clear(self):
        """Clear all vectors."""
        self.vectors = []
        self.metadata = []


# Global instance - lazy loaded on first use
vector_store = None

def get_vector_store():
    """Get or initialize vector store."""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store
