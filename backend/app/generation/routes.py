from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import AsyncGenerator

from .models import GenerateRequest
from .service import GenerationService

router = APIRouter(prefix="/api", tags=["generation"])

# Lazy load service to avoid early initialization
_generation_service = None

def get_generation_service():
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service


async def event_stream(query: str, chunks: list) -> AsyncGenerator[str, None]:
    """Wrap streaming generator with SSE format."""
    service = get_generation_service()
    async for event in service.generate_streaming(query, chunks):
        yield event


@router.post("/generate")
async def generate(request: GenerateRequest):
    """Generate response with streaming SSE.

    Request body:
    {
        "query": "How do I restart a pod?",
        "chunks": [{...}],
        "stream": true
    }

    Response: Server-Sent Events (text/event-stream)
    data: {"type":"metadata","sources":[...]}
    data: {"type":"token","content":"..."}
    data: {"type":"done","input_tokens":X,"output_tokens":Y}
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")

    if not request.chunks:
        raise HTTPException(status_code=400, detail="At least one chunk is required")

    if request.stream:
        return StreamingResponse(
            event_stream(request.query, request.chunks),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    else:
        result = await generation_service.generate(request.query, request.chunks)
        return result
