from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import time
from backend.app.search.vector_store import get_vector_store
from backend.app.database.postgres import db_client
from backend.app.cache.metrics import MetricsCollector

router = APIRouter(prefix="/api", tags=["search"])

def search_chunks(query: str, top_k: int = 10) -> list:
    """Search chunks using vector similarity."""
    try:
        # Get vector store
        vs = get_vector_store()

        # If vector store is empty, load from database
        if vs.size() == 0:
            print("Vector store empty, loading from database...")
            load_vector_store_from_db(vs)

        # Search
        results = vs.search(query, top_k=top_k)
        return results
    except Exception as e:
        print(f"Vector search error: {e}")
        return []


def load_vector_store_from_db(vs):
    """Load all chunks from database into vector store."""
    try:
        chunks = db_client.get_all_chunks()
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
                'section': chunk.get('section'),
                'page_number': chunk.get('page_number')
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
    filter: Optional[Dict[str, Any]] = None,
):
    """Search across documents using vector embeddings.

    Real-time semantic search using sentence-transformers.

    Request:
    {
        "query": "How do I restart a pod?",
        "top_k": 10
    }

    Response:
    {
        "query": "How do I restart a pod?",
        "results": [
            {
                "score": 0.95,
                "text": "chunk text...",
                "chunk_id": 123,
                "doc_id": 456
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

        # Search in vector store
        results = search_chunks(query, top_k=top_k)

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
