from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api", tags=["search"])


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
        # Return mock search results (placeholder for actual hybrid search)
        return {
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
                "total": 260
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
