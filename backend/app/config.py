import os
from functools import lru_cache

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rag.db")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    EMBEDDING_DIMENSION: int = 1536
    QDRANT_COLLECTION_NAME: str = "documents"

    FIXED_CHUNK_SIZE: int = 500
    FIXED_CHUNK_OVERLAP: int = 100

@lru_cache()
def get_settings():
    return Settings()
