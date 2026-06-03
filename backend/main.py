from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.generation import router as generation_router

app = FastAPI(
    title="Technical Support Copilot RAG",
    description="Production RAG system with semantic search and streaming generation",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(generation_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Technical Support Copilot",
        "version": "0.1.0",
        "endpoints": {
            "health": "GET /health",
            "generate": "POST /api/generate",
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
