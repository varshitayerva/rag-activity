from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import time
from backend.app.search.vector_store import get_vector_store
from backend.app.database.postgres import db_client
from backend.app.cache.metrics import MetricsCollector
from backend.app.generation.service import generate_answer, stream_answer

router = APIRouter(prefix="/api", tags=["search"])

def search_chunks(query: str, top_k: int = 10, filters: Dict[str, Any] = None) -> list:
    """Search chunks using vector similarity with optional filtering."""
    try:
        # Get vector store
        vs = get_vector_store()

        # If vector store is empty, load from database
        if vs.size() == 0:
            print("Vector store empty, loading from database...")
            load_vector_store_from_db(vs)

        # Search
        results = vs.search(query, top_k=top_k)

        # Apply filters to results
        if filters:
            results = apply_filters(results, filters)

        return results
    except Exception as e:
        print(f"Vector search error: {e}")
        return []


def apply_filters(results: list, filters: Dict[str, Any] = None) -> list:
    """Filter search results by relevance, department, category, and date."""
    # Filter by relevance threshold - show only highly relevant results
    if not results:
        return []

    # Sort by score descending
    sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)

    # Keep results that are at least 60% of the top score to reduce noise
    if sorted_results:
        top_score = sorted_results[0].get('score', 0)
        threshold = max(top_score * 0.6, 0.1)  # 60% of top score, minimum 0.1
        filtered = [r for r in sorted_results if r.get('score', 0) >= threshold]
    else:
        filtered = []

    if not filters:
        return filtered

    department = filters.get('department')
    category = filters.get('category')
    date_from = filters.get('dateFrom')
    date_to = filters.get('dateTo')

    # Filter by department
    if department:
        filtered = [r for r in filtered if r.get('department') == department]

    # Filter by category
    if category:
        filtered = [r for r in filtered if r.get('category') == category]

    # Filter by date range
    if date_from:
        filtered = [r for r in filtered if str(r.get('created_at', '')).startswith(date_from)]

    if date_to:
        filtered = [r for r in filtered if str(r.get('created_at', '')).startswith(date_to) or
                    str(r.get('created_at', '')[:10]) < date_to]

    return filtered


def load_vector_store_from_db(vs):
    """Load all chunks from database into vector store."""
    try:
        chunks = db_client.get_chunks_with_filters()
        if not chunks:
            print("No chunks found in database")
            return

        print(f"Loading {len(chunks)} chunks into vector store...")

        # Prepare chunks for vector store
        texts = [chunk['text'] for chunk in chunks]
        metadata_list = [
            {
                'chunk_id': chunk['id'],
                'text': chunk['text'],
                'doc_id': chunk['document_id'],
                'doc': chunk.get('filename'),
                'section': chunk.get('section'),
                'page_number': chunk.get('page_number'),
                'department': chunk.get('department'),
                'category': chunk.get('category'),
                'created_at': str(chunk.get('created_at', ''))
            }
            for chunk in chunks
        ]

        # Add to vector store
        vs.add(texts, metadata_list)
        print(f"Vector store loaded with {len(chunks)} chunks")

    except Exception as e:
        print(f"Error loading vector store from database: {e}")


@router.post("/search")
async def search(
    query: str,
    top_k: int = 10,
    department: str = None,
    category: str = None,
    dateFrom: str = None,
    dateTo: str = None,
):
    """Search across documents using vector embeddings with optional filters.

    Real-time semantic search using sentence-transformers.

    Request:
    {
        "query": "How do I restart a pod?",
        "top_k": 10,
        "department": "Platform",
        "category": "Troubleshooting",
        "dateFrom": "2024-01-01",
        "dateTo": "2024-12-31"
    }

    Response:
    {
        "query": "How do I restart a pod?",
        "results": [
            {
                "score": 0.95,
                "text": "chunk text...",
                "chunk_id": 123,
                "doc_id": 456,
                "department": "Platform",
                "category": "Troubleshooting"
            }
        ],
        "latency_ms": 125,
        "result_count": 1
    }
    """
    if not query or len(query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        start_time = time.time()

        # Build filters
        filters = {}
        if department:
            filters['department'] = department
        if category:
            filters['category'] = category
        if dateFrom:
            filters['dateFrom'] = dateFrom
        if dateTo:
            filters['dateTo'] = dateTo

        # Search in vector store with filters
        results = search_chunks(query, top_k=top_k, filters=filters if filters else None)

        latency_ms = int((time.time() - start_time) * 1000)

        response = {
            "query": query,
            "results": results,
            "latency_ms": latency_ms,
            "result_count": len(results),
            "search_type": "vector-semantic"
        }

        # Record metrics
        MetricsCollector.record_latency(latency_ms)
        MetricsCollector.record_embedding_hit()  # Track search as query

        # Estimate tokens: ~1 token per word in query + ~50 tokens per result
        input_tokens = len(query.split()) + 10  # Query tokens + buffer
        output_tokens = len(results) * 50 if results else 0
        MetricsCollector.record_tokens(input_tokens, output_tokens)

        if results:
            MetricsCollector.record_retrieval_hit()
        else:
            MetricsCollector.record_retrieval_miss()

        return response

    except HTTPException:
        raise
    except Exception as e:
        MetricsCollector.record_retrieval_miss()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    try:
        documents = db_client.list_documents()
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: int):
    """Get chunks for a specific document."""
    try:
        chunks = db_client.get_chunks(doc_id)
        return {
            "doc_id": doc_id,
            "chunks": chunks,
            "count": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {str(e)}")


@router.post("/search/rebuild")
async def rebuild_vector_store():
    """Rebuild the vector store from database."""
    try:
        vs = get_vector_store(reset=True)
        load_vector_store_from_db(vs)
        return {
            "status": "success",
            "message": "Vector store rebuilt",
            "chunks_loaded": vs.size()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild: {str(e)}")


@router.post("/generate")
async def generate(
    query: str,
    top_k: int = 10,
    department: str = None,
    category: str = None,
    dateFrom: str = None,
    dateTo: str = None,
    stream: bool = False
):
    """Search documents and generate an LLM answer using Groq.

    Returns either streamed or complete answer based on 'stream' parameter.
    """
    if not query or len(query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        start_time = time.time()

        # Build filters
        filters = {}
        if department:
            filters['department'] = department
        if category:
            filters['category'] = category
        if dateFrom:
            filters['dateFrom'] = dateFrom
        if dateTo:
            filters['dateTo'] = dateTo

        # Search for relevant documents
        results = search_chunks(query, top_k=top_k, filters=filters if filters else None)

        if not results:
            return {
                "query": query,
                "answer": "No relevant documents found. Please refine your search query.",
                "sources": [],
                "latency_ms": int((time.time() - start_time) * 1000)
            }

        # Generate answer using Groq with streaming
        if stream:
            async def generate_stream():
                for chunk in stream_answer(query, results):
                    yield chunk

            return StreamingResponse(generate_stream(), media_type="text/event-stream")

        # Non-streaming response
        answer = generate_answer(query, results)
        latency_ms = int((time.time() - start_time) * 1000)

        response = {
            "query": query,
            "answer": answer,
            "sources": results[:3],  # Top 3 sources
            "latency_ms": latency_ms,
            "result_count": len(results)
        }

        # Record metrics
        MetricsCollector.record_latency(latency_ms)
        MetricsCollector.record_retrieval_hit() if results else MetricsCollector.record_retrieval_miss()
        tokens = len(query.split()) + len(answer.split())
        MetricsCollector.record_tokens(len(query.split()), len(answer.split()))

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
