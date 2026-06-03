import json
import os
from typing import AsyncGenerator, List, Optional

from .models import Chunk, SourceAttribution
from .prompts import SYSTEM_PROMPT, format_context, build_prompt


class GenerationService:
    """
    Generation service supporting multiple LLM providers.

    Supports:
    - Hugging Face Inference API (free, OpenAI-compatible)
    - Groq (free cloud API)
    - Anthropic Claude (cloud API with free tier)
    - Ollama (local, if you download models)

    Default: Hugging Face Inference API (completely free)
    """

    def __init__(self, provider: str = "huggingface", api_key: Optional[str] = None):
        """
        Initialize generation service.

        Args:
            provider: 'huggingface' (default), 'groq', 'anthropic', or 'ollama'
            api_key: API key for the provider (uses env var if not provided)

        Environment variables:
            HF_TOKEN - for Hugging Face Inference API
            GROQ_API_KEY - for Groq
            ANTHROPIC_API_KEY - for Anthropic Claude
            OLLAMA_BASE_URL - for Ollama (default: http://localhost:11434)
        """
        self.provider = provider.lower()

        if self.provider == "huggingface":
            self._init_huggingface(api_key)
        elif self.provider == "groq":
            self._init_groq(api_key)
        elif self.provider == "anthropic":
            self._init_anthropic(api_key)
        elif self.provider == "ollama":
            self._init_ollama()
        else:
            raise ValueError(
                f"Unknown provider: {provider}. Use 'huggingface', 'groq', 'anthropic', or 'ollama'"
            )

    def _init_huggingface(self, api_key: Optional[str] = None):
        """Initialize Hugging Face Inference API client (free, OpenAI-compatible)."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")

        api_key_to_use = api_key or os.getenv("HF_TOKEN")
        if not api_key_to_use:
            raise ValueError(
                "HF_TOKEN not set. Get free token at https://huggingface.co/settings/tokens"
            )

        self.client = AsyncOpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=api_key_to_use,
        )
        self.model = "openai/gpt-oss-120b:groq"  # Free, fast model
        self.provider_name = "Hugging Face Inference API"

    def _init_groq(self, api_key: Optional[str] = None):
        """Initialize Groq client (free cloud API)."""
        try:
            from groq import AsyncGroq
        except ImportError:
            raise ImportError("groq not installed. Run: pip install groq")

        api_key_to_use = api_key or os.getenv("GROQ_API_KEY")
        if not api_key_to_use:
            raise ValueError(
                "GROQ_API_KEY not set. Get free key at https://console.groq.com/"
            )

        self.client = AsyncGroq(api_key=api_key_to_use)
        self.model = "mixtral-8x7b-32768"  # Fast, free tier model
        self.provider_name = "Groq"

    def _init_anthropic(self, api_key: Optional[str] = None):
        """Initialize Anthropic Claude client."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic not installed. Run: pip install anthropic")

        api_key_to_use = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key_to_use:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Get free key at https://console.anthropic.com/"
            )

        self.client = AsyncAnthropic(api_key=api_key_to_use)
        self.model = "claude-3-5-sonnet-20241022"
        self.provider_name = "Anthropic Claude"

    def _init_ollama(self):
        """Initialize Ollama client (local)."""
        import httpx

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = base_url
        self.model = "mistral"  # Default model, can override
        self.provider_name = "Ollama"

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

        if self.provider == "huggingface":
            async for event in self._stream_huggingface(prompt):
                yield event
        elif self.provider == "groq":
            async for event in self._stream_groq(prompt):
                yield event
        elif self.provider == "anthropic":
            async for event in self._stream_anthropic(prompt):
                yield event
        elif self.provider == "ollama":
            async for event in self._stream_ollama(prompt):
                yield event

    async def _stream_huggingface(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Hugging Face Inference API (OpenAI-compatible)."""
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

            final_message = await stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

        yield json.dumps(
            {
                "type": "done",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        yield "\n"

    async def _stream_groq(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Groq API."""
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

            final_message = await stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

        yield json.dumps(
            {
                "type": "done",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        yield "\n"

    async def _stream_anthropic(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Anthropic Claude."""
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

            final_message = await stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

        yield json.dumps(
            {
                "type": "done",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        yield "\n"

    async def _stream_ollama(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Ollama (local)."""
        request_data = {
            "model": self.model,
            "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
            "stream": True,
        }

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=request_data,
            ) as response:
                token_count = 0

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")

                        if token:
                            token_count += 1
                            yield json.dumps({"type": "token", "content": token})
                            yield "\n"

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
        prompt = build_prompt(query, context)

        if self.provider == "huggingface":
            return await self._generate_huggingface(prompt, sources)
        elif self.provider == "groq":
            return await self._generate_groq(prompt, sources)
        elif self.provider == "anthropic":
            return await self._generate_anthropic(prompt, sources)
        elif self.provider == "ollama":
            return await self._generate_ollama(prompt, sources)

    async def _generate_huggingface(self, prompt: str, sources: List[SourceAttribution]) -> dict:
        """Generate from Hugging Face Inference API."""
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "response": message.choices[0].message.content,
            "sources": [s.model_dump() for s in sources],
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        }

    async def _generate_groq(self, prompt: str, sources: List[SourceAttribution]) -> dict:
        """Generate from Groq."""
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

    async def _generate_anthropic(self, prompt: str, sources: List[SourceAttribution]) -> dict:
        """Generate from Anthropic."""
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

    async def _generate_ollama(self, prompt: str, sources: List[SourceAttribution]) -> dict:
        """Generate from Ollama."""
        request_data = {
            "model": self.model,
            "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
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
                "input_tokens": len(prompt.split()),
                "output_tokens": len(result.get("response", "").split()),
            }

        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "sources": [s.model_dump() for s in sources],
                "input_tokens": 0,
                "output_tokens": 0,
            }
