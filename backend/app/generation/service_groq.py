"""
Alternative Generation Service using Groq API (Free Tier)
Fast inference, free tier available, no payment required
"""

import json
import os
from typing import AsyncGenerator, List, Optional

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

from .models import Chunk, SourceAttribution
from .prompts import SYSTEM_PROMPT, format_context, build_prompt


class GroqGenerationService:
    """Handles Groq integration with streaming responses (FREE TIER AVAILABLE)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key (uses GROQ_API_KEY env var if not provided)

        Setup:
            1. Go to https://console.groq.com/
            2. Sign up (free)
            3. Create API key
            4. Set: set GROQ_API_KEY=your-key
        """
        if AsyncGroq is None:
            raise ImportError("groq not installed. Run: pip install groq")

        api_key_to_use = api_key or os.getenv("GROQ_API_KEY")
        if api_key_to_use:
            self.client = AsyncGroq(api_key=api_key_to_use)
        else:
            self.client = AsyncGroq()

        # Groq available models: mixtral-8x7b-32768, llama2-70b-4096, gemma-7b-it
        self.model = "mixtral-8x7b-32768"  # Fast and free tier

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
        """Generate streaming response using Groq (free tier)."""
        sources = self.extract_sources(chunks)
        context = format_context([chunk.model_dump() for chunk in chunks])
        prompt = build_prompt(query, context)

        # Emit sources metadata
        yield json.dumps({"type": "metadata", "sources": [s.model_dump() for s in sources]})
        yield "\n"

        try:
            # Stream from Groq
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                input_tokens = 0
                output_tokens = 0

                async for text in stream.text_stream:
                    if text:
                        yield json.dumps({"type": "token", "content": text})
                        yield "\n"

                # Get final message for token counts
                final_message = await stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens

            # Emit completion
            yield json.dumps(
                {
                    "type": "done",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            )
            yield "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)})
            yield "\n"

    async def generate(self, query: str, chunks: List[Chunk]) -> dict:
        """Generate response without streaming."""
        sources = self.extract_sources(chunks)
        context = format_context([chunk.model_dump() for chunk in chunks])
        prompt = build_prompt(query, context)

        try:
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

        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "sources": [s.model_dump() for s in sources],
                "input_tokens": 0,
                "output_tokens": 0,
            }
