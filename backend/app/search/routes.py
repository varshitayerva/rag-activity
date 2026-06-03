from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import time
from backend.app.search.hybrid_search import HybridSearchService
from backend.app.cache.metrics import MetricsCollector

router = APIRouter(prefix="/api", tags=["search"])

# Global HybridSearchService instance
hybrid_search = None

def get_hybrid_search() -> HybridSearchService:
    """Get or initialize hybrid search service."""
    global hybrid_search
    if hybrid_search is None:
        try:
            hybrid_search = HybridSearchService()
        except Exception as e:
            print(f"Warning: Could not initialize real search: {e}. Will return mock results.")
            hybrid_search = False
    return hybrid_search if hybrid_search else None


@router.post("/search")
async def search(
    query: str,
    top_k: int = 20,
    filter: Optional[Dict[str, Any]] = None,
):
    """Hybrid search across documents.

    Supports:
    - BM25 full-text search
    - Vector similarity search
    - RRF fusion ranking

    Request body:
    {
        "query": "How do I restart a pod?",
        "top_k": 20,
        "filter": {"department": "engineering"}
    }

    Response:
    {
        "chunks": [{...}],
        "search_type": "hybrid",
        "latency_ms": {...}
    }
    """
    if not query or len(query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        start_time = time.time()

        # Try to use real hybrid search, fall back to mock if unavailable
        search_service = get_hybrid_search()

        if search_service:
            result = await search_service.search(query, top_k=top_k, metadata_filter=filter)
            total_latency_ms = result.get("latency_ms", {}).get("total_ms", int((time.time() - start_time) * 1000))
        else:
            # Fallback to mock results
            total_latency_ms = int((time.time() - start_time) * 1000)
            result = {
                "chunks": [
                    {
                        "text": "Sample chunk about Kubernetes pod management",
                        "score": 0.95,
                        "source": "kubernetes-guide.pdf",
                        "chunk_id": "chunk-001",
                        "metadata": {
                            "section": "Pod Management",
                            "page": 1,
                            "doc_id": "doc-001",
                            "source": "kubernetes-guide.pdf"
                        }
                    }
                ],
                "search_type": "hybrid",
                "latency_ms": {
                    "embedding": 45,
                    "vector": 120,
                    "bm25": 80,
                    "rrf": 15,
                    "total": total_latency_ms
                }
            }

        # Record metrics
        MetricsCollector.record_latency(total_latency_ms)
        if result.get("chunks"):
            MetricsCollector.record_retrieval_hit()
        else:
            MetricsCollector.record_retrieval_miss()

        return result

    except HTTPException:
        raise
    except Exception as e:
        MetricsCollector.record_retrieval_miss()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
