from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import time
import logging
from backend.app.search.hybrid_search import HybridSearchService
from backend.app.database.postgres import db_client
from backend.app.cache.metrics import MetricsCollector
from backend.app.generation.service import generate_answer, stream_answer
from backend.app.validation import validate_search_query, validate_filters
from backend.app.auth import require_auth, require_demo_mode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])

# Global hybrid search service (initialized on first use)
_hybrid_search_service = None

def get_hybrid_search_service() -> HybridSearchService:
    """Get or create hybrid search service instance (singleton)."""
    global _hybrid_search_service
    if _hybrid_search_service is None:
        logger.info("Initializing HybridSearchService")
        _hybrid_search_service = HybridSearchService()
        logger.info(f"HybridSearchService ready: {_hybrid_search_service.get_index_stats()}")
    return _hybrid_search_service


async def search_chunks(query: str, top_k: int = 10, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Search chunks using hybrid search (pgvector + BM25 with RRF fusion).

    Returns full result dict including chunks, confidence_score, and metadata.
    """
    try:
        hybrid_search = get_hybrid_search_service()

        metadata_filter = None
        if filters:
            metadata_filter = {}
            if filters.get('department'):
                metadata_filter['department'] = filters['department']
            if filters.get('category'):
                metadata_filter['category'] = filters['category']
            if filters.get('dateFrom'):
                metadata_filter['dateFrom'] = filters['dateFrom']
            if filters.get('dateTo'):
                metadata_filter['dateTo'] = filters['dateTo']

        result = await hybrid_search.search(query, top_k=top_k, metadata_filter=metadata_filter)
        # Return full result dict with chunks, confidence_score, etc.
        return result
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        return {
            'chunks': [],
            'confidence_score': 0.0,
            'num_results': 0,
            'error': str(e)
        }


@router.post("/search")
async def search_endpoint(
    query: str,
    top_k: int = 10,
    department: str = None,
    category: str = None,
    dateFrom: str = None,
    dateTo: str = None,
    api_key: Optional[str] = Depends(require_auth) if not require_demo_mode() else None,
):
    """Search using hybrid search (pgvector HNSW + BM25) with RRF fusion."""
    is_valid, error = validate_search_query(query)
    if not is_valid:
        logger.warning(f"Invalid search query: {error}")
        raise HTTPException(status_code=400, detail=error)

    try:
        start_time = time.time()

        filters = {}
        if department:
            filters['department'] = department
        if category:
            filters['category'] = category
        if dateFrom:
            filters['dateFrom'] = dateFrom
        if dateTo:
            filters['dateTo'] = dateTo

        is_valid, error = validate_filters({**filters, 'top_k': top_k})
        if not is_valid:
            logger.warning(f"Invalid filters: {error}")
            raise HTTPException(status_code=400, detail=error)

        logger.info(f"Hybrid search: {query[:50]}...")

        search_result = await search_chunks(query, top_k=top_k, filters=filters if filters else None)
        results = search_result.get('chunks', [])
        latency_ms = int((time.time() - start_time) * 1000)

        response = {
            "query": query,
            "results": results,
            "search_type": "hybrid",
            "confidence_score": search_result.get('confidence_score', 0.0),
            "latency_ms": latency_ms,
            "result_count": len(results)
        }

        MetricsCollector.record_latency(latency_ms)
        MetricsCollector.record_embedding_hit()
        input_tokens = len(query.split()) + 10
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
        logger.error(f"Search failed: {e}")
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
async def rebuild_vector_index():
    """Rebuild the vector index from database."""
    try:
        hybrid_search = get_hybrid_search_service()
        chunks = db_client.get_chunks_with_filters()
        if chunks:
            hybrid_search.index_chunks(chunks)
            return {
                "status": "success",
                "message": "Vector index rebuilt",
                "chunks_indexed": len(chunks)
            }
        return {
            "status": "success",
            "message": "No chunks to index",
            "chunks_indexed": 0
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
    """Search and generate LLM answer using Groq with hybrid search."""
    if not query or len(query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        start_time = time.time()

        filters = {}
        if department:
            filters['department'] = department
        if category:
            filters['category'] = category
        if dateFrom:
            filters['dateFrom'] = dateFrom
        if dateTo:
            filters['dateTo'] = dateTo

        search_result = await search_chunks(query, top_k=top_k, filters=filters if filters else None)
        results = search_result.get('chunks', [])
        confidence_score = search_result.get('confidence_score', 0.0)

        if not results:
            return {
                "query": query,
                "answer": "No relevant documents found. Please refine your search query.",
                "sources": [],
                "confidence_score": 0.0,
                "latency_ms": int((time.time() - start_time) * 1000)
            }

        if stream:
            async def generate_stream():
                for chunk in stream_answer(query, results):
                    yield chunk

            return StreamingResponse(generate_stream(), media_type="text/event-stream")

        answer = generate_answer(query, results)
        latency_ms = int((time.time() - start_time) * 1000)

        response = {
            "query": query,
            "answer": answer,
            "sources": results[:3],
            "confidence_score": confidence_score,
            "latency_ms": latency_ms,
            "result_count": len(results)
        }

        MetricsCollector.record_latency(latency_ms)
        MetricsCollector.record_embedding_hit()
        MetricsCollector.record_retrieval_hit() if results else MetricsCollector.record_retrieval_miss()
        MetricsCollector.record_tokens(len(query.split()), len(answer.split()))

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
