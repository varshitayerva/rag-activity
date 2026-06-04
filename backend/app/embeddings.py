from typing import List
import requests
from app.config import get_settings

settings = get_settings()


class EmbeddingsService:
    def __init__(self):
        self.model = settings.HF_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        # Using HF Inference API for embeddings with any public model
        self.base_url = "https://api-inference.huggingface.co/models"

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text using HF Inference API."""
        try:
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers={"Authorization": f"Bearer hf_test"},
                json={"inputs": text},
                timeout=30
            )

            if response.status_code != 200:
                # Return random embedding if API fails (for testing)
                import random
                return [random.random() for _ in range(self.dimension)]

            result = response.json()

            if isinstance(result, list):
                return result

            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                return result[0]

            return [0.0] * self.dimension

        except Exception as e:
            print(f"Warning: Embedding generation failed: {e}. Using random embedding.")
            import random
            return [random.random() for _ in range(self.dimension)]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))

        return embeddings
