"""LLM generation service using Groq API."""

import os
from typing import Optional
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_answer(query: str, documents: list) -> str:
    """Generate an answer using Groq based on retrieved documents."""

    if not documents:
        return "No relevant documents found. Please refine your search."

    # Build context from documents
    context = "\n\n".join([
        f"Document: {doc.get('doc', 'Unknown')}\n"
        f"Content: {doc.get('text', '')[:500]}..."
        for doc in documents[:5]
    ])

    system_prompt = """You are a helpful technical support assistant.
Answer questions based ONLY on the provided documents.
If the answer is not in the documents, say "I don't have that information in my knowledge base."
Be concise and clear."""

    user_message = f"""Based on these documents:

{context}

Answer this question: {query}

Provide a clear, concise answer."""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return message.choices[0].message.content
    except Exception as e:
        print(f"Generation error: {e}")
        return f"Error generating answer: {str(e)}"


def stream_answer(query: str, documents: list):
    """Stream answer from Groq for real-time response."""

    if not documents:
        yield "No relevant documents found. Please refine your search."
        return

    context = "\n\n".join([
        f"Document: {doc.get('doc', 'Unknown')}\n"
        f"Content: {doc.get('text', '')[:500]}..."
        for doc in documents[:5]
    ])

    system_prompt = """You are a helpful technical support assistant.
Answer questions based ONLY on the provided documents.
If the answer is not in the documents, say "I don't have that information in my knowledge base."
Be concise and clear."""

    user_message = f"""Based on these documents:

{context}

Answer this question: {query}

Provide a clear, concise answer."""

    try:
        with client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=True
        ) as stream:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {str(e)}"
