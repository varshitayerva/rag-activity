import json
import os
from typing import AsyncGenerator, List, Optional
from anthropic import AsyncAnthropic

from .models import Chunk, SourceAttribution
from .prompts import SYSTEM_PROMPT, format_context, build_prompt


class GenerationService:
    """Handles Claude Sonnet 4.0 integration with streaming and source attribution."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client. Uses ANTHROPIC_API_KEY env var if api_key is None."""
        # Use provided api_key, fall back to env var, or None (will error if not set)
        api_key_to_use = api_key or os.getenv("ANTHROPIC_API_KEY")

        # Initialize with minimal parameters to avoid httpx compatibility issues
        if api_key_to_use:
            self.client = AsyncAnthropic(api_key=api_key_to_use)
        else:
            # AsyncAnthropic will auto-detect ANTHROPIC_API_KEY from env
            self.client = AsyncAnthropic()

        self.model = "claude-3-5-sonnet-20241022"

    def extract_sources(self, chunks: List[Chunk]) -> List[SourceAttribution]:
        """Extract source metadata from chunks."""
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
        """Generate response with streaming SSE format.

        Yields JSON strings in SSE format:
        - {"type": "metadata", "sources": [...]}
        - {"type": "token", "content": "..."}
        - {"type": "done", "input_tokens": X, "output_tokens": Y}
        """
        sources = self.extract_sources(chunks)
        context = format_context([chunk.model_dump() for chunk in chunks])
        prompt = build_prompt(query, context)

        # Emit sources metadata
        yield json.dumps({"type": "metadata", "sources": [s.model_dump() for s in sources]})
        yield "\n"

        full_text = ""
        input_tokens = 0
        output_tokens = 0

        # Stream from Claude
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                yield json.dumps({"type": "token", "content": text})
                yield "\n"

            # Get final message for token counts
            final_message = await stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

        # Emit completion with token counts
        yield json.dumps(
            {
                "type": "done",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        yield "\n"

    async def generate(self, query: str, chunks: List[Chunk]) -> dict:
        """Generate response without streaming (for testing)."""
        sources = self.extract_sources(chunks)
        context = format_context([chunk.model_dump() for chunk in chunks])
        prompt = build_prompt(query, context)

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "response": message.content[0].text,
            "sources": [s.model_dump() for s in sources],
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        }
