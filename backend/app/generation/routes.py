import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
import json
from typing import AsyncGenerator, Optional

from .models import GenerateRequest
from .service import GenerationService
from app.cache import CachedGenerationWrapper

router = APIRouter(prefix="/api", tags=["generation"])

# Lazy load service - supports multiple providers
_generation_services = {}
_cached_services = {}


def get_generation_service(provider: Optional[str] = None) -> GenerationService:
    """Get or create generation service for the specified provider.

    Args:
        provider: 'groq' (default), 'anthropic', or 'ollama'
                 Can also use GENERATION_PROVIDER env var
    """
    provider = provider or os.getenv("GENERATION_PROVIDER", "groq")

    if provider not in _generation_services:
        try:
            _generation_services[provider] = GenerationService(provider=provider)
        except (ImportError, ValueError) as e:
            raise HTTPException(status_code=500, detail=str(e))

    return _generation_services[provider]


def get_cached_generation_service(provider: Optional[str] = None, cache_manager=None):
    """Get generation service wrapped with M4 caching."""
    service = get_generation_service(provider)

    # Create cache wrapper only if cache_manager is available
    if cache_manager:
        cache_key = f"{provider}_cached"
        if cache_key not in _cached_services:
            _cached_services[cache_key] = CachedGenerationWrapper(service, cache_manager)
        return _cached_services[cache_key]

    # Fallback to unwrapped service if no cache
    return service


async def event_stream(query: str, chunks: list, provider: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Wrap streaming generator with SSE format."""
    service = get_generation_service(provider)
    async for event in service.generate_streaming(query, chunks):
        yield event


@router.post("/generate")
async def generate(
    request: GenerateRequest,
    provider: Optional[str] = Query(None, description="LLM provider: groq, anthropic, or ollama"),
):
    """Generate response with streaming SSE and M4 caching.

    Request body:
    {
        "query": "How do I restart a pod?",
        "chunks": [{...}],
        "stream": true
    }

    Query parameters:
    - provider: 'groq' (default, free), 'anthropic', or 'ollama'

    Response: Server-Sent Events (text/event-stream)
    data: {"type":"metadata","sources":[...]}
    data: {"type":"token","content":"..."}
    data: {"type":"done","input_tokens":X,"output_tokens":Y}

    M4 Integration:
    - Layer 3 caching for non-streaming responses (2h TTL)
    - Context compression (75% token reduction)
    - Graceful degradation if Redis unavailable
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")

    if not request.chunks:
        raise HTTPException(status_code=400, detail="At least one chunk is required")

    try:
        # Import cache_manager from main.py scope (if available)
        from main import cache_manager

        # Get cached service wrapper (with compression + caching) if cache available
        if cache_manager:
            service = get_cached_generation_service(provider, cache_manager)
        else:
            service = get_generation_service(provider)

        if request.stream:
            # Streaming responses: compress but don't cache (SSE too complex to cache)
            if hasattr(service, 'generate_streaming'):
                return StreamingResponse(
                    service.generate_streaming(request.query, request.chunks),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
                )
            else:
                # Fallback for unwrapped service
                return StreamingResponse(
                    event_stream(request.query, request.chunks, provider),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
                )
        else:
            # Non-streaming: Layer 3 cache + compression
            if hasattr(service, 'generate'):
                result = await service.generate(request.query, request.chunks)
            else:
                # Fallback for unwrapped service
                unwrapped = get_generation_service(provider)
                result = await unwrapped.generate(request.query, request.chunks)

            return JSONResponse(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def config():
    """Get current generation config and available providers."""
    current_provider = os.getenv("GENERATION_PROVIDER", "groq")

    return {
        "current_provider": current_provider,
        "available_providers": {
            "huggingface": {
                "description": "Hugging Face Inference API (free, OpenAI-compatible)",
                "requires": "HF_TOKEN",
                "setup": "https://huggingface.co/settings/tokens",
                "cost": "Free forever",
                "default": True,
            },
            "groq": {
                "description": "Groq API (free cloud, no download needed)",
                "requires": "GROQ_API_KEY",
                "setup": "https://console.groq.com/",
                "cost": "Free",
            },
            "anthropic": {
                "description": "Anthropic Claude (cloud API)",
                "requires": "ANTHROPIC_API_KEY",
                "setup": "https://console.anthropic.com/",
                "cost": "$5 free credit",
            },
            "ollama": {
                "description": "Ollama (local, download models)",
                "requires": "None (runs locally)",
                "setup": "https://ollama.ai/",
                "cost": "Free (uses your computer)",
            },
        },
        "example_usage": {
            "huggingface": "POST /api/generate?provider=huggingface (default)",
            "groq": "POST /api/generate?provider=groq",
            "anthropic": "POST /api/generate?provider=anthropic",
            "ollama": "POST /api/generate?provider=ollama",
        },
    }
