"""LLM generation service using Groq API."""

import os
from typing import Optional
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_answer(query: str, documents: list) -> str:
    """Generate an enhanced answer using Groq based on retrieved documents."""

    if not documents:
        return "No relevant documents found. Please refine your search."

    # Build comprehensive context from documents
    context = "\n\n".join([
        f"[{doc.get('doc', 'Unknown')} - Relevance: {doc.get('score', 0):.0%}]\n"
        f"{doc.get('text', '')}"
        for doc in documents[:5]
    ])

    system_prompt = """You are an expert technical documentation assistant. Your role is to:
1. Synthesize information from multiple sources
2. Explain complex topics in clear, structured ways
3. Provide practical examples and step-by-step guidance
4. Highlight key points and important details
5. Make connections between related concepts

When answering:
- Use clear formatting with headers, bullet points, and numbered lists
- Provide concrete examples when helpful
- Explain the "why" not just the "what"
- Structure complex answers logically
- Be comprehensive but concise
- If information spans multiple documents, synthesize it coherently

Base your answer ONLY on the provided documents. If the exact answer isn't available, say so clearly."""

    user_message = f"""Question: {query}

Available Documentation:
{context}

Please provide a comprehensive, well-structured answer that:
1. Directly addresses the question
2. Explains key concepts clearly
3. Provides practical examples if relevant
4. Uses formatting (headers, bullets, numbers) for readability
5. Highlights important information
6. Concludes with any important warnings or best practices

Format your response with:
- A clear opening sentence answering the question
- Detailed explanation with examples
- Step-by-step instructions if applicable
- Key takeaways or best practices
- Related tips if relevant"""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7  # Slightly higher temp for better synthesis
        )
        return message.choices[0].message.content
    except Exception as e:
        print(f"Generation error: {e}")
        return f"Error generating answer: {str(e)}"


def stream_answer(query: str, documents: list):
    """Stream enhanced answer from Groq for real-time response."""

    if not documents:
        yield "No relevant documents found. Please refine your search."
        return

    context = "\n\n".join([
        f"[{doc.get('doc', 'Unknown')} - Relevance: {doc.get('score', 0):.0%}]\n"
        f"{doc.get('text', '')}"
        for doc in documents[:5]
    ])

    system_prompt = """You are an expert technical documentation assistant. Your role is to:
1. Synthesize information from multiple sources
2. Explain complex topics in clear, structured ways
3. Provide practical examples and step-by-step guidance
4. Highlight key points and important details
5. Make connections between related concepts

When answering:
- Use clear formatting with headers, bullet points, and numbered lists
- Provide concrete examples when helpful
- Explain the "why" not just the "what"
- Structure complex answers logically
- Be comprehensive but concise
- If information spans multiple documents, synthesize it coherently

Base your answer ONLY on the provided documents. If the exact answer isn't available, say so clearly."""

    user_message = f"""Question: {query}

Available Documentation:
{context}

Please provide a comprehensive, well-structured answer that:
1. Directly addresses the question
2. Explains key concepts clearly
3. Provides practical examples if relevant
4. Uses formatting (headers, bullets, numbers) for readability
5. Highlights important information
6. Concludes with any important warnings or best practices

Format your response with:
- A clear opening sentence answering the question
- Detailed explanation with examples
- Step-by-step instructions if applicable
- Key takeaways or best practices
- Related tips if relevant"""

    try:
        with client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            stream=True
        ) as stream:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {str(e)}"
