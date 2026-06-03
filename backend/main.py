from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import os
from app.search.hybrid_search import HybridSearchService

# Initialize FastAPI app
app = FastAPI(
    title="FDE RAG Search API",
    description="Hybrid search API combining vector (Qdrant) and BM25 search with RRF fusion",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search service
qdrant_storage_path = os.getenv("QDRANT_STORAGE_PATH", "./qdrant_storage")
openai_api_key = os.getenv("OPENAI_API_KEY")

try:
    search_service = HybridSearchService(
        qdrant_storage_path=qdrant_storage_path,
        openai_api_key=openai_api_key
    )
except Exception as e:
    print(f"Warning: Failed to initialize search service: {e}")
    search_service = None


# ============ Request/Response Models ============

class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., description="Search query string")
    top_k: int = Field(default=20, ge=1, le=100, description="Number of results to return")
    search_type: Literal["vector", "bm25", "hybrid"] = Field(
        default="hybrid",
        description="Search method: 'vector' (semantic), 'bm25' (keyword), 'hybrid' (both with RRF fusion)"
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters (department, category, etc.)"
    )


class ChunkResult(BaseModel):
    """Individual search result chunk."""
    chunk_id: str
    text: str
    doc_id: str
    filename: str
    section: str
    page: int
    department: str
    category: str
    score: float
    rank: int


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    query: str
    chunks: List[ChunkResult]
    search_type: str
    num_results: int
    latency_ms: Dict[str, int]


class IndexChunk(BaseModel):
    """Chunk data for indexing."""
    chunk_id: str
    text: str
    doc_id: str = ""
    filename: str = ""
    section: str = ""
    page: int = 0
    department: str = ""
    category: str = ""
    uploaded_at: str = ""


class IndexRequest(BaseModel):
    """Request model for indexing endpoint."""
    chunks: List[IndexChunk] = Field(..., description="List of chunks to index")


class IndexResponse(BaseModel):
    """Response model for indexing endpoint."""
    status: str
    num_chunks_indexed: int


class StatsResponse(BaseModel):
    """Response model for stats endpoint."""
    qdrant_documents: int
    bm25_documents: int
    vector_dimension: int
    embedding_model: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service_initialized: bool


# ============ Endpoints ============

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service_initialized": search_service is not None
    }


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest):
    """
    Perform search with configurable search type.

    - **query**: Search query string
    - **top_k**: Number of results (1-100)
    - **search_type**: "vector" (semantic), "bm25" (keyword), or "hybrid" (RRF fusion, default)
    - **metadata_filter**: Optional metadata filters
    """
    if search_service is None:
        raise HTTPException(status_code=503, detail="Search service not initialized")

    try:
        if request.search_type == "hybrid":
            # Hybrid search with RRF fusion
            result = await search_service.search(
                query=request.query,
                top_k=request.top_k,
                metadata_filter=request.metadata_filter
            )
        elif request.search_type == "vector":
            # Vector-only search
            import time
            latency = {}
            start_time = time.time()

            embed_start = time.time()
            query_embedding = search_service.embeddings.embed_query(request.query)
            latency['embedding_ms'] = int((time.time() - embed_start) * 1000)

            vector_start = time.time()
            results = search_service.vector_db.search(query_embedding, top_k=request.top_k)
            latency['vector_search_ms'] = int((time.time() - vector_start) * 1000)

            latency['total_ms'] = int((time.time() - start_time) * 1000)

            result = {
                'query': request.query,
                'chunks': results,
                'search_type': 'vector',
                'num_results': len(results),
                'latency_ms': latency,
            }
        elif request.search_type == "bm25":
            # BM25-only search
            import time
            latency = {}
            start_time = time.time()

            bm25_start = time.time()
            results = search_service.bm25.search(request.query, top_k=request.top_k)
            latency['bm25_search_ms'] = int((time.time() - bm25_start) * 1000)

            latency['total_ms'] = int((time.time() - start_time) * 1000)

            result = {
                'query': request.query,
                'chunks': results,
                'search_type': 'bm25',
                'num_results': len(results),
                'latency_ms': latency,
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown search_type: {request.search_type}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/index", response_model=IndexResponse, tags=["Indexing"])
async def index_chunks(request: IndexRequest):
    """
    Index new chunks in both Qdrant (vector) and BM25 (keyword).

    Chunks will be embedded using OpenAI embeddings and indexed for hybrid search.
    """
    if search_service is None:
        raise HTTPException(status_code=503, detail="Search service not initialized")

    try:
        # Convert Pydantic models to dicts for the service
        chunks = [chunk.dict() for chunk in request.chunks]

        # Index chunks (synchronous operation)
        search_service.index_chunks(chunks)

        return {
            "status": "success",
            "num_chunks_indexed": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.get("/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats():
    """Get statistics about the indexed data."""
    if search_service is None:
        raise HTTPException(status_code=503, detail="Search service not initialized")

    try:
        stats = search_service.get_index_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.delete("/index", tags=["Indexing"])
async def clear_index():
    """
    Delete and reset the entire search index.

    WARNING: This will delete all indexed data. Use with caution.
    """
    if search_service is None:
        raise HTTPException(status_code=503, detail="Search service not initialized")

    try:
        search_service.vector_db.delete_collection()
        search_service.bm25 = None  # Reset BM25 index
        return {
            "status": "success",
            "message": "Index cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}")


# ============ Startup/Shutdown ============

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print(f"FastAPI server starting...")
    if search_service:
        print(f"Search service initialized with Qdrant storage: {qdrant_storage_path}")
    else:
        print("Warning: Search service not initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    print("FastAPI server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
