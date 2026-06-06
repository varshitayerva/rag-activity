import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Hugging Face
    hf_token: str = os.getenv("HF_TOKEN", "")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:varsh@localhost:5432/rag_db")

    # Qdrant
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "qdrant_key_12345")

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "text-embedding-3-small"

    # Anthropic
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Groq
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    # Generation
    generation_provider: str = os.getenv("GENERATION_PROVIDER", "huggingface")

    # Embedding
    embedding_dimension: int = 1536

    # Qdrant Collection
    qdrant_collection_name: str = "documents"

    # Chunking
    fixed_chunk_size: int = 500
    fixed_chunk_overlap: int = 100

    # Cache TTLs (seconds)
    embedding_cache_ttl: int = int(os.getenv("EMBEDDING_CACHE_TTL", "86400"))  # 24 hours
    retrieval_cache_ttl: int = int(os.getenv("RETRIEVAL_CACHE_TTL", "14400"))  # 4 hours
    response_cache_ttl: int = int(os.getenv("RESPONSE_CACHE_TTL", "7200"))      # 2 hours

    # Context compression
    context_compression_max_chunks: int = int(os.getenv("CONTEXT_COMPRESSION_MAX_CHUNKS", "5"))
    context_compression_max_tokens: int = int(os.getenv("CONTEXT_COMPRESSION_MAX_TOKENS", "2500"))

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
