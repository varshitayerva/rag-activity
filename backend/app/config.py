from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379"

    # Database
    database_url: str = "postgresql://rag_user:rag_password@localhost:5432/rag_db"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = "qdrant_key_12345"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "text-embedding-3-small"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Cache TTLs (seconds)
    embedding_cache_ttl: int = 86400  # 24 hours
    retrieval_cache_ttl: int = 14400  # 4 hours
    response_cache_ttl: int = 7200    # 2 hours

    # Context compression
    context_compression_max_chunks: int = 5
    context_compression_max_tokens: int = 2500

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
