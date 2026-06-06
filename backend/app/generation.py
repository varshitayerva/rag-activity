from typing import List, Dict, Any, AsyncGenerator
import requests
import json
from app.config import get_settings

settings = get_settings()


class GenerationService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment variables")

        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1"

    SYSTEM_PROMPT = """You are a technical support assistant for a knowledge base.

CRITICAL RULES:
1. You MUST answer ONLY based on the provided documentation chunks.
2. Do NOT make up information, steps, or solutions not in the chunks.
3. If the documentation doesn't contain enough information, respond with:
   "I don't have reliable information to answer this question. Please consult the original documentation or contact support."
4. ALWAYS cite the exact source document and section for every answer.
5. Use the format: [Source: filename section_name]

Format your responses clearly with proper structure."""

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = ["## DOCUMENTATION CONTEXT\n"]

        for idx, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            section = chunk.get("section", "Unknown Section")
            context_parts.append(f"### Chunk {idx} ({section})\n{text}\n")

        return "\n".join(context_parts)

    def _build_prompt(self, query: str, context: str) -> str:
        """Build the full prompt for generation."""
        return f"""{context}

## USER QUESTION
{query}

Please answer based ONLY on the above documentation. If the documentation doesn't cover this, say so."""

    async def generate_streaming(
        self, query: str, chunks: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """Generate response with streaming."""
        if not settings.GROQ_API_KEY:
            yield "Error: GROQ_API_KEY not set"
            return

        context = self._build_context(chunks)
        prompt = self._build_prompt(query, context)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 512,
                "temperature": 0.7,
                "stream": True
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=30
            )

            if response.status_code != 200:
                yield f"Error: {response.status_code} - {response.text}"
                return

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            pass

        except Exception as e:
            yield f"Error generating response: {str(e)}"

    def generate(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Generate non-streaming response."""
        if not settings.GROQ_API_KEY:
            return "Error: GROQ_API_KEY not set"

        context = self._build_context(chunks)
        prompt = self._build_prompt(query, context)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 512,
                "temperature": 0.7,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                return f"Error: {response.status_code} - {response.text}"

            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']

            return "No response from API"

        except Exception as e:
            return f"Error generating response: {str(e)}"

    @staticmethod
    def extract_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract source information from chunks."""
        sources = []
        seen = set()

        for chunk in chunks:
            source_key = f"{chunk.get('id')}"
            if source_key not in seen:
                sources.append(
                    {
                        "chunk_id": chunk.get("id"),
                        "text": chunk.get("text", "")[:200] + "...",
                        "section": chunk.get("section", "Unknown"),
                        "page": chunk.get("page_number"),
                    }
                )
                seen.add(source_key)

        return sources
