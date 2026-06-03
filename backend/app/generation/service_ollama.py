"""
Alternative Generation Service using Ollama (Local, Free)
No API key needed - runs models locally on your computer
"""

import json
from typing import AsyncGenerator, List, Optional
import httpx

from .models import Chunk, SourceAttribution
from .prompts import SYSTEM_PROMPT, format_context, build_prompt


class OllamaGenerationService:
    """Handles Ollama integration with streaming responses (LOCAL, FREE)."""

    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.

        Args:
            model: Model name (mistral, llama2, neural-chat, etc.)
            base_url: Ollama server URL (default: local)

        Setup:
            1. Download Ollama from https://ollama.ai/
            2. Run: ollama pull mistral
            3. Ollama runs on http://localhost:11434
        """
        self.model = model
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    def extract_sources(self, chunks: List[Chunk]) -> List[SourceAttribution]:
        """Extract unique sources from chunks."""
        sources = []
        seen = set()

        for chunk in chunks:
            source_key = (chunk.source, chunk.metadata.section)
            if source_key not in seen:
                sources.append(
                    SourceAttribution(
                        doc=chunk.source,
                        section=chunk.metadata.section,
                        chunk_id=chunk.chunk_id,
                    )
                )
                seen.add(source_key)

        return sources

    async def generate_streaming(
        self, query: str, chunks: List[Chunk]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Ollama (local)."""
        sources = self.extract_sources(chunks)
        context = format_context([chunk.model_dump() for chunk in chunks])
        prompt = build_prompt(query, context)

        # Emit sources metadata
        yield json.dumps({"type": "metadata", "sources": [s.model_dump() for s in sources]})
        yield "\n"

        # Build request for Ollama
        request_data = {
            "model": self.model,
            "prompt": f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {query}",
            "stream": True,
        }

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=request_data,
            ) as response:
                token_count = 0
                full_text = ""

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")

                        if token:
                            full_text += token
                            token_count += 1
                            yield json.dumps({"type": "token", "content": token})
                            yield "\n"

                # Emit done event
                yield json.dumps(
                    {
                        "type": "done",
                        "input_tokens": len(prompt.split()),
                        "output_tokens": token_count,
                    }
                )
                yield "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)})
            yield "\n"

    async def generate(self, query: str, chunks: List[Chunk]) -> dict:
        """Generate response without streaming (for testing)."""
        sources = self.extract_sources(chunks)
        context = format_context([chunk.model_dump() for chunk in chunks])

        request_data = {
            "model": self.model,
            "prompt": f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {query}",
            "stream": False,
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=request_data,
            )
            result = response.json()

            return {
                "response": result.get("response", ""),
                "sources": [s.model_dump() for s in sources],
                "input_tokens": len(context.split()),
                "output_tokens": len(result.get("response", "").split()),
            }

        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "sources": [s.model_dump() for s in sources],
                "input_tokens": 0,
                "output_tokens": 0,
            }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
