"""Fast vector indexing with FAISS for scalable search."""

import numpy as np
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FAISSIndex:
    """FAISS-based vector index for fast similarity search."""

    def __init__(self, dimension: int = 384):
        """Initialize FAISS index."""
        self.dimension = dimension
        self.index = None
        self.vectors = []
        self.metadata = []
        self.vector_count = 0
        self._init_index()

    def _init_index(self):
        """Initialize FAISS index."""
        try:
            import faiss
            # Use simple flat index for now
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"FAISS index initialized (dimension: {self.dimension})")
        except ImportError:
            logger.warning("FAISS not installed - vector indexing disabled")
            self.index = None

    def add_vectors(self, vectors: List[np.ndarray], metadata: List[Dict[str, Any]]):
        """Add vectors to index."""
        if not self.index:
            logger.warning("FAISS index not available")
            return

        try:
            vectors_array = np.array(vectors, dtype=np.float32)

            if vectors_array.shape[1] != self.dimension:
                raise ValueError(f"Vector dimension mismatch: {vectors_array.shape[1]} vs {self.dimension}")

            self.index.add(vectors_array)
            self.vectors.extend(vectors)
            self.metadata.extend(metadata)
            self.vector_count += len(vectors)

            logger.info(f"Added {len(vectors)} vectors to index (total: {self.vector_count})")
        except Exception as e:
            logger.error(f"Error adding vectors: {e}")

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if not self.index or self.vector_count == 0:
            return []

        try:
            query_array = np.array([query_vector], dtype=np.float32)
            distances, indices = self.index.search(query_array, min(k, self.vector_count))

            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx >= 0 and idx < len(self.metadata):
                    # Convert L2 distance to similarity score
                    similarity = 1 / (1 + distance)
                    result = dict(self.metadata[idx])
                    result['score'] = float(similarity)
                    results.append(result)

            return results
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []

    def clear(self):
        """Clear index."""
        self._init_index()
        self.vectors.clear()
        self.metadata.clear()
        self.vector_count = 0
        logger.info("Index cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'vector_count': self.vector_count,
            'dimension': self.dimension,
            'faiss_available': self.index is not None,
            'index_type': 'FAISS_FlatL2' if self.index else 'None',
        }


class VectorIndexManager:
    """Manager for vector indexing."""

    def __init__(self):
        self.faiss_index = FAISSIndex()
        self.use_faiss = self.faiss_index.index is not None

    def index_vectors(self, vectors: List[np.ndarray], metadata: List[Dict]):
        """Index vectors."""
        if self.use_faiss:
            self.faiss_index.add_vectors(vectors, metadata)
            logger.info(f"Indexed {len(vectors)} vectors with FAISS")
        else:
            logger.info("FAISS not available - skipping indexing")

    def search_vectors(self, query_vector: np.ndarray, k: int = 10) -> List[Dict[str, Any]]:
        """Search vectors using FAISS if available."""
        if self.use_faiss:
            return self.faiss_index.search(query_vector, k)
        return []

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return self.faiss_index.get_stats()


# Global instance
vector_index_manager = VectorIndexManager()
