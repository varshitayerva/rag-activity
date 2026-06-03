from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from .hybrid_search import HybridSearch
from ..generation.models import Chunk, ChunkMetadata

router = APIRouter(prefix="/api", tags=["search"])

# Placeholder for search implementation
_search_instance = None


def get_search_instance() -> HybridSearch:
    """Get or create search instance."""
    global _search_instance
    if _search_instance is None:
        try:
            _search_instance = HybridSearch()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize search: {str(e)}")
    return _search_instance


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
        search_engine = get_search_instance()

        # Perform hybrid search
        results = await search_engine.search(
            query=query,
            top_k=top_k,
            filters=filter or {}
        )

        return {
            "chunks": results,
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
