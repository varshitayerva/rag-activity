"""LLM generation service using Groq API."""

import os
from typing import Optional, Dict, Any
from groq import Groq
from backend.app.hallucination_control import HallucinationValidator

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
hallucination_validator = HallucinationValidator()

def generate_answer(query: str, documents: list) -> Dict[str, Any]:
    """Generate an enhanced answer using Groq with hallucination controls."""

    if not documents:
        return {
            "answer": "No relevant documents found. Please refine your search.",
            "sources": [],
            "hallucination_risk": 0.0,
            "risk_level": "LOW"
        }

    context = "\n\n".join([
        f"[Chunk {idx} - {doc.get('doc', 'Unknown')}]\n"
        f"{doc.get('text', '')}"
        for idx, doc in enumerate(documents[:5])
    ])

    system_prompt = """You are a technical documentation assistant that MUST prioritize accuracy.

CRITICAL RULES:
1. ONLY use information from provided documentation chunks
2. DO NOT invent or assume information
3. Cite sources explicitly: [Source: Chunk N] for every claim
4. If information is incomplete, say so clearly
5. Never use phrases like "I believe", "according to my training", "commonly known"

When uncertain about any detail, mark with [UNCERTAIN] and explain what's missing."""

    user_message = f"""Question: {query}

Documentation Chunks:
{context}

Provide a well-structured answer that:
1. Addresses the question directly
2. Cites each claim with [Source: Chunk N]
3. Uses clear formatting
4. Marks uncertain information as [UNCERTAIN]
5. Says "I don't have this information" if needed"""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5
        )
        answer = message.choices[0].message.content

        validation = hallucination_validator.calculate_hallucination_risk(
            answer, documents, 0.7
        )

        return {
            "answer": answer,
            "sources": documents,
            "hallucination_risk": validation['hallucination_risk'],
            "risk_level": validation['risk_level'],
            "validation": validation
        }
    except Exception as e:
        print(f"Generation error: {e}")
        return {
            "answer": f"Error generating answer: {str(e)}",
            "sources": [],
            "hallucination_risk": 1.0,
            "risk_level": "HIGH",
            "error": str(e)
        }


def stream_answer(query: str, documents: list):
    """Stream enhanced answer with hallucination controls."""

    if not documents:
        yield "No relevant documents found. Please refine your search."
        return

    context = "\n\n".join([
        f"[Chunk {idx} - {doc.get('doc', 'Unknown')}]\n"
        f"{doc.get('text', '')}"
        for idx, doc in enumerate(documents[:5])
    ])

    system_prompt = """You are a technical documentation assistant that MUST prioritize accuracy.

CRITICAL RULES:
1. ONLY use information from provided documentation chunks
2. DO NOT invent or assume information
3. Cite sources explicitly: [Source: Chunk N] for every claim
4. If information is incomplete, say so clearly
5. Never use phrases like "I believe", "according to my training", "commonly known"

When uncertain about any detail, mark with [UNCERTAIN] and explain what's missing."""

    user_message = f"""Question: {query}

Documentation Chunks:
{context}

Provide a well-structured answer that:
1. Addresses the question directly
2. Cites each claim with [Source: Chunk N]
3. Uses clear formatting
4. Marks uncertain information as [UNCERTAIN]
5. Says "I don't have this information" if needed"""

    try:
        with client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            stream=True
        ) as stream:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {str(e)}"
