import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.generation import router as generation_router
from backend.app.search.routes import router as search_router
from backend.app.api.routes import router as metrics_router

app = FastAPI(
    title="Technical Support Copilot RAG",
    description="Production-grade RAG system with semantic search and streaming generation",
    version="0.1.0",
)

# CORS middleware - allow frontend and all development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(generation_router)
app.include_router(search_router)
app.include_router(metrics_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    provider = os.getenv("GENERATION_PROVIDER", "huggingface")
    return {
        "status": "ok",
        "version": "0.1.0",
        "provider": provider,
    }


@app.get("/api/metrics")
async def metrics():
    """Get system performance metrics and cache statistics."""
    from backend.app.cache.metrics import MetricsCollector
    return MetricsCollector.get_metrics()


@app.get("/")
async def root():
    """Root endpoint with service info."""
    provider = os.getenv("GENERATION_PROVIDER", "huggingface")

    return {
        "service": "Technical Support Copilot RAG",
        "version": "0.1.0",
        "provider": provider,
        "endpoints": {
            "health": "GET /health",
            "generate": "POST /api/generate?provider=huggingface|groq|anthropic|ollama",
            "config": "GET /api/config",
            "metrics": "GET /api/metrics",
        },
        "setup": {
            "huggingface": "set HF_TOKEN=your-token (free at https://huggingface.co/settings/tokens)",
            "groq": "set GROQ_API_KEY=your-key (free at https://console.groq.com/)",
            "anthropic": "set ANTHROPIC_API_KEY=your-key (free at https://console.anthropic.com/)",
            "ollama": "Install from https://ollama.ai/ and run: ollama serve",
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
