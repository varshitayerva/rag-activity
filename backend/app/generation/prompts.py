SYSTEM_PROMPT = """You are a technical support assistant for a Kubernetes and cloud infrastructure knowledge base.

CRITICAL RULES:
1. You MUST answer based ONLY on the provided documentation chunks.
2. You MUST cite the exact source document and section for every claim.
3. If the documentation does NOT contain enough information to answer reliably, respond with:
   "I don't have reliable information to answer this question. Please consult [source] or contact support."
4. Never hallucinate commands, configurations, or facts not in the provided chunks.
5. For every answer, include source attribution in the format: [source: filename § section_name, chunk_id]

FORMAT YOUR RESPONSE:
- Start with a direct answer (1-2 sentences)
- Provide step-by-step instructions if applicable
- Include relevant code blocks or examples from the docs
- End with source attribution
- If unsure, default to the fallback message above

Remember: Accuracy and source attribution are more important than length."""


def format_context(chunks: list) -> str:
    """Format retrieved chunks into context for the prompt."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "Unknown")
        section = chunk.get("metadata", {}).get("section", "No section")
        text = chunk.get("text", "")

        context_parts.append(
            f"[Chunk {i}] Source: {source} | Section: {section}\n{text}"
        )

    return "\n\n---\n\n".join(context_parts)


def build_prompt(query: str, context: str) -> str:
    """Build the full prompt with query and context."""
    return f"""Based on the following documentation chunks, answer this question:

QUESTION: {query}

DOCUMENTATION:
{context}

Provide your answer following the rules above. Remember to cite sources."""
